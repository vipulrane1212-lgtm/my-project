#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Directly fix HONSE tier based on user's correction"""

import json
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

KPI_LOGS_FILE = Path("kpi_logs.json")
HONSE_CONTRACT = "5ZQU5EUPKBUBSWLSBOC7QNF7DS8XDRLNEWEPAAIGPUMP"

def fix_honse_tiers():
    """Fix HONSE alert tiers based on Telegram posts."""
    print("=" * 80)
    print("FIXING HONSE TIER BASED ON TELEGRAM POSTS")
    print("=" * 80)
    
    # Load kpi_logs
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
    
    # Find HONSE alerts
    honse_alerts = [
        a for a in alerts 
        if a.get('token', '').upper() == 'HONSE' 
        or a.get('contract', '') == HONSE_CONTRACT
    ]
    
    print(f"\n🔍 Found {len(honse_alerts)} HONSE alerts")
    
    # Create backup
    backup_path = KPI_LOGS_FILE.with_suffix('.json.backup3')
    import shutil
    shutil.copy2(KPI_LOGS_FILE, backup_path)
    print(f"📦 Backup created: {backup_path}")
    
    # Based on user's information:
    # Post 243: Should be Tier 1 (was posted as "TIER 2 LOCKED")
    # Post 239: Correctly Tier 2 (has Glydo Top 5 + 4 confirmations)
    
    # Sort by timestamp (newest first)
    honse_alerts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    updated_count = 0
    
    for i, alert in enumerate(honse_alerts):
        token = alert.get('token', 'UNKNOWN')
        timestamp = alert.get('timestamp', '')
        current_tier = alert.get('tier')
        
        print(f"\n  Alert #{i+1}:")
        print(f"    Token: {token}")
        print(f"    Timestamp: {timestamp}")
        print(f"    Current tier: {current_tier}")
        
        # Most recent HONSE alert (index 0) is likely post 243 - should be Tier 1
        if i == 0:
            if current_tier != 1:
                alert['tier'] = 1
                updated_count += 1
                print(f"    ✅ Updated to Tier 1 (Post 243 - was incorrectly posted as Tier 2)")
            else:
                print(f"    ✅ Already Tier 1 (Post 243)")
        
        # Older HONSE alert (index 1) might be post 239 - should be Tier 2
        # But we need to check if it has the characteristics
        elif i == 1:
            # Check if it has characteristics of post 239 (Glydo + 4 confirmations)
            # Since we don't have that data saved, we'll leave it as is for now
            # Or update to Tier 2 if user confirms
            print(f"    ℹ️  Older alert - keeping current tier {current_tier}")
            print(f"       (If this is post 239, it should be Tier 2)")
    
    # Save updated data
    if updated_count > 0:
        try:
            with open(KPI_LOGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"\n✅ Saved to {KPI_LOGS_FILE}")
            print(f"✅ Updated {updated_count} HONSE alert(s)")
        except Exception as e:
            print(f"❌ Error saving {KPI_LOGS_FILE}: {e}")
            return
    else:
        print(f"\n⚠️  No HONSE alerts were updated")

if __name__ == "__main__":
    fix_honse_tiers()

