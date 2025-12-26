# Railway Deployment Guide

## ✅ Completed Steps

1. ✅ Updated `telegram_monitor_new.py` to use environment variables
2. ✅ Fixed all hardcoded Windows paths for debug logging
3. ✅ Created `Procfile` for Railway
4. ✅ Created `.railwayignore` to exclude unnecessary files

## 📋 Next Steps

### Option 1: Set Environment Variables via Railway Dashboard (Recommended - Easiest)

1. Go to your Railway project: https://railway.app/project/3b315a2d-7565-4bec-96d6-6b21f35ca241
2. If you don't have a service yet:
   - Click **+ New** → **Empty Service**
   - Or connect a GitHub repo
3. Click on your service
4. Go to the **Variables** tab
5. Click **+ New Variable** and add each of these:

   - **Variable Name:** `API_ID` → **Value:** `25177061`
   - **Variable Name:** `API_HASH` → **Value:** `c11ea2f1db2aa742144dfa2a30448408`
   - **Variable Name:** `BOT_TOKEN` → **Value:** `8231103146:AAElHbn-WfOfafitmPGnDZ2WeA61HaAlXUA`
   - **Variable Name:** `SESSION_NAME` → **Value:** `blackhat_empire_session`

6. Click **Add** for each variable

### Option 2: Set Variables via CLI (After Service is Created)

**Note:** You need to create a service first via the dashboard, then link it.

```powershell
# Login (already done)
railway login

# Link to your project (already done)
railway link -p 3b315a2d-7565-4bec-96d6-6b21f35ca241

# Link to a service (after creating one in dashboard)
railway service

# Then set environment variables
railway variables --set "API_ID=25177061" --set "API_HASH=c11ea2f1db2aa742144dfa2a30448408" --set "BOT_TOKEN=8231103146:AAElHbn-WfOfafitmPGnDZ2WeA61HaAlXUA" --set "SESSION_NAME=blackhat_empire_session"
```

## 🚀 Deploy

### Via Railway Dashboard (Recommended):

1. Go to your project: https://railway.app/project/3b315a2d-7565-4bec-96d6-6b21f35ca241
2. If no service exists:
   - Click **+ New** → **Empty Service**
   - Or **+ New** → **GitHub Repo** (if you want to connect GitHub)
3. In your service:
   - Go to **Settings** tab
   - Set **Start Command** to: `python telegram_monitor_new.py`
   - Or Railway will auto-detect from `Procfile`
4. Click **Deploy** or it will auto-deploy when you push to GitHub

### Via CLI (After service is created):
```bash
railway up
```

**Note:** If you're on a free/limited plan, deployment via dashboard is recommended.

## 📝 Important Notes

### Session File Handling

The Telegram session file (`blackhat_empire_session.session`) needs to be uploaded to Railway:

**Option A: Upload via Railway Dashboard**
1. Go to your service
2. Click on **Files** tab
3. Upload `blackhat_empire_session.session` to the root directory

**Option B: Let it create on first run**
- On first deployment, Railway will prompt for phone authentication
- Check Railway logs to see the authentication code
- Enter the code when prompted

**Option C: Use Railway Volumes (Persistent Storage)**
1. In Railway dashboard, go to your service
2. Click **+ New** → **Volume**
3. Mount it to `/data` or `/storage`
4. Update script to save session to that path

### Monitoring

- View logs: `railway logs` or in Railway dashboard
- Check service status in Railway dashboard
- Monitor resource usage

## 🔧 Troubleshooting

### If deployment fails:
1. Check Railway logs for errors
2. Verify all environment variables are set
3. Ensure `requirements.txt` includes all dependencies
4. Check that Python version is compatible (3.9+)

### If bot doesn't connect:
1. Verify `BOT_TOKEN` is correct
2. Check that session file exists or authentication completed
3. Review logs for connection errors

### If alerts aren't sending:
1. Verify bot is added to groups/channels as admin
2. Check that users are subscribed (`/subscribe` command)
3. Review tier filtering settings

## 📦 Files Created

- `Procfile` - Tells Railway how to run your app
- `.railwayignore` - Excludes unnecessary files from deployment
- `RAILWAY_DEPLOYMENT.md` - This guide

## ✨ What Changed in telegram_monitor_new.py

1. **Environment Variables**: Now reads from `os.getenv()` instead of hardcoded values
2. **Debug Logging**: Optional - only logs if `DEBUG_LOG_PATH` environment variable is set
3. **Platform Agnostic**: Removed all Windows-specific paths

## 🎯 Next Steps After Deployment

1. Set environment variables (see above)
2. Upload session file or authenticate on first run
3. Deploy: `railway up` or via dashboard
4. Monitor logs to ensure it's running
5. Test bot commands: `/start`, `/subscribe` in Telegram

Good luck! 🚀

