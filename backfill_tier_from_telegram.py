#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backfill tier and MCAP from old Telegram alert posts.

This script:
1. Connects to Telegram
2. Fetches old alert messages from the alert channel/group
3. Extracts tier and MCAP from message text
4. Updates kpi_logs.json with correct data
"""

import asyncio
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from telethon import TelegramClient
from telethon.tl.types import Message
import os

# Load environment variables
API_ID = int(os.getenv('API_ID', '25177061'))
API_HASH = os.getenv('API_HASH', '')
SESSION_NAME = os.getenv('SESSION_NAME', 'telegram_monitor')

# Alert channel/group ID (update this to your actual alert channel)
ALERT_CHAT_ID = os.getenv('ALERT_CHAT_ID')  # Can be channel username or ID

KPI_LOGS_FILE = Path("kpi_logs.json")


def parse_tier_from_message(text: str) -> Optional[int]:
    """Extract tier from Telegram message text."""
    if not text:
        return None
    
    # Look for "TIER 1", "TIER 2", "TIER 3" in the message
    tier_patterns = [
        r'TIER\s*(\d+)',
        r'TIER\s*(\d+)\s*LOCKED',
        r'🚨.*TIER\s*(\d+)',
    ]
    
    for pattern in tier_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            tier = int(match.group(1))
            if tier in [1, 2, 3]:
                return tier
    
    # Also check for tier emojis/names
    if '🚀' in text and ('ULTRA' in text.upper() or 'TIER 1' in text.upper()):
        return 1
    elif '🔥' in text and ('HIGH' in text.upper() or 'TIER 2' in text.upper()):
        return 2
    elif '⚡' in text and ('MEDIUM' in text.upper() or 'TIER 3' in text.upper()):
        return 3
    
    return None


def parse_mcap_from_message(text: str) -> Optional[float]:
    """Extract market cap from Telegram message text."""
    if not text:
        return None
    
    # Look for "Current MC: $XXX" or "Current MC: $XXXK" or "Current MC: $XXX.XXK"
    # Pattern: "Current MC: **$143.5K**" or "Current MC: $143,500"
    mcap_patterns = [
        r'Current\s+MC[:\s]+\*?\*?\$?([\d,]+\.?\d*)\s*([KMkm]?)\*?\*?',
        r'MC[:\s]+\*?\*?\$?([\d,]+\.?\d*)\s*([KMkm]?)\*?\*?',
        r'\$\s*([\d,]+\.?\d*)\s*([KMkm]?)\s*MC',
    ]
    
    for pattern in mcap_patterns:
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
                elif not multiplier_str and value < 1000:
                    # If no multiplier and value is small, assume it's in thousands
                    value *= 1000
                
                return value
            except (ValueError, TypeError):
                continue
    
    return None


def parse_token_from_message(text: str) -> Optional[str]:
    """Extract token name from Telegram message text."""
    if not text:
        return None
    
    # Look for token after 🔥 emoji
    token_pattern = r'🔥\s*\*\*([A-Z0-9]+)\*\*|([A-Z0-9]+))'
    match = re.search(token_pattern, text)
    if match:
        return match.group(1) or match.group(2)
    
    # Alternative: look for token in "ALPHA INCOMING — TIER X LOCKED" line
    # Usually token appears shortly after
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if 'TIER' in line and 'LOCKED' in line:
            # Token is usually in the next few lines
            for j in range(i+1, min(i+5, len(lines))):
                token_match = re.search(r'\*\*([A-Z0-9]+)\*\*', lines[j])
                if token_match:
                    return token_match.group(1)
    
    return None


def parse_contract_from_message(text: str) -> Optional[str]:
    """Extract contract address from Telegram message text."""
    if not text:
        return None
    
    # Look for contract in code block (backticks)
    contract_pattern = r'`([A-Z0-9]{32,44})`'
    match = re.search(contract_pattern, text)
    if match:
        return match.group(1)
    
    # Alternative: look for Solana address pattern
    solana_pattern = r'([A-Z0-9]{32,44})'
    matches = re.findall(solana_pattern, text)
    # Filter for likely contract addresses (long alphanumeric strings)
    for match in matches:
        if len(match) >= 32 and match.isalnum():
            return match
    
    return None


def parse_timestamp_from_message(message: Message) -> str:
    """Get timestamp from Telegram message."""
    if message.date:
        # Convert to UTC ISO format
        return message.date.replace(tzinfo=timezone.utc).isoformat()
    return datetime.now(timezone.utc).isoformat()


async def fetch_old_alerts(client: TelegramClient, chat_id: str, limit: int = 1000) -> List[Dict]:
    """Fetch old alert messages from Telegram."""
    print(f"📡 Fetching old alerts from {chat_id}...")
    
    alerts = []
    try:
        async for message in client.iter_messages(chat_id, limit=limit):
            if not message.text:
                continue
            
            text = message.text
            
            # Check if this looks like an alert message
            if 'ALPHA INCOMING' not in text and 'TIER' not in text:
                continue
            
            # Extract data from message
            tier = parse_tier_from_message(text)
            mcap = parse_mcap_from_message(text)
            token = parse_token_from_message(text)
            contract = parse_contract_from_message(text)
            timestamp = parse_timestamp_from_message(message)
            
            if token or contract:
                alerts.append({
                    'message_id': message.id,
                    'timestamp': timestamp,
                    'tier': tier,
                    'mcap': mcap,
                    'token': token,
                    'contract': contract,
                    'text': text[:200]  # First 200 chars for debugging
                })
        
        print(f"✅ Fetched {len(alerts)} alert messages")
        return alerts
    
    except Exception as e:
        print(f"❌ Error fetching alerts: {e}")
        return []


def load_kpi_logs() -> Dict:
    """Load kpi_logs.json."""
    if not KPI_LOGS_FILE.exists():
        return {"alerts": []}
    
    try:
        with open(KPI_LOGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading kpi_logs.json: {e}")
        return {"alerts": []}


def save_kpi_logs(data: Dict):
    """Save kpi_logs.json."""
    try:
        # Create backup
        backup_path = KPI_LOGS_FILE.with_suffix('.json.backup')
        if KPI_LOGS_FILE.exists():
            import shutil
            shutil.copy2(KPI_LOGS_FILE, backup_path)
            print(f"📦 Backup created: {backup_path}")
        
        with open(KPI_LOGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved to {KPI_LOGS_FILE}")
    except Exception as e:
        print(f"❌ Error saving kpi_logs.json: {e}")


def match_alert_to_telegram(alert: Dict, telegram_alerts: List[Dict]) -> Optional[Dict]:
    """Match an alert from kpi_logs to a Telegram alert message."""
    alert_token = alert.get('token', '').upper()
    alert_contract = alert.get('contract', '')
    alert_timestamp = alert.get('timestamp', '')
    
    best_match = None
    best_score = 0
    
    # Try to match by contract (most reliable) - exact match
    if alert_contract:
        for tg_alert in telegram_alerts:
            tg_contract = tg_alert.get('contract', '')
            if tg_contract and tg_contract == alert_contract:
                # Also check token matches
                tg_token = (tg_alert.get('token') or '').upper()
                if tg_token == alert_token or not alert_token:
                    return tg_alert  # Perfect match
    
    # Try to match by token + timestamp (within 2 hours for better matching)
    if alert_token and alert_timestamp:
        try:
            alert_time = datetime.fromisoformat(alert_timestamp.replace('Z', '+00:00'))
            for tg_alert in telegram_alerts:
                tg_token = (tg_alert.get('token') or '').upper()
                if tg_token == alert_token:
                    tg_timestamp = tg_alert.get('timestamp', '')
                    if tg_timestamp:
                        try:
                            tg_time = datetime.fromisoformat(tg_timestamp.replace('Z', '+00:00'))
                            time_diff = abs((alert_time - tg_time).total_seconds())
                            if time_diff < 7200:  # Within 2 hours
                                # Score: closer timestamp = better match
                                score = 1.0 / (1.0 + time_diff / 3600)  # Normalize to 0-1
                                if score > best_score:
                                    best_score = score
                                    best_match = tg_alert
                        except:
                            pass
        except:
            pass
    
    return best_match


def update_alerts_with_telegram_data(kpi_data: Dict, telegram_alerts: List[Dict]) -> Tuple[int, int]:
    """Update alerts in kpi_logs.json with data from Telegram messages."""
    alerts = kpi_data.get('alerts', [])
    updated_count = 0
    matched_count = 0
    
    print(f"\n📊 Processing {len(alerts)} alerts...")
    
    for alert in alerts:
        # Try to match this alert to a Telegram message
        tg_alert = match_alert_to_telegram(alert, telegram_alerts)
        
        if tg_alert:
            matched_count += 1
            updated = False
            
            # Update tier if missing or None
            if alert.get('tier') is None and tg_alert.get('tier') is not None:
                alert['tier'] = tg_alert['tier']
                updated = True
                print(f"  ✅ Updated tier for {alert.get('token')}: {tg_alert['tier']}")
            
            # Update MCAP if missing or None
            if alert.get('mc_usd') is None and tg_alert.get('mcap') is not None:
                alert['mc_usd'] = tg_alert['mcap']
                updated = True
                print(f"  ✅ Updated MCAP for {alert.get('token')}: ${tg_alert['mcap']:,.0f}")
            
            # Update entry_mc if missing
            if alert.get('entry_mc') is None and tg_alert.get('mcap') is not None:
                alert['entry_mc'] = tg_alert['mcap']
                updated = True
            
            # Update timestamp if more accurate
            if tg_alert.get('timestamp'):
                alert['timestamp'] = tg_alert['timestamp']
                updated = True
            
            if updated:
                updated_count += 1
    
    print(f"\n📈 Summary:")
    print(f"  Matched: {matched_count}/{len(alerts)} alerts")
    print(f"  Updated: {updated_count} alerts")
    
    return matched_count, updated_count


async def main():
    """Main function to backfill tier and MCAP from Telegram."""
    print("=" * 80)
    print("BACKFILL TIER AND MCAP FROM TELEGRAM POSTS")
    print("=" * 80)
    
    # Check if ALERT_CHAT_ID is set
    if not ALERT_CHAT_ID:
        print("❌ ALERT_CHAT_ID environment variable not set!")
        print("   Set it to your alert channel/group ID or username")
        return
    
    # Load existing kpi_logs
    kpi_data = load_kpi_logs()
    alerts = kpi_data.get('alerts', [])
    print(f"\n📋 Loaded {len(alerts)} alerts from kpi_logs.json")
    
    # Count alerts without tier
    alerts_without_tier = [a for a in alerts if a.get('tier') is None]
    print(f"⚠️  {len(alerts_without_tier)} alerts missing tier field")
    
    # Connect to Telegram
    print(f"\n🔌 Connecting to Telegram...")
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    
    try:
        await client.start()
        print("✅ Connected to Telegram")
        
        # Fetch old alerts from Telegram
        telegram_alerts = await fetch_old_alerts(client, ALERT_CHAT_ID, limit=1000)
        
        if not telegram_alerts:
            print("⚠️  No alerts found in Telegram. Check ALERT_CHAT_ID.")
            return
        
        # Update kpi_logs with Telegram data
        matched, updated = update_alerts_with_telegram_data(kpi_data, telegram_alerts)
        
        # Save updated kpi_logs
        if updated > 0:
            save_kpi_logs(kpi_data)
            print(f"\n✅ Successfully updated {updated} alerts!")
        else:
            print("\n⚠️  No alerts were updated (all already have tier/MCAP or couldn't match)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.disconnect()
        print("\n🔌 Disconnected from Telegram")


if __name__ == "__main__":
    asyncio.run(main())

