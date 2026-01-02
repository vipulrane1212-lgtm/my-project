#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check if recent alerts (DHG, MWG, BLAST) are in kpi_logs.json
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

KPI_LOGS_FILE = Path("kpi_logs.json")

# The 3 missing alerts from user report
MISSING_ALERTS = [
    {
        "token": "DHG",
        "contract": "3R48QGXWZN5WYQZUWOXQXUFVUEEUYC9WDDOCSQPPBONK",
        "timestamp": "2026-01-03T00:41:00+00:00",  # Approximate from user message
        "mcap": 237600
    },
    {
        "token": "MWG",
        "contract": "3RQEUT98EKX1KJT1OWKP1WHN71XTVXAGTZB2HLQSFACK",
        "timestamp": "2026-01-03T00:45:00+00:00",
        "mcap": 143800
    },
    {
        "token": "BLAST",
        "contract": "9IEWUXV5Y9VAEK6GLVFZVKWZBMSVKEKUKAA61XATWA97",
        "timestamp": "2026-01-03T00:47:00+00:00",
        "mcap": 458400
    }
]

def check_alerts():
    print("="*80)
    print("CHECKING FOR MISSING RECENT ALERTS")
    print("="*80)
    
    if not KPI_LOGS_FILE.exists():
        print(f"❌ {KPI_LOGS_FILE} not found!")
        return
    
    with open(KPI_LOGS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    alerts = data.get("alerts", [])
    print(f"\n[INFO] Total alerts in kpi_logs.json: {len(alerts)}")
    
    # Check each missing alert
    for missing in MISSING_ALERTS:
        print(f"\n[CHECK] Checking for {missing['token']}...")
        print(f"   Contract: {missing['contract']}")
        print(f"   Expected timestamp: {missing['timestamp']}")
        
        # Search by contract (most reliable)
        found_by_contract = None
        for alert in alerts:
            if alert.get("contract") == missing["contract"]:
                found_by_contract = alert
                break
        
        # Search by token and timestamp (within 10 minutes)
        found_by_token = None
        missing_time = datetime.fromisoformat(missing["timestamp"].replace("Z", "+00:00"))
        for alert in alerts:
            if alert.get("token") == missing["token"]:
                alert_time_str = alert.get("timestamp", "")
                if alert_time_str:
                    try:
                        alert_time = datetime.fromisoformat(alert_time_str.replace("Z", "+00:00"))
                        time_diff = abs((alert_time - missing_time).total_seconds())
                        if time_diff < 600:  # Within 10 minutes
                            found_by_token = alert
                            break
                    except:
                        pass
        
        if found_by_contract:
            print(f"   [OK] FOUND by contract!")
            print(f"      Token: {found_by_contract.get('token')}")
            print(f"      Timestamp: {found_by_contract.get('timestamp')}")
            print(f"      MCAP: ${found_by_contract.get('mc_usd', 0):,.0f}")
            print(f"      Tier: {found_by_contract.get('tier')}")
        elif found_by_token:
            print(f"   [WARNING] FOUND by token (different contract?)")
            print(f"      Token: {found_by_token.get('token')}")
            print(f"      Contract: {found_by_token.get('contract')}")
            print(f"      Timestamp: {found_by_token.get('timestamp')}")
            print(f"      MCAP: ${found_by_token.get('mc_usd', 0):,.0f}")
        else:
            print(f"   [ERROR] NOT FOUND in kpi_logs.json")
            print(f"      This alert is MISSING!")
    
    # Check latest alerts
    print(f"\n[INFO] Latest 5 alerts in kpi_logs.json:")
    sorted_alerts = sorted(alerts, key=lambda x: x.get("timestamp", ""), reverse=True)
    for i, alert in enumerate(sorted_alerts[:5], 1):
        token = alert.get("token", "UNKNOWN")
        timestamp = alert.get("timestamp", "")[:19]
        contract = alert.get("contract", "")[:20] + "..." if alert.get("contract") else "N/A"
        print(f"   {i}. {token} - {timestamp} - {contract}")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    check_alerts()

