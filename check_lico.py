#!/usr/bin/env python3
"""Check LICO alert data"""

import json
from datetime import datetime, timezone

with open('kpi_logs.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

alerts = [a for a in data.get('alerts', []) if a.get('token') == 'LICO']
if alerts:
    print(f"Found {len(alerts)} LICO alert(s):\n")
    for i, alert in enumerate(sorted(alerts, key=lambda x: x.get('timestamp', ''), reverse=True), 1):
        print(f"LICO Alert #{i}:")
        print(f"  Level: {alert.get('level')}")
        print(f"  Tier (from field): {alert.get('tier')}")
        print(f"  Timestamp: {alert.get('timestamp')}")
        print(f"  Contract: {alert.get('contract')}")
        print(f"  Score: {alert.get('score')}")
        print()
else:
    print("No LICO alerts found")

