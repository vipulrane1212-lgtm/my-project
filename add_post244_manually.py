#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Manually add Post 244 (LICO, Tier 3) to kpi_logs.json"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone
import shutil

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

KPI_LOGS_FILE = Path("kpi_logs.json")
LICO_CONTRACT = "678QT3ZQCCBLJJZB5IC5FVMAV94AYRIWSZ3FUYSRVYNC"

def add_post244():
    """Add Post 244 to kpi_logs.json"""
    print("=" * 80)
    print("ADDING POST 244 (LICO, TIER 3) TO JSON")
    print("=" * 80)
    
    # Post 244 details from Telegram
    post244_timestamp = "2025-12-26T10:50:00.000000+00:00"  # Dec 26 at 10:50 AM
    post244_mc = 265600.0  # $265.6K
    
    if not KPI_LOGS_FILE.exists():
        print(f"❌ {KPI_LOGS_FILE} not found!")
        return
    
    # Create backup
    backup_path = KPI_LOGS_FILE.with_suffix('.json.backup5')
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
    
    # Check if post 244 already exists
    existing = [
        a for a in alerts
        if a.get('token', '').upper() == 'LICO'
        and a.get('contract') == LICO_CONTRACT
        and 200000 <= (a.get('mc_usd') or a.get('entry_mc', 0)) <= 300000
    ]
    
    if existing:
        print(f"\n⚠️  Post 244 already exists in JSON!")
        for alert in existing:
            print(f"   Timestamp: {alert.get('timestamp')}")
            print(f"   Tier: {alert.get('tier')}")
            print(f"   MC: ${(alert.get('mc_usd') or alert.get('entry_mc', 0)):,.0f}")
        return
    
    # Get the latest LICO alert to use as a template
    lico_alerts = [
        a for a in alerts
        if a.get('token', '').upper() == 'LICO'
        and a.get('contract') == LICO_CONTRACT
    ]
    
    if not lico_alerts:
        print("❌ No existing LICO alerts found to use as template!")
        return
    
    # Use the most recent LICO alert as template
    latest_lico = max(lico_alerts, key=lambda x: x.get('timestamp', ''))
    print(f"\n📋 Using latest LICO alert as template:")
    print(f"   Timestamp: {latest_lico.get('timestamp')}")
    print(f"   Tier: {latest_lico.get('tier')}")
    
    # Create post 244 alert entry
    post244_alert = latest_lico.copy()
    post244_alert.update({
        "timestamp": post244_timestamp,
        "tier": 3,  # Post 244 is TIER 3
        "level": "MEDIUM",  # Tier 3 = MEDIUM level
        "mc_usd": post244_mc,
        "entry_mc": post244_mc,
    })
    
    # Add to alerts list (insert at the end, sorted by timestamp)
    alerts.append(post244_alert)
    
    # Sort alerts by timestamp (newest first)
    alerts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    # Update last_updated
    data['last_updated'] = post244_timestamp
    
    # Save
    try:
        with open(KPI_LOGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Saved to {KPI_LOGS_FILE}")
        print(f"✅ Added Post 244 (LICO, Tier 3, MC ${post244_mc:,.0f})")
        print(f"✅ Total alerts: {len(alerts)}")
    except Exception as e:
        print(f"❌ Error saving {KPI_LOGS_FILE}: {e}")
        return
    
    # Verify
    print(f"\n🔍 Verifying...")
    verify_alert = [
        a for a in alerts
        if a.get('token', '').upper() == 'LICO'
        and a.get('contract') == LICO_CONTRACT
        and a.get('timestamp') == post244_timestamp
    ]
    
    if verify_alert:
        alert = verify_alert[0]
        print(f"✅ Post 244 verified:")
        print(f"   Token: {alert.get('token')}")
        print(f"   Tier: {alert.get('tier')} ✅")
        print(f"   MC: ${alert.get('mc_usd'):,.0f} ✅")
        print(f"   Timestamp: {alert.get('timestamp')} ✅")
    else:
        print(f"❌ Verification failed!")

if __name__ == "__main__":
    add_post244()

