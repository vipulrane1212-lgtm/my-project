#!/usr/bin/env python3
"""Verify backfill results and check data integrity"""

import json
from collections import defaultdict
from datetime import datetime, timezone

def verify_backfill():
    """Verify that backfill was successful."""
    print("=" * 80)
    print("VERIFYING BACKFILL RESULTS")
    print("=" * 80)
    
    # Load kpi_logs
    try:
        with open('kpi_logs.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading kpi_logs.json: {e}")
        return
    
    alerts = data.get('alerts', [])
    print(f"\n📊 Total alerts: {len(alerts)}")
    
    # Check tier field
    alerts_with_tier = [a for a in alerts if a.get('tier') is not None]
    alerts_without_tier = [a for a in alerts if a.get('tier') is None]
    
    print(f"\n✅ Alerts with tier field: {len(alerts_with_tier)} ({len(alerts_with_tier)/len(alerts)*100:.1f}%)")
    print(f"⚠️  Alerts without tier field: {len(alerts_without_tier)} ({len(alerts_without_tier)/len(alerts)*100:.1f}%)")
    
    # Tier distribution
    tier_dist = defaultdict(int)
    for alert in alerts:
        tier = alert.get('tier')
        if tier in [1, 2, 3]:
            tier_dist[tier] += 1
    
    print(f"\n📈 Tier Distribution (from tier field):")
    print(f"  Tier 1: {tier_dist[1]}")
    print(f"  Tier 2: {tier_dist[2]}")
    print(f"  Tier 3: {tier_dist[3]}")
    print(f"  Total: {sum(tier_dist.values())}")
    
    # Check MCAP
    alerts_with_mcap = [a for a in alerts if a.get('mc_usd') or a.get('entry_mc')]
    alerts_without_mcap = [a for a in alerts if not (a.get('mc_usd') or a.get('entry_mc'))]
    
    print(f"\n💰 MCAP Status:")
    print(f"  ✅ Alerts with MCAP: {len(alerts_with_mcap)} ({len(alerts_with_mcap)/len(alerts)*100:.1f}%)")
    print(f"  ⚠️  Alerts without MCAP: {len(alerts_without_mcap)} ({len(alerts_without_mcap)/len(alerts)*100:.1f}%)")
    
    # Check timestamps
    valid_timestamps = 0
    invalid_timestamps = 0
    for alert in alerts:
        ts = alert.get('timestamp', '')
        if ts:
            try:
                datetime.fromisoformat(ts.replace('Z', '+00:00'))
                valid_timestamps += 1
            except:
                invalid_timestamps += 1
        else:
            invalid_timestamps += 1
    
    print(f"\n⏰ Timestamp Status:")
    print(f"  ✅ Valid timestamps: {valid_timestamps}")
    print(f"  ⚠️  Invalid timestamps: {invalid_timestamps}")
    
    # Recent alerts (last 24 hours)
    now = datetime.now(timezone.utc)
    recent_count = 0
    for alert in alerts:
        ts = alert.get('timestamp', '')
        if ts:
            try:
                alert_time = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                if (now - alert_time).total_seconds() < 86400:  # 24 hours
                    recent_count += 1
            except:
                pass
    
    print(f"\n🕐 Recent Alerts (last 24h): {recent_count}")
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    
    if len(alerts_without_tier) == 0:
        print("✅ All alerts have tier field!")
    else:
        print(f"⚠️  {len(alerts_without_tier)} alerts still missing tier field")
        print("   Run backfill script to fix")
    
    if len(alerts_without_mcap) == 0:
        print("✅ All alerts have MCAP!")
    else:
        print(f"⚠️  {len(alerts_without_mcap)} alerts still missing MCAP")
        print("   Run backfill script to fix")
    
    if invalid_timestamps == 0:
        print("✅ All alerts have valid timestamps!")
    else:
        print(f"⚠️  {invalid_timestamps} alerts have invalid timestamps")
    
    print(f"\n📊 Expected Tier Distribution (after backfill):")
    print(f"  Tier 1: ~{tier_dist[1]} alerts")
    print(f"  Tier 2: ~{tier_dist[2]} alerts")
    print(f"  Tier 3: ~{tier_dist[3]} alerts")
    print(f"  Total: {sum(tier_dist.values())} alerts")

if __name__ == "__main__":
    verify_backfill()

