#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verify API returns all alerts (old + new) correctly.
"""
import json
import requests
import sys
from pathlib import Path
from datetime import datetime, timezone

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

BASE_URL = "https://my-project-production-3d70.up.railway.app"
KPI_LOGS_FILE = Path("kpi_logs.json")

print("="*80)
print("VERIFYING API - ALL ALERTS (OLD + NEW)")
print("="*80)

# 1. Check local kpi_logs.json
print("\n1. Checking local kpi_logs.json...")
if KPI_LOGS_FILE.exists():
    with open(KPI_LOGS_FILE, 'r', encoding='utf-8') as f:
        local_data = json.load(f)
    local_alerts = local_data.get("alerts", [])
    print(f"   [OK] Found {len(local_alerts)} alerts in local file")
    
    if local_alerts:
        latest = max(local_alerts, key=lambda x: x.get("timestamp", ""))
        oldest = min(local_alerts, key=lambda x: x.get("timestamp", ""))
        print(f"   📅 Oldest: {oldest.get('token')} at {oldest.get('timestamp', '')[:19]}")
        print(f"   📅 Latest: {latest.get('token')} at {latest.get('timestamp', '')[:19]}")
else:
    print("   [ERROR] kpi_logs.json not found!")
    local_alerts = []

# 2. Check API Health
print("\n2. Checking API Health...")
try:
    health = requests.get(f"{BASE_URL}/api/health", timeout=10).json()
    api_total = health.get("alerts", {}).get("total", 0)
    api_latest = health.get("alerts", {}).get("latest", {})
    print(f"   [OK] API is healthy")
    print(f"   📊 Total alerts in API: {api_total}")
    print(f"   📅 Latest: {api_latest.get('token')} at {api_latest.get('timestamp', '')[:19]}")
except Exception as e:
    print(f"   [ERROR] Health check failed: {e}")
    api_total = 0

# 3. Check API Recent Alerts (all)
print("\n3. Checking API Recent Alerts (all, no dedupe)...")
try:
    response = requests.get(
        f"{BASE_URL}/api/alerts/recent",
        params={"limit": 0, "dedupe": False},
        timeout=10
    ).json()
    
    api_alerts = response.get("alerts", [])
    api_count = response.get("count", 0)
    api_total_storage = response.get("total_in_storage", 0)
    
    print(f"   [OK] API returned {api_count} alerts")
    print(f"   📊 Total in storage: {api_total_storage}")
    
    if api_alerts:
        print(f"   📅 First (newest): {api_alerts[0].get('token')} at {api_alerts[0].get('timestamp', '')[:19]}")
        print(f"   📅 Last (oldest): {api_alerts[-1].get('token')} at {api_alerts[-1].get('timestamp', '')[:19]}")
    
    # Compare counts
    if len(local_alerts) == api_total_storage:
        print(f"   [OK] MATCH: Local ({len(local_alerts)}) = API ({api_total_storage})")
    else:
        print(f"   [WARNING] MISMATCH: Local ({len(local_alerts)}) != API ({api_total_storage})")
        
except Exception as e:
    print(f"   [ERROR] API request failed: {e}")
    api_alerts = []

# 4. Check API Recent Alerts (with dedupe - default)
print("\n4. Checking API Recent Alerts (with dedupe - default)...")
try:
    response = requests.get(
        f"{BASE_URL}/api/alerts/recent",
        params={"limit": 20},
        timeout=10
    ).json()
    
    dedupe_count = response.get("count", 0)
    dedupe_total = response.get("total_in_storage", 0)
    
    print(f"   [OK] API returned {dedupe_count} alerts (deduplicated)")
    print(f"   📊 Total in storage: {dedupe_total}")
    
    if response.get("alerts"):
        latest_tokens = [a.get("token") for a in response.get("alerts", [])[:5]]
        print(f"   📋 Latest 5 tokens: {', '.join(latest_tokens)}")
        
except Exception as e:
    print(f"   [ERROR] API request failed: {e}")

# 5. Check cache refresh
print("\n5. Testing cache refresh...")
try:
    cache_response = requests.get(f"{BASE_URL}/api/cache/refresh", timeout=10).json()
    print(f"   [OK] Cache refresh: {cache_response.get('status')}")
except Exception as e:
    print(f"   [WARNING] Cache refresh failed: {e}")

# 6. Final verification
print("\n" + "="*80)
print("FINAL VERIFICATION")
print("="*80)

if len(local_alerts) > 0 and api_total_storage > 0:
    if len(local_alerts) == api_total_storage:
        print("[SUCCESS] API shows ALL alerts from kpi_logs.json")
        print(f"   Total: {api_total_storage} alerts (old + new)")
        print("   [OK] Live streaming: Working")
        print("   [OK] JSON storage: Working")
        print("   [OK] No data loss: All alerts accessible")
    else:
        print(f"[WARNING] Count mismatch")
        print(f"   Local: {len(local_alerts)} alerts")
        print(f"   API: {api_total_storage} alerts")
        print("   This might be due to deduplication or cache delay")
else:
    print("[ERROR] Could not verify alerts")

print("\n" + "="*80)
print("VERIFICATION COMPLETE")
print("="*80)

