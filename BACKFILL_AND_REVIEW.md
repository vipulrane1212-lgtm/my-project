# Backfill Tier & MCAP from Telegram Posts - Complete Guide

## Overview

This guide explains how to backfill missing tier and MCAP data from old Telegram alert posts to fix historical alert statistics on your website.

---

## Problem

**Old alerts in `kpi_logs.json` are missing:**
- `tier` field (all are `None`)
- `mc_usd` or `entry_mc` (market cap shown in Telegram post)
- Accurate timestamps

**Result:**
- Website shows incorrect tier distribution (TIER 3 = 0)
- Missing market cap data for historical alerts
- Historical stats are inaccurate

---

## Solution: Backfill Script

Created `backfill_tier_from_telegram.py` to:
1. Connect to Telegram
2. Fetch old alert messages from your alert channel/group
3. Extract tier and MCAP from message text
4. Match alerts to Telegram messages
5. Update `kpi_logs.json` with correct data

---

## How to Run Backfill

### Step 1: Set Environment Variables

```bash
# Required
export API_ID="your_api_id"
export API_HASH="your_api_hash"
export SESSION_NAME="telegram_monitor"  # Your existing session
export ALERT_CHAT_ID="your_alert_channel_id_or_username"  # e.g., "@solboy_calls" or "-1001234567890"
```

### Step 2: Run Backfill Script

```bash
python backfill_tier_from_telegram.py
```

### Step 3: Verify Results

The script will:
- Create a backup of `kpi_logs.json` → `kpi_logs.json.backup`
- Update alerts with tier and MCAP from Telegram
- Print summary of updates

---

## What Gets Extracted

### Tier Extraction

The script looks for:
- `"TIER 1"`, `"TIER 2"`, `"TIER 3"` in message text
- `"TIER 1 LOCKED"`, `"TIER 2 LOCKED"`, etc.
- Tier emojis: 🚀 (Tier 1), 🔥 (Tier 2), ⚡ (Tier 3)

### MCAP Extraction

The script looks for:
- `"Current MC: $143.5K"`
- `"Current MC: **$143,500**"`
- `"MC: $143K"`
- Handles K (thousands) and M (millions) multipliers

### Matching Logic

1. **By Contract Address** (most reliable)
   - Exact match on contract address

2. **By Token + Timestamp** (fallback)
   - Matches token name
   - Within 2 hours of alert timestamp

---

## Expected Results

After backfill:
- ✅ All alerts have `tier` field (1, 2, or 3)
- ✅ All alerts have `mc_usd` or `entry_mc` (market cap from Telegram)
- ✅ Accurate timestamps from Telegram messages
- ✅ Correct tier distribution on website
- ✅ Historical stats are accurate

---

## API Review & Fixes

### Current API Endpoints

All endpoints now use the `tier` field directly:

1. **`/api/stats`** - Tier distribution
   - Uses `get_tier_from_level(level, alert_tier, alert)`
   - Prioritizes `tier` field from alert

2. **`/api/alerts/recent`** - Recent alerts
   - Uses `tier` field directly
   - Deduplicates by default (`dedupe=true`)

3. **`/api/alerts/tiers`** - Tier breakdown
   - Counts alerts by tier using `tier` field

4. **`/api/alerts/stats/daily`** - Daily stats
   - Groups alerts by date and tier
   - Uses `tier` field for accurate breakdown

### Historical Stats Fix

**Before backfill:**
- Tier 1: 58 (HIGH alerts)
- Tier 2: 115 (all MEDIUM alerts - wrong!)
- Tier 3: 0 (missing - wrong!)

**After backfill:**
- Tier 1: X (alerts with `tier: 1`)
- Tier 2: Y (alerts with `tier: 2`)
- Tier 3: Z (alerts with `tier: 3`)
- Total: 173 (all alerts properly categorized)

---

## Verification Steps

### 1. Check Backfill Results

```bash
# Count alerts with tier field
python -c "import json; data = json.load(open('kpi_logs.json')); alerts = data.get('alerts', []); with_tier = [a for a in alerts if a.get('tier') is not None]; print(f'Alerts with tier: {len(with_tier)}/{len(alerts)}')"
```

### 2. Test API Endpoints

```bash
# Check tier distribution
curl https://my-project-production-3d70.up.railway.app/api/stats

# Check recent alerts
curl https://my-project-production-3d70.up.railway.app/api/alerts/recent?limit=5

# Check tier breakdown
curl https://my-project-production-3d70.up.railway.app/api/alerts/tiers
```

### 3. Verify Website Display

- Check tier distribution chart
- Verify historical stats
- Confirm MCAP is showing for old alerts

---

## Complete Review Checklist

### ✅ Data Integrity

- [ ] All alerts have `tier` field (1, 2, or 3)
- [ ] All alerts have `mc_usd` or `entry_mc` (market cap)
- [ ] Timestamps are accurate
- [ ] No duplicate alerts (deduplication working)

### ✅ API Endpoints

- [ ] `/api/stats` returns correct tier distribution
- [ ] `/api/alerts/recent` shows correct tiers
- [ ] `/api/alerts/tiers` has accurate counts
- [ ] `/api/alerts/stats/daily` shows correct daily breakdown

### ✅ Website Display

- [ ] Tier distribution chart is accurate
- [ ] Historical stats are correct
- [ ] MCAP is displayed for all alerts
- [ ] No duplicate alerts showing

### ✅ Data Source

- [ ] All data comes from `kpi_logs.json`
- [ ] No mismatches between Telegram and API
- [ ] Tier matches what was shown in Telegram post

---

## Troubleshooting

### Issue: Backfill script can't connect to Telegram

**Solution:**
- Check `API_ID`, `API_HASH`, and `SESSION_NAME` are correct
- Make sure session file exists (e.g., `telegram_monitor.session`)

### Issue: Can't find alert channel

**Solution:**
- Check `ALERT_CHAT_ID` is correct
- Use channel username (e.g., `@solboy_calls`) or ID (e.g., `-1001234567890`)
- Make sure bot/user has access to the channel

### Issue: Alerts not matching

**Solution:**
- Check if contract addresses match
- Verify token names are consistent
- Check timestamps are within 2 hours

### Issue: Tier/MCAP not extracted

**Solution:**
- Check message format matches expected pattern
- Verify message text contains "TIER X" and "Current MC: $XXX"
- Check if message was edited (edits might not be accessible)

---

## Summary of Changes

### Files Created/Modified

1. **`backfill_tier_from_telegram.py`** (NEW)
   - Script to backfill tier and MCAP from Telegram posts

2. **`api_server.py`** (UPDATED)
   - Uses `tier` field directly (prioritizes over heuristics)
   - Improved tier detection with heuristics for old alerts
   - Deduplication added to `/api/alerts/recent`

3. **`telegram_monitor_new.py`** (UPDATED)
   - Added debug logging for tier field
   - Ensures tier is saved correctly

### Key Improvements

✅ **Tier Detection:**
- Uses `tier` field directly (from Telegram post)
- Falls back to heuristics only if `tier` is missing
- Heuristics distinguish Tier 2 from Tier 3 using Glydo/hotlist data

✅ **Deduplication:**
- API deduplicates alerts by default (one per token)
- Prevents duplicate alerts on website

✅ **MCAP Handling:**
- Prioritizes `entry_mc` (market cap at alert time)
- Falls back to `mc_usd` if `entry_mc` missing
- Extracts from Telegram posts during backfill

✅ **Historical Stats:**
- All endpoints use `tier` field for accurate counts
- Daily stats properly grouped by tier
- Tier breakdown is accurate

---

## Next Steps

1. **Run backfill script** to update old alerts
2. **Verify results** using the checklist above
3. **Test API endpoints** to ensure everything works
4. **Check website** to confirm correct display
5. **Monitor new alerts** to ensure tier field is saved correctly

---

## Notes

- **Backup created:** `kpi_logs.json.backup` (before backfill)
- **Safe to re-run:** Script only updates missing fields
- **Incremental:** Can run multiple times safely
- **Telegram rate limits:** May take time for large channels

