#!/usr/bin/env python3
"""Check tier distribution in kpi_logs.json"""

import json
from collections import defaultdict

with open('kpi_logs.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

alerts = data.get('alerts', [])
print(f"Total alerts: {len(alerts)}\n")

# Count by level
levels = defaultdict(int)
for a in alerts:
    l = a.get('level', 'UNKNOWN')
    levels[l] += 1

print("Level distribution:")
for k, v in sorted(levels.items()):
    print(f"  {k}: {v}")

# Count by tier field
tier_field = defaultdict(int)
tier_none = 0
for a in alerts:
    t = a.get('tier')
    if t is None:
        tier_none += 1
    else:
        tier_field[t] += 1

print(f"\nTier field distribution:")
print(f"  None (missing): {tier_none}")
for k, v in sorted(tier_field.items()):
    print(f"  Tier {k}: {v}")

# Check MEDIUM alerts - how many have tier field?
medium_alerts = [a for a in alerts if a.get('level') == 'MEDIUM']
print(f"\nMEDIUM level alerts: {len(medium_alerts)}")
medium_with_tier = [a for a in medium_alerts if a.get('tier') is not None]
medium_tier2 = [a for a in medium_alerts if a.get('tier') == 2]
medium_tier3 = [a for a in medium_alerts if a.get('tier') == 3]
print(f"  With tier field: {len(medium_with_tier)}")
print(f"  Tier 2: {len(medium_tier2)}")
print(f"  Tier 3: {len(medium_tier3)}")
print(f"  Without tier field: {len(medium_alerts) - len(medium_with_tier)}")

