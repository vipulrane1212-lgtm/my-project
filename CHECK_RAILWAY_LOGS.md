# How to Check Railway Logs

## 🚀 Quick Steps

### Option 1: Railway Dashboard (Easiest)

1. **Go to Railway Dashboard**: https://railway.app/dashboard
2. **Select your project**: `my-project` (or whatever you named it)
3. **Click on your service** (the one running `telegram_monitor_new.py`)
4. **Click "Logs" tab** at the top
5. **Scroll down** to see recent logs

### Option 2: Railway CLI

```bash
# Install Railway CLI (if not already installed)
npm i -g @railway/cli

# Login
railway login

# Link to your project
railway link

# View logs
railway logs
```

## 🔍 What to Look For

### ✅ Good Signs (Bot is Working):
- `✅ Connected to Telegram`
- `📊 Alert tier (from Telegram post): X`
- `🚨 ALPHA INCOMING — TIER X LOCKED`
- `✅ Alert sent to Telegram`
- Recent timestamps (within last hour)

### ❌ Bad Signs (Bot Has Issues):
- `❌ Failed to connect`
- `ConnectionError`
- `CancelledError`
- `SyntaxError` or `IndentationError`
- No recent logs (older than 1 hour)
- `⚠️ Warning: Alert has no tier field`

### 🔎 Specific Things to Check for Post 244:

1. **Is the bot running?**
   - Look for recent log entries (within last hour)
   - Should see connection messages

2. **Is the bot processing messages?**
   - Look for `📊 Alert tier` messages
   - Look for `🚨 ALPHA INCOMING` messages
   - Should see alerts being processed

3. **Did the bot see post 244?**
   - Search logs for "LICO" or "244"
   - Look for timestamps around 10:50 AM
   - Check if there are any errors related to LICO

4. **Is there an error saving alerts?**
   - Look for `❌ Failed to save alert`
   - Look for `FileNotFoundError` or `PermissionError`
   - Check for JSON-related errors

## 📋 Sample Log Output (What You Should See)

```
✅ Connected to Telegram
📊 Monitoring channel: @solboy_calls
📊 Alert tier (from Telegram post): 3
🚨 ALPHA INCOMING — TIER 3 LOCKED
✅ Alert sent to Telegram
✅ Alert saved to kpi_logs.json
```

## 🛠️ Troubleshooting

### If Bot is Not Running:
1. Check Railway service status (should be "Running")
2. Check if there are any deployment errors
3. Restart the service if needed

### If Bot is Running But Not Processing:
1. Check if `ALERT_CHAT_ID` environment variable is set correctly
2. Verify the bot has access to the Telegram channel
3. Check for connection errors in logs

### If Bot Processes But Doesn't Save:
1. Check for file permission errors
2. Verify `kpi_logs.json` exists and is writable
3. Check for JSON parsing errors

## 🎯 For Post 244 Specifically

**Look for:**
- Any log entry around 10:50 AM (Dec 26)
- Any mention of "LICO" in the logs
- Any errors when processing LICO alerts
- Check if the bot was even running at 10:50 AM

**If you find post 244 in logs but it's not in JSON:**
- There might be an error saving it
- The bot might have crashed after processing but before saving
- Check for errors right after the LICO alert was processed

## 📞 Next Steps After Checking Logs

1. **If bot is not running**: Restart the service on Railway
2. **If bot is running but not processing**: Check environment variables and channel access
3. **If bot processed post 244 but didn't save**: We can manually add it to JSON
4. **If post 244 was posted manually** (not by the bot): We need to manually add it to JSON

---

**Need help?** Share the relevant log snippets and I can help diagnose the issue!

