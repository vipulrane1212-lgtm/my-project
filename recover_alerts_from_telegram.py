#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Recover alerts from Telegram channel and add them to kpi_logs.json

This script fetches alert messages from your Telegram alert channel
and adds any missing alerts to kpi_logs.json
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
                    # Use first group as default
                    ALERT_CHAT_ID = str(groups[0].get("id", groups[0]))
                    print(f"Using alert channel from alert_groups.json: {ALERT_CHAT_ID}")
    except Exception as e:
        print(f"Could not load alert_groups.json: {e}")

# Fallback to solboy_calls channel (you may need to update this)
if not ALERT_CHAT_ID:
    ALERT_CHAT_ID = "-1002782074434"  # Update this to your actual alert channel ID
    print(f"Using default alert channel: {ALERT_CHAT_ID}")

API_ID = int(os.getenv("API_ID", "25177061"))
API_HASH = os.getenv("API_HASH", "c11ea2f1db2aa742144dfa2a30448408")

# CRITICAL: Use a SEPARATE session file to avoid conflicts with Railway!
# Railway uses "railway_production_session" - we use a different one for recovery
SESSION_NAME = os.getenv("RECOVERY_SESSION_NAME", "recovery_session")

KPI_LOGS_FILE = Path("kpi_logs.json")


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
        
        # Extract confirmations
        confirmations = {}
        confirmation_lines = re.findall(r'✓\s*([^\n]+)', text)
        confirmation_count = len(confirmation_lines)
        if confirmation_count > 0:
            confirmations = {
                "total": confirmation_count,
                "details": confirmation_lines
            }
        
        # Check for Glydo
        glydo_in_top5 = "Glydo Top 5" in text or "glydo" in text.lower()
        
        # Check for Hot List
        hot_list_match = re.search(r'Hot List:\s*([🟢🔴])\s*(Yes|No)', text)
        hot_list = False
        if hot_list_match:
            hot_list = "🟢" in hot_list_match.group(0) or "Yes" in hot_list_match.group(0)
        
        if not token and not contract:
            return None  # Can't create alert without token or contract
        
        return {
            "timestamp": message_date.isoformat(),
            "level": level,
            "token": token or "UNKNOWN",
            "contract": contract,
            "tier": tier,
            "mc_usd": mcap,
            "current_mcap": mcap,
            "glydo_in_top5": glydo_in_top5,
            "hot_list": hot_list,
            "confirmations": confirmations,
            "matched_signals": [],
            "tags": [],
            "recovered": True,  # Mark as recovered
            "recovered_at": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        print(f"⚠️ Error parsing alert: {e}")
        return None


async def fetch_telegram_alerts(limit: int = 500) -> List[Dict]:
    """Fetch alert messages from Telegram channel."""
    if not TELEGRAM_AVAILABLE:
        print("[ERROR] telethon not available. Cannot fetch Telegram alerts.")
        return []
    
    try:
        # Use separate recovery session to avoid conflicts with Railway
        print(f"Using recovery session: {SESSION_NAME}")
        print("NOTE: This uses a separate session file to avoid conflicts with Railway")
        print("If this is your first time, you'll need to authenticate.")
        print()
        
        client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        await client.start()
        
        print(f"Fetching last {limit} messages from Telegram channel {ALERT_CHAT_ID}...")
        
        alerts = []
        count = 0
        async for message in client.iter_messages(int(ALERT_CHAT_ID), limit=limit):
            if message.text and ("ALPHA INCOMING" in message.text or "TIER" in message.text):
                parsed = parse_alert_from_message(message.text, message.date)
                if parsed:
                    alerts.append(parsed)
                    count += 1
                    if count % 10 == 0:
                        print(f"  Found {count} alerts...")
        
        await client.disconnect()
        print(f"[OK] Found {len(alerts)} alert messages in Telegram")
        return alerts
    
    except Exception as e:
        print(f"[ERROR] Error fetching Telegram alerts: {e}")
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
            print(f"⚠️ Error loading kpi_logs.json: {e}")
    return {"alerts": [], "true_positives": [], "false_positives": []}


def save_kpi_logs(data: Dict):
    """Save kpi_logs.json."""
    try:
        with open(KPI_LOGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved {len(data.get('alerts', []))} alerts to kpi_logs.json")
    except Exception as e:
        print(f"❌ Error saving kpi_logs.json: {e}")
        raise


def find_existing_alert(telegram_alert: Dict, existing_alerts: List[Dict]) -> Optional[Dict]:
    """Check if alert already exists in kpi_logs.json."""
    telegram_token = telegram_alert.get("token", "").upper()
    telegram_contract = telegram_alert.get("contract", "")
    telegram_timestamp = telegram_alert.get("timestamp", "")
    
    for existing in existing_alerts:
        existing_token = existing.get("token", "").upper()
        existing_contract = existing.get("contract", "")
        existing_timestamp = existing.get("timestamp", "")
        
        # Match by contract (most reliable)
        if telegram_contract and existing_contract:
            if telegram_contract == existing_contract:
                return existing
        
        # Match by token + timestamp (within 1 hour)
        if telegram_token and existing_token:
            if telegram_token == existing_token:
                try:
                    tg_time = datetime.fromisoformat(telegram_timestamp.replace('Z', '+00:00'))
                    ex_time = datetime.fromisoformat(existing_timestamp.replace('Z', '+00:00'))
                    time_diff = abs((tg_time - ex_time).total_seconds())
                    if time_diff < 3600:  # Within 1 hour
                        return existing
                except:
                    pass
    
    return None


async def main():
    """Main recovery function."""
    print("="*80)
    print("RECOVER ALERTS FROM TELEGRAM")
    print("="*80)
    
    # Load existing alerts
    kpi_data = load_kpi_logs()
    existing_alerts = kpi_data.get("alerts", [])
    print(f"\nCurrent alerts in kpi_logs.json: {len(existing_alerts)}")
    
    # Fetch alerts from Telegram
    telegram_alerts = await fetch_telegram_alerts(limit=500)
    
    if not telegram_alerts:
        print("❌ No alerts found in Telegram channel")
        return
    
    # Find missing alerts
    new_alerts = []
    for tg_alert in telegram_alerts:
        existing = find_existing_alert(tg_alert, existing_alerts)
        if not existing:
            new_alerts.append(tg_alert)
    
    print(f"\nFound {len(new_alerts)} new alerts to add")
    
    if not new_alerts:
        print("[OK] All alerts already in kpi_logs.json!")
        return
    
    # Show preview
    print("\nNew alerts to add:")
    for i, alert in enumerate(new_alerts[:10], 1):
        token = alert.get("token", "UNKNOWN")
        tier = alert.get("tier", "?")
        timestamp = alert.get("timestamp", "")[:10]
        print(f"  {i}. {token} - Tier {tier} - {timestamp}")
    
    if len(new_alerts) > 10:
        print(f"  ... and {len(new_alerts) - 10} more")
    
    # Ask for confirmation
    print(f"\n⚠️  This will add {len(new_alerts)} alerts to kpi_logs.json")
    response = input("Continue? (y/n): ").strip().lower()
    
    if response != 'y':
        print("❌ Cancelled")
        return
    
    # Add new alerts
    all_alerts = existing_alerts + new_alerts
    
    # Sort by timestamp (newest first)
    all_alerts.sort(
        key=lambda x: datetime.fromisoformat(x.get("timestamp", "2000-01-01").replace("Z", "+00:00")),
        reverse=True
    )
    
    kpi_data["alerts"] = all_alerts
    kpi_data["last_updated"] = datetime.now(timezone.utc).isoformat()
    
    # Save
    save_kpi_logs(kpi_data)
    
    print(f"\n[OK] Recovery complete! Added {len(new_alerts)} alerts")
    print(f"Total alerts now: {len(all_alerts)}")
    print("\nNext step: Commit to Git and push:")
    print("   git add kpi_logs.json")
    print("   git commit -m 'Recover alerts from Telegram'")
    print("   git push origin main")


if __name__ == "__main__":
    asyncio.run(main())

