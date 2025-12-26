# How to Run Backfill Script

## Quick Start

### Step 1: Set Environment Variables

You need to set the `ALERT_CHAT_ID` environment variable. This should be your Telegram channel/group where alerts are posted.

**Option A: Use your existing alert channel**
```bash
# If you're using @solboy_calls channel
export ALERT_CHAT_ID="@solboy_calls"

# OR if you have the channel ID (negative number)
export ALERT_CHAT_ID="-1001234567890"
```

**Option B: Find your channel ID**
1. Add @userinfobot to your channel
2. Forward a message from your channel to @userinfobot
3. It will show you the channel ID (e.g., `-1001449259153`)

### Step 2: Check Other Environment Variables

The script uses these from your existing setup:
- `API_ID` - Your Telegram API ID
- `API_HASH` - Your Telegram API Hash
- `SESSION_NAME` - Your session name (default: "telegram_monitor")

These should already be set if your bot is working.

### Step 3: Run Backfill Script

```bash
python backfill_tier_from_telegram.py
```

### Step 4: Verify Results

```bash
python verify_backfill.py
```

## Expected Output

When running the backfill script, you should see:
```
================================================================================
BACKFILL TIER AND MCAP FROM TELEGRAM POSTS
================================================================================

📋 Loaded 173 alerts from kpi_logs.json
⚠️  173 alerts missing tier field

🔌 Connecting to Telegram...
✅ Connected to Telegram
📡 Fetching old alerts from @solboy_calls...
✅ Fetched X alert messages

📊 Processing 173 alerts...
  ✅ Updated tier for TOKEN1: 1
  ✅ Updated MCAP for TOKEN1: $143500.0
  ...

📈 Summary:
  Matched: X/173 alerts
  Updated: X alerts

📦 Backup created: kpi_logs.json.backup
✅ Saved to kpi_logs.json
✅ Successfully updated X alerts!
```

## Troubleshooting

### Issue: "ALERT_CHAT_ID environment variable not set"

**Solution:**
```bash
# Windows PowerShell
$env:ALERT_CHAT_ID="@solboy_calls"

# Windows CMD
set ALERT_CHAT_ID=@solboy_calls

# Linux/Mac
export ALERT_CHAT_ID="@solboy_calls"
```

### Issue: "No alerts found in Telegram"

**Possible causes:**
1. Wrong channel ID - Check `ALERT_CHAT_ID` is correct
2. Bot doesn't have access - Make sure your bot/user can read the channel
3. Channel is private - You need to be a member/admin

**Solution:**
- Try using channel username (e.g., `@solboy_calls`) instead of ID
- Make sure you're logged in with the same account that has access

### Issue: "Can't connect to Telegram"

**Solution:**
- Check `API_ID` and `API_HASH` are correct
- Make sure session file exists (e.g., `telegram_monitor.session`)
- Try running your main bot first to ensure Telegram connection works

### Issue: "Alerts not matching"

**Possible causes:**
1. Contract addresses don't match
2. Token names are different
3. Timestamps are too far apart

**Solution:**
- The script matches by contract address first (most reliable)
- Then by token name + timestamp (within 2 hours)
- Check if your Telegram messages have the same contract addresses as in kpi_logs.json

## What Gets Updated

The script will update:
- ✅ `tier` field (1, 2, or 3) - extracted from "TIER X LOCKED" in message
- ✅ `mc_usd` field - extracted from "Current MC: $XXX" in message
- ✅ `entry_mc` field - same as mc_usd (market cap at alert time)
- ✅ `timestamp` - from Telegram message date (more accurate)

## Safety

- ✅ Creates backup: `kpi_logs.json.backup` before making changes
- ✅ Only updates missing fields (won't overwrite existing data)
- ✅ Safe to run multiple times
- ✅ Can be interrupted and resumed

## After Backfill

After running the backfill, verify with:
```bash
python verify_backfill.py
```

You should see:
- ✅ Alerts with tier field: 173 (100.0%)
- ✅ Tier distribution showing correct counts
- ✅ All alerts have MCAP

Then test your API:
```bash
curl https://my-project-production-3d70.up.railway.app/api/stats
```

The tier distribution should now be accurate!

