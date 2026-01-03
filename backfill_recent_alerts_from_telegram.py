#!/usr/bin/env python3
"""Backfill recent alerts from Telegram export that are missing from kpi_logs.json."""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional
import shutil

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

KPI_LOGS_FILE = Path("kpi_logs.json")
TELEGRAM_EXPORT = Path(r"c:\Users\Admin\Downloads\Telegram Desktop\ChatExport_2026-01-03 (1)\result.json")

def extract_text_from_entities(text_data) -> str:
    """Extract plain text from Telegram message entities."""
    if isinstance(text_data, str):
        return text_data
    if isinstance(text_data, list):
        result = []
        for item in text_data:
            if isinstance(item, str):
                result.append(item)
            elif isinstance(item, dict):
                text = item.get("text", "")
                if text:
                    result.append(text)
        return "".join(result)
    return ""

def parse_alert_from_telegram_message(message: Dict) -> Optional[Dict]:
    """Parse alert from Telegram message."""
    try:
        text_data = message.get("text", "")
        text = extract_text_from_entities(text_data)
        
        if "ALPHA INCOMING" not in text.upper() and "TIER" not in text.upper():
            return None
        
        date_str = message.get("date", "")
        if not date_str:
            return None
        
        try:
            # Parse date string (format: "2026-01-03T12:36:51")
            # CRITICAL: Telegram export dates are in IST (UTC+5:30), NOT UTC
            # Need to convert IST to UTC by subtracting 5 hours 30 minutes
            if "T" in date_str:
                # Remove timezone if present
                date_str_clean = date_str.split("+")[0].split("Z")[0]
                message_date = datetime.fromisoformat(date_str_clean)
                
                # Telegram export dates are in IST (UTC+5:30)
                # Convert to UTC by subtracting 5:30
                from datetime import timedelta
                ist_offset = timedelta(hours=5, minutes=30)
                message_date_utc = message_date - ist_offset
                
                # Set to UTC timezone
                message_date = message_date_utc.replace(tzinfo=timezone.utc)
            else:
                return None
        except Exception as e:
            print(f"Error parsing date '{date_str}': {e}")
            return None
        
        # Extract tier
        tier_match = re.search(r'TIER\s+(\d+)', text, re.IGNORECASE)
        tier = int(tier_match.group(1)) if tier_match else 3
        
        # Extract token (after 🔥)
        token_match = re.search(r'🔥\s*([A-Z0-9]+)', text) or \
                      re.search(r'ALPHA INCOMING.*?🔥\s*([A-Z0-9]+)', text, re.DOTALL)
        token = token_match.group(1) if token_match else None
        
        # Extract contract
        contract_match = re.search(r'([A-Za-z0-9]{32,44})', text)
        contract = contract_match.group(1) if contract_match and 32 <= len(contract_match.group(1)) <= 44 else None
        
        # Extract MCAP
        mcap = None
        mcap_match = re.search(r'Current MC:\s*\$?([0-9,.]+\.?[0-9]*)\s*([KMkm]?)', text, re.IGNORECASE)
        if mcap_match:
            mcap_str = mcap_match.group(1).replace(',', '')
            mcap_unit = (mcap_match.group(2) or '').upper()
            try:
                mcap = float(mcap_str)
                if mcap_unit == 'K':
                    mcap *= 1000
                elif mcap_unit == 'M':
                    mcap *= 1000000
            except:
                pass
        
        if not token or not contract:
            return None
        
        # Extract matched signals from description
        matched_signals = []
        if "whale" in text.lower() or "whalebuy" in text.lower():
            matched_signals.append("whalebuy")
        if "large" in text.lower() and "buy" in text.lower():
            matched_signals.append("large_buy")
        if "glydo" in text.lower() or "trending" in text.lower():
            matched_signals.append("glydo")
        if "momentum" in text.lower():
            matched_signals.append("momentum")
        if "volume" in text.lower():
            matched_signals.append("volume")
        if "early" in text.lower() and "trending" in text.lower():
            matched_signals.append("early_trending")
        
        return {
            "timestamp": message_date.isoformat(),
            "level": "HIGH" if tier == 1 else "MEDIUM",
            "token": token,
            "contract": contract,
            "tier": tier,
            "mc_usd": mcap,
            "current_mcap": mcap,
            "entry_mc": mcap,
            "matched_signals": matched_signals,
            "source": "telegram_export_backfill"
        }
    except Exception as e:
        print(f"Error parsing message: {e}")
        return None

def main():
    """Backfill missing alerts."""
    print("="*80)
    print("BACKFILL RECENT ALERTS FROM TELEGRAM EXPORT")
    print("="*80)
    print()
    
    # Load Telegram export
    if not TELEGRAM_EXPORT.exists():
        print(f"ERROR: Telegram export not found: {TELEGRAM_EXPORT}")
        return
    
    with open(TELEGRAM_EXPORT, 'r', encoding='utf-8') as f:
        telegram_data = json.load(f)
    
    messages = telegram_data.get("messages", [])
    print(f"Loaded {len(messages)} messages from Telegram export")
    
    # Parse alerts
    telegram_alerts = []
    for msg in messages:
        alert = parse_alert_from_telegram_message(msg)
        if alert:
            telegram_alerts.append(alert)
    
    print(f"Found {len(telegram_alerts)} alerts in Telegram export")
    print()
    
    # Load existing alerts
    if not KPI_LOGS_FILE.exists():
        print(f"ERROR: {KPI_LOGS_FILE} not found")
        return
    
    with open(KPI_LOGS_FILE, 'r', encoding='utf-8') as f:
        kpi_data = json.load(f)
    
    existing_alerts = kpi_data.get("alerts", [])
    print(f"Found {len(existing_alerts)} existing alerts in kpi_logs.json")
    print()
    
    # Find missing alerts
    existing_keys = {(a.get("token"), a.get("tier"), a.get("timestamp", "")[:10]) for a in existing_alerts}
    new_alerts = []
    
    for tg_alert in telegram_alerts:
        token = tg_alert.get("token")
        tier = tg_alert.get("tier")
        date = tg_alert.get("timestamp", "")[:10]
        key = (token, tier, date)
        
        if key not in existing_keys:
            new_alerts.append(tg_alert)
    
    print(f"Found {len(new_alerts)} new alerts to add")
    print()
    
    if new_alerts:
        print("New alerts to add:")
        for alert in new_alerts[:10]:
            print(f"  {alert.get('token')} Tier {alert.get('tier')}: {alert.get('timestamp')}")
        print()
        
        # Backup
        if KPI_LOGS_FILE.exists():
            backup_file = KPI_LOGS_FILE.with_suffix('.json.backup')
            shutil.copy2(KPI_LOGS_FILE, backup_file)
            print(f"Created backup: {backup_file}")
        
        # Add new alerts
        existing_alerts.extend(new_alerts)
        kpi_data["alerts"] = existing_alerts
        kpi_data["last_updated"] = datetime.now(timezone.utc).isoformat()
        
        # Save
        with open(KPI_LOGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(kpi_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n[SUCCESS] Added {len(new_alerts)} new alerts to kpi_logs.json")
        print(f"Total alerts now: {len(existing_alerts)}")
    else:
        print("No new alerts to add - all Telegram alerts are already in kpi_logs.json")

if __name__ == "__main__":
    main()

