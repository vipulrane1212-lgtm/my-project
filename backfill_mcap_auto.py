#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
backfill_mcap_auto.py

Automatically backfill market cap from Telegram posts using existing session.
"""

import json
import re
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone

try:
    from telethon import TelegramClient
    from telethon.tl.types import Message
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("ERROR: telethon not available. Install with: pip install telethon")


def parse_mcap_from_message(text: str) -> Optional[float]:
    """
    Parse market cap from Telegram alert message.
    Looks for patterns like:
    - "Current MC: $143.5K"
    - "Current MC: **$143.5K**"
    - "Current MC: $143500"
    """
    if not text:
        return None
    
    # Pattern 1: "Current MC: $143.5K" or "Current MC: **$143.5K**"
    patterns = [
        r'Current MC[:\s]+\*?\*?\$?([0-9,]+\.?[0-9]*)\s*([KMkm]?)\*?\*?',
        r'MC[:\s]+\*?\*?\$?([0-9,]+\.?[0-9]*)\s*([KMkm]?)\*?\*?',
        r'\$([0-9,]+\.?[0-9]*)\s*([KMkm]?)\s*MC',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value_str = match.group(1).replace(',', '')
            multiplier_str = match.group(2).upper() if len(match.groups()) > 1 and match.group(2) else ''
            
            try:
                value = float(value_str)
                
                # Apply multiplier
                if multiplier_str == 'K':
                    value *= 1000
                elif multiplier_str == 'M':
                    value *= 1000000
                
                return value
            except (ValueError, TypeError):
                continue
    
    return None


def match_alert_to_message(alert: Dict, message_text: str, message_date: datetime) -> bool:
    """Check if a message matches an alert based on token and timestamp."""
    alert_token = alert.get("token", "").upper()
    alert_timestamp = alert.get("timestamp", "")
    alert_contract = alert.get("contract", "")
    
    if not alert_token:
        return False
    
    # Check if token appears in message
    if alert_token.upper() not in message_text.upper():
        return False
    
    # Check if contract appears in message (more reliable)
    if alert_contract and len(alert_contract) > 8:
        contract_prefix = alert_contract[:8]
        if contract_prefix in message_text:
            return True
    
    # Check if timestamp is close (within 10 minutes)
    if alert_timestamp:
        try:
            alert_dt = datetime.fromisoformat(alert_timestamp.replace('Z', '+00:00'))
            time_diff = abs((message_date - alert_dt).total_seconds())
            if time_diff <= 600:  # 10 minutes
                return True
        except Exception:
            pass
    
    return False


async def fetch_telegram_messages(
    client: TelegramClient,
    chat_id: str,
    limit: int = 2000
) -> List[Tuple[str, datetime]]:
    """Fetch messages from Telegram channel/group."""
    messages = []
    
    try:
        # Convert to int if it's a numeric string
        try:
            chat_id_int = int(chat_id)
        except ValueError:
            chat_id_int = chat_id
        
        # Try to get entity first
        try:
            entity = await client.get_entity(chat_id_int)
            print(f"Fetching messages from {chat_id} ({getattr(entity, 'title', 'Unknown')})...")
        except Exception:
            print(f"Fetching messages from {chat_id}...")
            entity = chat_id_int
        
        count = 0
        async for message in client.iter_messages(entity, limit=limit):
            if message.text:
                messages.append((message.text, message.date))
                count += 1
                if count % 100 == 0:
                    print(f"  Fetched {count} messages...")
        print(f"Fetched {len(messages)} messages total")
    except Exception as e:
        print(f"Error fetching messages: {e}")
    
    return messages


def backfill_from_messages(
    kpi_data: Dict,
    telegram_messages: List[Tuple[str, datetime]]
) -> Dict:
    """Backfill MCAP from Telegram messages."""
    alerts = kpi_data.get("alerts", [])
    
    if not alerts:
        print("No alerts found in kpi_logs.json")
        return kpi_data
    
    print(f"\nFound {len(alerts)} alerts in kpi_logs.json")
    print(f"Found {len(telegram_messages)} Telegram messages")
    
    # Find alerts without MCAP
    alerts_without_mcap = [a for a in alerts if not a.get("mc_usd") and not a.get("entry_mc")]
    print(f"Found {len(alerts_without_mcap)} alerts without MCAP")
    
    if not alerts_without_mcap:
        print("All alerts already have MCAP!")
        return kpi_data
    
    # Match messages to alerts
    updated_count = 0
    matched_messages = []
    
    print("\nMatching messages to alerts...")
    for i, alert in enumerate(alerts_without_mcap):
        alert_token = alert.get("token", "")
        if not alert_token:
            continue
        
        # Find matching message
        for message_text, message_date in telegram_messages:
            if match_alert_to_message(alert, message_text, message_date):
                mcap = parse_mcap_from_message(message_text)
                if mcap:
                    alert["mc_usd"] = mcap
                    alert["mc_source"] = "telegram_post"
                    updated_count += 1
                    matched_messages.append((alert_token, mcap, message_date))
                    print(f"  [{i+1}/{len(alerts_without_mcap)}] {alert_token}: ${mcap:,.2f} (from {message_date.strftime('%Y-%m-%d %H:%M')})")
                    break
    
    # Update data
    kpi_data["alerts"] = alerts
    kpi_data["last_updated"] = datetime.now(timezone.utc).isoformat()
    kpi_data["backfill_info"] = {
        "backfilled_at": datetime.now(timezone.utc).isoformat(),
        "updated_count": updated_count,
        "total_alerts": len(alerts),
        "matched_messages": len(matched_messages)
    }
    
    print(f"\n{'='*60}")
    print(f"Backfill Summary:")
    print(f"  Updated: {updated_count} alerts")
    print(f"  Skipped: {len(alerts_without_mcap) - updated_count} alerts")
    print(f"  Total: {len(alerts)} alerts")
    print(f"{'='*60}")
    
    return kpi_data


def load_kpi_logs(file_path: str = "kpi_logs.json") -> Dict:
    """Load KPI logs from file."""
    log_file = Path(file_path)
    if not log_file.exists():
        print(f"File not found: {file_path}")
        return {}
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return {}


def save_kpi_logs(data: Dict, file_path: str = "kpi_logs.json"):
    """Save KPI logs to file."""
    log_file = Path(file_path)
    try:
        # Create backup
        backup_path = log_file.with_suffix('.json.backup')
        if log_file.exists():
            import shutil
            shutil.copy2(log_file, backup_path)
            print(f"\nBackup created: {backup_path}")
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Saved to {file_path}")
    except Exception as e:
        print(f"Error saving {file_path}: {e}")


async def main():
    """Main function."""
    print("="*60)
    print("Auto Backfilling Market Cap from Telegram Posts")
    print("="*60)
    
    if not TELEGRAM_AVAILABLE:
        print("ERROR: telethon is required. Install with: pip install telethon")
        return
    
    # Load KPI logs
    kpi_data = load_kpi_logs()
    if not kpi_data:
        return
    
    # Find session file
    session_files = list(Path('.').glob('*.session'))
    if not session_files:
        print("ERROR: No .session file found. Please run telegram_monitor_new.py first to create a session.")
        return
    
    # Use user session (not bot_session) - bots can't use get_dialogs
    session_file = None
    for sf in session_files:
        if 'bot_session' not in sf.name and 'blackhat' in sf.name:
            session_file = sf
            break
    if not session_file:
        # Use first non-bot session
        for sf in session_files:
            if 'bot_session' not in sf.name:
                session_file = sf
                break
    if not session_file:
        session_file = session_files[0]
    
    print(f"\nUsing session: {session_file.name}")
    
    # Get chat IDs from alert_groups.json
    chat_ids = []
    try:
        with open('alert_groups.json', 'r', encoding='utf-8') as f:
            alert_groups_data = json.load(f)
            if isinstance(alert_groups_data, dict) and 'groups' in alert_groups_data:
                chat_ids = [str(gid) for gid in alert_groups_data['groups']]
            elif isinstance(alert_groups_data, list):
                chat_ids = [str(gid) for gid in alert_groups_data]
            
            if chat_ids:
                print(f"Found {len(chat_ids)} chat IDs from alert_groups.json")
                for cid in chat_ids:
                    print(f"  - {cid}")
    except Exception as e:
        print(f"Could not load alert_groups.json: {e}")
    
    if not chat_ids:
        print("ERROR: No chat IDs found in alert_groups.json")
        return
    
    limit = 2000  # Default limit
    
    # Get API credentials from telegram_monitor_new.py
    API_ID = 25177061
    API_HASH = "c11ea2f1db2aa742144dfa2a30448408"
    
    # Connect to Telegram using existing session
    print(f"\nConnecting to Telegram with session {session_file.stem}...")
    client = TelegramClient(session_file.stem, API_ID, API_HASH)
    
    try:
        await client.start()
        print("Connected!")
        
        # Fetch messages from all chat IDs
        all_messages = []
        if not chat_ids:
            print("ERROR: No chat IDs found in alert_groups.json")
            return
        
        for chat_id in chat_ids:
            print(f"\nFetching messages from chat ID: {chat_id}")
            messages = await fetch_telegram_messages(client, chat_id, limit)
            all_messages.extend(messages)
            print(f"Got {len(messages)} messages from {chat_id}")
        
        messages = all_messages
        print(f"\nTotal messages collected: {len(messages)}")
        
        if not messages:
            print("No messages found. Check your chat ID.")
            return
        
        # Backfill
        updated_data = backfill_from_messages(kpi_data, messages)
        
        # Save automatically
        if updated_data.get("backfill_info", {}).get("updated_count", 0) > 0:
            print("\nAuto-saving changes...")
            save_kpi_logs(updated_data)
            print("\nBackfill complete! Market cap data saved to kpi_logs.json")
        else:
            print("\nNo changes needed - all alerts already have MCAP or couldn't be matched")
    
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

