# Railway JSON File Sync Issue

## The Problem

Your Lovable frontend shows the last alert as **3 hours ago** because:

1. **Local File**: Your local `kpi_logs.json` has the latest alert (EOS, 2.8 hours ago)
2. **Railway File**: Railway's `kpi_logs.json` might be **out of sync** with your local file
3. **API Reads Railway File**: The API on Railway reads from Railway's file, not your local file

## Why This Happens

### File Persistence on Railway

Railway has **two types of storage**:

1. **Ephemeral Storage** (default): Files are lost when the service restarts
2. **Persistent Volume** (optional): Files persist across restarts

Your `kpi_logs.json` is currently in **ephemeral storage**, which means:
- ✅ File persists during normal operation
- ❌ File might be reset if Railway redeploys
- ❌ File might not match your local Git version

## Solutions

### Option 1: Commit kpi_logs.json to Git (Recommended)

**Pros:**
- ✅ File syncs automatically with each Git push
- ✅ Railway gets the latest alerts on deployment
- ✅ Easy to track alert history

**Cons:**
- ⚠️ File grows over time (but JSON compresses well)
- ⚠️ Git history includes alert data

**Steps:**
```bash
# Make sure kpi_logs.json is NOT in .gitignore (it's already commented out)
git add kpi_logs.json
git commit -m "Add kpi_logs.json for Railway sync"
git push
```

### Option 2: Use Railway Persistent Volume

**Pros:**
- ✅ File persists across deployments
- ✅ No need to commit to Git

**Cons:**
- ⚠️ Requires Railway Pro plan (paid)
- ⚠️ More complex setup

### Option 3: Use External Database (Best for Production)

**Pros:**
- ✅ Real-time updates
- ✅ No file sync issues
- ✅ Scalable

**Cons:**
- ⚠️ More complex setup
- ⚠️ Additional cost

## Current Status Check

Run this to check if `kpi_logs.json` is in Git:

```bash
git ls-files | grep kpi_logs.json
```

If it's **not** in Git:
1. The file on Railway might be empty or old
2. You need to commit it to sync

If it **is** in Git:
1. Railway should have the latest version
2. Check Railway logs to see if alerts are being logged
3. The 3-hour gap might be real (no alerts triggered)

## Quick Fix: Force Sync

To ensure Railway has the latest alerts:

```bash
# 1. Make sure kpi_logs.json is tracked
git add kpi_logs.json

# 2. Commit it
git commit -m "Sync kpi_logs.json with latest alerts"

# 3. Push to GitHub
git push

# 4. Railway will auto-deploy and get the latest file
```

## Verify Railway Has Latest Data

After pushing, check Railway:

1. **Check API**: `https://my-project-production-3d70.up.railway.app/api/alerts/recent`
2. **Check Logs**: Railway dashboard → Logs → Look for "Alert sent" messages
3. **Compare Timestamps**: Latest alert in API should match your local file

## Why 3 Hours Ago?

If the latest alert is **actually 3 hours ago** (not a sync issue):
- ✅ This is **normal** - your filters are working!
- ✅ Alerts only trigger when conditions are met
- ✅ MCAP filter (500k) might be filtering out many tokens
- ✅ Tier thresholds are strict (which is good for quality)

## Recommendation

**For now**: Commit `kpi_logs.json` to Git so Railway stays in sync.

**Long-term**: Consider moving to a database (PostgreSQL/MongoDB) for better real-time updates and scalability.

