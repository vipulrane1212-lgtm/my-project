#!/usr/bin/env python3
"""
Check if session file exists on Railway and verify its validity.
Run this on Railway to diagnose session file issues.
"""
import os
import sys

# Fix Unicode for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

SESSION_NAME = os.getenv('SESSION_NAME', 'railway_production_session')
session_file = f"{SESSION_NAME}.session"

print("=" * 80)
print("RAILWAY SESSION FILE DIAGNOSTICS")
print("=" * 80)
print()
print(f"Looking for: {session_file}")
print(f"SESSION_NAME env: {SESSION_NAME}")
print(f"Current directory: {os.getcwd()}")
print()

# Check multiple paths
possible_paths = [
    session_file,  # Current directory
    f"/app/{session_file}",  # Railway /app directory
    f"/app/sessions/{session_file}",  # Railway volumes
    os.path.join(os.getcwd(), session_file),  # Absolute path
]

print("Checking paths:")
print("-" * 80)
for path in possible_paths:
    exists = os.path.exists(path)
    status = "EXISTS" if exists else "NOT FOUND"
    print(f"{status:10} {path}")
    
    if exists:
        try:
            file_size = os.path.getsize(path)
            print(f"            Size: {file_size:,} bytes")
            
            if file_size == 0:
                print("            ERROR: File is EMPTY (0 bytes)!")
            elif file_size < 1000:
                print("            WARNING: File is very small, might be corrupted!")
            
            # Try SQLite validation
            try:
                import sqlite3
                conn = sqlite3.connect(path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                conn.close()
                print(f"            Valid SQLite: YES (tables: {len(tables)})")
                if len(tables) == 0:
                    print("            ERROR: No tables found - file is invalid!")
            except sqlite3.DatabaseError as e:
                print(f"            ERROR: Not valid SQLite: {e}")
            except Exception as e:
                print(f"            WARNING: Could not validate SQLite: {e}")
        except Exception as e:
            print(f"            ERROR: Could not read file: {e}")
    
    print()

# List all .session files
print("=" * 80)
print("All .session files in current directory:")
print("-" * 80)
try:
    all_files = os.listdir('.')
    session_files = [f for f in all_files if f.endswith('.session')]
    if session_files:
        for f in session_files:
            size = os.path.getsize(f)
            print(f"  {f} ({size:,} bytes)")
    else:
        print("  No .session files found")
except Exception as e:
    print(f"  Error listing files: {e}")

print()
print("=" * 80)
print("All files in current directory (first 20):")
print("-" * 80)
try:
    all_files = os.listdir('.')
    for f in all_files[:20]:
        print(f"  {f}")
    if len(all_files) > 20:
        print(f"  ... and {len(all_files) - 20} more files")
except Exception as e:
    print(f"  Error: {e}")

print()
print("=" * 80)
print("All files in /app/ directory:")
print("-" * 80)
try:
    if os.path.exists('/app'):
        app_files = os.listdir('/app')
        for f in app_files[:20]:
            print(f"  {f}")
        if len(app_files) > 20:
            print(f"  ... and {len(app_files) - 20} more files")
    else:
        print("  /app/ directory does not exist")
except Exception as e:
    print(f"  Error: {e}")

print()
print("=" * 80)

