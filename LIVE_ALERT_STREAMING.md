# Live Alert Streaming - Complete Setup

## ✅ Single Endpoint: `/api/alerts/recent`

This is your **ONE endpoint** that streams live alerts with full persistence.

### Features

✅ **Streams Live Alerts** - Updates every 5 seconds or immediately on file change  
✅ **Stores in JSON** - All alerts saved to `kpi_logs.json`  
✅ **No Data Loss** - Git sync after every alert  
✅ **Survives Redeploy** - Git sync ensures alerts restored on redeploy  
✅ **Old + New Alerts** - Returns ALL alerts from storage  

### Usage

```bash
# Get recent alerts (default: 20)
GET /api/alerts/recent

# Get all alerts (no limit)
GET /api/alerts/recent?limit=0

# Filter by tier
GET /api/alerts/recent?tier=1

# Disable deduplication
GET /api/alerts/recent?dedupe=false
```

### Response Format

```json
{
  "alerts": [
    {
      "id": "7W359GHT_2026-01-02",
      "token": "YOSHI",
      "tier": 1,
      "level": "HIGH",
      "timestamp": "2026-01-02T20:40:08+00:00",
      "contract": "7W359GHTF2MPY9CB4SJFEC66UJ8ONNM3CR472WLLPUMP",
      "entryMc": 198100.0,
      "hotlist": "Yes",
      "description": "...",
      "confirmationCount": 2,
      "cohortTime": "3h ago"
    }
  ],
  "count": 20,
  "total_in_storage": 276,  // Total alerts in kpi_logs.json
  "timestamp": "2026-01-02T17:50:03+00:00"
}
```

## 🔄 How It Works

### 1. Alert Flow

```
Telegram Alert → Bot Receives → Save to kpi_logs.json → Git Sync → API Reads → Website Shows
```

### 2. Storage

- **File**: `kpi_logs.json` (or `/data/kpi_logs.json` on Railway)
- **Format**: JSON with `alerts` array
- **Location**: 
  - Local: `./kpi_logs.json`
  - Railway: `/data/kpi_logs.json` (persistent volume) or `./kpi_logs.json`

### 3. Persistence (No Data Loss)

**Git Sync After Every Alert:**
- Bot saves alert → Commits to Git → Pushes to remote
- On Railway redeploy → Git pulls → All alerts restored
- **Zero data loss** even on redeploy

**Git Credentials:**
- Set `GITHUB_TOKEN` in Railway Variables
- Token must have `repo` scope
- See `RAILWAY_GIT_SETUP_INSTRUCTIONS.md` for setup

### 4. Cache Refresh

- **TTL**: 5 seconds (fast updates)
- **File Change Detection**: Immediate refresh when `kpi_logs.json` is modified
- **Manual Refresh**: `GET /api/cache/refresh`

## 📊 Current Status

- **Total Alerts**: Check `total_in_storage` in API response
- **Latest Alert**: First item in `alerts` array (sorted newest first)
- **Storage**: All alerts in `kpi_logs.json`

## 🔧 Configuration

### Cache Settings

```python
CACHE_TTL_SECONDS = 5  # Refresh every 5 seconds
```

### File Paths

```python
# Local
KPI_LOGS_FILE = Path("kpi_logs.json")

# Railway (with persistent volume)
KPI_LOGS_FILE = Path("/data/kpi_logs.json")
```

## ✅ Verification

1. **Check API**: `GET /api/alerts/recent`
2. **Check Storage**: `kpi_logs.json` file
3. **Check Git**: `git log kpi_logs.json`
4. **Check Cache**: `GET /api/cache/refresh`

## 🚀 Summary

**One Endpoint**: `/api/alerts/recent`  
**Storage**: JSON (`kpi_logs.json`)  
**Persistence**: Git sync after every alert  
**Updates**: Every 5 seconds or on file change  
**No Data Loss**: ✅ Guaranteed  

Everything is already set up and working! 🎉

