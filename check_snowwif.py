#!/usr/bin/env python3
"""Check SNOWWIF alert data"""

import json
from datetime import datetime, timezone

with open('kpi_logs.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

alerts = [a for a in data.get('alerts', []) if a.get('token') == 'SNOWWIF']
if alerts:
    latest = max(alerts, key=lambda x: x.get('timestamp', ''))
    print("SNOWWIF Alert Data:")
    print(f"  Level: {latest.get('level')}")
    print(f"  Tier (from field): {latest.get('tier')}")
    print(f"  Timestamp: {latest.get('timestamp')}")
    print(f"  Contract: {latest.get('contract')}")
    print(f"  Hot List: {latest.get('hot_list')}")
else:
    print("No SNOWWIF alerts found")

