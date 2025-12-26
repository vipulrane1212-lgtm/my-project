# 📋 Complete API Response Fields Reference

## Recent Alerts Endpoint Response

**Endpoint:** `GET /api/alerts/recent`

### Complete Alert Object Structure

```json
{
  "id": "678QT3ZQ_2025-12-25",
  "token": "LICO",
  "tier": 3,
  "level": "MEDIUM",
  "timestamp": "2025-12-25T18:43:03.232405+00:00",
  "contract": "678QT3ZQCCBLJJZB5IC5FVMAV94AYRIWSZ3FUYSRVYNC",
  "score": 75,
  "liquidity": 35805.71,
  "callers": 18,
  "subs": 100791,
  "matchedSignals": ["Early trending"],
  "tags": ["weak_social"],
  "hotlist": "No",
  "description": "Hybrid heat: LICO's trending + mixed confirms—heat from all angles, no cold spots. Early signals set the stage. Cohort stole the show. Hot List? Standing ovation. Applaud with apes.",
  "currentMcap": 143500
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique alert identifier (contract prefix + date) |
| `token` | string | Token symbol (e.g., "LICO") |
| `tier` | number | Alert tier: 1 (ULTRA), 2 (HIGH), or 3 (MEDIUM) |
| `level` | string | Alert level: "HIGH" or "MEDIUM" |
| `timestamp` | string | Alert timestamp in ISO 8601 format (UTC) |
| `contract` | string | Solana contract address |
| `score` | number | Alert score (0-100) |
| `liquidity` | number | Liquidity in USD |
| `callers` | number | Number of callers |
| `subs` | number | Number of subscribers |
| `matchedSignals` | array | Array of matched signal sources (e.g., ["Early trending"]) |
| `tags` | array | Array of alert tags (e.g., ["weak_social"]) |
| `hotlist` | string | ✅ **NEW** - Hot List status: "Yes" or "No" |
| `description` | string | ✅ **NEW** - Spicy intro paragraph (same as Telegram post) |
| `currentMcap` | number | ✅ **NEW** - Market cap at alert time (the MC shown in the post, e.g., 143500 for $143.5K) |

### Important Notes

1. **`hotlist`**: Indicates if the token was in the Hot List when the alert was triggered
2. **`description`**: The same themed intro paragraph shown in the Telegram alert message
3. **`currentMcap`**: This is the **entry market cap** (market cap at the time the alert was called), NOT the current live market cap. This matches what's shown in the Telegram post.

### Example Response

```json
{
  "alerts": [
    {
      "id": "678QT3ZQ_2025-12-25",
      "token": "LICO",
      "tier": 3,
      "level": "MEDIUM",
      "timestamp": "2025-12-25T18:43:03.232405+00:00",
      "contract": "678QT3ZQCCBLJJZB5IC5FVMAV94AYRIWSZ3FUYSRVYNC",
      "score": 75,
      "liquidity": 35805.71,
      "callers": 18,
      "subs": 100791,
      "matchedSignals": ["Early trending"],
      "tags": ["weak_social"],
      "hotlist": "No",
      "description": "Hybrid heat: LICO's trending + mixed confirms—heat from all angles, no cold spots. Early signals set the stage. Cohort stole the show. Hot List? Standing ovation. Applaud with apes.",
      "currentMcap": 143500
    }
  ],
  "count": 1,
  "timestamp": "2025-12-25T19:00:00.000000+00:00"
}
```

---

## Updated: December 25, 2025

All three new fields (`hotlist`, `description`, `currentMcap`) are now included in the API response.

