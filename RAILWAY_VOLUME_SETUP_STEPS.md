# Railway Volume Setup - Step by Step Guide

## 🎯 Correct Way to Set Up Railway Volume

### Step 1: Go to Your PROJECT (Not Service)

1. Open Railway Dashboard: https://railway.app
2. Click on your **PROJECT** (not the service)
3. You should see your service listed under the project

### Step 2: Create Volume from Project Level

**Option A: From Project Dashboard**
1. In your project, click **+ New**
2. Select **Volume** (not Service)
3. Name it: `kpi-data`
4. Click **Create**

**Option B: From Service Settings**
1. Click on your **service** (e.g., "telegram_monitor_new")
2. Go to **Settings** tab
3. Scroll down to **Volumes** section
4. Click **+ New Volume**
5. Name: `kpi-data`
6. Mount Path: `/data`
7. Click **Create**

### Step 3: Verify Volume is Created

After creating the volume:
1. Go back to your service
2. Check **Settings** → **Volumes** section
3. You should see `kpi-data` volume listed
4. Mount path should show `/data`

### Step 4: Redeploy Service

1. Go to **Deployments** tab
2. Click **Redeploy** (or push new code to trigger auto-deploy)
3. Check logs - you should see:
   ```
   📦 Using Railway persistent volume: /data/kpi_logs.json
   ✅ Data will persist across Railway redeployments!
   ```

## 🔍 Troubleshooting

### If "No services found" Error:

**Problem:** You're trying to create volume from wrong place

**Solution:**
1. Make sure you're in your **PROJECT** dashboard (not service)
2. Or create volume from **Service Settings** → **Volumes** section
3. Make sure your service exists first

### If Volume Doesn't Appear:

1. **Refresh the page**
2. Check you're looking at the right service
3. Go to Service → Settings → Volumes
4. Volume should be listed there

### If Code Still Uses Local File:

1. **Check logs** - should show "Using Railway persistent volume"
2. If it shows "Using local file" with warning:
   - Volume might not be mounted correctly
   - Check mount path is exactly `/data`
   - Redeploy service

## ✅ Verification Steps

After setup, verify it's working:

### 1. Check Startup Logs:
```bash
railway logs
```

Look for:
```
📦 Using Railway persistent volume: /data/kpi_logs.json
✅ Data will persist across Railway redeployments!
```

### 2. Check File Location:
```bash
railway run ls -la /data/
```

Should show `kpi_logs.json` in `/data/` directory

### 3. Test Alert Saving:
- Trigger an alert
- Check logs for: `✅ Alert saved to /data/kpi_logs.json`
- Redeploy service
- Check if alerts still exist (they should!)

## 📸 Visual Guide

```
Railway Dashboard
├── Your Project
    ├── + New (create Volume here OR)
    └── Your Service
        ├── Settings
        │   └── Volumes section
        │       └── + New Volume (create here)
        ├── Deployments
        └── Logs
```

## 💡 Alternative: If Volume Still Doesn't Work

If Railway Volume setup is too complex, you can use the **automatic backup system** instead:

1. **Automatic backups are already active** - they create backups in `backups/` folder
2. **Manual Git sync** - run `python auto_sync_kpi_logs.py` periodically
3. **Recovery script** - `python recover_alerts_from_telegram.py` if data is lost

The automatic backup system provides good protection even without Railway Volume!

## 🆘 Still Having Issues?

1. **Check Railway Plan:**
   - Free plan: Volumes might not be available
   - Pro plan ($5/month): Volumes are available
   
2. **Try Alternative:**
   - Use automatic backups (already active)
   - Set up Git auto-sync locally
   - Manual Git commits after important alerts

3. **Contact Support:**
   - Railway Discord: https://discord.gg/railway
   - Or use backup system (works on free plan)

