# 🤖 Token Alert Bot - Complete User Guide

## 📋 Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Bot Commands](#bot-commands)
4. [Monitored Sources](#monitored-sources)
5. [Alert System](#alert-system)
6. [Alert Classes](#alert-classes)
7. [Understanding Alerts](#understanding-alerts)
8. [Best Practices](#best-practices)
9. [FAQ](#faq)
10. [Support](#support)

---

## 🎯 Overview

**Token Alert Bot** is an advanced Solana memecoin monitoring system that tracks 12+ Telegram sources in real-time to detect high-probability trading opportunities. The bot uses **V1 + V2 Alert Spec** - a backtest-validated strategy with **66.7% win rate** and **2,187.5% average ROI**.

### What Makes This Bot Special?

✅ **Proven Strategy**: Based on 1-day backtest with 24 alerts, 16 winners (66.7% win rate)  
✅ **Pre-XTRACK Detection**: Catches opportunities before they hit XTRACK  
✅ **Multi-Source Confirmation**: Only alerts when multiple sources agree  
✅ **V2 Confirmation Layer**: Classifies alerts by strength (CORE, CORE+, STRONG, ELITE)  
✅ **Real-Time Monitoring**: 12+ Telegram sources monitored 24/7  
✅ **Selective Alerts**: Only ~32% of tokens trigger alerts (quality over quantity)

---

## 🚀 Getting Started

### Step 1: Find the Bot

Search for the bot on Telegram using the bot username provided by your community admin.

### Step 2: Start the Bot

Send `/start` to the bot. You'll receive a welcome message explaining the bot's capabilities.

### Step 3: Subscribe to Alerts

Send `/subscribe` to start receiving real-time trading alerts.

### Step 4: Wait for Alerts

The bot will automatically send you alerts when high-quality trading opportunities are detected.

---

## 📱 Bot Commands

### `/start`
**Description**: Welcome message and bot introduction  
**Usage**: `/start`  
**Response**: Shows bot capabilities, monitored sources, and available commands

### `/subscribe`
**Description**: Subscribe to receive real-time trading alerts  
**Usage**: `/subscribe`  
**Response**: Confirmation that you're now subscribed  
**Note**: You'll receive all alerts (CORE, CORE+, STRONG, ELITE)

### `/unsubscribe`
**Description**: Stop receiving alerts  
**Usage**: `/unsubscribe`  
**Response**: Confirmation that you've unsubscribed  
**Note**: You can resubscribe anytime with `/subscribe`

### `/status`
**Description**: Check your subscription status  
**Usage**: `/status`  
**Response**: Shows if you're subscribed and total subscriber count

### `/help`
**Description**: Show help message  
**Usage**: `/help`  
**Response**: Same as `/start` - shows bot information

---

## 📊 Monitored Sources

The bot monitors **12+ Telegram sources** across multiple categories:

### 🟢 Buy-Based Sources (Primary Signals)
These sources report actual buy transactions:

1. **SOL SB1** - Smart Buy signals
2. **SOL SB/MB** - Smart Buy / Medium Buy tracker
3. **WhaleBuy** - Large whale transactions
4. **Large_Buys_Tracker** - Tracks significant buy volume
5. **Momentum_Tracker** - Momentum-based buy signals

### 🔵 Social/Confirmation Sources (Secondary Signals)
These sources provide social confirmation:

6. **Glydo** - Token discovery and trending
7. **KOLscope** - Key Opinion Leader tracking
8. **SpyDefi** - DeFi intelligence
9. **Call_Analyzer** - Call analysis
10. **PFBF Volume Alert** - Volume-based alerts
11. **Solana_Early_Trending** - Early trending tokens

### 🟡 Outcome Tracking
12. **XTRACK SOL NEW** - Used for outcome validation (not a trigger)

---

## 🚨 Alert System

### How Alerts Work

The bot uses a **two-stage alert system**:

#### **V1 Alert Spec** (Core Triggers)
Alerts are triggered when **at least one** of these patterns fires:

**Pattern A: Volume Dominance**
- Total pre-XTRACK buy size ≥ **50 SOL**
- Win Rate: ~60-66% in backtest
- Indicates strong buying pressure

**Pattern B: Fast Multi-Source Confirmation**
- ≥ **2 distinct buy sources** appear
- First and second buy occur within **≤ 5 minutes**
- Win Rate: ~66% in backtest
- Indicates coordinated buying

#### **V2 Confirmation Layer** (Strength Classification)
After V1 triggers, V2 evaluates additional confirmations:

**Pattern C: Buy + Social Validation**
- Large_Buys_Tracker buy + Glydo mention within 60 min
- Indicates: "Demand detected + distribution awareness"

**Pattern D: Sustained Accumulation**
- Time between first and last buy ≥ 4 hours
- AND ≥ 2 buy events total
- Indicates: "Not a spike — sustained positioning"

**Pattern E: Capitalized Context**
- Market cap ≥ $130k AND ≤ $1M
- Indicates: "Serious participants tolerated higher valuation"

### Eligibility Requirements

A token must meet **ALL** of these to trigger an alert:

✅ Valid Solana contract address (32+ characters)  
✅ Symbol is not numeric-only (e.g., "12345")  
✅ Symbol is not "UNKNOWN" (parsing succeeded)  
✅ Liquidity ≥ $10,000 (if available)  
✅ Market cap ≤ $1,000,000 (soft gate - won't reject if missing)

### Exclusion Rules

Alerts are **suppressed** if:

❌ **Caller-only noise**: Only social sources (KOLscope/SpyDefi), no buy sources  
❌ **Proven negative combo**: SOL_SB1 + KOLscope without other buy confirmation

---

## 🎯 Alert Classes

Every alert is classified by **V2 confirmation score** (0-3):

### 🔒 CORE (Score: 0)
- V1 triggered, but no V2 confirmations
- Still high quality (71.4% win rate in backtest)
- **Example**: Volume ≥ 50 SOL, but no social confirmation yet

### 🔒+ CORE+ (Score: 1)
- V1 triggered + 1 V2 confirmation
- 60% win rate in backtest
- **Example**: Volume ≥ 50 SOL + Capitalized Context ($130k-$1M MC)

### 🔥 STRONG (Score: 2)
- V1 triggered + 2 V2 confirmations
- Higher confidence signal
- **Example**: Volume ≥ 50 SOL + Buy+Social + Sustained Accumulation

### 💎 ELITE (Score: 3)
- V1 triggered + ALL 3 V2 confirmations
- Highest confidence signal
- **Example**: All patterns confirmed - maximum strength

**Important**: All alert classes are valid alerts. The difference is **priority and confidence**, not validity.

---

## 📨 Understanding Alerts

### Alert Format

Every alert includes:

```
🔒/🔒+/🔥/💎 [ALERT_CLASS] ALERT — Pre-XTRACK Momentum

[TOKEN_SYMBOL]

✅ V1 Trigger(s):
• VOLUME: 72.4 SOL (>= 50 SOL)
• MULTI_SOURCE: 3 sources within 2.1 min

🎯 V2 Confirmations (Score: 2/3):
• ✅ Buy + Social Validation (Large_Buys + Glydo)
• ✅ Sustained Accumulation (4+ hours, 2+ events)
• ❌ Capitalized Context

📊 Metrics:
• Total Pre-X Buy Size: 72.4 SOL
• Buy Sources: large_buys_tracker, sol_sb1, whalebuy
• Time Between Buys: 2.1 min
• Time Spread: 245.3 min
• Liquidity: $18,200
• Market Cap: $210,000

📄 CA: [CONTRACT_ADDRESS]

🕒 Alert Time: 2025-12-18T12:41:00+00:00
```

### Key Information in Alerts

**V1 Triggers**: Shows which core pattern fired (VOLUME, MULTI_SOURCE, or both)

**V2 Confirmations**: Shows which confirmations are present (✅) or missing (❌)

**Confirmation Score**: 0-3 rating of alert strength

**Alert Class**: CORE, CORE+, STRONG, or ELITE

**Metrics**:
- **Total Pre-X Buy Size**: Sum of all buy volume before XTRACK
- **Buy Sources**: Which sources detected buys
- **Time Between Buys**: How fast multi-source confirmation occurred
- **Time Spread**: Duration of pre-XTRACK activity
- **Liquidity**: Token liquidity in USD
- **Market Cap**: Token market cap in USD

**Contract Address (CA)**: Solana contract address for trading

---

## 💡 Best Practices

### 1. **Understand Alert Classes**
- **CORE** alerts are still high quality (71.4% win rate)
- **STRONG/ELITE** alerts have additional confirmations but don't guarantee success
- All alerts are pre-XTRACK opportunities

### 2. **Do Your Own Research (DYOR)**
- Bot provides signals, not financial advice
- Always verify contract addresses
- Check token fundamentals
- Monitor liquidity and market conditions

### 3. **Risk Management**
- Never invest more than you can afford to lose
- Set stop-losses
- Take profits at reasonable levels
- Diversify your positions

### 4. **Timing Matters**
- Alerts are **pre-XTRACK** - you're getting early signals
- Act quickly but don't FOMO
- Monitor for XTRACK confirmation after entry

### 5. **Track Performance**
- Keep a log of alerts you acted on
- Track win/loss ratio
- Learn which alert classes work best for you

---

## ❓ FAQ

### Q: How often will I receive alerts?
**A**: Alerts are selective - only ~32% of tokens trigger alerts. Expect 0-5 alerts per day depending on market conditions.

### Q: Are all alerts winners?
**A**: No. Backtest shows 66.7% win rate (16 winners / 24 alerts). Always do your own research.

### Q: What's the difference between CORE and ELITE alerts?
**A**: ELITE has all 3 V2 confirmations, CORE has none. However, CORE alerts actually had higher win rate (71.4%) in backtest. Both are valid signals.

### Q: How do I know if an alert is still valid?
**A**: Alerts are sent when patterns first match. Check the timestamp - older alerts may have already moved.

### Q: Can I filter alerts by class?
**A**: Currently, you receive all alerts. Filter by alert class is a planned feature.

### Q: What if I miss an alert?
**A**: Alerts are sent in real-time. If you miss one, check the contract address and do your own research to see current status.

### Q: How accurate is the bot?
**A**: Based on 1-day backtest: 66.7% win rate, 2,187.5% average ROI. Past performance doesn't guarantee future results.

### Q: Can I use this for automated trading?
**A**: The bot provides alerts only. Any trading decisions and execution are your responsibility.

### Q: What happens if the bot goes offline?
**A**: Alerts are only sent when the bot is running. The bot should be online 24/7 for best results.

### Q: How do I report issues?
**A**: Contact your community admin or use the support channels provided.

---

## 🛠️ Support

### Getting Help

1. **Check this README** - Most questions are answered here
2. **Use `/help` command** - Quick reference in the bot
3. **Contact Admin** - For technical issues or questions
4. **Community Channels** - Join community discussions

### Common Issues

**Not receiving alerts?**
- Check if you're subscribed (`/status`)
- Verify bot is online
- Check if alerts are being triggered (admin can verify)

**Alert seems wrong?**
- Verify contract address manually
- Check if token still meets criteria
- Remember: alerts are pre-XTRACK, conditions may change

**Bot not responding?**
- Bot may be offline
- Check with admin
- Try `/start` to verify connection

---

## 📊 Performance Metrics

### Backtest Results (1-Day Sample)

- **Total Alerts**: 24
- **Winners (≥5x)**: 16
- **Win Rate**: 66.7%
- **Average ROI**: 2,187.5%
- **Best Trade**: 100x multiplier
- **Alert Rate**: 32% of tokens (selective)

### V2 Score Breakdown

- **Score 0 (CORE)**: 14 alerts, 71.4% win rate
- **Score 1 (CORE+)**: 10 alerts, 60.0% win rate
- **Score 2 (STRONG)**: 0 alerts in sample
- **Score 3 (ELITE)**: 0 alerts in sample

### Pattern Performance

- **Volume Only**: 11 alerts, ~60% win rate
- **Multi-Source Only**: 7 alerts, ~66% win rate
- **Both Patterns**: 6 alerts, 100% win rate (in sample)

---

## ⚠️ Disclaimer

**This bot is for informational purposes only. It is not financial advice.**

- Trading cryptocurrencies involves substantial risk
- Past performance does not guarantee future results
- Always do your own research (DYOR)
- Never invest more than you can afford to lose
- The bot's signals are based on historical patterns and may not always be accurate
- You are solely responsible for your trading decisions

---

## 📝 Version Information

- **Bot Version**: V1 + V2 Alert Spec
- **Strategy**: Pre-XTRACK Momentum Filter
- **Last Updated**: 2025-12-18
- **Backtest Period**: 1 day (11,644 events, 74 tokens)

---

## 🎉 Ready to Start?

1. Send `/start` to the bot
2. Send `/subscribe` to receive alerts
3. Wait for high-quality signals
4. Do your own research
5. Trade responsibly

**Good luck and trade safely! 🚀**

---

*For technical details, see `V2_IMPLEMENTATION_COMPLETE.md` and `V1_ALERT_SPEC.md`*


