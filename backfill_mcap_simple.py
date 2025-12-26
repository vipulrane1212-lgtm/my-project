#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
backfill_mcap_simple.py

Simple script to extract market cap from alert messages if you have them saved.
You can paste alert messages or provide a file with alert messages.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone


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


def match_alert_to_message(alert: Dict, message_text: str) -> bool:
    """Check if a message matches an alert based on token."""
    alert_token = alert.get("token", "").upper()
    
    if not alert_token:
        return False
    
    # Check if token appears in message
    if alert_token.upper() not in message_text.upper():
        return False
    
    # Check if contract appears in message
    alert_contract = alert.get("contract", "")
    if alert_contract and alert_contract[:8] in message_text:
        return True
    
    return False


def backfill_from_text_messages(
    kpi_data: Dict,
    messages: List[str]
) -> Dict:
    """Backfill MCAP from text messages."""
    alerts = kpi_data.get("alerts", [])
    
    if not alerts:
        print("No alerts found in kpi_logs.json")
        return kpi_data
    
    print(f"Found {len(alerts)} alerts")
    print(f"Found {len(messages)} messages to process")
    
    # Find alerts without MCAP
    alerts_without_mcap = [a for a in alerts if not a.get("mc_usd") and not a.get("entry_mc")]
    print(f"Found {len(alerts_without_mcap)} alerts without MCAP")
    
    if not alerts_without_mcap:
        print("All alerts already have MCAP!")
        return kpi_data
    
    # Match messages to alerts
    updated_count = 0
    
    for alert in alerts_without_mcap:
        alert_token = alert.get("token", "")
        if not alert_token:
            continue
        
        # Find matching message
        for message_text in messages:
            if match_alert_to_message(alert, message_text):
                mcap = parse_mcap_from_message(message_text)
                if mcap:
                    alert["mc_usd"] = mcap
                    alert["mc_source"] = "telegram_post_manual"
                    updated_count += 1
                    print(f"  [OK] {alert_token}: ${mcap:,.2f}")
                    break
    
    # Update data
    kpi_data["alerts"] = alerts
    kpi_data["last_updated"] = datetime.now(timezone.utc).isoformat()
    kpi_data["backfill_info"] = {
        "backfilled_at": datetime.now(timezone.utc).isoformat(),
        "updated_count": updated_count,
        "total_alerts": len(alerts)
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


def main():
    """Main function."""
    print("="*60)
    print("Backfilling Market Cap from Alert Messages")
    print("="*60)
    
    # Load KPI logs
    kpi_data = load_kpi_logs()
    if not kpi_data:
        return
    
    # Get messages
    print("\nHow do you want to provide alert messages?")
    print("1. Paste messages directly")
    print("2. Load from file")
    choice = input("Choice (1 or 2): ").strip()
    
    messages = []
    
    if choice == "1":
        print("\nPaste alert messages (one per line, or empty line to finish):")
        while True:
            line = input()
            if not line.strip():
                break
            messages.append(line)
    elif choice == "2":
        file_path = input("File path: ").strip()
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                messages = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"Error reading file: {e}")
            return
    else:
        print("Invalid choice")
        return
    
    if not messages:
        print("No messages provided")
        return
    
    # Backfill
    updated_data = backfill_from_text_messages(kpi_data, messages)
    
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


if __name__ == "__main__":
    main()

