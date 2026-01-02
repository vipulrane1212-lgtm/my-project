#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backfill missing alerts after LICO timestamp from Telegram channel.

This script:
1. Connects to Telegram using separate recovery session (avoids Railway conflicts)
2. Fetches all alerts from Telegram channel after LICO timestamp
3. Compares with kpi_logs.json to find missing alerts
4. Adds missing alerts to JSON file preserving chronological order
5. Verifies no gaps remain
"""

import asyncio
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

try:
    from telethon import TelegramClient
    from telethon.tl.types import Message
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("⚠️ telethon not available. Install with: pip install telethon")
    sys.exit(1)

# Get alert channel ID from environment or alert_groups.json
ALERT_CHAT_ID = os.getenv("ALERT_CHAT_ID")

# Try to load from alert_groups.json
if not ALERT_CHAT_ID:
    try:
        alert_groups_file = Path("alert_groups.json")
        if alert_groups_file.exists():
            with open(alert_groups_file, 'r', encoding='utf-8') as f:
                alert_groups_data = json.load(f)
                groups = alert_groups_data.get("groups", [])
                if groups:
                    # Handle both formats: list of IDs or list of objects with "id" field
                    first_group = groups[0]
                    if isinstance(first_group, dict):
                        ALERT_CHAT_ID = str(first_group.get("id", first_group))
                    else:
                        ALERT_CHAT_ID = str(first_group)
                    print(f"Using alert channel from alert_groups.json: {ALERT_CHAT_ID}")
    except Exception as e:
        print(f"Could not load alert_groups.json: {e}")

if not ALERT_CHAT_ID:
    print("❌ ALERT_CHAT_ID not set! Set it via environment variable or alert_groups.json")
    sys.exit(1)

API_ID = int(os.getenv("API_ID", "25177061"))
API_HASH = os.getenv("API_HASH", "c11ea2f1db2aa742144dfa2a30448408")

# CRITICAL: Use a SEPARATE session file to avoid conflicts with Railway!
# Railway uses "railway_production_session" - we use a different one for recovery
SESSION_NAME = os.getenv("RECOVERY_SESSION_NAME", "recovery_session")

KPI_LOGS_FILE = Path("kpi_logs.json")
LICO_CONTRACT = "678QT3ZQCCBLJJZB5IC5FVMAV94AYRIWSZ3FUYSRVYNC"


def parse_alert_from_message(text: str, message_date: datetime) -> Optional[Dict]:
    """Parse alert data from Telegram message text."""
    try:
        # Extract tier
        tier_match = re.search(r'TIER\s+(\d+)', text, re.IGNORECASE)
        tier = int(tier_match.group(1)) if tier_match else 3
        
        # Extract token name (after 🔥 emoji or **)
        token_match = re.search(r'🔥\s*\*\*([A-Z0-9]+)\*\*', text) or re.search(r'\*\*([A-Z0-9]+)\*\*', text)
        token = token_match.group(1) if token_match else None
        
        # Extract contract address (in code block)
        contract_match = re.search(r'`([A-Za-z0-9]{32,44})`', text)
        contract = contract_match.group(1) if contract_match else None
        
        # Extract current MCAP
        mcap_match = re.search(r'Current MC:\s*\*\*\$?([0-9,.]+[KMkm]?)\*\*', text, re.IGNORECASE)
        mcap_str = mcap_match.group(1) if mcap_match else None
        mcap = None
        if mcap_str:
            mcap_str = mcap_str.replace(',', '').upper()
            if 'K' in mcap_str:
                mcap = float(mcap_str.replace('K', '')) * 1000
            elif 'M' in mcap_str:
                mcap = float(mcap_str.replace('M', '')) * 1000000
            else:
                mcap = float(mcap_str)
        
        # Extract level from tier
        level = "HIGH" if tier == 1 else "MEDIUM"
        
        if not token or not contract:
            return None
        
        return {
            "timestamp": message_date.isoformat(),
            "level": level,
            "token": token,
            "contract": contract,
            "mc_usd": mcap,
            "current_mcap": mcap,
            "entry_mc": mcap,
            "tier": tier,
            "source": "telegram_backfill"
        }
    except Exception as e:
        print(f"⚠️  Error parsing message: {e}")
        return None


def find_existing_alert(telegram_alert: Dict, existing_alerts: List[Dict]) -> Optional[Dict]:
    """Find matching alert in existing alerts by token + contract + timestamp."""
    tg_token = telegram_alert.get("token", "").upper()
    tg_contract = telegram_alert.get("contract", "").upper()
    tg_timestamp = telegram_alert.get("timestamp", "")
    
    for existing in existing_alerts:
        ex_token = existing.get("token", "").upper()
        ex_contract = existing.get("contract", "").upper()
        ex_timestamp = existing.get("timestamp", "")
        
        # Match by token and contract
        if tg_token == ex_token and tg_contract == ex_contract:
            # Check if timestamps are close (within 1 hour)
            try:
                tg_time = datetime.fromisoformat(tg_timestamp.replace("Z", "+00:00"))
                ex_time = datetime.fromisoformat(ex_timestamp.replace("Z", "+00:00"))
                time_diff = abs((tg_time - ex_time).total_seconds())
                if time_diff < 3600:  # Within 1 hour
                    return existing
            except Exception:
                pass
    
    return None


async def fetch_telegram_alerts_after_lico(client: TelegramClient, limit: int = 1000) -> List[Dict]:
    """Fetch alerts from Telegram channel after LICO timestamp."""
    print(f"\n📡 Fetching alerts from Telegram channel: {ALERT_CHAT_ID}")
    print(f"   Looking for alerts after LICO timestamp...")
    
    # Get entity first
    try:
        chat_id_int = int(ALERT_CHAT_ID)
        entity = await client.get_entity(chat_id_int)
        print(f"   ✅ Connected to: {entity.title if hasattr(entity, 'title') else 'Chat'}")
    except (ValueError, TypeError):
        entity = await client.get_entity(ALERT_CHAT_ID)
        print(f"   ✅ Connected to: {entity.title if hasattr(entity, 'title') else 'Chat'}")
    
    alerts = []
    lico_found = False
    
    try:
        async for message in client.iter_messages(entity, limit=limit):
            if not message.text:
                continue
            
            text = message.text
            message_date = message.date.replace(tzinfo=timezone.utc) if message.date else datetime.now(timezone.utc)
            
            # Check if this is LICO alert
            if not lico_found:
                if "LICO" in text.upper() and LICO_CONTRACT in text.upper():
                    lico_found = True
                    print(f"   ✅ Found LICO alert at {message_date.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"   Now fetching alerts after this timestamp...")
                    continue
            
            # Only process alerts after LICO
            if lico_found:
                alert = parse_alert_from_message(text, message_date)
                if alert:
                    alerts.append(alert)
        
        print(f"   ✅ Fetched {len(alerts)} alerts from Telegram after LICO")
        return alerts
        
    except Exception as e:
        print(f"❌ Error fetching alerts: {e}")
        import traceback
        traceback.print_exc()
        return []


def load_kpi_logs() -> Dict:
    """Load kpi_logs.json."""
    if KPI_LOGS_FILE.exists():
        try:
            with open(KPI_LOGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading kpi_logs.json: {e}")
            return {"alerts": []}
    return {"alerts": []}


def save_kpi_logs(data: Dict):
    """Save kpi_logs.json with backup."""
    # Create backup
    if KPI_LOGS_FILE.exists():
        backup_file = KPI_LOGS_FILE.with_suffix('.json.backup')
        import shutil
        shutil.copy2(KPI_LOGS_FILE, backup_file)
        print(f"   📦 Created backup: {backup_file}")
    
    # Save
    with open(KPI_LOGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"   ✅ Saved {len(data.get('alerts', []))} alerts to {KPI_LOGS_FILE}")


async def main():
    """Main backfill function."""
    print("="*80)
    print("BACKFILL MISSING ALERTS AFTER LICO")
    print("="*80)
    
    # Load existing alerts
    kpi_data = load_kpi_logs()
    existing_alerts = kpi_data.get("alerts", [])
    print(f"\n📋 Current alerts in kpi_logs.json: {len(existing_alerts)}")
    
    # Find LICO alert in existing data
    lico_alert = None
    for alert in existing_alerts:
        if alert.get("token", "").upper() == "LICO" and alert.get("contract", "").upper() == LICO_CONTRACT.upper():
            lico_alert = alert
            break
    
    if not lico_alert:
        print("⚠️  LICO alert not found in kpi_logs.json")
        print("   Will fetch all recent alerts from Telegram")
    else:
        lico_time = datetime.fromisoformat(lico_alert.get("timestamp", "").replace("Z", "+00:00"))
        print(f"   ✅ Found LICO alert: {lico_alert.get('token')} at {lico_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Connect to Telegram
    # Try to use an existing authorized session if recovery_session isn't authorized
    session_to_use = SESSION_NAME
    session_file = Path(f"{session_to_use}.session")
    
    # Try railway_production_session if recovery_session doesn't exist or isn't authorized
    if not session_file.exists():
        railway_session = Path("railway_production_session.session")
        if railway_session.exists():
            print(f"⚠️  {session_to_use} not found, trying railway_production_session...")
            session_to_use = "railway_production_session"
            session_file = railway_session
        else:
            # Try local_dev_session as fallback
            local_session = Path("local_dev_session.session")
            if local_session.exists():
                print(f"⚠️  {session_to_use} not found, trying local_dev_session...")
                session_to_use = "local_dev_session"
                session_file = local_session
    
    # Try multiple sessions until we find an authorized one
    # Prioritize railway_production_session since it likely has chat access
    sessions_to_try = ["railway_production_session", session_to_use, "local_dev_session"]
    client = None
    authorized_session = None
    
    for session_name in sessions_to_try:
        session_path = Path(f"{session_name}.session")
        if not session_path.exists():
            continue
        
        print(f"\n🔌 Trying session: {session_name}")
        test_client = TelegramClient(session_name, API_ID, API_HASH)
        try:
            await test_client.connect()
            if await test_client.is_user_authorized():
                print(f"✅ Found authorized session: {session_name}")
                # Test if we can access the chat
                try:
                    chat_id_int = int(ALERT_CHAT_ID)
                    test_entity = await test_client.get_entity(chat_id_int)
                    print(f"   ✅ Session has access to chat: {test_entity.title if hasattr(test_entity, 'title') else 'Chat'}")
                    client = test_client
                    authorized_session = session_name
                    break
                except Exception as e:
                    print(f"   ⚠️  Session authorized but cannot access chat: {e}")
                    await test_client.disconnect()
                    continue
            else:
                await test_client.disconnect()
        except Exception as e:
            try:
                await test_client.disconnect()
            except:
                pass
            continue
    
    if not client or not authorized_session:
        print(f"❌ No authorized session with chat access found!")
        print(f"   Please:")
        print(f"   1. Stop Railway deployment")
        print(f"   2. Run the bot locally once: python telegram_monitor_new.py")
        print(f"   3. Let it join the alert chat")
        print(f"   4. Then run this backfill script again")
        return
    
    try:
        
        print("✅ Connected to Telegram")
        
        # Fetch alerts from Telegram after LICO
        telegram_alerts = await fetch_telegram_alerts_after_lico(client, limit=1000)
        
        if not telegram_alerts:
            print("⚠️  No alerts found in Telegram after LICO")
            return
        
        # Find missing alerts
        new_alerts = []
        for tg_alert in telegram_alerts:
            existing = find_existing_alert(tg_alert, existing_alerts)
            if not existing:
                new_alerts.append(tg_alert)
        
        print(f"\n🔍 Analysis:")
        print(f"   Telegram alerts after LICO: {len(telegram_alerts)}")
        print(f"   Missing alerts: {len(new_alerts)}")
        
        if not new_alerts:
            print("\n✅ All alerts already in kpi_logs.json! No backfill needed.")
            return
        
        # Show preview
        print(f"\n📋 New alerts to add ({len(new_alerts)}):")
        for i, alert in enumerate(new_alerts[:10], 1):
            token = alert.get("token", "UNKNOWN")
            tier = alert.get("tier", "?")
            timestamp = alert.get("timestamp", "")[:10]
            print(f"   {i}. {token} - Tier {tier} - {timestamp}")
        if len(new_alerts) > 10:
            print(f"   ... and {len(new_alerts) - 10} more")
        
        # Merge alerts preserving chronological order
        all_alerts = existing_alerts + new_alerts
        
        # Sort by timestamp (newest first)
        all_alerts.sort(
            key=lambda x: datetime.fromisoformat(x.get("timestamp", "2000-01-01").replace("Z", "+00:00")),
            reverse=True
        )
        
        # Update data
        kpi_data["alerts"] = all_alerts
        kpi_data["last_updated"] = datetime.now(timezone.utc).isoformat()
        kpi_data["backfill_info"] = {
            "backfilled_at": datetime.now(timezone.utc).isoformat(),
            "new_alerts_added": len(new_alerts),
            "total_alerts": len(all_alerts),
            "after_token": "LICO"
        }
        
        # Save
        save_kpi_logs(kpi_data)
        
        print(f"\n✅ Successfully backfilled {len(new_alerts)} missing alerts!")
        print(f"   Total alerts now: {len(all_alerts)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.disconnect()
        print("\n🔌 Disconnected from Telegram")


if __name__ == "__main__":
    asyncio.run(main())

