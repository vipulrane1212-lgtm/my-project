#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify API response against kpi_logs.json and identify issues"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

KPI_LOGS_FILE = Path("kpi_logs.json")

# API response data (from user)
API_RESPONSE = {
    "alerts": [
        {"token": "EOS", "tier": 3, "level": "MEDIUM", "timestamp": "2025-12-26T03:20:38.839724+00:00", "contract": "9GCHKPMBEEDPPCPRVWT7B9O9MM8BUUHWDL64TUFPUMP"},
        {"token": "LICO", "tier": 1, "level": "HIGH", "timestamp": "2025-12-26T02:44:50.389002+00:00", "contract": "678QT3ZQCCBLJJZB5IC5FVMAV94AYRIWSZ3FUYSRVYNC"},
        {"token": "BANK", "tier": 3, "level": "MEDIUM", "timestamp": "2025-12-26T02:42:24.892085+00:00", "contract": "8TB4MYMMTJBPW9P7KSEUPAGBQXK8IPNPJFAH8MVCPUMP"},
        {"token": "HONSE", "tier": 1, "level": "MEDIUM", "timestamp": "2025-12-26T02:04:24.707584+00:00", "contract": "5ZQU5EUPKBUBSWLSBOC7QNF7DS8XDRLNEWEPAAIGPUMP"},
        {"token": "SNOWWIF", "tier": 1, "level": "HIGH", "timestamp": "2025-12-26T01:54:56.413443+00:00", "contract": "D3HZIGZUE8XCJBU8PFYLGC8IEPA5ZNBFCWQJUMEUPUMP"},
        {"token": "TRANSPARENT", "tier": 3, "level": "MEDIUM", "timestamp": "2025-12-26T01:22:56.720045+00:00", "contract": "DVZPHSFCNAKHY8CUURKW1NV3KZLVTS5FV19WJSANZRFC"},
        {"token": "SNSWAP", "tier": 3, "level": "MEDIUM", "timestamp": "2025-12-26T01:10:06.881279+00:00", "contract": "ATK1H4THSWJ9CFQQTBFJCHWPDEMTP4PZKY4LFGB9PUMP"},
        {"token": "GM", "tier": 3, "level": "MEDIUM", "timestamp": "2025-12-25T23:15:05.198902+00:00", "contract": "9RABDMWL2HCMAH5YZXJBLIIYXHIBBD2JSEH3Q6KCPUMP"},
        {"token": "MARKOVIC", "tier": 3, "level": "MEDIUM", "timestamp": "2025-12-25T23:05:05.487232+00:00", "contract": "GRFDWLCYXCBTRXFT8KRDVRYIATEXJSQCRZLUX3PNPUMP"},
        {"token": "ZAZU", "tier": 1, "level": "HIGH", "timestamp": "2025-12-25T23:01:43.752972+00:00", "contract": "F6DPFEYBSEHCAG8KPBHZ71WYAGUBH2763ZJL7J6SPUMP"},
        {"token": "LARPBALL", "tier": 1, "level": "HIGH", "timestamp": "2025-12-25T22:55:19.181505+00:00", "contract": "CE5HEYZTBWUP5U2UDCMDFGHJMH7OH7VVPVKNP3FFPUMP"},
        {"token": "DIPSHIELD", "tier": 1, "level": "HIGH", "timestamp": "2025-12-25T22:41:03.690019+00:00", "contract": "JAWMGP9M3Z7SEWOEVFGDH2Q54AMIDI116BJ1LY9XPUMP"},
        {"token": "BEGUY", "tier": 1, "level": "HIGH", "timestamp": "2025-12-25T22:37:22.912683+00:00", "contract": "4JZJ5VGDCR1QAR1YN8KOHWXAKIED6EFA24GEFDUFPUMP"},
        {"token": "CLICKMAS", "tier": 3, "level": "MEDIUM", "timestamp": "2025-12-25T22:06:22.549820+00:00", "contract": "ETR6CANGS2SUEVXW6BVWJWCDMS1ZPVVX423GYDFMPUMP"},
        {"token": "CHARIZARD", "tier": 3, "level": "MEDIUM", "timestamp": "2025-12-25T22:04:37.700513+00:00", "contract": "3WZD8XONBRVAREQ1QY4VUQIV1ZO9RWA2YDTY9FZBTBUR"},
        {"token": "SILVER", "tier": 1, "level": "HIGH", "timestamp": "2025-12-25T21:43:38.684714+00:00", "contract": "DVGUBPGNIXDWVCM654YIALCMNIY2CDUYJXJK3U9GPUMP"},
        {"token": "LAUNCHR", "tier": 1, "level": "HIGH", "timestamp": "2025-12-25T21:28:03.405228+00:00", "contract": "86ZNAUJEVLMTNNAZECET1ZYR7HN2PEF5ZPEWUKTDPUMP"},
        {"token": "NULL", "tier": 3, "level": "MEDIUM", "timestamp": "2025-12-25T20:34:46.668236+00:00", "contract": "48EKHWWADM7LJ57MSUDYDQ36CXX23RATDBU74PA1NULL"},
        {"token": "PHBT", "tier": 1, "level": "HIGH", "timestamp": "2025-12-25T20:32:06.582568+00:00", "contract": "8FFFYZVJ3LUGCRVWR1JPDB33ZMZMQK2PVLQXJTK5PUMP"},
        {"token": "PILLS", "tier": 1, "level": "HIGH", "timestamp": "2025-12-25T20:19:59.332618+00:00", "contract": "4EWKFNCS8LCEF46RI3Q1VKGAVKK5PMUCFQ9RGNMMPUMP"},
    ]
}

def verify_api_vs_json():
    """Verify API response against kpi_logs.json"""
    print("=" * 80)
    print("VERIFYING API RESPONSE VS kpi_logs.json")
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
    print(f"\n📋 Loaded {len(alerts)} alerts from kpi_logs.json")
    print(f"📡 API returned {len(API_RESPONSE['alerts'])} alerts\n")
    
    # Create lookup by contract + timestamp
    json_alerts_by_contract = {}
    for alert in alerts:
        contract = alert.get('contract', '')
        timestamp = alert.get('timestamp', '')
        if contract and timestamp:
            key = (contract, timestamp)
            json_alerts_by_contract[key] = alert
    
    # Verify each API alert
    issues = []
    matched = []
    missing_in_json = []
    
    print("🔍 Verifying API alerts against JSON...\n")
    
    for api_alert in API_RESPONSE['alerts']:
        contract = api_alert.get('contract', '')
        timestamp = api_alert.get('timestamp', '')
        token = api_alert.get('token', 'UNKNOWN')
        api_tier = api_alert.get('tier')
        api_level = api_alert.get('level')
        
        key = (contract, timestamp)
        json_alert = json_alerts_by_contract.get(key)
        
        if not json_alert:
            missing_in_json.append({
                'token': token,
                'contract': contract,
                'timestamp': timestamp,
                'api_tier': api_tier
            })
            print(f"❌ {token}: NOT FOUND in JSON (contract: {contract[:20]}..., timestamp: {timestamp})")
            continue
        
        json_tier = json_alert.get('tier')
        json_level = json_alert.get('level', 'MEDIUM')
        
        matched.append(token)
        
        # Check tier mismatch
        if json_tier != api_tier:
            issues.append({
                'token': token,
                'contract': contract[:20],
                'timestamp': timestamp,
                'api_tier': api_tier,
                'json_tier': json_tier,
                'api_level': api_level,
                'json_level': json_level,
                'type': 'tier_mismatch'
            })
            print(f"⚠️  {token}: Tier mismatch - API: {api_tier}, JSON: {json_tier} (Level: {api_level})")
        
        # Check level mismatch
        if json_level != api_level:
            issues.append({
                'token': token,
                'contract': contract[:20],
                'timestamp': timestamp,
                'api_tier': api_tier,
                'json_tier': json_tier,
                'api_level': api_level,
                'json_level': json_level,
                'type': 'level_mismatch'
            })
            print(f"⚠️  {token}: Level mismatch - API: {api_level}, JSON: {json_level}")
    
    # Check for alerts in JSON that are missing from API
    print(f"\n🔍 Checking for alerts in JSON missing from API...\n")
    
    api_contracts = {a.get('contract') for a in API_RESPONSE['alerts']}
    missing_in_api = []
    
    # Get recent alerts (last 24 hours)
    cutoff_time = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    for alert in alerts:
        contract = alert.get('contract', '')
        timestamp = alert.get('timestamp', '')
        token = alert.get('token', 'UNKNOWN')
        
        if not contract or not timestamp:
            continue
        
        try:
            alert_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            if alert_time < cutoff_time:
                continue  # Skip old alerts
        except:
            continue
        
        if contract not in api_contracts:
            missing_in_api.append({
                'token': token,
                'contract': contract,
                'timestamp': timestamp,
                'tier': alert.get('tier'),
                'level': alert.get('level')
            })
            print(f"⚠️  {token}: In JSON but missing from API (tier: {alert.get('tier')}, level: {alert.get('level')})")
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"✅ Matched: {len(matched)}/{len(API_RESPONSE['alerts'])} alerts")
    print(f"⚠️  Tier/Level mismatches: {len([i for i in issues if i['type'] == 'tier_mismatch'])}")
    print(f"⚠️  Missing in JSON: {len(missing_in_json)}")
    print(f"⚠️  Missing in API: {len(missing_in_api)}")
    
    if issues:
        print(f"\n📊 Issues found:")
        tier_issues = [i for i in issues if i['type'] == 'tier_mismatch']
        level_issues = [i for i in issues if i['type'] == 'level_mismatch']
        
        if tier_issues:
            print(f"\n  Tier Mismatches ({len(tier_issues)}):")
            for issue in tier_issues:
                print(f"    - {issue['token']}: API={issue['api_tier']}, JSON={issue['json_tier']} (Level: {issue['api_level']})")
        
        if level_issues:
            print(f"\n  Level Mismatches ({len(level_issues)}):")
            for issue in level_issues:
                print(f"    - {issue['token']}: API={issue['api_level']}, JSON={issue['json_level']}")
    
    if missing_in_json:
        print(f"\n  Missing in JSON ({len(missing_in_json)}):")
        for item in missing_in_json:
            print(f"    - {item['token']}: {item['contract'][:20]}...")
    
    if missing_in_api:
        print(f"\n  Missing in API ({len(missing_in_api)}):")
        for item in missing_in_api[:10]:  # Show first 10
            print(f"    - {item['token']}: tier={item['tier']}, level={item['level']}")
        if len(missing_in_api) > 10:
            print(f"    ... and {len(missing_in_api) - 10} more")
    
    return {
        'issues': issues,
        'missing_in_json': missing_in_json,
        'missing_in_api': missing_in_api,
        'matched': matched
    }

if __name__ == "__main__":
    verify_api_vs_json()

