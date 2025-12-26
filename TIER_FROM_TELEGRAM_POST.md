# Tier from Telegram Post - How It Works

## ✅ Confirmed: API Uses Tier from Telegram Post

The API **already uses the tier field directly** from the alert, which is the same tier shown in the Telegram post.

## Flow

### 1. Alert Created
- Alert object has `tier` field set (1, 2, or 3)
- This comes from `live_monitor_core.py` → `opportunity["tier"]`

### 2. Telegram Post Created
- `format_alert()` in `live_alert_formatter.py` line 552: `tier = alert.get("tier")`
- Line 603: `text = f"🚨 **ALPHA INCOMING — TIER {tier} LOCKED**`
- **This is the tier shown in Telegram**

### 3. Alert Saved
- `telegram_monitor_new.py` line 418: `self.kpi_logger.log_alert(alert, level)`
- `kpi_logger.py` line 71: `"tier": alert.get("tier")`
- **The tier field is saved to kpi_logs.json**

### 4. API Returns Tier
- `api_server.py` line 94-95: `if alert_tier is not None and alert_tier in [1, 2, 3]: return alert_tier`
- **API uses the tier field directly (same as Telegram post)**

## Priority Order

1. **Tier field** (from alert) → **This is what was shown in Telegram** ✅
2. Heuristics (only if tier field is missing, for old alerts)

## Current Status

**The API already does this correctly!** It prioritizes the `tier` field, which is the same tier shown in the Telegram post.

**If you're seeing wrong tiers:**
- Check if `tier` field is being saved in `kpi_logs.json`
- New alerts should have the `tier` field saved correctly
- Old alerts without `tier` field will use heuristics (which may not be 100% accurate)

## Verification

To verify the tier is being saved correctly:

1. **Check a recent alert in kpi_logs.json:**
   ```json
   {
     "tier": 1,  // ← This should match what was shown in Telegram
     "level": "HIGH",
     ...
   }
   ```

2. **Check API response:**
   ```json
   {
     "tier": 1,  // ← Should match Telegram post
     ...
   }
   ```

3. **If tier is None:**
   - The alert was created before tier field was added
   - API will use heuristics (may not be 100% accurate)

## Summary

✅ **API uses tier from Telegram post** - The `tier` field in the alert is what's shown in Telegram, and the API uses it directly.

✅ **Priority:** Tier field → Heuristics (only for old alerts)

✅ **New alerts:** Will have correct tier field saved

⚠️ **Old alerts:** May not have tier field, will use heuristics

