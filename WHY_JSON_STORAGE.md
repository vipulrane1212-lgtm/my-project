# Why Alerts Are Stored in JSON

## Current Architecture

Your alerts are stored in `kpi_logs.json` because:

1. **Simple File-Based Storage**: JSON files are easy to read, write, and debug
2. **No Database Required**: No need for PostgreSQL, MySQL, or MongoDB setup
3. **Works on Railway**: Railway's filesystem persists files between deployments
4. **Easy to Backup**: Just copy the JSON file
5. **Human-Readable**: You can open and inspect the file directly

## How It Works

### Alert Flow:
```
1. Alert Triggered → telegram_monitor_new.py processes it
2. Alert Logged → kpi_logger.log_alert() saves to kpi_logs.json
3. Alert Sent → Telegram bot sends the alert
4. API Reads → api_server.py reads from kpi_logs.json
5. Frontend Shows → Lovable AI displays the alerts
```

### Code Locations:

**Saving Alerts** (telegram_monitor_new.py:418):
```python
# Log alert for KPI tracking
level = alert.get("level", "MEDIUM")
self.kpi_logger.log_alert(alert, level)  # Saves to kpi_logs.json
```

**Reading Alerts** (api_server.py:193):
```python
kpi_data = load_json_file(KPI_LOGS_FILE, {"alerts": []})
alerts = kpi_data.get("alerts", [])
```

## Why Last Alert Shows 3 Hours Ago

**This is normal!** Alerts only trigger when:
- ✅ Token meets tier thresholds (TIER 1/2/3 criteria)
- ✅ Market cap < 500k (your filter)
- ✅ Multiple confirmations align (Glydo, Momentum, Smart Money, etc.)
- ✅ Not a duplicate (within 5 minutes)

**If no alerts in 3 hours**, it means:
- No tokens met the criteria
- All tokens exceeded 500k MCAP
- Market is quiet
- This is **expected behavior** - you only want quality alerts!

## Current Status

**Latest Alert**: EOS token, 2.8 hours ago (MEDIUM tier)
**Total Alerts**: 173 alerts in the file
**Last 5 Alerts**:
1. EOS - 2.8h ago (MEDIUM)
2. LICO - 3.4h ago (HIGH)
3. BANK - 3.4h ago (MEDIUM)
4. HONSE - 4.1h ago (MEDIUM)
5. SNOWWIF - 4.2h ago (HIGH)

## Railway File Persistence

**Important**: Railway persists files in the `/app` directory between deployments, BUT:
- Files are **ephemeral** - if you delete the service, files are lost
- Files are **shared** across deployments from the same Git repo
- The `kpi_logs.json` file on Railway should match your local file (if synced via Git)

## If You Want Real-Time Updates

If you want alerts to appear instantly on Lovable (instead of reading from JSON):

### Option 1: Keep JSON (Current - Recommended)
- ✅ Simple, works well
- ✅ No additional infrastructure
- ✅ File persists on Railway
- ⚠️ Small delay (API reads file on each request)

### Option 2: Add Database (More Complex)
- Use PostgreSQL or MongoDB
- Real-time updates via WebSockets
- More infrastructure to manage
- Better for high-frequency updates

### Option 3: In-Memory Cache (Hybrid)
- Keep JSON for persistence
- Add Redis for real-time updates
- More complex setup

## Recommendation

**Keep the JSON storage** - it's working well! The 3-hour gap is normal and means your filters are working (only quality alerts are being sent).

If you want to verify Railway has the latest data:
1. Check Railway logs for recent alerts
2. Test the API: `https://my-project-production-3d70.up.railway.app/api/alerts/recent`
3. Compare with local `kpi_logs.json`

## Troubleshooting

**If Lovable shows old alerts:**
1. ✅ Check Railway API: `https://my-project-production-3d70.up.railway.app/api/alerts/recent`
2. ✅ Check Railway logs for recent alert activity
3. ✅ Verify `kpi_logs.json` is in Git (so it syncs to Railway)
4. ✅ Check if alerts are being filtered out (MCAP > 500k, tier filters, etc.)

**If no alerts in hours:**
- This is **normal** - your filters are strict (which is good!)
- Check Railway logs to see if alerts are being triggered but filtered
- Lower MCAP threshold if you want more alerts (currently 500k)

