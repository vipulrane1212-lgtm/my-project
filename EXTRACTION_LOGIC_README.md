# Token Data Extraction Logic Documentation

## Overview
This document provides comprehensive documentation of all monitored Telegram sources, their IDs, and the extraction logic used to parse Contract Address (CA), Token Name, and Market Cap (MC) from messages.

---

## Monitored Sources

### Forum Topics

#### 1. SOL SB1
- **Group ID**: `-1002134751475`
- **Group Title**: `Blackhat SOL Alerts`
- **Thread ID**: `3285418`
- **Source Code**: `sol_sb1`
- **Type**: Forum Topic

#### 2. SOL SB/MB
- **Group ID**: `-1002134751475`
- **Group Title**: `Blackhat SOL Alerts`
- **Thread ID**: `3285420`
- **Source Code**: `sol_sb_mb`
- **Type**: Forum Topic

#### 3. WhaleBuy
- **Group ID**: `-1002134751475`
- **Group Title**: `Blackhat SOL Alerts`
- **Thread ID**: `3285422`
- **Source Code**: `whalebuy`
- **Type**: Forum Topic

#### 4. XTRACK SOL NEW
- **Group ID**: `-1002134751475`
- **Group Title**: `Blackhat SOL Alerts`
- **Thread ID**: `3502440`
- **Source Code**: `xtrack`
- **Type**: Forum Topic

#### 5. Momentum Tracker
- **Group ID**: `-1002195249735`
- **Group Title**: `Orion Tracker`
- **Thread ID**: `8037`
- **Source Code**: `momentum_tracker`
- **Type**: Forum Topic

#### 6. Large Buys Tracker
- **Group ID**: `-1002195249735`
- **Group Title**: `Orion Tracker`
- **Thread ID**: `8047`
- **Source Code**: `large_buys_tracker`
- **Type**: Forum Topic

### Channels

#### 7. Glydo Alerts
- **Channel ID**: `-1002782074434`
- **Channel Name**: `Glydo Alerts`
- **Source Code**: `glydo`
- **Type**: Channel

#### 8. pfbf volume alert
- **Channel ID**: `-1002225558516`
- **Channel Name**: `pfbf volume alert`
- **Source Code**: `pfbf_volume_alert`
- **Type**: Channel

#### 9. call analyzer
- **Channel ID**: `-1002050218130`
- **Channel Name**: `call analyzer`
- **Source Code**: `call_analyzer`
- **Type**: Channel

#### 10. kolscope
- **Channel ID**: `-1002397610468`
- **Channel Name**: `kolscope`
- **Source Code**: `kolscope`
- **Type**: Channel

#### 11. spydefi
- **Channel ID**: `-1001960616143`
- **Channel Name**: `spydefi`
- **Source Code**: `spydefi`
- **Type**: Channel

#### 12. Solana Early Trending
- **Channel ID**: `-1002093384030`
- **Channel Name**: `Solana Early Trending`
- **Source Code**: `solana_early_trending`
- **Type**: Channel

---

## Extraction Logic by Source

### Contract Address (CA) Extraction

The system uses a unified extraction method that checks multiple patterns in priority order:

#### Priority 1: Source-Specific Patterns

1. **Solana Early Trending**
   - Pattern: `soul_sniper_bot?start=15_([A-Za-z0-9]{32,44})`
   - Example URL: `https://t.me/soul_sniper_bot?start=15_AJ37PzYsw6Bn7XscietdaGQbrm3oCNYuphL4iK34pump`
   - Extracted CA: `AJ37PzYsw6Bn7XscietdaGQbrm3oCNYuphL4iK34pump`
   - Regex: `r'soul_sniper_bot\?start=15_([A-Za-z0-9]{32,44})'`

2. **SpyDefi (Solana)**
   - Pattern: `spydefi_bot?start=([A-Za-z0-9]{32,44})`
   - Example URL: `https://t.me/spydefi_bot?start=ABC123...XYZ`
   - Regex: `r'(?:spydefi_bot|SpyDefi_bot)\?start=([A-Za-z0-9]{32,44})'`
   - **Note**: Ethereum addresses (0x...) are explicitly rejected

3. **KOLscope**
   - Pattern: `KOLscopeBot?start=([A-Za-z0-9]{32,44})`
   - Regex: `r'KOLscopeBot\?start=([A-Za-z0-9]{32,44})'`

#### Priority 2: URL Entity Patterns

4. **GMGN.ai Links**
   - Pattern 1: `gmgn.ai/sol/token/rLkfkJiz_CONTRACT`
   - Pattern 2: `gmgn.ai/sol/token/CONTRACT` (direct)
   - Pattern 3: `gmgn.ai/sol/token/PREFIX_CONTRACT` (any prefix)
   - Regex Patterns:
     - `r'gmgn\.ai/sol/token/[^\s\)]*rLkfkJiz_([A-Za-z0-9]{32,44})'`
     - `r'gmgn\.ai/sol/token/([A-Za-z0-9]{32,44})'`
     - `r'gmgn\.ai/sol/token/[A-Za-z0-9]+_([A-Za-z0-9]{32,44})'`

5. **Pump.fun Links**
   - Pattern: `pump.fun/CONTRACT`
   - Regex: `r'pump\.fun/([A-Za-z0-9]{32,44})'`

#### Priority 3: Text Patterns

6. **Common Text Patterns**
   - `📄 CONTRACT_ADDRESS`
   - `CA: CONTRACT_ADDRESS`
   - `Mint: CONTRACT_ADDRESS`
   - `Contract: CONTRACT_ADDRESS`
   - Regex: `r'📄\s*([A-Za-z0-9]{32,44})'`, `r'CA:\s*([A-Za-z0-9]{32,44})'`, etc.

7. **Generic Address Pattern** (fallback)
   - Regex: `r'\b([A-Za-z0-9]{32,44})\b'`

#### Validation Rules
- Length: 32-44 characters
- Format: Alphanumeric only (A-Z, a-z, 0-9)
- Reject: Ethereum addresses (starting with `0x`)
- Case: Converted to uppercase

---

### Token Name/Symbol Extraction

Extraction methods are tried in priority order:

#### Method 0: Solana Early Trending (Highest Priority)
- **Pattern**: `🔥 TOKEN_NAME New Trending`
- **Example**: `🔥 ‎The Goon New Trending` → `THE GOON`
- **Regex**: `r'🔥\s*‎?([^\n]+?)\s+New\s+Trending'`
- **Source**: `solana_early_trending`

#### Method 1: Large Buys Tracker
- **Pattern**: `💰 TOKEN ($X.XK)`
- **Example**: `💰 E91 ($49.2K) - 10.65 SOL BUY` → `E91`
- **Regex**: `r'💰\s*([A-Za-z0-9\-]+)\s*\('`
- **Source**: `large_buys_tracker`

#### Method 2: Momentum Tracker
- **Pattern**: `⚡ TOKEN ($X.XK)`
- **Example**: `⚡ likely ($13.4K) - ⏫ 41.06% in 1.5s` → `LIKELY`
- **Regex**: `r'⚡\s*([A-Za-z0-9\-]+)\s*\('`
- **Source**: `momentum_tracker`

#### Method 3: Swapped Format (Priority - token being bought)
- **Pattern**: `Swapped X ANY_TOKEN for Y #TOKEN`
- **Example**: `Swapped 1 #SOL ($128.37) for 14,312,725.39 #SLIDING On #Jupiter` → `SLIDING`
- **Regex**: `r'Swapped\s+[\d,.]+(?:\s*\([^)]+\))?\s+#?[A-Za-z0-9]+\s+[^#]*for\s+[\d,.]+\s+#([A-Za-z0-9™©®]+)'`
- **Sources**: `sol_sb1`, `sol_sb_mb`, `momentum_tracker`
- **Note**: Extracts token AFTER "for" (the token being bought)

#### Method 4: XTRACK Format
- **Pattern**: `TOKEN did 👉 Xx`
- **Example**: `SLIDING did 👉 4x` → `SLIDING`
- **Regex**: `r'([A-Za-z0-9]+)\s+did\s+👉'`
- **Source**: `xtrack`

#### Method 5: CALLERS Format
- **Pattern**: `⚪ TOKEN (#TOKEN)`
- **Example**: `⚪ SLIDING (#SLIDING)` → `SLIDING` (prefers symbol in parentheses)
- **Regex**: `r'⚪\s*([^(]+?)\s*\(#([^)]+)\)'`
- **Source**: `call_analyzer`

#### Method 6: CALL ALERT Format
- **Pattern**: `CALL ALERT: TOKEN`
- **Example**: `CALL ALERT: SLIDING` → `SLIDING`
- **Regex**: `r'CALL ALERT:\s*([A-Za-z0-9\-]+)'`
- **Source**: `call_analyzer`, `kolscope`

#### Method 7: SpyDefi Format
- **Pattern**: `call on TOKEN`
- **Example**: `call on SLIDING` → `SLIDING`
- **Regex**: `r'call on\s+([A-Za-z0-9\-]+)'`
- **Source**: `spydefi`

#### Method 8: Hash Tag Format (#TOKEN)
- **Pattern**: `#TOKEN` at start of message
- **Example**: `#SLIDING` → `SLIDING`
- **Regex**: `r'^#([A-Za-z0-9]+(?:\.\.\.[A-Za-z0-9]+)?)'`
- **Note**: Skips if message contains "Swapped" (first #TOKEN is trader ID)

#### Method 9: Dollar Format ($TOKEN)
- **Pattern**: `$TOKEN`
- **Example**: `$SLIDING` → `SLIDING`
- **Regex**: `r'\$([A-Za-z0-9]+)'`
- **Note**: Rejects pure numbers (e.g., "$24" from "$24.4K")

#### Special Case: Glydo
- **Pattern**: `1. $SYMBOL` or `1. #SYMBOL` or `$SYMBOL`
- **Example**: `1. $PP` → `PP`
- **Regex**: `r'\d+\.\s*\$?([A-Za-z0-9]+)'`, `r'\d+\.\s*#([A-Za-z0-9]+)'`, `r'\$\s*([A-Za-z0-9]+)'`
- **Source**: `glydo`
- **Note**: Glydo messages contain SYMBOL ONLY (no contract address). Uses placeholder `GLYDO_SYMBOL` for matching.

---

### Market Cap (MC) Extraction

#### Pattern 1: Solana Early Trending (Highest Priority)
- **Pattern**: `💰 MC: $NUMBER`
- **Example**: `💰 MC: $54,726` → `54726.0`
- **Regex**: `r'💰\s*MC:\s*\$?([\d,]+)'`
- **Source**: `solana_early_trending`
- **Format**: Direct number (no K/M suffix)

#### Pattern 2: XTRACK Format
- **Pattern**: `MC: $X.XK 👉` or `MC: $X.XM 👉`
- **Example**: `MC: $53.8k 👉` → `53800.0`
- **Regex**: `r'MC[:\s]+\$?([\d,\.]+[KMkm]?)\s*👉'`
- **Source**: `xtrack`
- **Format**: Supports K (thousands) and M (millions) suffixes

#### Pattern 3: General MCap Format
- **Pattern**: `MCap: $X.XK` or `Market Cap: $X.XK`
- **Example**: `MCap: $1.5M` → `1500000.0`
- **Regex**: `r'MCap[:\s]+\$?([\d,\.]+[KMkm]?)'`, `r'Market\s+Cap[:\s]+\$?([\d,\.]+[KMkm]?)'`

#### Pattern 4: Parentheses Format
- **Pattern**: `($X.XK)` or `($X.XM)`
- **Example**: `💰 E91 ($49.2K) - 10.65 SOL BUY` → `49200.0`
- **Regex**: `r'\(\$([\d,\.]+[KMkm]?)\)'`
- **Source**: `large_buys_tracker`, `momentum_tracker`

#### Pattern 5: Current MCap Format
- **Pattern**: `Current MCap: $X.XK`
- **Regex**: `r'Current MCap:\s*\$?([\d,\.]+[KMkm]?)'`

#### Conversion Rules
- **K suffix**: Multiply by 1,000 (e.g., `$24.4K` → `24400.0`)
- **M suffix**: Multiply by 1,000,000 (e.g., `$1.5M` → `1500000.0`)
- **B suffix**: Multiply by 1,000,000,000 (e.g., `$2.3B` → `2300000000.0`)
- **No suffix**: Use number as-is (e.g., `$54,726` → `54726.0`)
- **Commas**: Removed before conversion

---

## Source-Specific Details

### 1. SOL SB1 / SOL SB/MB (`sol_sb1`, `sol_sb_mb`)
- **Message Format**: "Swapped X #SOL for Y #TOKEN"
- **CA Extraction**: From GMGN links or text patterns
- **Token Extraction**: Method 3 (Swapped format - token after "for")
- **MC Extraction**: From parentheses format or general patterns

### 2. WhaleBuy (`whalebuy`)
- **Message Format**: Similar to SOL SB1/SB/MB
- **CA Extraction**: From GMGN links or text patterns
- **Token Extraction**: Method 3 (Swapped format)
- **MC Extraction**: From parentheses format

### 3. XTRACK SOL NEW (`xtrack`)
- **Message Format**: "TOKEN did 👉 Xx" with MC and multiplier
- **CA Extraction**: From GMGN links (often `rLkfkJiz_CONTRACT` format)
- **Token Extraction**: Method 4 (`TOKEN did 👉`)
- **MC Extraction**: Pattern 2 (`MC: $X.XK 👉`)
- **Special**: Also extracts multiplier (e.g., `4x` → `4.0`)

### 4. Momentum Tracker (`momentum_tracker`)
- **Message Format**: `⚡ TOKEN ($X.XK) - ⏫ PERCENTAGE`
- **CA Extraction**: From GMGN links or text patterns
- **Token Extraction**: Method 2 (`⚡ TOKEN`)
- **MC Extraction**: Pattern 4 (parentheses format)

### 5. Large Buys Tracker (`large_buys_tracker`)
- **Message Format**: `💰 TOKEN ($X.XK) - Y SOL BUY`
- **CA Extraction**: From GMGN links or text patterns
- **Token Extraction**: Method 1 (`💰 TOKEN`)
- **MC Extraction**: Pattern 4 (parentheses format)
- **Special**: Also extracts buy size in SOL

### 6. Glydo Alerts (`glydo`)
- **Message Format**: List format `1. $SYMBOL`, `2. $SYMBOL`, etc.
- **CA Extraction**: **NONE** (symbol-only source)
- **Token Extraction**: Special Glydo parser (extracts multiple symbols)
- **MC Extraction**: **NONE**
- **Special**: Uses placeholder CA `GLYDO_SYMBOL` for matching with other sources

### 7. pfbf volume alert (`pfbf_volume_alert`)
- **Message Format**: Various formats
- **CA Extraction**: Standard patterns (GMGN, text, etc.)
- **Token Extraction**: Fallback methods (#TOKEN, $TOKEN, etc.)
- **MC Extraction**: General patterns

### 8. call analyzer (`call_analyzer`)
- **Message Format**: `CALL ALERT: TOKEN` or `⚪ TOKEN (#TOKEN)`
- **CA Extraction**: Standard patterns
- **Token Extraction**: Method 5 (CALLERS) or Method 6 (CALL ALERT)
- **MC Extraction**: General patterns

### 9. kolscope (`kolscope`)
- **Message Format**: `CALL ALERT: TOKEN` or `DIP MODE: TOKEN`
- **CA Extraction**: From `KOLscopeBot?start=CONTRACT` URLs
- **Token Extraction**: Method 6 (CALL ALERT) or fallback
- **MC Extraction**: General patterns

### 10. spydefi (`spydefi`)
- **Message Format**: `call on TOKEN` with bot links
- **CA Extraction**: From `spydefi_bot?start=CONTRACT` URLs (Solana only, rejects Ethereum)
- **Token Extraction**: Method 7 (`call on TOKEN`)
- **MC Extraction**: General patterns
- **Special**: Explicitly rejects Ethereum addresses (0x...)

### 11. Solana Early Trending (`solana_early_trending`)
- **Message Format**: `🔥 TOKEN_NAME New Trending` with detailed stats
- **CA Extraction**: Priority 1 (`soul_sniper_bot?start=15_CONTRACT`)
- **Token Extraction**: Method 0 (highest priority, `🔥 TOKEN_NAME New Trending`)
- **MC Extraction**: Pattern 1 (highest priority, `💰 MC: $NUMBER`)
- **Example Message**:
  ```
  🔥 ‎The Goon New Trending
  💰 MC: $54,726 • 🔝 $60.7K
  💧 Liq: $21.8K
  ```
  - Token: `THE GOON`
  - CA: From `https://t.me/soul_sniper_bot?start=15_AJ37PzYsw6Bn7XscietdaGQbrm3oCNYuphL4iK34pump`
  - MC: `54726.0`

---

## Additional Metrics Extracted

### Buy Size (SOL)
- **Patterns**:
  - `Y SOL BUY` → `Y`
  - `Swapped X #SOL` → `X`
  - `💰 TOKEN ($X.XK) - Y SOL BUY` → `Y`
- **Regex**: `r'(\d+\.?\d*)\s*SOL\s*BUY'`, `r'Swapped\s+(\d+\.?\d*)\s*#?SOL'`

### Liquidity
- **Patterns**:
  - `LIQ: $X.XK`
  - `Liquidity: $X.XK`
  - `💧 LIQ: $X.XK`
- **Regex**: `r'LIQ[:\s]+\$?([\d,\.]+[KMkm]?)'`, `r'💧\s*LIQ[:\s]+\$?([\d,\.]+[KMkm]?)'`

### XTRACK Multiplier
- **Pattern**: `did 👉 Xx` or `Xx+`
- **Example**: `did 👉 4x` → `4.0`
- **Regex**: `r'did\s+👉\s*(\d+x)'`, `r'(\d+x\+?)'`
- **Source**: `xtrack` only

---

## Validation Rules

### Solana Address Validation
```python
def is_valid_solana_address(address: str) -> bool:
    - Length: 32-44 characters
    - Format: Alphanumeric only (A-Z, a-z, 0-9)
    - Reject: Ethereum addresses (starting with 0x)
    - Case: Converted to uppercase
```

### Token Name Validation
- Minimum length: 1-2 characters (varies by method)
- Maximum length: 20-50 characters (varies by method)
- Format: Alphanumeric, hyphens allowed
- Special characters: Removed (™, ©, ®)

---

## Extraction Priority Summary

### Contract Address Priority:
1. Source-specific bot URLs (Solana Early Trending, SpyDefi, KOLscope)
2. GMGN.ai URLs (multiple patterns)
3. Pump.fun URLs
4. Text patterns (📄, CA:, Mint:, Contract:)
5. Generic address pattern (fallback)

### Token Name Priority:
1. Solana Early Trending format
2. Large Buys Tracker format
3. Momentum Tracker format
4. Swapped format (token after "for")
5. XTRACK format
6. CALLERS format
7. CALL ALERT format
8. SpyDefi format
9. Hash tag format (#TOKEN)
10. Dollar format ($TOKEN)

### Market Cap Priority:
1. Solana Early Trending format (`💰 MC: $NUMBER`)
2. XTRACK format (`MC: $X.XK 👉`)
3. General MCap formats
4. Parentheses format (`($X.XK)`)
5. Current MCap format

---

## Example Messages by Source

### Solana Early Trending
```
🔥 ‎The Goon New Trending
🕒 Age: 4m | Security: ✅
💰 MC: $54,726 • 🔝 $60.7K
💧 Liq: $21.8K
[Link: https://t.me/soul_sniper_bot?start=15_AJ37PzYsw6Bn7XscietdaGQbrm3oCNYuphL4iK34pump]
```
**Extracted**:
- Token: `THE GOON`
- CA: `AJ37PzYsw6Bn7XscietdaGQbrm3oCNYuphL4iK34pump`
- MC: `54726.0`

### XTRACK
```
SLIDING did 👉 4x
💰 MC: $53.8k 👉 $180k
[Link: https://gmgn.ai/sol/token/rLkfkJiz_ABC123...XYZ]
```
**Extracted**:
- Token: `SLIDING`
- CA: `ABC123...XYZ` (from GMGN link)
- MC: `53800.0`
- Multiplier: `4.0`

### Large Buys Tracker
```
💰 E91 ($49.2K) - 10.65 SOL BUY
[Link: https://gmgn.ai/sol/token/E91_CONTRACT_ADDRESS]
```
**Extracted**:
- Token: `E91`
- CA: `CONTRACT_ADDRESS` (from GMGN link)
- MC: `49200.0`
- Buy Size: `10.65` SOL

### Momentum Tracker
```
⚡ likely ($13.4K) - ⏫ 41.06% in 1.5s
[Link: https://gmgn.ai/sol/token/LIKELY_CONTRACT]
```
**Extracted**:
- Token: `LIKELY`
- CA: `CONTRACT` (from GMGN link)
- MC: `13400.0`

### SOL SB1/SB/MB
```
Swapped 1 #SOL ($128.37) for 14,312,725.39 #SLIDING On #Jupiter
[Link: https://gmgn.ai/sol/token/SLIDING_CONTRACT]
```
**Extracted**:
- Token: `SLIDING` (after "for")
- CA: `CONTRACT` (from GMGN link)
- MC: May not be present

### Glydo
```
1. $PP
2. $PROBABLE
3. #SLIDING
```
**Extracted**:
- Tokens: `PP`, `PROBABLE`, `SLIDING` (multiple symbols)
- CA: `GLYDO_PP` (placeholder, matched later with other sources)
- MC: None

---

## Notes for Cross-Analysis

1. **Glydo is symbol-only**: Requires matching with other sources to get contract address
2. **Priority matters**: Higher priority patterns are tried first
3. **Fallback logic**: If primary extraction fails, system tries lower priority methods
4. **Validation is strict**: Invalid Solana addresses are rejected
5. **Ethereum addresses**: Explicitly rejected (SpyDefi may contain both)
6. **Multiple symbols**: Some sources (Glydo) can extract multiple tokens per message
7. **URL entities**: Telegram message entities are checked first for URLs, then text is parsed

---

## Technical Implementation

- **Language**: Python 3
- **Regex Library**: `re` (standard library)
- **Validation**: Custom `is_valid_solana_address()` function
- **Case Handling**: All addresses converted to uppercase
- **Error Handling**: Returns `None` if extraction fails at any step
- **Multi-source**: Same extraction logic used across all sources with source-specific priorities

---

*Last Updated: 2025-12-18*
*Version: 1.0*







