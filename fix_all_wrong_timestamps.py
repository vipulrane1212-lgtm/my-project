#!/usr/bin/env python3
"""Fix all wrong timestamps - convert IST to UTC."""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
import shutil

KPI_LOGS_FILE = Path("kpi_logs.json")
IST_OFFSET = timedelta(hours=5, minutes=30)

def main():
    """Fix timestamps that are in IST instead of UTC."""
    print("="*80)
    print("FIX TIMESTAMPS - CONVERT IST TO UTC")
    print("="*80)
    print()
    
    with open(KPI_LOGS_FILE, 'r', encoding='utf-8') as f:
        kpi_data = json.load(f)
    
    alerts = kpi_data.get("alerts", [])
    print(f"Found {len(alerts)} alerts")
    print()
    
    now = datetime.now(timezone.utc)
    fixed_count = 0
    
    for alert in alerts:
        # Only fix alerts that were backfilled (they have IST timestamps)
        if alert.get("source") != "telegram_export_backfill":
            continue
        
        timestamp_str = alert.get("timestamp", "")
        if not timestamp_str:
            continue
        
        try:
            # Parse current timestamp
            current_timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            if current_timestamp.tzinfo is None:
                current_timestamp = current_timestamp.replace(tzinfo=timezone.utc)
            else:
                current_timestamp = current_timestamp.astimezone(timezone.utc)
            
            # Check if timestamp is in the future (more than 1 hour ahead)
            time_diff = (current_timestamp - now).total_seconds()
            
            if time_diff > 3600:  # More than 1 hour in the future
                # This is likely an IST timestamp stored as UTC
                # Convert IST to UTC by subtracting 5:30
                corrected_timestamp = current_timestamp - IST_OFFSET
                
                token = alert.get("token", "UNKNOWN")
                print(f"Fixing {token}:")
                print(f"  Old: {current_timestamp.isoformat()} (in future by {int(time_diff/3600)}h)")
                print(f"  New: {corrected_timestamp.isoformat()}")
                
                alert["timestamp"] = corrected_timestamp.isoformat()
                fixed_count += 1
        except Exception as e:
            print(f"Error fixing alert: {e}")
            continue
    
    if fixed_count > 0:
        # Backup
        backup_file = KPI_LOGS_FILE.with_suffix('.json.backup')
        shutil.copy2(KPI_LOGS_FILE, backup_file)
        print(f"\nCreated backup: {backup_file}")
        
        # Save
        kpi_data["alerts"] = alerts
        kpi_data["last_updated"] = datetime.now(timezone.utc).isoformat()
        
        with open(KPI_LOGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(kpi_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n[SUCCESS] Fixed {fixed_count} alert timestamps (IST -> UTC)")
    else:
        print("\nNo timestamps needed fixing")

if __name__ == "__main__":
    main()

