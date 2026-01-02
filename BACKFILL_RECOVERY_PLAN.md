# Backfill Recovery Plan

## Step 1: Stop Railway Deployment

### Option A: Via Railway Dashboard (Recommended)
1. Go to Railway dashboard: https://railway.app
2. Navigate to your project
3. Click on your service
4. Go to **Settings** tab
5. Find **"Auto Deploy"** or **"GitHub"** section
6. **Disable Auto Deploy** temporarily
7. Or go to **Deployments** tab and **Stop** the current deployment

### Option B: Via Railway CLI
```bash
railway service
railway down  # Stop the service
```

## Step 2: Set Up Local Session with Chat Access

1. Make sure you have `railway_production_session.session` locally
2. Run the bot locally once to ensure it joins the alert chat:
   ```bash
   python telegram_monitor_new.py
   ```
3. Let it run for a few seconds to join the chat
4. Stop it (Ctrl+C)

## Step 3: Run Backfill Script

```bash
python backfill_missing_after_lico.py
```

The script will:
- Use `railway_production_session` (which has chat access)
- Fetch alerts from Telegram after LICO timestamp
- Compare with local `kpi_logs.json`
- Add missing alerts
- Save updated `kpi_logs.json`

## Step 4: Verify and Commit

1. Check the recovered alerts:
   ```bash
   # Verify alerts were added
   python -c "import json; data = json.load(open('kpi_logs.json')); print(f'Total alerts: {len(data[\"alerts\"])}')"
   ```

2. Commit the recovered alerts:
   ```bash
   git add kpi_logs.json
   git commit -m "Recover missing alerts after LICO via backfill"
   git push origin main
   ```

## Step 5: Re-enable Railway Deployment

### Option A: Via Railway Dashboard
1. Go to Railway dashboard
2. Your service → **Settings** tab
3. **Enable Auto Deploy** again
4. Or manually trigger a new deployment

### Option B: Via Railway CLI
```bash
railway up  # Start/redeploy the service
```

## Step 6: Verify Deployment

1. Check Railway logs to ensure bot started successfully
2. Check API to verify alerts are showing:
   - Visit your Railway API URL: `/api/alerts/recent`
   - Should show all recovered alerts

