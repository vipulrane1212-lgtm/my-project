#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyze kpi_logs.json for gaps and issues
Shows recent alerts and identifies potential problems
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

KPI_LOGS_FILE = Path("kpi_logs.json")

def analyze_alerts():
    """Analyze alerts in kpi_logs.json for issues."""
    print("=" * 80)
    print("ANALYZING kpi_logs.json FOR ISSUES")
    print("=" * 80)
    
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
    print(f"📋 Total alerts in JSON: {len(alerts)}")
    
    if not alerts:
        print("⚠️ No alerts found in JSON!")
        return
    
    # Sort by timestamp
    alerts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    # Analyze recent alerts (last 24 hours)
    now = datetime.now(timezone.utc)
    recent_alerts = []
    alerts_by_token = defaultdict(list)
    
    for alert in alerts:
        try:
            alert_time = datetime.fromisoformat(alert.get('timestamp', '').replace('Z', '+00:00'))
            hours_ago = (now - alert_time).total_seconds() / 3600
            
            if hours_ago <= 24:
                recent_alerts.append((alert, hours_ago))
            
            token = alert.get('token', 'UNKNOWN').upper()
            alerts_by_token[token].append(alert)
        except Exception:
            continue
    
    print(f"\n📊 Recent alerts (last 24 hours): {len(recent_alerts)}")
    print("\n" + "-" * 80)
    
    # Show recent alerts with potential issues
    issues_found = []
    for alert, hours_ago in recent_alerts[:20]:  # Show last 20
        token = alert.get('token', 'UNKNOWN')
        tier = alert.get('tier', '?')
        timestamp = alert.get('timestamp', 'N/A')
        current_mcap = alert.get('current_mcap')
        mc_usd = alert.get('mc_usd', 0)
        entry_mc = alert.get('entry_mc')
        contract = alert.get('contract', 'N/A')[:8] + '...'
        
        # Check for issues
        issues = []
        if current_mcap is None:
            issues.append("❌ Missing current_mcap field")
        if entry_mc is None:
            issues.append("⚠️ Missing entry_mc field")
        if tier is None or tier not in [1, 2, 3]:
            issues.append("❌ Invalid or missing tier")
        
        status = "✅" if not issues else "⚠️"
        time_str = f"{hours_ago:.1f}h ago" if hours_ago < 1 else f"{int(hours_ago)}h ago"
        
        mcap_display = current_mcap or mc_usd or 0
        print(f"{status} {token} (Tier {tier}) - ${mcap_display:,.0f} - {time_str}")
        print(f"   Contract: {contract} | Timestamp: {timestamp}")
        if issues:
            for issue in issues:
                print(f"   {issue}")
            issues_found.append((token, issues))
        print()
    
    # Check for duplicate tokens (multiple alerts for same token)
    print("\n" + "=" * 80)
    print("DUPLICATE TOKENS (multiple alerts)")
    print("=" * 80)
    
    duplicates = {token: alerts_list for token, alerts_list in alerts_by_token.items() if len(alerts_list) > 1}
    if duplicates:
        for token, alerts_list in sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
            alerts_list.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            print(f"\n🔁 {token}: {len(alerts_list)} alerts")
            for i, alert in enumerate(alerts_list[:5], 1):  # Show latest 5
                timestamp = alert.get('timestamp', 'N/A')
                tier = alert.get('tier', '?')
                mcap = alert.get('current_mcap') or alert.get('mc_usd', 0)
                print(f"   {i}. Tier {tier}, MC ${mcap:,.0f}, {timestamp}")
    else:
        print("✅ No duplicate tokens found")
    
    # Check for missing fields
    print("\n" + "=" * 80)
    print("FIELD COMPLETENESS (recent alerts)")
    print("=" * 80)
    
    fields_to_check = {
        'current_mcap': 'Current MCAP from post',
        'entry_mc': 'Entry MCAP',
        'tier': 'Tier',
        'contract': 'Contract address',
        'matched_signals': 'Matched signals'
    }
    
    for field, description in fields_to_check.items():
        missing_count = sum(1 for alert, _ in recent_alerts if not alert.get(field))
        total = len(recent_alerts)
        percentage = (1 - missing_count / total) * 100 if total > 0 else 0
        status = "✅" if percentage >= 90 else "⚠️" if percentage >= 50 else "❌"
        print(f"{status} {description}: {total - missing_count}/{total} ({percentage:.1f}%)")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total alerts: {len(alerts)}")
    print(f"Recent alerts (24h): {len(recent_alerts)}")
    print(f"Unique tokens: {len(alerts_by_token)}")
    print(f"Tokens with duplicates: {len(duplicates)}")
    print(f"Alerts with issues: {len(issues_found)}")
    
    if issues_found:
        print(f"\n⚠️ Found {len(issues_found)} alert(s) with issues:")
        for token, issues in issues_found[:10]:
            print(f"   - {token}: {', '.join(issues)}")
    
    # Check for time gaps (missing alerts)
    print("\n" + "=" * 80)
    print("TIME GAPS ANALYSIS")
    print("=" * 80)
    
    if len(recent_alerts) > 1:
        gaps = []
        for i in range(len(recent_alerts) - 1):
            alert1_time = datetime.fromisoformat(recent_alerts[i][0].get('timestamp', '').replace('Z', '+00:00'))
            alert2_time = datetime.fromisoformat(recent_alerts[i+1][0].get('timestamp', '').replace('Z', '+00:00'))
            gap_hours = (alert1_time - alert2_time).total_seconds() / 3600
            
            if gap_hours > 3:  # Gaps larger than 3 hours
                gaps.append((gap_hours, recent_alerts[i][0].get('token'), recent_alerts[i+1][0].get('token')))
        
        if gaps:
            print(f"⚠️ Found {len(gaps)} time gap(s) > 3 hours:")
            for gap_hours, token1, token2 in gaps[:5]:
                print(f"   - {gap_hours:.1f}h gap between {token1} and {token2}")
        else:
            print("✅ No significant time gaps found")
    
    print("\n💡 To check for missing Telegram alerts, run:")
    print("   python check_missing_alerts.py")
    print("   (Requires ALERT_CHAT_ID environment variable)")

if __name__ == "__main__":
    analyze_alerts()

