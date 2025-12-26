#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix old alerts in kpi_logs.json by adding current_mcap field
Uses mc_usd or entry_mc as fallback for historical alerts
"""

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

def fix_old_alerts():
    """Add current_mcap field to old alerts that are missing it."""
    print("=" * 80)
    print("FIXING OLD ALERTS - ADDING current_mcap FIELD")
    print("=" * 80)
    
    if not KPI_LOGS_FILE.exists():
        print(f"❌ {KPI_LOGS_FILE} not found!")
        return
    
    # Create backup
    backup_path = KPI_LOGS_FILE.with_suffix('.json.backup7')
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
    
    fixed_count = 0
    stats = {
        'from_mc_usd': 0,
        'from_entry_mc': 0,
        'from_live_mcap': 0,
        'already_has': 0,
        'no_data': 0
    }
    
    for alert in alerts:
        # Check if current_mcap already exists
        if alert.get('current_mcap') is not None:
            stats['already_has'] += 1
            continue
        
        # Try to get current_mcap from available fields
        # Priority: live_mcap > mc_usd > entry_mc
        current_mcap = None
        source = None
        
        # First try live_mcap (from DexScreener)
        if alert.get('live_mcap') is not None:
            current_mcap = alert.get('live_mcap')
            source = 'live_mcap'
            stats['from_live_mcap'] += 1
        
        # Then try mc_usd (this is usually the MCAP that was shown)
        elif alert.get('mc_usd') is not None:
            current_mcap = alert.get('mc_usd')
            source = 'mc_usd'
            stats['from_mc_usd'] += 1
        
        # Finally try entry_mc (MCAP when alert was triggered)
        elif alert.get('entry_mc') is not None:
            current_mcap = alert.get('entry_mc')
            source = 'entry_mc'
            stats['from_entry_mc'] += 1
        
        # If we found a value, add it
        if current_mcap is not None:
            alert['current_mcap'] = current_mcap
            alert['current_mcap_source'] = source  # Track where it came from
            fixed_count += 1
        else:
            stats['no_data'] += 1
            token = alert.get('token', 'UNKNOWN')
            timestamp = alert.get('timestamp', 'N/A')
            print(f"⚠️ No MCAP data for {token} at {timestamp}")
    
    if fixed_count > 0:
        try:
            with open(KPI_LOGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"\n✅ Saved to {KPI_LOGS_FILE}")
        except Exception as e:
            print(f"❌ Error saving {KPI_LOGS_FILE}: {e}")
            return
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total alerts: {len(alerts)}")
    print(f"Already had current_mcap: {stats['already_has']}")
    print(f"Fixed (added current_mcap): {fixed_count}")
    print(f"  - From live_mcap: {stats['from_live_mcap']}")
    print(f"  - From mc_usd: {stats['from_mc_usd']}")
    print(f"  - From entry_mc: {stats['from_entry_mc']}")
    print(f"No MCAP data available: {stats['no_data']}")
    
    if fixed_count > 0:
        print(f"\n✅ Successfully added current_mcap to {fixed_count} alert(s)")
        print(f"💡 Old alerts now have current_mcap field for API compatibility")
    else:
        print(f"\n✅ All alerts already have current_mcap field or no data available")

if __name__ == "__main__":
    fix_old_alerts()

