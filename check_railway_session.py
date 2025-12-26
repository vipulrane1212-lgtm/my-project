#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_railway_session.py

Check if session file exists on Railway and verify it's valid.
"""

import os
import sys

# Fix Unicode encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

SESSION_NAME = os.getenv('SESSION_NAME', 'railway_production_session')
session_file = f"{SESSION_NAME}.session"

print("="*80)
print("CHECKING SESSION FILE ON RAILWAY")
print("="*80)
print()

# Check multiple possible locations
possible_paths = [
    session_file,  # Current directory
    f"/app/{session_file}",  # Railway /app directory
    os.path.join(os.getcwd(), session_file),  # Absolute path from current dir
]

print(f"Looking for: {session_file}")
print(f"SESSION_NAME env: {SESSION_NAME}")
print(f"Current working directory: {os.getcwd()}")
print()

print("Checking possible paths:")
for path in possible_paths:
    exists = os.path.exists(path)
    size = os.path.getsize(path) if exists else 0
    print(f"  {path}: {'✅ EXISTS' if exists else '❌ NOT FOUND'} ({size} bytes)")

print()

# List all .session files in current directory
print("All .session files in current directory:")
try:
    files = [f for f in os.listdir('.') if f.endswith('.session')]
    for f in files:
        size = os.path.getsize(f)
        print(f"  {f}: {size} bytes")
except Exception as e:
    print(f"  Error listing files: {e}")

print()

# Check if file is valid SQLite
session_found = False
actual_path = None
for path in possible_paths:
    if os.path.exists(path):
        session_found = True
        actual_path = path
        try:
            import sqlite3
            conn = sqlite3.connect(path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            conn.close()
            print(f"✅ Session file is valid SQLite at: {path}")
            print(f"   Tables: {tables}")
        except Exception as e:
            print(f"⚠️  Session file exists but is invalid: {e}")
        break

if not session_found:
    print("❌ Session file not found in any location!")
    print()
    print("SOLUTION:")
    print("1. Ensure session file is in GitHub")
    print("2. Wait for Railway to redeploy")
    print("3. Or upload manually via Railway Dashboard → Files tab")

print()
print("="*80)

