#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyze Vercel logs to find missing alerts
"""
import json
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

LOG_FILE = Path(r"c:\Users\Admin\Downloads\logs.1767381646182.json")

print("="*80)
print("ANALYZING VERCEL LOGS FOR MISSING ALERTS")
print("="*80)

# The 3 missing alerts
MISSING_TOKENS = ["DHG", "MWG", "BLAST"]
MISSING_CONTRACTS = [
    "3R48QGXWZN5WYQZUWOXQXUFVUEEUYC9WDDOCSQPPBONK",  # DHG
    "3RQEUT98EKX1KJT1OWKP1WHN71XTVXAGTZB2HLQSFACK",  # MWG
    "9IEWUXV5Y9VAEK6GLVFZVKWZBMSVKEKUKAA61XATWA97"   # BLAST
]

if not LOG_FILE.exists():
    print(f"[ERROR] Log file not found: {LOG_FILE}")
    sys.exit(1)

print(f"\n[INFO] Reading log file: {LOG_FILE}")
print(f"[INFO] File size: {LOG_FILE.stat().st_size / 1024 / 1024:.2f} MB")

# Read as JSON array
with open(LOG_FILE, 'r', encoding='utf-8') as f:
    try:
        logs = json.load(f)
        if not isinstance(logs, list):
            logs = [logs]
    except json.JSONDecodeError:
        # Try NDJSON format
        logs = []
        f.seek(0)
        for line in f:
            if line.strip():
                try:
                    logs.append(json.loads(line))
                except:
                    pass

print(f"[INFO] Loaded {len(logs)} log entries")

# Search for missing tokens
print(f"\n[SEARCH] Looking for missing alerts: {', '.join(MISSING_TOKENS)}")

found_tokens = {}
for token in MISSING_TOKENS:
    found_tokens[token] = []

for log in logs:
    message = log.get("message", "")
    if any(token in message for token in MISSING_TOKENS):
        for token in MISSING_TOKENS:
            if token in message:
                found_tokens[token].append({
                    "timestamp": log.get("timestamp", ""),
                    "message": message[:200]
                })

# Search for contracts
print(f"\n[SEARCH] Looking for missing contracts...")
found_contracts = {}
for contract in MISSING_CONTRACTS:
    found_contracts[contract] = []
    short_contract = contract[:20] + "..."
    for log in logs:
        message = log.get("message", "")
        if contract in message or short_contract in message:
            found_contracts[contract].append({
                "timestamp": log.get("timestamp", ""),
                "message": message[:200]
            })

# Search for "Alert saved" messages
print(f"\n[SEARCH] Looking for 'Alert saved' messages...")
saved_alerts = []
for log in logs:
    message = log.get("message", "")
    if "Alert saved to kpi_logs.json" in message:
        saved_alerts.append({
            "timestamp": log.get("timestamp", ""),
            "message": message
        })

# Search for duplicate skip messages
print(f"\n[SEARCH] Looking for 'duplicate' or 'Skipping' messages...")
duplicate_messages = []
for log in logs:
    message = log.get("message", "")
    if "duplicate" in message.lower() or "Skipping" in message:
        duplicate_messages.append({
            "timestamp": log.get("timestamp", ""),
            "message": message
        })

# Print results
print("\n" + "="*80)
print("RESULTS")
print("="*80)

for token in MISSING_TOKENS:
    print(f"\n[{token}]")
    if found_tokens[token]:
        print(f"  [FOUND] {len(found_tokens[token])} mentions")
        for entry in found_tokens[token][:3]:
            print(f"    {entry['timestamp']}: {entry['message']}")
    else:
        print(f"  [NOT FOUND] No mentions in logs")

print(f"\n[ALERT SAVES]")
print(f"  Total 'Alert saved' messages: {len(saved_alerts)}")
if saved_alerts:
    print(f"  Last 5 saves:")
    for entry in saved_alerts[-5:]:
        print(f"    {entry['timestamp']}: {entry['message']}")

print(f"\n[DUPLICATE SKIPS]")
print(f"  Total duplicate/skip messages: {len(duplicate_messages)}")
if duplicate_messages:
    print(f"  Last 5 duplicates:")
    for entry in duplicate_messages[-5:]:
        print(f"    {entry['timestamp']}: {entry['message']}")

print("\n" + "="*80)

