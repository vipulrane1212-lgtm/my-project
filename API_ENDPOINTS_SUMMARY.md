# SolBoy Alerts API Endpoints

## Base URL
```
https://my-project-production-3d70.up.railway.app
```

---

## 📊 Tier Endpoints

### 1. Get Recent Alerts (with Tier Filter)
**Endpoint:** `GET /api/alerts/recent`

**Query Parameters:**
- `limit` (optional, default: 20) - Number of alerts to return
- `tier` (optional) - Filter by tier: `1`, `2`, or `3`

**Examples:**
```
GET /api/alerts/recent
GET /api/alerts/recent?limit=50
GET /api/alerts/recent?tier=1
GET /api/alerts/recent?limit=10&tier=2
```

**Response:**
```json
{
  "alerts": [
    {
      "id": "D3HZIGZU_2025-12-26",
      "token": "SNOWWIF",
      "tier": 1,
      "level": "HIGH",
      "timestamp": "2025-12-26T01:54:56.413443+00:00",
      "contract": "D3HZIGZUE8XCJBU8PFYLGC8IEPA5ZNBFCWQJUMEUPUMP",
      "score": 25,
      "liquidity": 123456.78,
      "callers": 150,
      "subs": 50000,
      "matchedSignals": ["Glydo Top 5", "Momentum spike"],
      "tags": ["has_glydo"],
      "hotlist": "Yes",
      "description": "Spicy intro paragraph...",
      "currentMcap": 75000.0
    }
  ],
  "count": 1,
  "timestamp": "2025-12-26T05:00:00.000000+00:00"
}
```

**Fields:**
- `tier`: 1 (TIER 1 ULTRA), 2 (TIER 2 HIGH), or 3 (TIER 3 MEDIUM)
- `hotlist`: "Yes" or "No" (whether token was in Hot List/Glydo Top 5)

---

### 2. Get Tier Breakdown
**Endpoint:** `GET /api/alerts/tiers`

**Description:** Get count and recent alerts for each tier.

**Response:**
```json
{
  "tier1": {
    "count": 45,
    "alerts": [
      {
        "token": "SNOWWIF",
        "timestamp": "2025-12-26T01:54:56.413443+00:00",
        "contract": "D3HZIGZUE8XCJBU8PFYLGC8IEPA5ZNBFCWQJUMEUPUMP"
      }
    ]
  },
  "tier2": {
    "count": 120,
    "alerts": [...]
  },
  "tier3": {
    "count": 200,
    "alerts": [...]
  },
  "total": 365
}
```

---

## 🔥 Hotlist Endpoints

### Hotlist is included in Recent Alerts

The `hotlist` field is included in the `/api/alerts/recent` endpoint response.

**To filter by hotlist status**, you can:
1. Call `/api/alerts/recent` and filter client-side
2. Use the `tier=1` filter (TIER 1 alerts often have hotlist="Yes")

**Hotlist Field:**
- `hotlist: "Yes"` - Token was in Glydo Top 5 (Hot List) when alert was triggered
- `hotlist: "No"` - Token was not in Hot List

**Example:**
```json
{
  "alerts": [
    {
      "token": "SNOWWIF",
      "tier": 1,
      "hotlist": "Yes",  // ← Hotlist status here
      ...
    }
  ]
}
```

---

## 📈 Other Endpoints

### 3. Get Statistics
**Endpoint:** `GET /api/stats`

**Response:**
```json
{
  "totalSubscribers": 1250,
  "userSubscribers": 850,
  "groupSubscribers": 400,
  "totalAlerts": 365,
  "tier1Alerts": 45,
  "tier2Alerts": 120,
  "tier3Alerts": 200,
  "winRate": 68.5,
  "recentAlerts24h": 12,
  "recentAlerts7d": 89,
  "truePositives": 250,
  "falsePositives": 115,
  "lastUpdated": "2025-12-26T05:00:00.000000+00:00"
}
```

---

### 4. Get Daily Statistics
**Endpoint:** `GET /api/alerts/stats/daily?days=7`

**Query Parameters:**
- `days` (optional, default: 7) - Number of days

**Response:**
```json
{
  "period": 7,
  "data": [
    {
      "date": "2025-12-20",
      "total": 15,
      "tier1": 2,
      "tier2": 5,
      "tier3": 8
    },
    ...
  ]
}
```

---

### 5. Get Subscribers
**Endpoint:** `GET /api/subscribers`

**Response:**
```json
{
  "totalSubscribers": 1250,
  "userSubscribers": 850,
  "groupSubscribers": 400,
  "usersWithPreferences": 120,
  "lastUpdated": "2025-12-26T05:00:00.000000+00:00"
}
```

---

### 6. Health Check
**Endpoint:** `GET /api/health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-26T05:00:00.000000+00:00",
  "files": {
    "subscriptions": true,
    "kpi_logs": true,
    "alert_groups": true,
    "user_preferences": true
  }
}
```

---

## 🔧 Tier Filtering Examples

### Get only TIER 1 alerts:
```
GET https://my-project-production-3d70.up.railway.app/api/alerts/recent?tier=1
```

### Get only TIER 2 alerts:
```
GET https://my-project-production-3d70.up.railway.app/api/alerts/recent?tier=2
```

### Get only TIER 3 alerts:
```
GET https://my-project-production-3d70.up.railway.app/api/alerts/recent?tier=3
```

### Get last 50 alerts (all tiers):
```
GET https://my-project-production-3d70.up.railway.app/api/alerts/recent?limit=50
```

---

## 🐛 Fixed Issues

### Tier Mapping Bug (FIXED)
**Problem:** Tier 1 alerts (stored as `level="HIGH"`) were showing as Tier 2 in the API.

**Root Cause:** 
- Tier 1 alerts → `level="HIGH"` 
- API converted `"HIGH"` → tier 2 (incorrect)

**Fix:**
- API now uses `tier` field directly from alert if available
- `get_tier_from_level()` now maps `"HIGH"` → tier 1 (correct)
- Falls back to level conversion only if `tier` field is missing

**Result:** SNOWWIF and other Tier 1 alerts now correctly show as `tier: 1` in the API.

---

## 📝 Notes

1. **Tier Field Priority:** The API now prioritizes the `tier` field from the alert over level conversion
2. **Backward Compatibility:** Older alerts without `tier` field will use level conversion (HIGH → tier 1, MEDIUM → tier 2)
3. **Hotlist:** Included in each alert in `/api/alerts/recent` response
4. **Real-time:** Data is read from `kpi_logs.json` on each request (no caching)

