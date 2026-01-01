# 🚀 Complete Setup Guide - Data Persistence & Recovery

## ✅ Quick Fix (Do This First!)

### Step 1: Recover Lost Alerts

Run the recovery script to get alerts from Telegram:

```bash
python recover_alerts_from_telegram.py
```

This will:
- ✅ Fetch alerts from your Telegram channel
- ✅ Add missing alerts to `kpi_logs.json`
- ✅ Show you what was recovered

### Step 2: Commit Recovered Data

```bash
git add kpi_logs.json
git commit -m "Recover alerts from Telegram"
git push origin main
```

Railway will auto-deploy with recovered data!

---

## 🎯 Best Long-Term Solution: Railway Volume

### Why Railway Volume?
- ✅ Data persists across redeployments
- ✅ No manual syncing needed
- ✅ Production-ready
- ⚠️ Requires Railway Pro plan ($5/month)

### Setup Steps:

**IMPORTANT:** Railway Volumes require **Railway Pro plan** ($5/month). If you're on free tier, skip to "Free Alternative" below.

1. **Go to Railway Dashboard**
   - Click on your **PROJECT** (not service)
   - Or go to your **Service** → **Settings** tab
   - Scroll to **Volumes** section

2. **Create Volume**
   - Click **+ New Volume** (from project level OR service settings)
   - Name: `kpi-data`
   - Mount Path: `/data`
   - Click **Create**

3. **Verify Volume**
   - Go to Service → Settings → Volumes
   - Should see `kpi-data` volume listed with mount `/data`

4. **Redeploy**
   - Push code or manually redeploy
   - Check logs - should show "Using Railway persistent volume"

**If you get "No services found" error:**
- Make sure you're creating volume from **PROJECT** level, not service level
- Or create from Service → Settings → Volumes section
- Check you have Railway Pro plan (free tier doesn't support volumes)

---

## 💰 Free Alternative: Automatic Backups (NO Railway Pro Needed!)

**Good News:** You don't need Railway Pro! The code already has automatic backups that work on free tier.

### What's Already Active:

✅ **Automatic Backups** - Every alert creates a backup automatically
✅ **Last 5 Backups Kept** - Stored in `backups/` folder  
✅ **Enhanced Save Reliability** - 5 retries with emergency save
✅ **Recovery Script** - Can recover from Telegram if needed

### How It Works:

1. **Every alert is saved** with automatic backup
2. **Backups are created** before each save
3. **If Railway redeploys**, you can recover from backups
4. **Recovery script** can get alerts from Telegram

### Optional: Auto Git Sync (For Extra Safety)

If you want extra protection, use automatic Git commits:

### Option A: Local Scheduled Task (Windows)

1. **Create sync script** (already created: `auto_sync_kpi_logs.py`)

2. **Set up Task Scheduler:**
   - Open Task Scheduler
   - Create Basic Task
   - Name: "Sync KPI Logs"
   - Trigger: Daily, every hour
   - Action: Start a program
   - Program: `python`
   - Arguments: `C:\Users\Admin\Desktop\amaverse\auto_sync_kpi_logs.py`
   - Start in: `C:\Users\Admin\Desktop\amaverse`

3. **Done!** Script runs every hour automatically

### Option B: Manual Sync (Simplest)

Just run this after important alerts:

```bash
python auto_sync_kpi_logs.py
```

Or manually:
```bash
git add kpi_logs.json
git commit -m "Update alerts"
git push origin main
```

---

## 📋 What's Already Done

✅ **Code Updated:**
- `kpi_logger.py` automatically uses `/data` volume if available
- Falls back to local file if no volume

✅ **Recovery Script:**
- `recover_alerts_from_telegram.py` - Recovers lost alerts

✅ **Auto-Sync Script:**
- `auto_sync_kpi_logs.py` - Commits to Git automatically

---

## 🧪 Test Everything

### 1. Test Recovery:
```bash
python recover_alerts_from_telegram.py
```

### 2. Test Auto-Sync:
```bash
python auto_sync_kpi_logs.py
```

### 3. Verify API:
```bash
curl https://your-railway-url.up.railway.app/api/alerts/recent
```

---

## ⚠️ Important Notes

- **Railway Volume** = Best solution (persistent storage)
- **Auto Git Sync** = Free alternative (requires local setup)
- **Manual Sync** = Simplest (just commit when needed)

**Recommendation:** Use Railway Volume if you can afford $5/month. Otherwise, use auto Git sync.

---

## 🆘 Troubleshooting

### Alerts Not Showing on Website?
1. Check Railway logs: `railway logs`
2. Verify `kpi_logs.json` exists: `railway run ls -la kpi_logs.json`
3. Test API: `/api/health` endpoint
4. Check if alerts are being filtered (MCAP > 500k)

### Recovery Script Not Working?
1. Check Telegram session file exists
2. Verify `ALERT_CHAT_ID` is correct
3. Check API credentials in environment

### Auto-Sync Not Working?
1. Verify git is configured: `git config --global user.name`
2. Check git credentials are set
3. Test manually: `git status`

---

## 📞 Need Help?

Check these files:
- `RAILWAY_DATA_PERSISTENCE_FIX.md` - Detailed explanation
- `recover_alerts_from_telegram.py` - Recovery script
- `auto_sync_kpi_logs.py` - Auto-sync script

