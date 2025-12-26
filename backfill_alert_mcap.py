#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
backfill_alert_mcap.py

Backfill market cap data for old alerts in kpi_logs.json.
Tries to get MCAP from:
1. Live store (if still available)
2. DexScreener API (current MCAP - not historical, but better than nothing)
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone
import time

# Try to import dependencies
try:
    from live_store import LiveStore
    LIVE_STORE_AVAILABLE = True
except ImportError:
    LIVE_STORE_AVAILABLE = False
    print("⚠️  live_store not available")

try:
    from dexscreener_fetcher import get_live_mcap_and_symbol
    DEXSCREENER_AVAILABLE = True
except ImportError:
    DEXSCREENER_AVAILABLE = False
    print("⚠️  dexscreener_fetcher not available")


def load_kpi_logs(file_path: str = "kpi_logs.json") -> Dict:
    """Load KPI logs from file."""
    log_file = Path(file_path)
    if not log_file.exists():
        print(f"❌ File not found: {file_path}")
        return {}
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading {file_path}: {e}")
        return {}


def save_kpi_logs(data: Dict, file_path: str = "kpi_logs.json"):
    """Save KPI logs to file."""
    log_file = Path(file_path)
    try:
        # Create backup
        backup_path = log_file.with_suffix('.json.backup')
        if log_file.exists():
            import shutil
            shutil.copy2(log_file, backup_path)
            print(f"📦 Backup created: {backup_path}")
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved to {file_path}")
    except Exception as e:
        print(f"❌ Error saving {file_path}: {e}")


def get_mcap_from_live_store(store: LiveStore, token: str, contract: str) -> Optional[float]:
    """Try to get MCAP from live store."""
    if not LIVE_STORE_AVAILABLE:
        return None
    
    try:
        # Try with token first
        mcap_data = store.get_last_mcap(token)
        if mcap_data and isinstance(mcap_data, dict):
            mcap = mcap_data.get("mc_usd")
            if mcap:
                return float(mcap)
        
        # Try with contract as fallback
        mcap_data = store.get_last_mcap(contract)
        if mcap_data and isinstance(mcap_data, dict):
            mcap = mcap_data.get("mc_usd")
            if mcap:
                return float(mcap)
    except Exception as e:
        print(f"  ⚠️  Live store error for {token}: {e}")
    
    return None


def get_mcap_from_dexscreener(contract: str) -> Optional[float]:
    """Try to get current MCAP from DexScreener (not historical, but better than nothing)."""
    if not DEXSCREENER_AVAILABLE:
        return None
    
    if not contract or len(contract) < 20:
        return None
    
    try:
        symbol, mcap, liq, chain_id = get_live_mcap_and_symbol(contract)
        if mcap:
            return float(mcap)
        # Small delay to avoid rate limiting
        time.sleep(0.5)
    except Exception as e:
        print(f"  ⚠️  DexScreener error for {contract}: {e}")
    
    return None


def backfill_alerts_mcap(kpi_data: Dict, use_dexscreener: bool = False) -> Dict:
    """Backfill MCAP for alerts that don't have it."""
    alerts = kpi_data.get("alerts", [])
    
    if not alerts:
        print("❌ No alerts found in kpi_logs.json")
        return kpi_data
    
    print(f"Found {len(alerts)} alerts")
    
    # Initialize live store if available
    store = None
    if LIVE_STORE_AVAILABLE:
        try:
            store = LiveStore()
            print("Live store initialized")
        except Exception as e:
            print(f"Could not initialize live store: {e}")
    
    # Count alerts without MCAP
    alerts_without_mcap = [a for a in alerts if not a.get("mc_usd") and not a.get("entry_mc")]
    print(f"Found {len(alerts_without_mcap)} alerts without MCAP")
    
    if not alerts_without_mcap:
        print("✅ All alerts already have MCAP!")
        return kpi_data
    
    # Process alerts
    updated_count = 0
    skipped_count = 0
    
    for i, alert in enumerate(alerts):
        # Skip if already has MCAP
        if alert.get("mc_usd") or alert.get("entry_mc"):
            continue
        
        token = alert.get("token", "")
        contract = alert.get("contract", "")
        
        if not contract:
            skipped_count += 1
            continue
        
        print(f"\n[{i+1}/{len(alerts_without_mcap)}] Processing {token} ({contract[:8]}...)")
        
        mcap = None
        source = None
        
        # Try live store first (most likely to have historical data)
        if store:
            mcap = get_mcap_from_live_store(store, token, contract)
            if mcap:
                source = "live_store"
                print(f"  [OK] Found MCAP from live store: ${mcap:,.2f}")
        
        # Try DexScreener as fallback (current MCAP, not historical)
        if not mcap and use_dexscreener:
            mcap = get_mcap_from_dexscreener(contract)
            if mcap:
                source = "dexscreener_current"
                print(f"  [WARN] Found CURRENT MCAP from DexScreener: ${mcap:,.2f} (not historical)")
        
        # Update alert
        if mcap:
            alert["mc_usd"] = mcap
            if source:
                alert["mc_source"] = source
            updated_count += 1
        else:
            skipped_count += 1
            print(f"  [FAIL] Could not find MCAP for {token}")
    
    # Update data
    kpi_data["alerts"] = alerts
    kpi_data["last_updated"] = datetime.now(timezone.utc).isoformat()
    kpi_data["backfill_info"] = {
        "backfilled_at": datetime.now(timezone.utc).isoformat(),
        "updated_count": updated_count,
        "skipped_count": skipped_count,
        "total_alerts": len(alerts)
    }
    
    print(f"\n{'='*60}")
    print(f"Backfill Summary:")
    print(f"  Updated: {updated_count} alerts")
    print(f"  Skipped: {skipped_count} alerts")
    print(f"  Total: {len(alerts)} alerts")
    print(f"{'='*60}")
    
    return kpi_data


def main():
    """Main function."""
    print("="*60)
    print("Backfilling Market Cap for Old Alerts")
    print("="*60)
    
    # Load KPI logs
    kpi_data = load_kpi_logs()
    if not kpi_data:
        return
    
    # Ask user if they want to use DexScreener (for current MCAP)
    print("\nNote: DexScreener will return CURRENT market cap, not historical.")
    print("   This is better than nothing, but won't be the exact MCAP from alert time.")
    use_dexscreener = input("\nUse DexScreener for alerts without MCAP? (y/n): ").lower().strip() == 'y'
    
    # Backfill
    updated_data = backfill_alerts_mcap(kpi_data, use_dexscreener=use_dexscreener)
    
    # Save
    if updated_data.get("backfill_info", {}).get("updated_count", 0) > 0:
        save_confirm = input("\nSave changes? (y/n): ").lower().strip() == 'y'
        if save_confirm:
            save_kpi_logs(updated_data)
            print("\nBackfill complete!")
        else:
            print("\nChanges not saved")
    else:
        print("\nNo changes needed - all alerts already have MCAP or couldn't be updated")


if __name__ == "__main__":
    main()

