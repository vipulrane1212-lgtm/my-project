#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
backfill_entry_mcap.py

Backfill entry_mcap field for all historical alerts.
Entry MCAP = The MCAP that was shown in the Telegram post (the "Current MC" at posting time).

This script:
1. Loads all alerts from kpi_logs.json
2. For each alert, sets entry_mc = current_mcap (the MCAP shown in Telegram post)
3. If current_mcap is missing, uses mc_usd as fallback
4. Saves the updated alerts back to kpi_logs.json
"""

import json
from pathlib import Path
from datetime import datetime, timezone

KPI_LOGS_FILE = "kpi_logs.json"

def load_kpi_logs():
    """Load KPI logs from file."""
    if not Path(KPI_LOGS_FILE).exists():
        print(f"ERROR: {KPI_LOGS_FILE} not found")
        return None
    
    try:
        with open(KPI_LOGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"ERROR: Error loading {KPI_LOGS_FILE}: {e}")
        return None

def save_kpi_logs(data):
    """Save KPI logs to file with backup."""
        # Create backup
    backup_file = f"{KPI_LOGS_FILE}.backup_entry_mcap"
    if Path(KPI_LOGS_FILE).exists():
        import shutil
        shutil.copy2(KPI_LOGS_FILE, backup_file)
        print(f"Backup created: {backup_file}")
    
    try:
        with open(KPI_LOGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Saved to {KPI_LOGS_FILE}")
        return True
    except Exception as e:
        print(f"ERROR: Error saving {KPI_LOGS_FILE}: {e}")
        return False

def backfill_entry_mcap():
    """Backfill entry_mcap for all alerts."""
    print("="*80)
    print("BACKFILLING ENTRY MCAP FOR ALL ALERTS")
    print("="*80)
    print("Entry MCAP = MCAP shown in Telegram post (the 'Current MC' at posting time)")
    print()
    
    # Load KPI logs
    kpi_data = load_kpi_logs()
    if not kpi_data:
        return
    
    alerts = kpi_data.get("alerts", [])
    print(f"Loaded {len(alerts)} alerts")
    print()
    
    updated_count = 0
    no_mcap_count = 0
    
    for alert in alerts:
        # Get the MCAP that was shown in the Telegram post
        # Priority: current_mcap > mc_usd > entry_mc (old field)
        entry_mcap_value = None
        
        # First try current_mcap (this is what was shown in Telegram post)
        current_mcap = alert.get("current_mcap")
        if current_mcap is not None:
            try:
                entry_mcap_value = float(current_mcap)
            except (ValueError, TypeError):
                pass
        
        # If no current_mcap, try mc_usd (this should be the current MCAP from the post)
        if entry_mcap_value is None:
            mc_usd = alert.get("mc_usd")
            if mc_usd is not None:
                try:
                    entry_mcap_value = float(mc_usd)
                except (ValueError, TypeError):
                    pass
        
        # If still no value, try old entry_mc field (might have the value)
        if entry_mcap_value is None:
            entry_mc_old = alert.get("entry_mc")
            if entry_mc_old is not None:
                try:
                    entry_mcap_value = float(entry_mc_old)
                except (ValueError, TypeError):
                    pass
        
        # Update entry_mc field with the MCAP from the Telegram post
        if entry_mcap_value is not None:
            # Update entry_mc to be the MCAP shown in Telegram post
            alert["entry_mc"] = entry_mcap_value
            # Also ensure current_mcap is set (for consistency)
            if alert.get("current_mcap") is None:
                alert["current_mcap"] = entry_mcap_value
            updated_count += 1
        else:
            no_mcap_count += 1
            token = alert.get("token", "UNKNOWN")
            timestamp = alert.get("timestamp", "UNKNOWN")
            print(f"WARNING: No MCAP data for {token} at {timestamp}")
    
    print()
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total alerts: {len(alerts)}")
    print(f"Updated (entry_mc set): {updated_count}")
    print(f"No MCAP data available: {no_mcap_count}")
    print()
    
    if updated_count > 0:
        # Update last_updated timestamp
        kpi_data["last_updated"] = datetime.now(timezone.utc).isoformat()
        
        if save_kpi_logs(kpi_data):
            print("SUCCESS: Backfill complete!")
            print(f"SUCCESS: {updated_count} alerts now have entry_mc = MCAP from Telegram post")
            if no_mcap_count > 0:
                print(f"WARNING: {no_mcap_count} alerts couldn't be updated (no MCAP data)")
        else:
            print("ERROR: Failed to save updated alerts")
    else:
        print("WARNING: No alerts needed updating")

if __name__ == "__main__":
    backfill_entry_mcap()

