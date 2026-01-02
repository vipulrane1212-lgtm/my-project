# Missing Alerts Debug Report

**Date**: 2026-01-03  
**Issue**: 3 alerts (DHG, MWG, BLAST) from Telegram not appearing in API

## 🔍 Investigation Results

### Alerts Checked:
1. **DHG** (Contract: `3R48QGXWZN5WYQZUWOXQXUFVUEEUYC9WDDOCSQPPBONK`)
   - ✅ Found in kpi_logs.json BUT it's an OLD alert (2026-01-02T19:57:19)
   - ❌ NEW alert (2026-01-03T00:41:00) is MISSING

2. **MWG** (Contract: `3RQEUT98EKX1KJT1OWKP1WHN71XTVXAGTZB2HLQSFACK`)
   - ❌ NOT FOUND in kpi_logs.json
   - This alert is completely MISSING

3. **BLAST** (Contract: `9IEWUXV5Y9VAEK6GLVFZVKWZBMSVKEKUKAA61XATWA97`)
   - ✅ Found in kpi_logs.json BUT it's an OLD alert (2026-01-02T14:09:14)
   - ❌ NEW alert (2026-01-03T00:47:00) is MISSING

## 🎯 Root Cause Analysis

### Possible Causes:

1. **Bot Not Running**
   - The bot must be running to receive messages from source channels
   - If bot is stopped, it won't process new alerts
   - **Check**: Is the bot running on Railway/local?

2. **Bot Not Receiving Source Messages**
   - Bot monitors specific channels (Glydo, XTRACK, etc.)
   - If source channels aren't sending messages, bot won't generate alerts
   - **Check**: Are source channels active?

3. **Alert Generation Failed**
   - Bot receives message but fails to parse/generate alert
   - **Check**: Bot logs for parse errors

4. **Save Failed Silently**
   - Alert generated but save to kpi_logs.json failed
   - **Fixed**: Added better error handling and logging

## ✅ Fixes Applied

### 1. Enhanced Error Handling in `telegram_monitor_new.py`
- Added try-catch around `log_alert()` call
- Logs errors if save fails
- Continues processing even if save fails (to prevent blocking)

### 2. Enhanced Error Handling in `kpi_logger.py`
- Added detailed logging for save attempts
- Logs file state (mtime, size, exists)
- Better error messages with alert details

### 3. Debug Logging
- Added instrumentation to track:
  - When alerts are saved
  - When saves fail
  - File state at save time
  - Contract addresses for tracking

## 🔧 Next Steps

### 1. Check Bot Status
```bash
# Check if bot is running on Railway
# Check Railway logs for errors
```

### 2. Check Bot Logs
Look for:
- `✅ Alert saved to kpi_logs.json` - Confirms saves
- `❌ CRITICAL: Failed to save alert` - Indicates save failures
- `[SOURCE] 📨 Message #X received` - Confirms message reception
- `[SOURCE] ❌ [PARSE FAILED]` - Indicates parse errors

### 3. Verify Source Channels
- Check if source channels (Glydo, XTRACK, etc.) are sending messages
- Bot only processes messages from monitored channels

### 4. Check Debug Logs
- Debug logs are written to `.cursor/debug.log`
- Check for save failures or errors

## 📊 Current Status

- **Total Alerts in kpi_logs.json**: 285
- **Latest Alert**: SZN (2026-01-02T23:10:08)
- **Missing Alerts**: 3 (DHG, MWG, BLAST from 2026-01-03)

## 🚨 Critical Questions

1. **Was the bot running when these alerts were sent?**
   - If no → Bot needs to be running 24/7
   - If yes → Check logs for errors

2. **Did the bot receive the source messages?**
   - Check logs for `[SOURCE] 📨 Message received`
   - If no messages received → Source channels might be inactive

3. **Did alert generation succeed?**
   - Check logs for `ingest_event returned alerts`
   - If no alerts generated → Check parse/generation logic

4. **Did save succeed?**
   - Check logs for `✅ Alert saved to kpi_logs.json`
   - If save failed → Check file permissions/disk space

## 🔄 Recovery

If alerts are missing, you can:
1. **Backfill from Telegram** - Use `recover_alerts_from_telegram.py`
2. **Manual Add** - Add missing alerts manually to kpi_logs.json
3. **Check Railway Logs** - Look for errors in Railway deployment

## 📝 Notes

- The fix ensures ALL alerts are saved BEFORE filters
- Enhanced error handling prevents silent failures
- Debug logging tracks every save attempt
- Bot must be running 24/7 to catch all alerts

**Status**: 🔍 **INVESTIGATION COMPLETE - ENHANCED ERROR HANDLING ADDED**

