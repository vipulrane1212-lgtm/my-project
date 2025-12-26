#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check which recent Telegram alerts are missing from kpi_logs.json
Compares alerts from Telegram channel with alerts in JSON file
"""

import json
import os
import sys
import re
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

try:
    from telethon import TelegramClient
    from telethon.tl.types import Message
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("⚠️ Warning: telethon not available. Install with: pip install telethon")

KPI_LOGS_FILE = Path("kpi_logs.json")
ALERT_CHAT_ID = os.getenv("ALERT_CHAT_ID")  # e.g., -1001234567890

def parse_alert_from_message(message_text: str) -> Optional[Dict]:
    """Parse alert details from Telegram message text."""
    if not message_text or "ALPHA INCOMING" not in message_text:
        return None
    
    alert = {}
    
    # Extract tier
    tier_match = re.search(r'TIER\s+(\d+)\s+LOCKED', message_text, re.IGNORECASE)
    if tier_match:
        alert['tier'] = int(tier_match.group(1))
    
    # Extract token name (after 🔥 emoji)
    token_match = re.search(r'🔥\s+\*\*([A-Z0-9]+)\*\*', message_text)
    if token_match:
        alert['token'] = token_match.group(1)
    
    # Extract Current MC
    mcap_match = re.search(r'Current MC:\s*\*\*\$?([0-9,]+\.?[0-9]*)\s*([KMkm]?)\*\*', message_text)
    if mcap_match:
        mcap_value = float(mcap_match.group(1).replace(',', ''))
        mcap_unit = mcap_match.group(2).upper() if mcap_match.group(2) else ''
        if mcap_unit == 'K':
            mcap_value *= 1000
        elif mcap_unit == 'M':
            mcap_value *= 1000000
        alert['current_mcap'] = mcap_value
    
    # Extract contract address (in code block)
    contract_match = re.search(r'`([A-Z0-9]{32,44})`', message_text)
    if contract_match:
        alert['contract'] = contract_match.group(1)
    
    # Extract level (MEDIUM/HIGH)
    if '⚡️ MEDIUM' in message_text or 'MEDIUM' in message_text:
        alert['level'] = 'MEDIUM'
    elif '🚀 ULTRA' in message_text or '🔥 HIGH' in message_text:
        alert['level'] = 'HIGH'
    
    return alert if alert.get('token') else None

def load_json_alerts() -> List[Dict]:
    """Load alerts from kpi_logs.json."""
    if not KPI_LOGS_FILE.exists():
        print(f"❌ {KPI_LOGS_FILE} not found!")
        return []
    
    try:
        with open(KPI_LOGS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('alerts', [])
    except Exception as e:
        print(f"❌ Error loading {KPI_LOGS_FILE}: {e}")
        return []

def find_matching_alert(telegram_alert: Dict, json_alerts: List[Dict]) -> Optional[Dict]:
    """Find matching alert in JSON by token and contract."""
    token = telegram_alert.get('token', '').upper()
    contract = telegram_alert.get('contract', '')
    
    if not token:
        return None
    
    # Try to find by token + contract (most accurate)
    if contract:
        for alert in json_alerts:
            if (alert.get('token', '').upper() == token and 
                alert.get('contract', '') == contract):
                return alert
    
    # Fallback: find by token only (latest one)
    matching = [a for a in json_alerts if a.get('token', '').upper() == token]
    if matching:
        # Return the most recent one
        matching.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return matching[0]
    
    return None

async def fetch_telegram_alerts(limit: int = 50) -> List[Tuple[Message, Dict]]:
    """Fetch recent alerts from Telegram channel."""
    if not TELEGRAM_AVAILABLE:
        print("❌ telethon not available. Cannot fetch Telegram alerts.")
        return []
    
    if not ALERT_CHAT_ID:
        print("❌ ALERT_CHAT_ID environment variable not set!")
        print("   Set it to your Telegram channel/group ID (e.g., -1001234567890)")
        return []
    
    try:
        api_id = os.getenv("API_ID")
        api_hash = os.getenv("API_HASH")
        session_name = os.getenv("SESSION_NAME", "telegram_monitor")
        
        if not api_id or not api_hash:
            print("❌ API_ID or API_HASH not set in environment variables!")
            return []
        
        client = TelegramClient(session_name, int(api_id), api_hash)
        await client.start()
        
        print(f"📡 Fetching last {limit} messages from Telegram channel...")
        messages = []
        async for message in client.iter_messages(int(ALERT_CHAT_ID), limit=limit):
            if message.text and "ALPHA INCOMING" in message.text:
                parsed = parse_alert_from_message(message.text)
                if parsed:
                    parsed['telegram_date'] = message.date
                    parsed['telegram_id'] = message.id
                    messages.append((message, parsed))
        
        await client.disconnect()
        print(f"✅ Found {len(messages)} alert messages in Telegram")
        return messages
    except Exception as e:
        print(f"❌ Error fetching Telegram alerts: {e}")
        import traceback
        traceback.print_exc()
        return []

def check_missing_alerts():
    """Main function to check for missing alerts."""
    print("=" * 80)
    print("CHECKING FOR MISSING ALERTS IN kpi_logs.json")
    print("=" * 80)
    
    # Load JSON alerts
    json_alerts = load_json_alerts()
    print(f"📋 Loaded {len(json_alerts)} alerts from {KPI_LOGS_FILE}")
    
    if not TELEGRAM_AVAILABLE or not ALERT_CHAT_ID:
        print("\n⚠️ Cannot fetch Telegram alerts. Checking JSON alerts only...")
        print("\n📊 Recent alerts in JSON (last 10):")
        json_alerts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        for i, alert in enumerate(json_alerts[:10], 1):
            timestamp = alert.get('timestamp', 'N/A')
            token = alert.get('token', 'UNKNOWN')
            tier = alert.get('tier', '?')
            mcap = alert.get('current_mcap') or alert.get('mc_usd', 0)
            print(f"  {i}. {token} (Tier {tier}) - ${mcap:,.0f} - {timestamp}")
        return
    
    # Fetch Telegram alerts
    import asyncio
    telegram_alerts = asyncio.run(fetch_telegram_alerts(limit=50))
    
    if not telegram_alerts:
        print("⚠️ No Telegram alerts found or error occurred")
        return
    
    print(f"\n🔍 Comparing {len(telegram_alerts)} Telegram alerts with {len(json_alerts)} JSON alerts...")
    
    missing_alerts = []
    matched_alerts = []
    
    # Check each Telegram alert
    for message, telegram_alert in telegram_alerts:
        token = telegram_alert.get('token', 'UNKNOWN')
        contract = telegram_alert.get('contract', 'N/A')
        tier = telegram_alert.get('tier', '?')
        current_mcap = telegram_alert.get('current_mcap', 0)
        telegram_date = telegram_alert.get('telegram_date')
        
        # Find matching alert in JSON
        json_match = find_matching_alert(telegram_alert, json_alerts)
        
        if json_match:
            matched_alerts.append((telegram_alert, json_match))
            # Check if data matches
            json_tier = json_match.get('tier')
            json_mcap = json_match.get('current_mcap') or json_match.get('mc_usd', 0)
            
            issues = []
            if json_tier != tier:
                issues.append(f"Tier mismatch: Telegram={tier}, JSON={json_tier}")
            if abs(json_mcap - current_mcap) > 1000:  # Allow 1k difference
                issues.append(f"MCAP mismatch: Telegram=${current_mcap:,.0f}, JSON=${json_mcap:,.0f}")
            
            if issues:
                print(f"\n⚠️ {token} (Contract: {contract[:8]}...) - MATCHED but has issues:")
                for issue in issues:
                    print(f"   - {issue}")
        else:
            missing_alerts.append((message, telegram_alert))
            print(f"\n❌ MISSING: {token} (Tier {tier}, MC ${current_mcap:,.0f})")
            print(f"   Contract: {contract}")
            print(f"   Telegram Date: {telegram_date}")
            print(f"   Message ID: {telegram_alert.get('telegram_id', 'N/A')}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Matched alerts: {len(matched_alerts)}")
    print(f"❌ Missing alerts: {len(missing_alerts)}")
    
    if missing_alerts:
        print(f"\n⚠️ {len(missing_alerts)} alert(s) were posted to Telegram but NOT saved to kpi_logs.json:")
        for message, alert in missing_alerts:
            token = alert.get('token', 'UNKNOWN')
            tier = alert.get('tier', '?')
            mcap = alert.get('current_mcap', 0)
            date = alert.get('telegram_date', 'N/A')
            print(f"   - {token} (Tier {tier}, MC ${mcap:,.0f}) posted at {date}")
        
        print("\n💡 Possible causes:")
        print("   1. Alert processing failed before saving to JSON")
        print("   2. Error during kpi_logger.log_alert()")
        print("   3. Alert was filtered out (MCAP > 500k, duplicate, etc.)")
        print("   4. Bot was not running when alert was posted")
    else:
        print("\n✅ All Telegram alerts are present in kpi_logs.json!")

if __name__ == "__main__":
    check_missing_alerts()

