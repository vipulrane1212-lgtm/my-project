# API Update for Lovable - Entry MCAP Field Change

## ⚠️ IMPORTANT: API Field Change

**Date:** December 26, 2025  
**Status:** ✅ Deployed and Ready

## What Changed

### Before:
- `currentMcap` = MCAP shown in Telegram post
- `entryMc` = MCAP when alert was triggered (before posting)

### After (Current):
- `entryMc` = **MCAP shown in Telegram post** (the "Current MC" at the time of posting)
- `currentMcap` field **removed** from API response

## API Response Format

Each alert in `/api/alerts/recent` now returns:

```json
{
  "id": "contract_id_timestamp",
  "token": "TOKEN_NAME",
  "tier": 1,
  "level": "HIGH",
  "timestamp": "2025-12-26T10:50:00.000000+00:00",
  "contract": "CONTRACT_ADDRESS",
  "score": 79,
  "liquidity": 39472.41,
  "callers": 21,
  "subs": 113650,
  "matchedSignals": ["glydo"],
  "tags": ["has_glydo"],
  "hotlist": "Yes",
  "description": "Spicy intro paragraph...",
  "entryMc": 265600.0,  // ⚠️ THIS IS THE MCAP FROM TELEGRAM POST
  "confirmationCount": 2,
  "cohortTime": "0s ago"
}
```

## What Lovable Needs to Do

### 1. Update Field Mapping

**Change from:**
```javascript
// OLD (don't use)
const currentMC = alert.currentMcap;
const entryMC = alert.entryMc;
```

**Change to:**
```javascript
// NEW (use this)
const entryMC = alert.entryMc;  // This is the MCAP from Telegram post
// currentMcap field no longer exists
```

### 2. Display Update

**For "Entry MCAP" display:**
- Use: `alert.entryMc`
- This is the MCAP that was shown in the Telegram post (the "Current MC" at posting time)

**Example:**
```javascript
// Display Entry MCAP
const entryMC = alert.entryMc || 0;
const formattedMC = `$${(entryMC / 1000).toFixed(1)}K`; // e.g., "$265.6K"
```

### 3. Remove currentMcap References

**Remove any code that uses:**
- `alert.currentMcap`
- `currentMcap` field

**The API no longer returns this field.**

## Backfill Status

✅ **All historical alerts have been updated:**
- 157 alerts updated with correct `entryMc` (MCAP from Telegram post)
- 17 old alerts couldn't be updated (no MCAP data available - these are very old alerts)

## API Endpoint

**No changes to endpoint URL:**
```
GET https://my-project-production-3d70.up.railway.app/api/alerts/recent?limit=50&dedupe=false
```

## Testing

**Test the API:**
```bash
curl https://my-project-production-3d70.up.railway.app/api/alerts/recent?limit=5
```

**Verify response:**
- Each alert should have `entryMc` field
- `entryMc` should be the MCAP value (number)
- No `currentMcap` field should be present

## Summary

**Action Required in Lovable:**
1. ✅ Use `alert.entryMc` for Entry MCAP display
2. ✅ Remove any references to `alert.currentMcap`
3. ✅ Update display logic to show `entryMc` as the MCAP from Telegram post

**No other changes needed** - all other fields remain the same.

---

**Last Updated:** December 26, 2025  
**Status:** ✅ Ready for Lovable Integration

