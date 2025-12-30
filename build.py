#!/usr/bin/env python3
"""
build.py - Railway build script

This script runs during Railway's build phase to verify the application
can start without running the full monitoring system.
"""

import sys
import os

def main():
    print("Railway Build Phase - Verifying Application Setup")
    print("Python environment ready")
    print("Dependencies should be installed via requirements.txt")

    # Basic import test
    try:
        import asyncio
        import json
        print("Core Python imports successful")

        # Test telethon import (but don't connect)
        import telethon
        print("Telethon library available")

        # Test other key imports
        from message_parser import MessageParser
        from live_monitor_core import LiveMemecoinMonitor
        print("Application modules importable")

    except ImportError as e:
        print(f"Import error: {e}")
        sys.exit(1)

    print("Build verification complete!")
    print("Ready for deployment")
    return 0

if __name__ == "__main__":
    sys.exit(main())
