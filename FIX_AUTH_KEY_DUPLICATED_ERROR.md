# 🔧 Fix: AuthKeyDuplicatedError

## ❌ Error Message
```
telethon.errors.rpcerrorlist.AuthKeyDuplicatedError: The authorization key (session file) was used under two different IP addresses simultaneously, and can no longer be used.
```

## 🔍 What This Means
Your Telegram session file is being used from **two different IP addresses** at the same time. This happens when:
- The bot is running **locally** AND on **Railway** simultaneously
- The same session file was copied between different machines
- Multiple instances of the bot are running with the same session

## ✅ Solution

### Option 1: Run Only on Railway (Recommended)

1. **Stop the bot locally** (if running):
   - Press `Ctrl+C` in your local terminal
   - Make sure no local instance is running

2. **Delete the session file on Railway**:
   - Go to Railway dashboard: https://railway.app/project/3b315a2d-7565-4bec-96d6-6b21f35ca241
   - Click on your service
   - Go to **Files** tab
   - Find and delete: `blackhat_empire_session.session` (or whatever your SESSION_NAME is)
   - Also delete: `bot_session.session` if it exists

3. **Redeploy on Railway**:
   - Railway will automatically redeploy when you push to GitHub
   - OR manually trigger a redeploy in Railway dashboard
   - On first run, Railway will create a new session

4. **Authenticate on Railway** (if needed):
   - Check Railway logs for authentication code
   - Enter the code when prompted

### Option 2: Run Only Locally

1. **Stop the bot on Railway**:
   - Go to Railway dashboard
   - Click on your service
   - Click **Settings** → **Delete Service** (or just stop it)

2. **Delete local session file** (if corrupted):
   - Delete: `blackhat_empire_session.session`
   - Delete: `bot_session.session`

3. **Run locally**:
   - The bot will create a new session on first run
   - Authenticate with your phone number

### Option 3: Use Different Sessions

If you need to run in both places:

1. **Create separate session names**:
   - Local: `SESSION_NAME=local_session`
   - Railway: `SESSION_NAME=railway_session`

2. **Set different SESSION_NAME in Railway**:
   - Go to Railway → Variables
   - Set `SESSION_NAME=railway_session`

3. **Authenticate both separately**

## 🚨 Prevention

**IMPORTANT:** Only run the bot in **ONE place at a time**:
- ✅ Run locally **OR** on Railway
- ❌ **NOT** both simultaneously

## 📝 Quick Fix Commands

### Delete Session on Railway (via CLI)
```bash
railway run rm blackhat_empire_session.session
railway run rm bot_session.session
```

### Check if Bot is Running Locally
```bash
# Windows PowerShell
Get-Process python | Where-Object {$_.Path -like "*telegram*"}

# Or check if port is in use
netstat -ano | findstr :5000
```

## ✅ After Fixing

Once you've deleted the session file and redeployed:
1. Check Railway logs to confirm bot connects successfully
2. Verify alerts are being processed
3. Make sure only ONE instance is running

---

**Last Updated:** December 26, 2025

