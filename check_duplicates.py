#!/usr/bin/env python3
"""Check for duplicate alerts in kpi_logs.json"""

import json
from collections import defaultdict
from datetime import datetime, timezone

with open('kpi_logs.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

alerts = data.get('alerts', [])
print(f"Total alerts: {len(alerts)}\n")

# Group by token
by_token = defaultdict(list)
for alert in alerts:
    token = alert.get('token', 'UNKNOWN')
    by_token[token].append(alert)

# Find tokens with multiple alerts
duplicates = {token: alerts for token, alerts in by_token.items() if len(alerts) > 1}

print(f"Tokens with multiple alerts: {len(duplicates)}\n")

# Show SNOWWIF specifically
if 'SNOWWIF' in duplicates:
    print("SNOWWIF Alerts (all):")
    for i, alert in enumerate(sorted(duplicates['SNOWWIF'], key=lambda x: x.get('timestamp', '')), 1):
        print(f"\n  Alert #{i}:")
        print(f"    Level: {alert.get('level')}")
        print(f"    Tier: {alert.get('tier')}")
        print(f"    Timestamp: {alert.get('timestamp')}")
        print(f"    Contract: {alert.get('contract')}")
        print(f"    Score: {alert.get('score')}")

# Show top 10 tokens with most alerts
print(f"\n\nTop 10 tokens with most alerts:")
sorted_dups = sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True)
for token, token_alerts in sorted_dups[:10]:
    print(f"  {token}: {len(token_alerts)} alerts")

