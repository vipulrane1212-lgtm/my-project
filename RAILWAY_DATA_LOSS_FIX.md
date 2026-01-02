# Railway Data Loss Fix - CRITICAL

## 🚨 Problem

Every time you commit code changes, Railway redeploys and **resets the filesystem** to what's in the remote Git repository. This means:

- ✅ Alerts saved to `/data/kpi_logs.json` (Railway volume) → **LOST on redeploy**
- ✅ Alerts committed locally but NOT pushed → **LOST on redeploy**
- ✅ Only alerts in **remote Git** survive redeployments

## ✅ Solution Implemented

### 1. Git Sync After EVERY Alert (No Batching)
**Before:** Git sync every 3 alerts or 15 minutes
**After:** Git sync **immediately after EVERY alert**

This ensures:
- ✅ Every alert is committed to Git immediately
- ✅ Every alert is pushed to remote Git immediately
- ✅ Zero data loss window - alerts are in Git before any redeploy

### 2. Reliable Git Push (With Retry)
**Before:** Push was optional, failures were silent
**After:** Push is **REQUIRED**, with retry logic and error reporting

This ensures:
- ✅ Push failures are detected and retried
- ✅ Critical errors are logged clearly
- ✅ You know immediately if alerts aren't in remote Git

## 🔧 How It Works Now

### Alert Flow:
```
1. Alert detected → telegram_monitor_new.py
2. Alert saved → kpi_logger.log_alert()
3. File saved → kpi_logs.json (immediate disk write)
4. Git sync → sync_to_git() called immediately
5. Git commit → Commits kpi_logs.json locally
6. Git push → Pushes to remote (REQUIRED, with retry)
7. ✅ Alert is now in remote Git - survives redeploy!
```

### On Railway Redeploy:
```
1. Railway pulls latest code from Git
2. Railway resets filesystem to Git state
3. ✅ kpi_logs.json from Git is loaded
4. Bot continues with all alerts intact
```

## 📋 Verification

### Check Git Sync is Working:
Look for this in Railway logs after each alert:
```
✅ Synced XXX alerts to Git and pushed to remote
```

### Check if Push Failed:
If you see this, there's a problem:
```
❌ CRITICAL: Git push failed after retry: [error]
   Alerts are committed locally but NOT in remote Git!
   Railway redeploy will LOSE these alerts!
```

### Verify Alerts in Git:
```bash
git log --oneline kpi_logs.json | head -5
# Should show recent commits for each alert
```

## ⚠️ Important Notes

1. **Git Push is Now REQUIRED** - If push fails, alerts will be lost on redeploy
2. **No Batching** - Every alert is synced immediately (no waiting)
3. **Railway Volume Still Helps** - But Git is the source of truth for redeploys
4. **Network Issues** - If Railway can't push to Git, alerts will be lost

## 🎯 Best Practices

1. **Monitor Railway Logs** - Check for Git push failures
2. **Set Up Railway Volume** - Provides additional safety net
3. **Check Git History** - Verify alerts are being committed
4. **Test Redeploy** - Verify alerts survive after redeploy

## 🚨 If Data Loss Still Occurs

1. **Check Git History:**
   ```bash
   git log kpi_logs.json
   ```

2. **Check Railway Logs:**
   Look for "Git push failed" messages

3. **Run Backfill:**
   ```bash
   python backfill_missing_after_lico.py
   ```

4. **Verify Git Push:**
   ```bash
   git push origin main
   ```

---

**Summary:** The system now syncs to Git **after every single alert** and **always pushes to remote**. This is the ONLY way to prevent data loss on Railway redeployments, since Railway resets the filesystem to the remote Git state.

