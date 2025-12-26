#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
send_henrick_alert.py

Send the exact HENRICK alert with all new features for verification.
"""

import asyncio
import json
import os
from datetime import datetime, timedelta, timezone

from telethon import TelegramClient
from live_alert_formatter import format_alert
from live_config import load_config

# Telegram API credentials
API_ID = 25177061
API_HASH = "c11ea2f1db2aa742144dfa2a30448408"
BOT_TOKEN = "8276826313:AAH2vOYZmqDfmvflNwtz3FimjMsg3gtgqjs"

async def send_henrick_alert():
    """Send the exact HENRICK alert with new 0-100 scoring system"""
    # Recreate HENRICK alert with new scoring (should score ~100)
    # Base 2x = 10, SB1 = 18, SB_MB = 16, Glydo = 12, SpyDefi = 6, Whalebuy = 14
    # Contract = 8, MC sweet spot = 8, LIQ = 5, Callers ≥20 = 10, Subs ≥100k = 8, Large buy = 6
    # Total: 10 + 18 + 16 + 12 + 6 + 14 + 8 + 8 + 5 + 10 + 8 + 6 = 115 (capped at 100)
    henrick_alert = {
        "alert_id": "HENRICK:2025-12-22T05:00:00+00:00:HIGH",
        "level": "HIGH",
        "token": "HENRICK",
        "contract": "9SRL87CZJSKFSS2OJFX1ATSQQPPQ472G2SS516UT9DUJ",
        "score": 100.0,  # Should score ~100 with new system
        "cohort_start_utc": (datetime.now(timezone.utc) - timedelta(minutes=37)).isoformat(),
        "cohort_start_ist": (datetime.now(timezone.utc) + timedelta(hours=5, minutes=30) - timedelta(minutes=37)).isoformat(),
        "mc_usd": 150000.0,  # In sweet spot (10K-500K)
        "mc_source": "dexscreener_live",
        "liq_usd": 25000.0,  # Above 5K threshold
        "callers": 25,  # ≥20 = +10 points
        "subs": 131279,  # ≥100k = +8 points
        "matched_signals": ["glydo", "sol_sb1", "sol_sb_mb", "spydefi", "whalebuy"],
        "time_since_cohort_seconds": 37 * 60,  # 37 minutes
        "cohort_multiplier": 2.0,
        "base_multiplier": 2.0,
        # Buy data for testing
        "last_buy_sol": 5.2,  # Example buy amount
        "top_buy_sol": 25.0,  # Whale buy (>20 SOL = +6 points)
    }
    
    print("=" * 80)
    print("Sending HENRICK Alert with New Professional Template")
    print("=" * 80)
    print(f"\nAlert Data:")
    print(json.dumps(henrick_alert, indent=2))
    print("\n" + "=" * 80)
    
    # Load weights
    config = load_config("automation_rules.json")
    weights = config.get("weights", {})
    
    # Format alert with new template
    alert_message = format_alert(henrick_alert, weights=weights)
    
    # Add header
    header = "*NEW 0-100 SCORING SYSTEM — HENRICK TEST*\n\n"
    full_message = header + alert_message
    
    print("\nFormatted Alert Preview:")
    print("-" * 80)
    try:
        print(full_message)
    except UnicodeEncodeError:
        print(full_message.encode('ascii', 'ignore').decode('ascii'))
    print("-" * 80)
    
    # Connect bot client
    bot_client = TelegramClient('bot_session', API_ID, API_HASH)
    try:
        await bot_client.start(bot_token=BOT_TOKEN)
        bot_me = await bot_client.get_me()
        print(f"\n[OK] Bot connected: @{bot_me.username} ({bot_me.first_name})")
        
        # Get subscribed users
        subscribed_users = set()
        try:
            if os.path.exists("subscriptions.json"):
                with open("subscriptions.json", "r", encoding="utf-8") as f:
                    sub_data = json.load(f)
                    subscribed_users = set(sub_data.get("users", []))
        except:
            pass
        
        # Send to first subscribed user
        if subscribed_users:
            user_id = list(subscribed_users)[0]
            print(f"\n[SEND] Sending to subscribed user ID: {user_id}")
            await bot_client.send_message(
                user_id,
                full_message,
                parse_mode='Markdown',
                link_preview=False
            )
            print(f"[OK] HENRICK alert sent successfully with all new features!")
        else:
            print("[WARN] No subscribed users found. Use /subscribe command to the bot first.")
            
    except Exception as e:
        print(f"[ERROR] Failed to send: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await bot_client.disconnect()

if __name__ == '__main__':
    asyncio.run(send_henrick_alert())

