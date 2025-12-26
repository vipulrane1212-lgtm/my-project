#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check if Post 244 (LICO, TIER 3, MC $265.6K) is in kpi_logs.json"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

KPI_LOGS_FILE = Path("kpi_logs.json")
LICO_CONTRACT = "678QT3ZQCCBLJJZB5IC5FVMAV94AYRIWSZ3FUYSRVYNC"

def check_post244():
    """Check if Post 244 is in JSON"""
    print("=" * 80)
    print("CHECKING POST 244 STATUS")
    print("=" * 80)
    print("\nPost 244 Details:")
    print("  - Token: LICO")
    print("  - Contract: 678QT3ZQCCBLJJZB5IC5FVMAV94AYRIWSZ3FUYSRVYNC")
    print("  - Tier: 3 (from Telegram post)")
    print("  - MC: $265.6K")
    print("  - Posted: Dec 26 at 10:50 AM")
    print()
    
    if not KPI_LOGS_FILE.exists():
        print(f"❌ {KPI_LOGS_FILE} not found!")
        return
    
    try:
        with open(KPI_LOGS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading {KPI_LOGS_FILE}: {e}")
        return
    
    alerts = data.get('alerts', [])
    print(f"📋 Total alerts in JSON: {len(alerts)}")
    
    # Find all LICO alerts
    lico_alerts = [
        a for a in alerts 
        if a.get('token', '').upper() == 'LICO' 
        and a.get('contract', '') == LICO_CONTRACT
    ]
    
    print(f"\n🔍 Found {len(lico_alerts)} LICO alerts:")
    
    for i, alert in enumerate(lico_alerts, 1):
        timestamp = alert.get('timestamp', '')
        tier = alert.get('tier')
        mc_usd = alert.get('mc_usd') or alert.get('entry_mc', 0)
        level = alert.get('level', 'UNKNOWN')
        
        print(f"\n  {i}. LICO Alert:")
        print(f"     Timestamp: {timestamp}")
        print(f"     Tier: {tier}")
        print(f"     Level: {level}")
        print(f"     MC: ${mc_usd:,.0f}")
        
        # Check if this matches post 244
        if 200000 <= mc_usd <= 300000:
            print(f"     ✅ MATCHES POST 244 (MC ${mc_usd:,.0f}K is close to $265.6K)")
            if tier == 3:
                print(f"     ✅ Tier is correct (3)")
            else:
                print(f"     ❌ Tier is WRONG! Should be 3, but is {tier}")
        else:
            print(f"     ❌ NOT post 244 (MC ${mc_usd:,.0f}K doesn't match $265.6K)")
    
    # Check latest alert timestamp
    if alerts:
        latest_alert = max(alerts, key=lambda x: x.get('timestamp', ''))
        latest_time = latest_alert.get('timestamp', '')
        print(f"\n📅 Latest alert in JSON: {latest_time}")
        
        # Post 244 was posted around 10:50 AM on Dec 26
        # That's approximately 2025-12-26T10:50:00+00:00
        post244_time_str = "2025-12-26T10:50:00+00:00"
        
        try:
            latest_dt = datetime.fromisoformat(latest_time.replace('Z', '+00:00'))
            post244_dt = datetime.fromisoformat(post244_time_str.replace('Z', '+00:00'))
            
            if latest_dt < post244_dt:
                print(f"⚠️  Post 244 (10:50 AM) is NEWER than latest alert in JSON!")
                print(f"   Post 244 hasn't been processed/saved yet.")
                print(f"   The API is showing the older LICO alert because post 244 isn't in JSON.")
            else:
                print(f"✅ Latest alert is newer than post 244")
        except Exception as e:
            print(f"⚠️  Could not compare timestamps: {e}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    post244_found = any(
        200000 <= (a.get('mc_usd') or a.get('entry_mc', 0)) <= 300000
        for a in lico_alerts
    )
    
    if post244_found:
        matching_alert = next(
            a for a in lico_alerts
            if 200000 <= (a.get('mc_usd') or a.get('entry_mc', 0)) <= 300000
        )
        if matching_alert.get('tier') == 3:
            print("✅ Post 244 is in JSON with correct tier (3)")
        else:
            print(f"❌ Post 244 is in JSON but tier is WRONG! Should be 3, but is {matching_alert.get('tier')}")
    else:
        print("❌ Post 244 is NOT in JSON yet!")
        print("   The bot hasn't processed/saved post 244 yet.")
        print("   The API is showing the older LICO alert (02:44:50, tier 1) because")
        print("   post 244 (10:50 AM, tier 3) hasn't been saved to JSON yet.")

if __name__ == "__main__":
    check_post244()

