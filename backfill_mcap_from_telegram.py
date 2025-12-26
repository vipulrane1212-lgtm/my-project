#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
backfill_mcap_from_telegram.py

Backfill market cap data for old alerts by fetching from Telegram posts.
Extracts MCAP from the formatted alert messages that were sent.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
import asyncio

try:
    from telethon import TelegramClient
    from telethon.tl.types import Message
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("Warning: telethon not available")


def parse_mcap_from_message(text: str) -> Optional[float]:
    """
    Parse market cap from Telegram alert message.
    Looks for patterns like:
    - "Current MC: $143.5K"
    - "Current MC: **$143,500**"
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
    
    if not alert_token or not alert_timestamp:
        return False
    
    # Check if token appears in message
    if alert_token.upper() not in message_text.upper():
        return False
    
    # Check if timestamp is close (within 5 minutes)
    try:
        alert_dt = datetime.fromisoformat(alert_timestamp.replace('Z', '+00:00'))
        time_diff = abs((message_date - alert_dt).total_seconds())
        if time_diff > 300:  # 5 minutes
            return False
    except Exception:
        # If timestamp parsing fails, still try to match by token
        pass
    
    return True


async def fetch_telegram_messages(
    client: TelegramClient,
    chat_id: str,
    limit: int = 1000
) -> List[Tuple[str, datetime]]:
    """Fetch messages from Telegram channel/group."""
    messages = []
    
    try:
        async for message in client.iter_messages(chat_id, limit=limit):
            if message.text:
                messages.append((message.text, message.date))
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
    
    print(f"Found {len(alerts)} alerts")
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
    
    for alert in alerts_without_mcap:
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
                    print(f"  [OK] {alert_token}: ${mcap:,.2f} (from message at {message_date})")
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
            print(f"Backup created: {backup_path}")
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Saved to {file_path}")
    except Exception as e:
        print(f"Error saving {file_path}: {e}")


async def main():
    """Main function."""
    print("="*60)
    print("Backfilling Market Cap from Telegram Posts")
    print("="*60)
    
    if not TELEGRAM_AVAILABLE:
        print("ERROR: telethon is required. Install with: pip install telethon")
        return
    
    # Load KPI logs
    kpi_data = load_kpi_logs()
    if not kpi_data:
        return
    
    # Get Telegram credentials
    print("\nTelegram Configuration:")
    session_name = input("Session name (e.g., 'bot_session'): ").strip() or "bot_session"
    api_id = input("API ID (from https://my.telegram.org): ").strip()
    api_hash = input("API Hash: ").strip()
    chat_id = input("Chat/Channel ID (e.g., @channelname or -1001234567890): ").strip()
    limit = input("Number of messages to fetch (default 1000): ").strip()
    limit = int(limit) if limit.isdigit() else 1000
    
    if not api_id or not api_hash or not chat_id:
        print("ERROR: API ID, API Hash, and Chat ID are required")
        return
    
    # Connect to Telegram
    print(f"\nConnecting to Telegram...")
    client = TelegramClient(session_name, int(api_id), api_hash)
    
    try:
        await client.start()
        print("Connected!")
        
        # Fetch messages
        print(f"\nFetching last {limit} messages from {chat_id}...")
        messages = await fetch_telegram_messages(client, chat_id, limit)
        print(f"Fetched {len(messages)} messages")
        
        # Backfill
        updated_data = backfill_from_messages(kpi_data, messages)
        
        # Save
        if updated_data.get("backfill_info", {}).get("updated_count", 0) > 0:
            save_confirm = input("\nSave changes? (y/n): ").lower().strip() == 'y'
            if save_confirm:
                save_kpi_logs(updated_data)
                print("\nBackfill complete!")
            else:
                print("\nChanges not saved")
        else:
            print("\nNo changes needed - all alerts already have MCAP or couldn't be matched")
    
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

