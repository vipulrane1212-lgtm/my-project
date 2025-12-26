# Deployment Checklist & Live Monitoring KPIs

## Immediate (Before Deploy)

### ✅ Configuration Files

1. **automation_rules.json** - Final social-regime config with all improvements:
   - ✅ Social-regime scoring structure
   - ✅ CA/social requirement for HIGH
   - ✅ Churn penalty settings
   - ✅ Dynamic thresholding enabled
   - ✅ Low liquidity penalty

2. **channels.json** - Real chat IDs/webhooks:
   ```json
   {
     "channels": {
       "alerts_high": {
         "chat_id": "YOUR_HIGH_ALERTS_CHAT_ID",
         "name": "alerts_high",
         "notify_webhook": "YOUR_WEBHOOK_URL"
       },
       "alerts_medium": {
         "chat_id": "YOUR_MEDIUM_ALERTS_CHAT_ID",
         "name": "alerts_medium",
         "notify_webhook": null
       }
     }
   }
   ```

### ✅ Storage Setup

1. **Enable TTL storage (Redis)** for dedupe and symbol→CA cache:
   ```bash
   # Set Redis URL in environment or config
   export REDIS_URL="redis://localhost:6379/0"
   ```

2. **Symbol→CA cache TTL**: 72 hours (already configured in retention)

### ✅ Data Capture

1. **Ensure ingestion captures:**
   - ✅ `last_buy_sol` - Most recent buy size in SOL
   - ✅ `top_buy_sol` - Largest buy size in SOL
   - ✅ `callers` - Callers count from messages
   - ✅ `subs` - Subscribers count from messages
   - ✅ `contract` - Contract address
   - ✅ `liquidity_usd` - Liquidity in USD

2. **Verify message parser extracts:**
   - Buy sizes from whalebuy, large_buys_tracker feeds
   - Callers/subs from kolscope, spydefi feeds
   - Contract addresses from all sources

## Staging Deployment

### Phase 1: Staging Channels (24-48h test)

1. **Route HIGH → Staging Trading Channel (Private)**
   - Use private Telegram channel for HIGH alerts
   - Enable notifications for immediate review
   - Log all HIGH alerts with metadata

2. **Route MEDIUM → Logging/Watchlist Channel**
   - Use separate channel for MEDIUM alerts
   - **No push notifications** (reduce noise)
   - Log for analysis

3. **Run live on 24-48h test window**
   - Monitor alert quality
   - Track false positives
   - Verify scoring behavior

## KPIs to Track (First 48-72h)

### Daily Metrics

1. **Alert Volume:**
   - HIGH alerts per day (target: 5-15)
   - MEDIUM alerts per day (target: 20-50)
   - Total alerts per day

2. **Precision Metrics:**
   - **HIGH precision** (manually label first 20 HIGHs):
     - Target: >45-55% initially
     - Track: True Positives / (True Positives + False Positives)
   - **MEDIUM precision** (sample check):
     - Target: 30-40%

3. **Recall Metrics:**
   - **HIGH recall** relative to winners observed:
     - Track: True Positives / (True Positives + False Negatives)
     - Monitor drift over time
   - **MEDIUM recall**:
     - Target: ≥90%

### False Positive Analysis

**Log tags for each alert:**
- `no_ca` - Missing contract address
- `low_liq` - Liquidity < $5K
- `late_sb1` - SB1 appeared late (penalized)
- `late_glydo` - Glydo appeared late (penalized)
- `tiny_buy` - Buy size < 5 SOL
- `churn` - Repeated cohort without >4x peak
- `weak_social` - Callers < 20 or subs < 100k

**Track false positives by cause:**
```python
fp_causes = {
    "no_ca": 0,
    "low_liq": 0,
    "late_sb1": 0,
    "late_glydo": 0,
    "tiny_buy": 0,
    "churn": 0,
    "weak_social": 0
}
```

### Time-to-Peak Distribution

**For hits (true positives):**
- Track time from alert to peak multiplier
- Should match backtest median: ~minutes to hours
- Log distribution: <5min, 5-15min, 15-60min, 1-4h, >4h

## Monitoring & Adjustments

### If Precision < 40% After 48h:

**Option 1: Raise HIGH threshold**
```json
"thresholds": {
  "high": 72  // Increase by 2-5 points
}
```

**Option 2: Apply stricter CA gating**
```json
"thresholds": {
  "high_require_ca_or_social": true,
  "high_social_callers_min": 25,  // Increase from 20
  "high_social_subs_min": 150000  // Increase from 100k
}
```

**Option 3: Increase penalties**
```json
"scoring": {
  "sources": {
    "sol_sb1": -8,  // Increase penalty from -6
    "glydo": -12    // Increase penalty from -10
  }
}
```

### If HIGH Alerts Too Few:

**Option 1: Lower HIGH threshold**
```json
"thresholds": {
  "high": 68  // Decrease by 2-5 points
}
```

**Option 2: Relax penalties individually**
```json
"scoring": {
  "sources": {
    "sol_sb1": -4,  // Reduce penalty from -6
    "glydo": -8     // Reduce penalty from -10
  }
}
```

**Option 3: Reduce social requirements**
```json
"thresholds": {
  "high_social_callers_min": 15,  // Decrease from 20
  "high_social_subs_min": 80000   // Decrease from 100k
}
```

## Production Deployment

### Pre-Production Checklist

- [ ] Staging test completed (48h)
- [ ] HIGH precision ≥ 45%
- [ ] Alert volume within targets
- [ ] False positive causes identified and addressed
- [ ] Redis TTL storage verified
- [ ] Symbol→CA cache working (72h TTL)
- [ ] Buy size extraction verified
- [ ] CA/social requirement tested
- [ ] Churn penalty working
- [ ] Dynamic thresholding tested
- [ ] Low liquidity penalty working

### Production Setup

1. **Update channels.json** with production chat IDs
2. **Enable Redis** for production (if not already)
3. **Set up monitoring dashboard** (optional):
   - Alert rate over time
   - Precision/recall trends
   - False positive breakdown
4. **Set up alerting** for system health:
   - Alert rate spikes (>20 HIGH/day)
   - System errors
   - Redis connection issues

## Implementation Features Summary

### ✅ A. CA/Social Requirement for HIGH
- Requires contract OR (callers ≥20 AND subs ≥100k)
- Configurable via `high_require_ca_or_social`

### ✅ B. Buy-Size Boost Check
- Top buy ≥20 SOL → +8 points
- Last buy ≥5 SOL → +4 points
- Already tracking, now included in scoring

### ✅ C. Churn Penalty
- Checks for repeated cohorts in past 48h
- Applies -6 penalty if no >4x peak found
- Configurable via `churn_penalty`, `churn_window_hours`

### ✅ D. Low Liquidity Filter
- If liq_usd < $5K → -8 points
- Configurable via `low_liq_penalty`, `low_liq_threshold_usd`

### ✅ E. Early Cohort Bonus (Tuned)
- Window: 10-15 minutes (using 15 as max)
- Uses symbol→CA cache TTL for robust first-seen detection
- +15 points for early detection

### ✅ F. Dynamic Thresholding
- If alert rate >10 HIGH/day → increase threshold by +2
- Configurable via `dynamic_threshold_enabled`, `dynamic_threshold_alert_rate`

## Notes

- All features are backward compatible
- Configurable via automation_rules.json
- Can be enabled/disabled individually
- Ready for production testing
