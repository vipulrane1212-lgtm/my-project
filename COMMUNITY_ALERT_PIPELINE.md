# 🚀 Community Alert Pipeline - Complete Documentation

## Overview

This document describes the complete alert pipeline system for community members using the Token Alert Bot. It covers the entire flow from source monitoring to alert delivery.

---

## 📊 Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SOURCE MONITORING                         │
│  (12+ Telegram Channels/Forums)                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    MESSAGE PARSING                           │
│  • Extract token symbol                                      │
│  • Extract contract address                                  │
│  • Extract market cap, liquidity, buy size                  │
│  • Classify source type (buy/social)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    TOKEN STATE TRACKING                       │
│  • Aggregate events per token                                │
│  • Track buy sources                                         │
│  • Track social sources                                      │
│  • Calculate time spreads                                    │
│  • Maintain pre-XTRACK state                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    V1 ALERT SPEC EVALUATION                   │
│  • Eligibility filters (contract, symbol, liquidity)         │
│  • Exclusion rules (caller-only, negative combos)           │
│  • Pattern A: Volume Dominance (≥50 SOL)                     │
│  • Pattern B: Fast Multi-Source (2+ sources, ≤5 min)         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    V2 CONFIRMATION LAYER                     │
│  • Pattern C: Buy + Social Validation                        │
│  • Pattern D: Sustained Accumulation                         │
│  • Pattern E: Capitalized Context                           │
│  • Calculate confirmation score (0-3)                        │
│  • Assign alert class (CORE, CORE+, STRONG, ELITE)          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    ALERT FORMATTING                           │
│  • Format V1 triggers                                        │
│  • Format V2 confirmations                                   │
│  • Include all metrics                                       │
│  • Add contract address                                      │
│  • Add timestamp                                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    ALERT DISTRIBUTION                        │
│  • Check subscribed users                                    │
│  • Check alert chat ID                                       │
│  • Send to Telegram                                          │
│  • Log to file (auto_buy_signals.json)                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 Complete Alert Flow

### Step 1: Source Monitoring

The bot monitors **12+ Telegram sources** in real-time:

**Buy-Based Sources:**
- SOL SB1
- SOL SB/MB
- WhaleBuy
- Large_Buys_Tracker
- Momentum_Tracker

**Social/Confirmation Sources:**
- Glydo
- KOLscope
- SpyDefi
- Call_Analyzer
- PFBF Volume Alert
- Solana_Early_Trending

**Outcome Tracking:**
- XTRACK SOL NEW (for validation only)

### Step 2: Message Processing

For each incoming message:

1. **Parse Message**
   - Extract token symbol
   - Extract contract address (Solana format validation)
   - Extract market cap (handle K/M/B suffixes)
   - Extract liquidity
   - Extract buy size (SOL)
   - Extract unique wallets, callers (if available)

2. **Classify Source**
   - Determine if source is buy-based or social
   - Track source type for pattern matching

3. **Update Token State**
   - Create or update token record
   - Aggregate events chronologically
   - Track pre-XTRACK events only

### Step 3: Eligibility Filtering

Before evaluating patterns, tokens must pass **hard requirements**:

✅ **Contract & Symbol**
- Valid Solana contract address (32+ characters)
- Symbol not numeric-only
- Symbol not "UNKNOWN"

✅ **Liquidity**
- ≥ $10,000 (if available)
- Must come from buy-based source (if liquidity data present)

✅ **Market Cap**
- ≤ $1,000,000 (soft gate - won't reject if missing)

### Step 4: Exclusion Rules

Tokens are **automatically rejected** if:

❌ **Caller-Only Noise**
- Only social sources (KOLscope/SpyDefi)
- No buy sources present

❌ **Proven Negative Combo**
- SOL_SB1 + KOLscope
- Without other qualifying buy confirmation

### Step 5: V1 Pattern Evaluation

Alerts trigger when **at least one** V1 pattern fires:

**Pattern A: Volume Dominance**
```
IF total_preX_buy_SOL ≥ 50 SOL
THEN trigger VOLUME pattern
```

**Pattern B: Fast Multi-Source Confirmation**
```
IF distinct_buy_sources ≥ 2
AND time_between_first_second_buy ≤ 5 minutes
THEN trigger MULTI_SOURCE pattern
```

**Both patterns can fire simultaneously** (highest confidence)

### Step 6: V2 Confirmation Scoring

After V1 triggers, V2 evaluates confirmations:

**Pattern C: Buy + Social Validation**
```
IF large_buys_tracker IN buy_sources
AND glydo IN social_sources
AND time_between ≤ 60 minutes
THEN C_confirmed = TRUE
```

**Pattern D: Sustained Accumulation**
```
IF time_spread ≥ 240 minutes (4 hours)
AND buy_event_count ≥ 2
THEN D_confirmed = TRUE
```

**Pattern E: Capitalized Context**
```
IF market_cap ≥ $130,000
AND market_cap ≤ $1,000,000
THEN E_confirmed = TRUE
```

**Confirmation Score Calculation:**
```
score = 0
IF C_confirmed: score += 1
IF D_confirmed: score += 1
IF E_confirmed: score += 1
```

**Alert Class Assignment:**
```
IF score == 0: alert_class = "CORE"
IF score == 1: alert_class = "CORE+"
IF score == 2: alert_class = "STRONG"
IF score == 3: alert_class = "ELITE"
```

### Step 7: Alert Formatting

The alert is formatted with:

- **Header**: Alert class emoji and class name
- **Token Symbol**: The token being alerted
- **V1 Triggers**: Which patterns fired (VOLUME, MULTI_SOURCE)
- **V2 Confirmations**: Which confirmations are present (✅/❌)
- **Metrics**: Buy size, sources, time data, MC, LP
- **Contract Address**: Solana CA for trading
- **Timestamp**: When alert was generated

### Step 8: Alert Distribution

Alerts are sent to:

1. **Subscribed Users**
   - All users who sent `/subscribe`
   - Individual DM messages
   - Real-time delivery

2. **Alert Chat/Group** (if configured)
   - Central channel for all alerts
   - Set via `ALERT_CHAT_ID`

3. **Log File**
   - Saved to `auto_buy_signals.json`
   - Complete alert data for analysis
   - Persistent history

---

## 📱 User Interaction Flow

### Subscription Flow

```
User → /start
  ↓
Bot → Welcome message + instructions
  ↓
User → /subscribe
  ↓
Bot → Confirmation + subscription saved
  ↓
User → Receives alerts automatically
```

### Alert Receipt Flow

```
Alert Triggered
  ↓
Format Alert
  ↓
Check Subscriptions
  ↓
Send to Each Subscribed User
  ↓
Log to File
  ↓
User Receives Alert in Telegram
```

### Unsubscription Flow

```
User → /unsubscribe
  ↓
Bot → Remove from subscriptions
  ↓
Bot → Confirmation message
  ↓
User → No longer receives alerts
```

---

## 📊 Alert Data Structure

### Complete Alert Payload

```json
{
  "token": "TOKEN_SYMBOL",
  "contract": "SOLANA_CONTRACT_ADDRESS",
  "v1_trigger": ["VOLUME", "MULTI_SOURCE"],
  "total_preX_buy_SOL": 72.4,
  "buy_sources": ["sol_sb1", "large_buys_tracker"],
  "time_between_first_second_buy_minutes": 2.1,
  "liquidity_usd": 18200,
  "market_cap_usd": 210000,
  "v2_confirmations": {
    "C_buy_plus_social": true,
    "D_sustained_accumulation": false,
    "E_capitalized_context": true
  },
  "confirmation_score": 2,
  "alert_class": "STRONG",
  "timestamp": "2025-12-18T12:41:00+00:00",
  "time_spread_minutes": 245.3
}
```

### Formatted Alert (Telegram)

```
🔥 **STRONG ALERT — Pre-XTRACK Momentum**

**TOKEN_SYMBOL**

✅ **V1 Trigger(s):**
• VOLUME: 72.4 SOL (>= 50 SOL)
• MULTI_SOURCE: 3 sources within 2.1 min

🎯 **V2 Confirmations (Score: 2/3):**
• ✅ Buy + Social Validation (Large_Buys + Glydo)
• ❌ Sustained Accumulation
• ✅ Capitalized Context ($130k-$1M MC)

📊 **Metrics:**
• Total Pre-X Buy Size: 72.4 SOL
• Buy Sources: large_buys_tracker, sol_sb1, whalebuy
• Time Between Buys: 2.1 min
• Time Spread: 245.3 min
• Liquidity: $18,200
• Market Cap: $210,000

📄 **CA:** `CONTRACT_ADDRESS`

🕒 **Alert Time:** 2025-12-18T12:41:00+00:00
```

---

## 🎯 Alert Classes Explained

### 🔒 CORE (Score: 0)
- **Definition**: V1 triggered, no V2 confirmations
- **Win Rate**: 71.4% (in backtest)
- **When**: Volume or Multi-Source pattern fires, but no additional confirmations
- **Action**: Still high quality - evaluate based on V1 triggers

### 🔒+ CORE+ (Score: 1)
- **Definition**: V1 triggered + 1 V2 confirmation
- **Win Rate**: 60.0% (in backtest)
- **When**: One of C/D/E patterns confirmed
- **Action**: Additional confirmation present - slightly higher confidence

### 🔥 STRONG (Score: 2)
- **Definition**: V1 triggered + 2 V2 confirmations
- **Win Rate**: Not enough data in backtest
- **When**: Two of C/D/E patterns confirmed
- **Action**: Strong confirmation - higher priority

### 💎 ELITE (Score: 3)
- **Definition**: V1 triggered + ALL 3 V2 confirmations
- **Win Rate**: Not enough data in backtest
- **When**: All C/D/E patterns confirmed
- **Action**: Maximum confirmation - highest priority

---

## 📈 Performance Tracking

### Alert Statistics

The bot tracks:
- Total alerts sent
- Alert classes distribution
- V1 pattern breakdown
- V2 confirmation scores
- User subscription count

### Log Files

**`auto_buy_signals.json`**
- Complete alert history
- All alert data
- Timestamps
- For analysis and backtesting

**`subscriptions.json`**
- Subscribed user IDs
- Subscription timestamps
- For user management

**`token_state.json`**
- Current token states
- Event history
- For debugging and analysis

---

## 🔧 Technical Details

### Alert Frequency

- **Expected**: 0-5 alerts per day
- **Selectivity**: ~32% of tokens trigger alerts
- **Quality**: High - only proven patterns

### Alert Timing

- **Real-time**: Alerts sent immediately when patterns match
- **Pre-XTRACK**: All alerts are before XTRACK detection
- **First Alert Only**: One alert per token (first time pattern matches)

### Alert Reliability

- **Backtest Win Rate**: 66.7%
- **V1 Pattern A**: ~60-66% win rate
- **V1 Pattern B**: ~66% win rate
- **Both Patterns**: 100% win rate (in sample)

---

## 🛡️ Safety Features

### Eligibility Filters
- Prevents invalid tokens
- Ensures minimum liquidity
- Validates contract addresses

### Exclusion Rules
- Filters proven negative patterns
- Removes caller-only noise
- Prevents false positives

### Rate Limiting
- One alert per token
- Prevents spam
- Maintains quality

---

## 📚 Additional Resources

- **`BOT_README.md`**: Complete user guide
- **`V2_IMPLEMENTATION_COMPLETE.md`**: Technical implementation details
- **`V1_ALERT_SPEC.md`**: V1 Alert Spec documentation
- **`LIVE_MONITOR_READY.md`**: Deployment guide

---

## 🎓 Learning Resources

### Understanding Patterns

**Volume Dominance (Pattern A)**
- Large buy volume indicates strong interest
- 50 SOL threshold filters noise
- Higher volume = stronger signal

**Multi-Source Confirmation (Pattern B)**
- Multiple sources agreeing = coordinated buying
- 5-minute window = fast confirmation
- More sources = stronger signal

**V2 Confirmations**
- Additional context beyond V1
- Not required but add confidence
- Higher score = more confirmations

### Reading Alerts

1. **Check Alert Class**: CORE, CORE+, STRONG, ELITE
2. **Review V1 Triggers**: Which core pattern fired
3. **Check V2 Confirmations**: What additional context exists
4. **Verify Metrics**: Buy size, sources, MC, LP
5. **Validate Contract**: Always verify CA manually
6. **Check Timestamp**: How fresh is the alert

---

## ⚠️ Important Notes

1. **Alerts are signals, not advice** - Always DYOR
2. **Past performance ≠ future results** - Backtest is historical
3. **All alert classes are valid** - CORE has highest win rate
4. **Pre-XTRACK timing** - You're getting early signals
5. **One alert per token** - First pattern match only
6. **Real-time delivery** - Alerts sent immediately
7. **Selective by design** - Quality over quantity

---

## 🚀 Getting Started Checklist

- [ ] Read this documentation
- [ ] Read `BOT_README.md` user guide
- [ ] Find bot on Telegram
- [ ] Send `/start` to bot
- [ ] Send `/subscribe` to receive alerts
- [ ] Understand alert classes
- [ ] Learn to read alerts
- [ ] Set up risk management
- [ ] Start monitoring alerts
- [ ] Track your performance

---

*Last Updated: 2025-12-18*  
*Pipeline Version: V1 + V2*  
*Status: Production Ready*







