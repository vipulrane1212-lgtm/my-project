#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix MCAP for ZAZU and LARPBALL alerts based on Telegram posts"""

import json
import sys
from pathlib import Path
import shutil
from datetime import datetime, timezone

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

KPI_LOGS_FILE = Path("kpi_logs.json")

# Alert fixes from Telegram posts
ALERT_FIXES = {
    # ZAZU at 4:16 AM - Current MC: $142.0K (not $50.5K)
    "ZAZU_4_16": {
        "token": "ZAZU",
        "contract": "F6DPFEYBSEHCAG8KPBHZ71WYAGUBH2763ZJL7J6SPUMP",
        "timestamp_pattern": "2025-12-26T04:16",  # Around 4:16 AM
        "current_mcap": 142000.0,  # $142.0K
        "entry_mc": 50500.0,  # Keep entry MC as $50.5K
    },
    # LARPBALL at 4:25 AM - Current MC: $180.4K (not $44.4K)
    "LARPBALL_4_25": {
        "token": "LARPBALL",
        "contract": "CE5HEYZTBWUP5U2UDCMDFGHJMH7OH7VVPVKNP3FFPUMP",
        "timestamp_pattern": "2025-12-26T04:25",  # Around 4:25 AM
        "current_mcap": 180400.0,  # $180.4K
        "entry_mc": 44400.0,  # Keep entry MC as $44.4K
    },
}

def fix_mcap():
    """Fix MCAP for specific alerts"""
    print("=" * 80)
    print("FIXING MCAP FOR ZAZU AND LARPBALL ALERTS")
    print("=" * 80)
    
    if not KPI_LOGS_FILE.exists():
        print(f"❌ {KPI_LOGS_FILE} not found!")
        return
    
    # Create backup
    backup_path = KPI_LOGS_FILE.with_suffix('.json.backup6')
    shutil.copy2(KPI_LOGS_FILE, backup_path)
    print(f"📦 Backup created: {backup_path}")
    
    try:
        with open(KPI_LOGS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading {KPI_LOGS_FILE}: {e}")
        return
    
    alerts = data.get('alerts', [])
    print(f"📋 Loaded {len(alerts)} alerts")
    
    updated_count = 0
    
    for fix_name, fix_data in ALERT_FIXES.items():
        token = fix_data["token"]
        contract = fix_data["contract"]
        timestamp_pattern = fix_data["timestamp_pattern"]
        new_current_mcap = fix_data["current_mcap"]
        entry_mc = fix_data.get("entry_mc")
        
        print(f"\n🔍 Looking for {token} alert around {timestamp_pattern}...")
        
        # Find matching alerts - get the LATEST alert for this token/contract
        matching_alerts = []
        for alert in alerts:
            alert_token = alert.get('token', '').upper()
            alert_contract = alert.get('contract', '')
            
            # Match by token and contract
            if alert_token == token.upper() and alert_contract == contract:
                matching_alerts.append(alert)
        
        if not matching_alerts:
            print(f"  ❌ No {token} alerts found")
            continue
        
        # Sort by timestamp (newest first) and take the latest one
        matching_alerts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        alert = matching_alerts[0]  # Latest alert
        
        alert_timestamp = alert.get('timestamp', '')
        old_mc_usd = alert.get('mc_usd')
        old_current_mcap = alert.get('current_mcap')
        
        print(f"  ✅ Found latest {token} alert:")
        print(f"     Timestamp: {alert_timestamp}")
        print(f"     Old mc_usd: ${old_mc_usd:,.0f}" if old_mc_usd else "     Old mc_usd: None")
        print(f"     Old current_mcap: ${old_current_mcap:,.0f}" if old_current_mcap else "     Old current_mcap: None")
        
        # Update current_mcap (this is what was shown in Telegram post)
        alert['current_mcap'] = new_current_mcap
        alert['mc_usd'] = new_current_mcap  # Also update mc_usd to match
        
        # Update entry_mc if provided
        if entry_mc is not None:
            alert['entry_mc'] = entry_mc
        
        updated_count += 1
        print(f"     ✅ Updated:")
        print(f"        current_mcap: ${new_current_mcap:,.0f}")
        print(f"        mc_usd: ${new_current_mcap:,.0f}")
        if entry_mc is not None:
            print(f"        entry_mc: ${entry_mc:,.0f}")
    
    if updated_count > 0:
        try:
            with open(KPI_LOGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"\n✅ Saved to {KPI_LOGS_FILE}")
            print(f"✅ Updated {updated_count} alert(s)")
        except Exception as e:
            print(f"❌ Error saving {KPI_LOGS_FILE}: {e}")
            return
    else:
        print(f"\n⚠️  No matching alerts found to update")

if __name__ == "__main__":
    fix_mcap()

