# SolBoy Alerts API

**Base URL**: `https://my-project-production-3d70.up.railway.app`  
**Status**: ✅ **PRODUCTION READY**

## 🚀 Quick Start

### Single Endpoint for Live Alerts

**`GET /api/alerts/recent`** - Streams live alerts from JSON storage

```bash
# Get recent alerts (default: 20)
GET https://my-project-production-3d70.up.railway.app/api/alerts/recent

# Get all alerts (no limit)
GET https://my-project-production-3d70.up.railway.app/api/alerts/recent?limit=0

# Filter by tier
GET https://my-project-production-3d70.up.railway.app/api/alerts/recent?tier=1

# Disable deduplication
GET https://my-project-production-3d70.up.railway.app/api/alerts/recent?dedupe=false
```

## 📋 API Endpoints

### 1. Root Endpoint
**`GET /`**
- Returns API information and available endpoints
- **Response**: API version, endpoints list, features

### 2. Health Check
**`GET /api/health`**
- Returns system health status
- **Response**: 
  ```json
  {
    "status": "healthy",
    "timestamp": "2026-01-02T17:55:12+00:00",
    "files": {
      "subscriptions": true,
      "kpi_logs": true,
      "alert_groups": true,
      "user_preferences": true
    },
    "alerts": {
      "total": 276,
      "latest": {
        "token": "VIENNA",
        "timestamp": "2026-01-02T21:00:33+00:00",
        "tier": 3
      }
    }
  }
  ```

### 3. Recent Alerts ⭐ **MAIN ENDPOINT**
**`GET /api/alerts/recent`**

**Query Parameters:**
- `limit` (int, default: 20) - Number of alerts to return (0 = all)
- `tier` (int, optional) - Filter by tier (1, 2, or 3)
- `dedupe` (bool, default: true) - Show only latest alert per token

**Response:**
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
      "description": "YOSHI wildcard win: Trending post + volume spike...",
      "confirmationCount": 2,
      "cohortTime": "3h ago",
      "matchedSignals": ["glydo"],
      "liquidity": null,
      "callers": 0,
      "subs": 0
    }
  ],
  "count": 20,
  "total_in_storage": 276,
  "timestamp": "2026-01-02T17:50:03+00:00"
}
```

### 4. Statistics
**`GET /api/stats`**
- Returns real-time statistics
- **Response**:
  ```json
  {
    "totalSubscribers": 0,
    "userSubscribers": 0,
    "groupSubscribers": 0,
    "totalAlerts": 276,
    "tier1Alerts": 45,
    "tier2Alerts": 67,
    "tier3Alerts": 164,
    "winRate": 0.0,
    "recentAlerts24h": 27,
    "recentAlerts7d": 276,
    "truePositives": 0,
    "falsePositives": 0,
    "lastUpdated": "2026-01-02T17:55:48+00:00"
  }
  ```

### 5. Subscribers
**`GET /api/subscribers`**
- Returns subscriber information
- **Response**: Total subscribers, user subscribers, group subscribers

### 6. Tier Breakdown
**`GET /api/alerts/tiers`**
- Returns alert breakdown by tier
- **Response**: Count and recent alerts for each tier (1, 2, 3)

### 7. Daily Statistics
**`GET /api/alerts/stats/daily?days=7`**
- Returns daily statistics for charts
- **Query Parameters**: `days` (int, default: 7)

### 8. Cache Refresh
**`GET /api/cache/refresh`** or **`POST /api/cache/refresh`**
- Forces cache refresh
- **Response**: `{"status": "success", "message": "Cache invalidated, will refresh on next request"}`

## ✨ Features

### ✅ Live Streaming
- Updates every **5 seconds** or immediately on file change
- Real-time alert delivery

### ✅ JSON Storage
- All alerts stored in `kpi_logs.json`
- Human-readable format
- Easy to backup and restore

### ✅ No Data Loss
- **Git sync after every alert**
- All alerts committed and pushed to GitHub
- Survives Railway redeploys

### ✅ All Alerts Accessible
- Returns **old + new alerts**
- Historical data preserved
- No data loss on redeploy

## 🔄 How It Works

```
Telegram Alert → Bot Receives → Save to kpi_logs.json → Git Sync → API Reads → Website Shows
```

1. **Alert Received**: Bot receives alert from Telegram
2. **Save to JSON**: Alert saved to `kpi_logs.json`
3. **Git Sync**: Automatically commits and pushes to GitHub
4. **API Reads**: API reads from `kpi_logs.json` (cached for 5s)
5. **Website Shows**: Frontend displays alerts in real-time

## 📊 Current Status

- **Total Alerts**: 276 alerts stored
- **Recent Activity**: 27 alerts in last 24 hours
- **Latest Alert**: VIENNA (2026-01-02T21:00:33+00:00)
- **Cache**: Refreshes every 5 seconds or on file change

## 🔧 Configuration

### Cache Settings
- **TTL**: 5 seconds (fast updates)
- **File Change Detection**: Immediate refresh when `kpi_logs.json` is modified
- **Manual Refresh**: Use `/api/cache/refresh` endpoint

### Storage
- **Local**: `./kpi_logs.json`
- **Railway**: `/data/kpi_logs.json` (persistent volume) or `./kpi_logs.json`

### Git Sync
- **Automatic**: After every alert
- **Credentials**: Set `GITHUB_TOKEN` in Railway Variables
- **Scope**: Token must have `repo` scope

## 📝 Response Fields

### Alert Object
- `id` - Unique alert ID (contract + date)
- `token` - Token symbol (e.g., "YOSHI")
- `tier` - Alert tier (1, 2, or 3)
- `level` - Alert level ("HIGH" or "MEDIUM")
- `timestamp` - ISO 8601 timestamp
- `contract` - Solana contract address
- `entryMc` - Entry market cap (USD)
- `hotlist` - Hot list status ("Yes" or "No")
- `description` - Alert description
- `confirmationCount` - Number of confirmations
- `cohortTime` - Relative time (e.g., "3h ago")
- `matchedSignals` - Array of matched signals
- `liquidity` - Liquidity (USD)
- `callers` - Number of callers
- `subs` - Number of subscribers

## ✅ Verification

1. **Check API**: `GET /api/alerts/recent`
2. **Check Health**: `GET /api/health`
3. **Check Storage**: `kpi_logs.json` file
4. **Check Git**: `git log kpi_logs.json`
5. **Check Cache**: `GET /api/cache/refresh`

## 🔗 Quick Links

- **Base URL**: `https://my-project-production-3d70.up.railway.app`
- **API Docs**: `https://my-project-production-3d70.up.railway.app/docs` (FastAPI Swagger)
- **Health Check**: `https://my-project-production-3d70.up.railway.app/api/health`

## 📚 Additional Documentation

- **Live Streaming Guide**: `LIVE_ALERT_STREAMING.md`
- **API Status Report**: `API_STATUS_REPORT.md`
- **Git Setup**: `RAILWAY_GIT_SETUP_INSTRUCTIONS.md`
- **Detailed API Docs**: `API_DOCUMENTATION.md`

## 🚀 Summary

**One Endpoint**: `/api/alerts/recent`  
**Storage**: JSON (`kpi_logs.json`)  
**Persistence**: Git sync after every alert  
**Updates**: Every 5 seconds or on file change  
**No Data Loss**: ✅ Guaranteed  

**Status**: 🟢 **PRODUCTION READY**

