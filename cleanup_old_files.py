#!/usr/bin/env python3
"""Cleanup script to remove old/unused files"""

import os

# Files to KEEP (core system)
KEEP_FILES = {
    # Core monitoring system
    'telegram_monitor_new.py',
    'live_monitor_core.py',
    'tiered_strategy_engine.py',
    'message_parser.py',
    'live_alert_formatter.py',
    'live_config.py',
    'live_store.py',
    'dexscreener_fetcher.py',
    'kpi_logger.py',
    
    # Config files
    'automation_rules.json',
    'channels.json',
    'requirements.txt',
    
    # New backtest (for reference)
    'telegram_strategy_backtest.py',
    'backtest_report.md',
    'results.json',
    
    # Documentation
    'README.md',
    'EXTRACTION_LOGIC_README.md',
    
    # This cleanup script
    'cleanup_old_files.py',
}

# Directories to KEEP
KEEP_DIRS = {
    'scraped_sources_30h',
    '__pycache__',  # Will be regenerated
}

# Files to DELETE
FILES_TO_DELETE = []

def find_files_to_delete():
    """Find all files that should be deleted"""
    for filename in os.listdir('.'):
        if os.path.isfile(filename):
            if filename not in KEEP_FILES:
                # Check if it's a Python file, JSON, CSV, MD, or other data file
                ext = os.path.splitext(filename)[1].lower()
                if ext in ['.py', '.json', '.csv', '.md', '.txt', '.log', '.session', '.session-journal']:
                    # Skip if it's a config or important file
                    if not filename.startswith('.'):
                        FILES_TO_DELETE.append(filename)
        elif os.path.isdir(filename) and filename not in KEEP_DIRS:
            # Check directory contents
            for root, dirs, files in os.walk(filename):
                for file in files:
                    filepath = os.path.join(root, file)
                    if filepath not in KEEP_FILES:
                        FILES_TO_DELETE.append(filepath)

if __name__ == "__main__":
    find_files_to_delete()
    print(f"Found {len(FILES_TO_DELETE)} files to delete")
    print("\nFiles to delete:")
    for f in sorted(FILES_TO_DELETE):
        print(f"  - {f}")
    
    confirm = input("\nDelete these files? (yes/no): ")
    if confirm.lower() == 'yes':
        deleted = 0
        for f in FILES_TO_DELETE:
            try:
                if os.path.exists(f):
                    os.remove(f)
                    deleted += 1
            except Exception as e:
                print(f"Error deleting {f}: {e}")
        print(f"\nDeleted {deleted} files")
    else:
        print("Cancelled")






