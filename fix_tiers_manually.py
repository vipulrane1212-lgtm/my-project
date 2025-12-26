#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Manually fix tier field in kpi_logs.json using heuristics from API server"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

KPI_LOGS_FILE = Path("kpi_logs.json")


def get_tier_from_level(level: str, alert_tier: int = None, alert_data: dict = None) -> int:
    """Convert alert level to tier number using same logic as API server."""
    # If tier is explicitly provided, use it
    if alert_tier is not None and alert_tier in [1, 2, 3]:
        return alert_tier
    
    level_upper = level.upper()
    
    # Explicit tier strings
    if level_upper in ["ULTRA", "TIER 1", "TIER1", "1"]:
        return 1
    elif level_upper in ["TIER 2", "TIER2", "2"]:
        return 2
    elif level_upper in ["TIER 3", "TIER3", "3"]:
        return 3
    
    # CRITICAL: Tier 1 alerts are stored as level="HIGH"
    if "HIGH" in level_upper:
        return 1  # Tier 1 uses HIGH
    
    # PROBLEM: Both Tier 2 and Tier 3 use MEDIUM level
    # We need to use heuristics to distinguish them when tier field is missing
    elif "MEDIUM" in level_upper:
        if alert_data:
            # Try to infer tier from alert data
            # Tier 2: Has Glydo top 5 + confirmations
            # Tier 3: No Glydo top 5 OR delayed Glydo OR multiple non-Glydo confirmations
            
            glydo_in_top5 = alert_data.get("glydo_in_top5", False)
            hot_list = alert_data.get("hot_list")
            if isinstance(hot_list, dict):
                was_in_hot_list = hot_list.get("was_in_hot_list", False)
            else:
                was_in_hot_list = bool(hot_list)
            
            # If has Glydo top 5, more likely Tier 2
            if glydo_in_top5 or was_in_hot_list:
                # Check confirmations - Tier 2 needs at least 1 confirmation
                confirmations = alert_data.get("confirmations", {})
                if isinstance(confirmations, dict):
                    total_confirmations = confirmations.get("total", 0)
                    strong_confirmations = confirmations.get("strong_total", 0)
                    if total_confirmations >= 1 or strong_confirmations >= 1:
                        return 2  # Tier 2: Glydo top 5 + confirmations
            
            # Default MEDIUM to Tier 3 (more common, and safer default)
            return 3
        
        # No alert data available - default MEDIUM to Tier 3
        return 3
    
    return 3  # Default to tier 3


def fix_tiers():
    """Fix tier field in kpi_logs.json using heuristics."""
    print("=" * 80)
    print("FIXING TIER FIELD IN kpi_logs.json")
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
    
    # Create backup
    backup_path = KPI_LOGS_FILE.with_suffix('.json.backup')
    import shutil
    shutil.copy2(KPI_LOGS_FILE, backup_path)
    print(f"📦 Backup created: {backup_path}")
    
    # Fix tiers
    updated_count = 0
    tier_distribution = defaultdict(int)
    
    print(f"\n🔧 Fixing tiers...")
    
    for alert in alerts:
        # Skip if tier already exists
        if alert.get('tier') is not None:
            continue
        
        # Get level
        level = alert.get('level', 'MEDIUM')
        
        # Infer tier using heuristics
        tier = get_tier_from_level(level, None, alert)
        
        # Update alert
        alert['tier'] = tier
        tier_distribution[tier] += 1
        updated_count += 1
        
        token = alert.get('token', 'UNKNOWN')
        print(f"  ✅ {token}: level={level} → tier={tier}")
    
    # Save updated data
    try:
        with open(KPI_LOGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Saved to {KPI_LOGS_FILE}")
    except Exception as e:
        print(f"❌ Error saving {KPI_LOGS_FILE}: {e}")
        return
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"✅ Updated {updated_count} alerts with tier field")
    print(f"\n📊 Tier Distribution:")
    print(f"  Tier 1: {tier_distribution[1]}")
    print(f"  Tier 2: {tier_distribution[2]}")
    print(f"  Tier 3: {tier_distribution[3]}")
    print(f"  Total: {sum(tier_distribution.values())}")
    
    # Verify
    alerts_with_tier = [a for a in alerts if a.get('tier') is not None]
    print(f"\n✅ Alerts with tier field: {len(alerts_with_tier)}/{len(alerts)} ({len(alerts_with_tier)/len(alerts)*100:.1f}%)")
    
    print(f"\n💡 Note: Tiers were inferred using heuristics:")
    print(f"   - HIGH level → Tier 1")
    print(f"   - MEDIUM level with Glydo Top 5 + confirmations → Tier 2")
    print(f"   - MEDIUM level without Glydo Top 5 → Tier 3")
    print(f"\n   For 100% accuracy, run backfill script to get tiers from Telegram posts.")


if __name__ == "__main__":
    fix_tiers()

