#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automatic sync script for kpi_logs.json to Git

This script can be run periodically (via cron or scheduled task)
to automatically commit and push kpi_logs.json to Git.

Usage:
    python auto_sync_kpi_logs.py

Or set up as cron job (runs every hour):
    0 * * * * cd /path/to/amaverse && python auto_sync_kpi_logs.py
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime

KPI_LOGS_FILE = Path("kpi_logs.json")


def check_git_changes():
    """Check if kpi_logs.json has uncommitted changes."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain", str(KPI_LOGS_FILE)],
            capture_output=True,
            text=True,
            check=True
        )
        return bool(result.stdout.strip())
    except Exception as e:
        print(f"⚠️ Error checking git status: {e}")
        return False


def commit_and_push():
    """Commit and push kpi_logs.json to Git."""
    try:
        # Check if file exists
        if not KPI_LOGS_FILE.exists():
            print(f"⚠️ {KPI_LOGS_FILE} not found, skipping sync")
            return False
        
        # Check if there are changes
        if not check_git_changes():
            print("✅ No changes to sync")
            return True
        
        # Add file
        print("📝 Staging kpi_logs.json...")
        subprocess.run(
            ["git", "add", str(KPI_LOGS_FILE)],
            check=True
        )
        
        # Commit
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        commit_message = f"Auto-sync kpi_logs.json - {timestamp}"
        print(f"💾 Committing changes...")
        subprocess.run(
            ["git", "commit", "-m", commit_message],
            check=True
        )
        
        # Push
        print("🚀 Pushing to GitHub...")
        subprocess.run(
            ["git", "push", "origin", "main"],
            check=True
        )
        
        print("✅ Successfully synced kpi_logs.json to Git!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during git operations: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def main():
    """Main function."""
    print("="*60)
    print("AUTO-SYNC KPI_LOGS.JSON TO GIT")
    print("="*60)
    print()
    
    success = commit_and_push()
    
    if success:
        print("\n✅ Sync complete!")
        sys.exit(0)
    else:
        print("\n❌ Sync failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()

