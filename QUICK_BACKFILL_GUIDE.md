# Quick Backfill Guide

## Current Status
- ❌ **173 alerts missing tier field** (100%)
- ⚠️ **17 alerts missing MCAP** (9.8%)
- ✅ All alerts have valid timestamps

## Step 1: Find Your Alert Channel

Your alerts are being sent to a Telegram channel/group. We need to find which one.

**Check `alert_groups.json`:**
```bash
cat alert_groups.json
```

This will show you the group/channel IDs where alerts are sent.

**OR check your bot's groups:**
- Look at where your bot (@Plaguealertbot) is sending alerts
- That's the channel/group we need

## Step 2: Set Environment Variable

**Windows PowerShell:**
```powershell
$env:ALERT_CHAT_ID="@solboy_calls"
# OR if you have the channel ID:
$env:ALERT_CHAT_ID="-1001449259153"
```

**Windows CMD:**
```cmd
set ALERT_CHAT_ID=@solboy_calls
```

**Linux/Mac:**
```bash
export ALERT_CHAT_ID="@solboy_calls"
```

## Step 3: Run Backfill

```bash
python backfill_tier_from_telegram.py
```

## Step 4: Verify

```bash
python verify_backfill.py
```

You should see:
- ✅ Alerts with tier field: 173 (100.0%)
- ✅ Tier distribution showing correct counts

## What Channel Should I Use?

If you're not sure which channel to use:

1. **Check where your bot sends alerts:**
   - Look at your Telegram messages
   - Find where alerts are posted
   - That's your `ALERT_CHAT_ID`

2. **Common options:**
   - `@solboy_calls` - Your public channel
   - A private group where bot sends alerts
   - The channel ID (negative number like `-1001449259153`)

3. **To find channel ID:**
   - Add @userinfobot to your channel
   - Forward a message from your channel to @userinfobot
   - It will show you the channel ID

## Troubleshooting

**"ALERT_CHAT_ID environment variable not set"**
- Make sure you set it before running the script
- In PowerShell: `$env:ALERT_CHAT_ID="@solboy_calls"`

**"No alerts found in Telegram"**
- Check the channel ID is correct
- Make sure you have access to read the channel
- Try using channel username instead of ID

**"Can't connect to Telegram"**
- Your session file should already exist (from running the main bot)
- Check `API_ID` and `API_HASH` are set correctly

