#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check kpi_logs.json and sync to Git if needed"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def check_kpi_logs():
    """Check kpi_logs.json for recent alerts"""
    kpi_file = Path("kpi_logs.json")
    
    if not kpi_file.exists():
        print("[ERROR] kpi_logs.json not found!")
        return
    
    try:
        with open(kpi_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        alerts = data.get('alerts', [])
        print(f"Total alerts in file: {len(alerts)}")
        
        if not alerts:
            print("[WARN] No alerts found in file!")
            return
        
        # Sort by timestamp
        sorted_alerts = sorted(
            alerts,
            key=lambda x: datetime.fromisoformat(x.get('timestamp', '2000-01-01')).replace(tzinfo=timezone.utc),
            reverse=True
        )
        
        print("\nLast 10 alerts:")
        for i, alert in enumerate(sorted_alerts[:10], 1):
            token = alert.get('token', 'N/A')
            timestamp = alert.get('timestamp', 'N/A')
            tier = alert.get('tier', 'N/A')
            
            # Calculate time ago
            try:
                alert_time = datetime.fromisoformat(timestamp).replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                delta = now - alert_time
                
                if delta.days > 0:
                    time_ago = f"{delta.days}d {delta.seconds // 3600}h ago"
                elif delta.seconds >= 3600:
                    time_ago = f"{delta.seconds // 3600}h {(delta.seconds % 3600) // 60}m ago"
                elif delta.seconds >= 60:
                    time_ago = f"{delta.seconds // 60}m ago"
                else:
                    time_ago = f"{delta.seconds}s ago"
            except:
                time_ago = "unknown"
            
            print(f"  {i}. {token} - Tier {tier} - {time_ago}")
        
        # Check if latest alert is recent (within last 24 hours)
        latest = sorted_alerts[0]
        latest_time_str = latest.get('timestamp', '')
        try:
            latest_time = datetime.fromisoformat(latest_time_str).replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            hours_ago = (now - latest_time).total_seconds() / 3600
            
            print(f"\nLatest alert: {hours_ago:.1f} hours ago")
            
            if hours_ago > 24:
                print("[WARN] Latest alert is more than 24 hours old!")
            else:
                print("[OK] Latest alert is recent")
        except Exception as e:
            print(f"[WARN] Could not parse latest alert time: {e}")
        
        return sorted_alerts
        
    except Exception as e:
        print(f"[ERROR] Error reading kpi_logs.json: {e}")
        return None

if __name__ == "__main__":
    check_kpi_logs()

