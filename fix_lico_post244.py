#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix LICO post 244 - should be Tier 3, not Tier 1"""

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
LICO_CONTRACT = "678QT3ZQCCBLJJZB5IC5FVMAV94AYRIWSZ3FUYSRVYNC"

def fix_lico_post244():
    """Fix LICO post 244 - Telegram post says TIER 3, but JSON has Tier 1"""
    print("=" * 80)
    print("FIXING LICO POST 244 - TIER MISMATCH")
    print("=" * 80)
    
    # Post 244 details:
    # - Posted: Dec 26 at 10:50 (around 10:50 AM UTC)
    # - Shows: "TIER 3 LOCKED"
    # - Token: LICO
    # - Current MC: $265.6K
    # - Contract: 678QT3ZQCCBLJJZB5IC5FVMAV94AYRIWSZ3FUYSRVYNC
    
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
    print(f"\n📋 Loaded {len(alerts)} alerts")
    
    # Find LICO alerts
    lico_alerts = [
        a for a in alerts 
        if a.get('token', '').upper() == 'LICO' 
        and a.get('contract', '') == LICO_CONTRACT
    ]
    
    print(f"\n🔍 Found {len(lico_alerts)} LICO alerts")
    
    # Create backup
    backup_path = KPI_LOGS_FILE.with_suffix('.json.backup4')
    shutil.copy2(KPI_LOGS_FILE, backup_path)
    print(f"📦 Backup created: {backup_path}")
    
    # Post 244 was posted around 10:50 AM UTC on Dec 26
    # That's approximately 2025-12-26T10:50:00+00:00
    # The alert in JSON is 2025-12-26T02:44:50 (2:44 AM)
    # So post 244 is a NEWER alert that might not be in JSON yet, OR
    # The existing alert needs to be updated to Tier 3
    
    # Post 244 details:
    # - MC: $265.6K (much higher than the 02:44:50 alert which has $51.7K)
    # - Tier: 3 (not 1)
    # - Posted: Dec 26 at 10:50 AM
    
    # Check if there's an alert around 10:50 AM or with MC around $265K
    post244_mc = 265600.0  # $265.6K
    
    updated_count = 0
    
    for alert in alerts:
        if alert.get('token', '').upper() == 'LICO' and alert.get('contract') == LICO_CONTRACT:
            timestamp = alert.get('timestamp', '')
            current_tier = alert.get('tier')
            mc_usd = alert.get('mc_usd') or alert.get('entry_mc', 0)
            
            print(f"\n  LICO Alert:")
            print(f"    Timestamp: {timestamp}")
            print(f"    Current tier: {current_tier}")
            print(f"    MC: ${mc_usd:,.0f}")
            
            # Post 244 has MC: $265.6K
            # The alert at 02:44:50 has MC: $51.7K
            # So post 244 is a DIFFERENT alert (newer, higher MC)
            
            # Check if this alert matches post 244
            # Post 244: MC around $265K
            # Check if this alert matches post 244 by MC
            if 200000 <= mc_usd <= 300000:
                # This matches post 244 MC ($265.6K) - should be Tier 3
                if current_tier != 3:
                    alert['tier'] = 3
                    updated_count += 1
                    print(f"    ✅ Updated to Tier 3 (Post 244 - MC ${mc_usd:,.0f}K matches, Telegram says TIER 3)")
                else:
                    print(f"    ✅ Already Tier 3 (Post 244)")
            elif current_tier == 1 and mc_usd < 100000:
                # This is the older alert (02:44:50) with MC $51.7K
                # Post 244 is a DIFFERENT alert (newer, MC $265.6K)
                # But the API is showing this one because post 244 might not be in JSON yet
                print(f"    ℹ️  Older alert (MC ${mc_usd:,.0f}K) - this is NOT post 244")
                print(f"       Post 244 has MC $265.6K and is Tier 3")
                print(f"       If post 244 is not in JSON, it hasn't been processed yet")
    
    # If post 244 alert is not in JSON yet, we need to add it
    # But we can't do that without more data from the alert
    
    # For now, let's check if the latest LICO alert should be Tier 3
    # Based on the API response, it's showing the 02:44:50 alert as Tier 1
    # But post 244 (10:50 AM) is Tier 3 and is newer
    
    # Actually, wait - if post 244 is newer and not in JSON, that means the bot hasn't processed it yet
    # OR the bot processed it but saved it with the wrong tier
    
    # Let me check: The user is seeing post 244 as Tier 3 in Telegram, but API shows Tier 1
    # This means either:
    # 1. Post 244 hasn't been saved to JSON yet (newer than latest alert)
    # 2. Post 244 was saved but with wrong tier
    
    # Since post 244 is at 10:50 AM and the latest alert in JSON is 03:20:38 (3:20 AM),
    # post 244 is NEWER and might not be in JSON yet
    
    print(f"\n⚠️  NOTE: Post 244 (10:50 AM) is NEWER than latest alert in JSON (03:20:38)")
    print(f"   If post 244 hasn't been processed yet, it won't be in the API response.")
    print(f"   The API is showing the older LICO alert (02:44:50) with Tier 1.")
    
    # Save updated data
    if updated_count > 0:
        try:
            with open(KPI_LOGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"\n✅ Saved to {KPI_LOGS_FILE}")
            print(f"✅ Updated {updated_count} LICO alert(s)")
        except Exception as e:
            print(f"❌ Error saving {KPI_LOGS_FILE}: {e}")
            return
    else:
        print(f"\n⚠️  No LICO alerts were updated")
        print(f"   Post 244 might not be in JSON yet (it's newer than the latest alert)")

if __name__ == "__main__":
    fix_lico_post244()

