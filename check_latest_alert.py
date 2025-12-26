#!/usr/bin/env python3
"""Quick script to check the latest alert timestamp in kpi_logs.json"""

import json
from datetime import datetime, timezone
from pathlib import Path

def check_latest_alert():
    kpi_file = Path("kpi_logs.json")
    if not kpi_file.exists():
        print("ERROR: kpi_logs.json not found")
        return
    
    try:
        with open(kpi_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        alerts = data.get("alerts", [])
        if not alerts:
            print("WARNING: No alerts found in kpi_logs.json")
            return
        
        # Find latest alert
        latest = max(alerts, key=lambda x: x.get("timestamp", ""))
        
        latest_time = datetime.fromisoformat(latest.get("timestamp", "2000-01-01"))
        now = datetime.now(timezone.utc)
        diff = now - latest_time
        
        hours_ago = diff.total_seconds() / 3600
        minutes_ago = diff.total_seconds() / 60
        
        print("Latest Alert Info:")
        print(f"   Token: {latest.get('token', 'UNKNOWN')}")
        print(f"   Contract: {latest.get('contract', 'UNKNOWN')[:20]}...")
        print(f"   Tier: {latest.get('tier', 'N/A')}")
        print(f"   Level: {latest.get('level', 'N/A')}")
        print(f"   Timestamp: {latest.get('timestamp')}")
        print(f"   Time ago: {hours_ago:.1f} hours ({minutes_ago:.0f} minutes)")
        print(f"\nTotal alerts in file: {len(alerts)}")
        
        # Show last 5 alerts
        sorted_alerts = sorted(alerts, key=lambda x: x.get("timestamp", ""), reverse=True)
        print(f"\nLast 5 alerts:")
        for i, alert in enumerate(sorted_alerts[:5], 1):
            alert_time = datetime.fromisoformat(alert.get("timestamp", "2000-01-01"))
            alert_diff = now - alert_time
            alert_hours = alert_diff.total_seconds() / 3600
            print(f"   {i}. {alert.get('token', 'UNKNOWN')} - {alert_hours:.1f}h ago ({alert.get('level', 'N/A')})")
        
    except Exception as e:
        print(f"ERROR: Error reading kpi_logs.json: {e}")

if __name__ == "__main__":
    check_latest_alert()

