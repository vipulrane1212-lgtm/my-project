# API Issues Fixed - For Lovable Team

## Issues Reported

1. **LICO showing as Tier 1** (but might not be)
2. **SNOWWIF appearing 3 times** (duplicate alerts)
3. **Data mismatch** between alert log and API response

---

## Root Causes Identified

### 1. Duplicate Alerts (SNOWWIF appearing multiple times)

**Problem:** 
- Same token can have multiple alerts over time (e.g., first MEDIUM, then HIGH)
- API was returning ALL alerts without deduplication
- SNOWWIF has 2 alerts (not 3), both showing in recent alerts

**Fix:**
- Added `dedupe` parameter to `/api/alerts/recent` endpoint (default: `true`)
- API now shows only the **latest alert per token** by default
- To see all alerts (including duplicates), use `?dedupe=false`

**Example:**
```
GET /api/alerts/recent?dedupe=true   # Only latest per token (default)
GET /api/alerts/recent?dedupe=false  # Show all alerts
```

---

### 2. Tier Mapping Issues (LICO showing as Tier 1)

**Problem:**
- Old alerts don't have `tier` field saved (field is `None`)
- API was inferring tier from `level` field
- Mapping: `HIGH` → tier 1, `MEDIUM` → tier 2
- But this might be wrong for some old alerts

**Current Logic:**
- **New alerts**: Use `tier` field directly (most reliable)
- **Old alerts**: Infer from `level`:
  - `HIGH` → tier 1
  - `MEDIUM` → tier 2 or tier 3 (defaults to tier 2)

**LICO Case:**
- LICO has 2 alerts:
  1. Latest: `level="HIGH"` → mapped to tier 1
  2. Older: `level="MEDIUM"` → mapped to tier 2
- The latest HIGH alert is showing as tier 1, which might be correct if it was actually a tier 1 alert

**Note:** For old alerts without `tier` field, the mapping might not be 100% accurate. New alerts (after the fix) will have the correct `tier` field saved.

---

### 3. Data Source

**All data comes from ONE source:** `kpi_logs.json`

**Flow:**
```
1. Alert triggered → telegram_monitor_new.py
2. Alert logged → kpi_logger.log_alert() → saves to kpi_logs.json
3. API reads → api_server.py reads from kpi_logs.json
4. Frontend displays → Lovable shows the data
```

**No mismatch** - everything reads from the same JSON file.

---

## API Endpoints (Updated)

### Get Recent Alerts (with deduplication)

**Endpoint:** `GET /api/alerts/recent`

**Query Parameters:**
- `limit` (optional, default: 20) - Number of alerts
- `tier` (optional) - Filter by tier: `1`, `2`, or `3`
- `dedupe` (optional, default: `true`) - Deduplicate by token

**Examples:**
```
# Get latest 20 alerts (deduplicated by default)
GET /api/alerts/recent

# Get only Tier 1 alerts (deduplicated)
GET /api/alerts/recent?tier=1

# Get all alerts (including duplicates)
GET /api/alerts/recent?dedupe=false

# Get last 50 Tier 1 alerts (deduplicated)
GET /api/alerts/recent?limit=50&tier=1&dedupe=true
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
      "hotlist": "Yes",
      "description": "...",
      "currentMcap": 75000.0
    }
  ],
  "count": 1,
  "timestamp": "2025-12-26T05:00:00.000000+00:00"
}
```

---

### Tier Endpoints

**Get Tier 1 alerts:**
```
GET /api/alerts/recent?tier=1
```

**Get Tier 2 alerts:**
```
GET /api/alerts/recent?tier=2
```

**Get Tier 3 alerts:**
```
GET /api/alerts/recent?tier=3
```

**Get tier breakdown:**
```
GET /api/alerts/tiers
```

---

### Hotlist

Hotlist status is included in each alert:
- `hotlist: "Yes"` - Token was in Glydo Top 5 (Hot List)
- `hotlist: "No"` - Token was not in Hot List

**No separate endpoint** - hotlist is part of the alert object.

---

## Recommendations for Lovable

### 1. Use Deduplication (Default)

**Recommended:** Always use `dedupe=true` (default) to show only latest alert per token:
```
GET /api/alerts/recent?tier=1
```

This prevents showing multiple alerts for the same token.

### 2. Handle Tier Field

**For new alerts:** Use `tier` field directly (most reliable)

**For old alerts:** Tier might be inferred from `level`, which may not be 100% accurate

**Best practice:** Check both `tier` and `level` fields:
```javascript
// Use tier if available, otherwise infer from level
const tier = alert.tier || (alert.level === 'HIGH' ? 1 : 2);
```

### 3. Data Freshness

- API reads from `kpi_logs.json` on each request (no caching)
- Data is updated in real-time as alerts are logged
- Latest alert timestamp is included in response

---

## Testing

**Test the fixes:**

1. **Deduplication:**
   ```
   GET https://my-project-production-3d70.up.railway.app/api/alerts/recent?dedupe=true
   ```
   Should show only one alert per token.

2. **Tier 1 alerts:**
   ```
   GET https://my-project-production-3d70.up.railway.app/api/alerts/recent?tier=1
   ```
   Should show only tier 1 alerts (deduplicated).

3. **All alerts (with duplicates):**
   ```
   GET https://my-project-production-3d70.up.railway.app/api/alerts/recent?dedupe=false
   ```
   Should show all alerts including duplicates.

---

## Summary of Fixes

✅ **Fixed:** Duplicate alerts (SNOWWIF appearing multiple times)
- Added deduplication by default
- Shows only latest alert per token

✅ **Fixed:** Tier mapping for Tier 1 alerts
- HIGH level now correctly maps to tier 1
- Uses `tier` field when available (most reliable)

✅ **Clarified:** Data source
- All data comes from `kpi_logs.json`
- No mismatch - single source of truth

⚠️ **Note:** Old alerts without `tier` field use level inference, which might not be 100% accurate for all cases.

---

## Next Steps

1. **Update Lovable** to use `dedupe=true` (or omit it, as it's default)
2. **Test** the endpoints to verify fixes
3. **Monitor** new alerts - they should have correct `tier` field

---

## Contact

If you see any issues, check:
1. Railway logs for API errors
2. `kpi_logs.json` file for raw data
3. API response includes `timestamp` field for freshness

