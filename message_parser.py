#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
message_parser.py

Parses messages to extract token data:
- Symbol/token name
- Contract address
- Buy size (SOL)
- Market cap
- Liquidity
- XTRACK multiplier
"""

import re
from datetime import datetime, timezone
from typing import Dict, Optional, List
from dataclasses import dataclass

@dataclass
class ParsedMessage:
    """Parsed message data"""
    symbol: str
    contract_address: str
    source: str
    timestamp: datetime
    buy_size_sol: Optional[float] = None
    market_cap: Optional[float] = None
    liquidity: Optional[float] = None
    xtrack_multiplier: Optional[float] = None

class MessageParser:
    """Parses messages to extract token data"""
    
    @staticmethod
    def is_valid_solana_address(address: str) -> bool:
        """Validate Solana address"""
        if not address:
            return False
        if address.upper().startswith('0X'):
            return False  # Ethereum
        if len(address) < 32 or len(address) > 44:
            return False
        if not re.match(r'^[A-Za-z0-9]+$', address):
            return False
        return True
    
    @staticmethod
    def extract_contract_address(text: str, entities: List[Dict] = None) -> Optional[str]:
        """Extract contract address from text and entities"""
        if not text:
            return None

        # Detect Ethereum CA in SpyDefi-style links (we DO NOT treat as Solana CA)
        # Example: https://t.me/spydefi_bot?start=0x10cdbc0a4b0b180ed3be461750adba0bddd54444
        eth_match = re.search(r'spydefi_bot\?start=(0x[a-fA-F0-9]{40})', text, re.IGNORECASE)
        if eth_match:
            return None

        # Solana Early Trending: Soul_Sniper_Bot?start=track_CONTRACT (NEW FORMAT)
        soul_sniper_track = re.search(r'Soul_Sniper_Bot\?start=track_([A-Za-z0-9]{32,44})', text, re.IGNORECASE)
        if soul_sniper_track:
            addr = soul_sniper_track.group(1)
            if MessageParser.is_valid_solana_address(addr):
                return addr.upper()
        
        # Solana Early Trending: soul_sniper_bot?start=15_CONTRACT_ADDRESS (OLD FORMAT)
        solana_early_trending = re.search(r'soul_sniper_bot\?start=15_([A-Za-z0-9]{32,44})', text, re.IGNORECASE)
        if solana_early_trending:
            addr = solana_early_trending.group(1)
            if MessageParser.is_valid_solana_address(addr):
                return addr.upper()
        
        # Solana Early Trending: soul_scanner_bot?start=CONTRACT (alternative bot)
        solana_scanner = re.search(r'soul_scanner_bot\?start=([A-Za-z0-9]{32,44})', text, re.IGNORECASE)
        if solana_scanner:
            addr = solana_scanner.group(1)
            if MessageParser.is_valid_solana_address(addr):
                return addr.upper()

        # SpyDefi Solana CA present in start param (allow mixed case bot name)
        spy_solana = re.search(r'(?:spydefi_bot|SpyDefi_bot)\?start=([A-Za-z0-9]{32,44})', text, re.IGNORECASE)
        if spy_solana:
            addr = spy_solana.group(1)
            if MessageParser.is_valid_solana_address(addr):
                return addr.upper()
        
        # KOLscope: KOLscopeBot?start=CONTRACT (case variations)
        kolscope_match = re.search(r'KOLscopeBot\?start=([A-Za-z0-9]{32,44})', text, re.IGNORECASE)
        if kolscope_match:
            addr = kolscope_match.group(1)
            if MessageParser.is_valid_solana_address(addr):
                return addr.upper()
        
        # Method 1: Extract from URL entities (PRIORITY - check all entities)
        if entities:
            for entity in entities:
                if entity.get('type') == 'MessageEntityTextUrl' and 'url' in entity:
                    url = entity['url']
                    
                    # Solana Early Trending: Soul_Sniper_Bot?start=track_CONTRACT (NEW FORMAT - PRIORITY)
                    soul_sniper_track_match = re.search(r'Soul_Sniper_Bot\?start=track_([A-Za-z0-9]{32,44})', url, re.IGNORECASE)
                    if soul_sniper_track_match:
                        addr = soul_sniper_track_match.group(1)
                        if MessageParser.is_valid_solana_address(addr):
                            return addr.upper()
                    
                    # Solana Early Trending: soul_sniper_bot?start=15_CONTRACT_ADDRESS (OLD FORMAT)
                    solana_early_match = re.search(r'soul_sniper_bot\?start=15_([A-Za-z0-9]{32,44})', url, re.IGNORECASE)
                    if solana_early_match:
                        addr = solana_early_match.group(1)
                        if MessageParser.is_valid_solana_address(addr):
                            return addr.upper()
                    
                    # Solana Early Trending: soul_scanner_bot?start=CONTRACT (alternative bot)
                    solana_scanner_match = re.search(r'soul_scanner_bot\?start=([A-Za-z0-9]{32,44})', url, re.IGNORECASE)
                    if solana_scanner_match:
                        addr = solana_scanner_match.group(1)
                        if MessageParser.is_valid_solana_address(addr):
                            return addr.upper()
                    
                    # KOLscope: KOLscopeBot?start=CONTRACT (case variations)
                    kolscope_match = re.search(r'KOLscopeBot\?start=([A-Za-z0-9]{32,44})', url, re.IGNORECASE)
                    if kolscope_match:
                        addr = kolscope_match.group(1)
                        if MessageParser.is_valid_solana_address(addr):
                            return addr.upper()
                    
                    # SpyDefi: spydefi_bot?start=CONTRACT (case variations, reject Ethereum)
                    spydefi_match = re.search(r'(?:spydefi_bot|SpyDefi_bot)\?start=([A-Za-z0-9]{32,44})', url, re.IGNORECASE)
                    if spydefi_match:
                        addr = spydefi_match.group(1)
                        # Reject Ethereum addresses
                        if not addr.startswith('0x') and MessageParser.is_valid_solana_address(addr):
                            return addr.upper()
                    
                    # GMGN pattern (matches old script) - PRIORITY: token links over address links
                    # Token links contain the contract address we want
                    if 'gmgn.ai/sol/token/' in url:
                        # Pattern 1: gmgn.ai/sol/token/rLkfkJiz_CONTRACT?maker=... (WhaleBuy format with query params)
                        # Extract CA before ?maker= or other query parameters - stop at ? or ) or end
                        pattern1 = r'rLkfkJiz_([A-Za-z0-9]{32,44})(?=\?|\)|$)'
                        match = re.search(pattern1, url)
                        if match:
                            addr = match.group(1)
                            if MessageParser.is_valid_solana_address(addr):
                                return addr.upper()
                        # Pattern 2: gmgn.ai/sol/token/rLkfkJiz_CONTRACT (SingleBuys/XTrack format, no query)
                        pattern2 = r'gmgn\.ai/sol/token/[^\s\)]*rLkfkJiz_([A-Za-z0-9]{32,44})(?=\?|\)|$)'
                        match = re.search(pattern2, url)
                        if match:
                            addr = match.group(1)
                            if MessageParser.is_valid_solana_address(addr):
                                return addr.upper()
                        # Pattern 3: gmgn.ai/sol/token/CONTRACT (direct format)
                        pattern3 = r'gmgn\.ai/sol/token/([A-Za-z0-9]{32,44})(?=\?|\)|$)'
                        match = re.search(pattern3, url)
                        if match:
                            addr = match.group(1)
                            if MessageParser.is_valid_solana_address(addr):
                                return addr.upper()
                        # Pattern 4: Any prefix before contract
                        pattern4 = r'gmgn\.ai/sol/token/[A-Za-z0-9]+_([A-Za-z0-9]{32,44})(?=\?|\)|$)'
                        match = re.search(pattern4, url)
                        if match:
                            addr = match.group(1)
                            if MessageParser.is_valid_solana_address(addr):
                                return addr.upper()
                    
                    # Pump.fun pattern
                    if 'pump.fun/' in url:
                        pattern = r'pump\.fun/([A-Za-z0-9]{32,44})'
                        match = re.search(pattern, url)
                        if match:
                            addr = match.group(1)
                            if MessageParser.is_valid_solana_address(addr):
                                return addr.upper()

        # Method 2: Extract from URLs in text (matches old script) - CHECK BEFORE generic patterns
        # This ensures token links are prioritized over generic address matching
        url_pattern = r'https?://[^\s\)]+'
        urls = re.findall(url_pattern, text)
        for url in urls:
            # Solana Early Trending: Soul_Sniper_Bot?start=track_CONTRACT (NEW FORMAT - PRIORITY)
            soul_sniper_track_match = re.search(r'Soul_Sniper_Bot\?start=track_([A-Za-z0-9]{32,44})', url, re.IGNORECASE)
            if soul_sniper_track_match:
                addr = soul_sniper_track_match.group(1)
                if MessageParser.is_valid_solana_address(addr):
                    return addr.upper()
            
            # Solana Early Trending: soul_sniper_bot?start=15_CONTRACT_ADDRESS (OLD FORMAT)
            solana_early_match = re.search(r'soul_sniper_bot\?start=15_([A-Za-z0-9]{32,44})', url, re.IGNORECASE)
            if solana_early_match:
                addr = solana_early_match.group(1)
                if MessageParser.is_valid_solana_address(addr):
                    return addr.upper()
            
            # Solana Early Trending: soul_scanner_bot?start=CONTRACT (alternative bot)
            solana_scanner_match = re.search(r'soul_scanner_bot\?start=([A-Za-z0-9]{32,44})', url, re.IGNORECASE)
            if solana_scanner_match:
                addr = solana_scanner_match.group(1)
                if MessageParser.is_valid_solana_address(addr):
                    return addr.upper()
            
            # KOLscope: KOLscopeBot?start=CONTRACT
            kolscope_match = re.search(r'KOLscopeBot\?start=([A-Za-z0-9]{32,44})', url, re.IGNORECASE)
            if kolscope_match:
                addr = kolscope_match.group(1)
                if MessageParser.is_valid_solana_address(addr):
                    return addr.upper()
            
            # SpyDefi: spydefi_bot?start=CONTRACT (reject Ethereum)
            spydefi_match = re.search(r'(?:spydefi_bot|SpyDefi_bot)\?start=([A-Za-z0-9]{32,44})', url, re.IGNORECASE)
            if spydefi_match:
                addr = spydefi_match.group(1)
                if not addr.startswith('0x') and MessageParser.is_valid_solana_address(addr):
                    return addr.upper()
            
            # PRIORITY: Token links (gmgn.ai/sol/token/) should be checked BEFORE address links
            if 'gmgn.ai/sol/token/' in url:
                # Pattern 1: gmgn.ai/sol/token/rLkfkJiz_CONTRACT?maker=... (WhaleBuy format with query params)
                # Extract CA before ?maker= or other query parameters - use lookahead to stop at ? or ) or end
                pattern1 = r'rLkfkJiz_([A-Za-z0-9]{32,44})(?=\?|\)|$)'
                match = re.search(pattern1, url)
                if match:
                    addr = match.group(1)
                    if MessageParser.is_valid_solana_address(addr):
                        return addr.upper()
                # Pattern 2: gmgn.ai/sol/token/rLkfkJiz_CONTRACT (SingleBuys/XTrack format, no query)
                pattern2 = r'gmgn\.ai/sol/token/[^\s\)]*rLkfkJiz_([A-Za-z0-9]{32,44})(?=\?|\)|$)'
                match = re.search(pattern2, url)
                if match:
                    addr = match.group(1)
                    if MessageParser.is_valid_solana_address(addr):
                        return addr.upper()
                # Pattern 3: gmgn.ai/sol/token/CONTRACT (direct format)
                pattern3 = r'gmgn\.ai/sol/token/([A-Za-z0-9]{32,44})(?=\?|\)|$)'
                match = re.search(pattern3, url)
                if match:
                    addr = match.group(1)
                    if MessageParser.is_valid_solana_address(addr):
                        return addr.upper()
                # Pattern 4: Any prefix before contract
                pattern4 = r'gmgn\.ai/sol/token/[A-Za-z0-9]+_([A-Za-z0-9]{32,44})(?=\?|\)|$)'
                match = re.search(pattern4, url)
                if match:
                    addr = match.group(1)
                    if MessageParser.is_valid_solana_address(addr):
                        return addr.upper()
            elif 'pump.fun/' in url:
                pattern = r'pump\.fun/([A-Za-z0-9]{32,44})'
                match = re.search(pattern, url)
                if match:
                    addr = match.group(1)
                    if MessageParser.is_valid_solana_address(addr):
                        return addr.upper()
        
        # Method 3: Extract from text patterns (PFBF format: "Mint: CONTRACT_ADDRESS")
        # Example: "Mint: Ec1zHFvVWibrCbZQEcG1VoAZozkWtFNjY8feQewupump"
        patterns = [
            r'Mint:\s*([A-Za-z0-9]{32,44})',  # PFBF format: "Mint: CONTRACT" (PRIORITY - check first)
            r'📄\s*([A-Za-z0-9]{32,44})',
            r'CA:\s*([A-Za-z0-9]{32,44})',
            r'Contract:\s*([A-Za-z0-9]{32,44})',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Reject Ethereum addresses
                if match.startswith('0x'):
                    continue
                if MessageParser.is_valid_solana_address(match):
                    return match.upper()
        
        return None
    
    @staticmethod
    def extract_symbol(text: str) -> Optional[str]:
        """Extract token symbol from text (matches old script logic)"""
        if not text:
            return None
        
        # Method 0: Extract from PFBF format "Name: Full Name (TokenName)" (PRIORITY - highest)
        # Example: "Name: Silk Road (SilkRoad)" -> extract "SilkRoad"
        pfbf_match = re.search(r'Name:\s*[^(]+\(([A-Za-z0-9\-]+)\)', text, re.IGNORECASE)
        if pfbf_match:
            token_name = pfbf_match.group(1).strip()
            if token_name and len(token_name) >= 1 and len(token_name) <= 50:
                return token_name.upper()
        
        # Method 0.3: Extract from SOL_SB_MB format "Swapped X SOL for Y #$TOKEN On EXCHANGE" (HIGHEST PRIORITY for SOL_SB_MB)
        # Example: "Swapped 2.97 #SOL ($349.13) for 16,984,188.19 #$dns  On #FLASH" -> extract "dns"
        # Structure: "for [amount] #$TOKEN On #EXCHANGE" - token is after "for", exchange is after "On"
        # Pattern: Match "for [amount] #$TOKEN On" - extract token name from #$TOKEN format
        # MUST check this BEFORE Method 3 (line 370) and Method 7 (line 426) which also match #TOKEN patterns
        # Pattern 1: "for [amount] #$TOKEN On" - highest priority, most specific (token with $ sign)
        swapped_for_match = re.search(r'for\s+[\d,.]+\s+#\$([A-Za-z0-9]+)\s+On', text, re.IGNORECASE | re.UNICODE)
        if swapped_for_match:
            token_name = swapped_for_match.group(1).strip()
            if token_name and len(token_name) >= 1 and len(token_name) <= 50:
                return token_name.upper()
        # Pattern 2: "for [amount] #TOKEN On" (but skip exchange names like FLASH, Jupiter, etc.)
        swapped_for_match2 = re.search(r'for\s+[\d,.]+\s+#([A-Za-z0-9]+)\s+On', text, re.IGNORECASE | re.UNICODE)
        if swapped_for_match2:
            token_name = swapped_for_match2.group(1).strip()
            # Skip exchange names (FLASH, Jupiter, Raydium, etc.) - these come AFTER "On", not after "for"
            if token_name and token_name.upper() not in ['SOL', 'USD', 'USDC', 'WSOL', 'FLASH', 'JUPITER', 'RAYDIUM', 'PUMPFUN', 'PUMPSWAP', 'BINANCE'] and len(token_name) >= 1 and len(token_name) <= 50:
                return token_name.upper()
        
        # Method 0.4: Extract from SOL_SB_MB format "🟢 BUY TOKEN on EXCHANGE" (PRIORITY - high, check BEFORE WhaleBuy)
        # Example: "🟢 BUY Toly on PumpSwap" -> extract "Toly"
        # Example: "🟢 BUY Æ on PumpSwap" -> extract "Æ"
        # Example: "🟢 BUY VERDIS on PumpFun" -> extract "VERDIS"
        # Example: "🟢 BUY Ω on Raydium CAMM" -> extract "Ω"
        # Pattern: Match "BUY TOKEN on" - capture token name (can be single Unicode char or word) before "on"
        # Use [^\s] to match any non-whitespace including Unicode, or .+? for multi-char tokens
        sol_sb_mb_match = re.search(r'BUY\s+([^\s]+)\s+on', text, re.IGNORECASE | re.UNICODE)
        if sol_sb_mb_match:
            token_name = sol_sb_mb_match.group(1).strip()
            # Don't clean - the pattern already captures just the token name before "on EXCHANGE"
            # The token name can include Unicode characters like Æ, Ω, etc.
            if token_name and len(token_name) >= 1 and len(token_name) <= 50:
                return token_name.upper()
        
        # Method 0.2: Extract from WhaleBuy format "[TokenName💊]" or "[TokenName💊 (https://...)]" (PRIORITY - high)
        # Example: "✨🟢Buy 2.91 SOL 23.6M [Asgore💊] $0.00001 MCP $15K" -> extract "Asgore"
        # Example: "🟢Buy 1.96 WSOL 4.9M [VEIL💊 (https://gmgn.ai/sol/token/rLkfkJiz_...)] $0.00005 MCP $48.9K" -> extract "VEIL"
        # Example: "🟢Buy 4.42 WSOL 12.8M [bearcoin (https://gmgn.ai/sol/token/rLkfkJiz_...)] $0.00004 MCP $41.8K" -> extract "bearcoin"
        # Pattern: Find [TokenName💊] or [TokenName (https://...)] that appears after "Buy" and "SOL"/"WSOL" keywords
        # Check for WhaleBuy format: has "Buy" and "SOL"/"WSOL" and "MCP"
        if ('Buy' in text or '🟢' in text) and ('SOL' in text or 'WSOL' in text) and 'MCP' in text:
            # Pattern 1: [TOKEN💊 (https://...)] - extract token before emoji and link
            whalebuy_with_link = re.search(r'\[([A-Za-z0-9\-]+)[💊]?\s*\(https://', text, re.IGNORECASE)
            if whalebuy_with_link:
                token_name = whalebuy_with_link.group(1).strip()
                if token_name and len(token_name) >= 1 and len(token_name) <= 50:
                    return token_name.upper()
            
            # Pattern 2: [TokenName💊] or [TokenName] (old format without links)
            # Find all bracket patterns and take the one that appears after Buy and SOL
            bracket_matches = list(re.finditer(r'\[([A-Za-z0-9\-]+)', text, re.IGNORECASE))
            if bracket_matches and len(bracket_matches) >= 2:
                # Take the last bracket match (usually the token name, not whale identifier like [whale_NUB])
                token_name = bracket_matches[-1].group(1).strip()
                if token_name and len(token_name) >= 1 and len(token_name) <= 50:
                    return token_name.upper()
        
        # Method 0.3: Extract from KOLscope format "made Xx+ on TOKEN" (PRIORITY - high)
        # Example: "@SPACEBASEDAPESS made 3x+ on Æ." -> extract "Æ"
        # Example: "@GODOFCALLS1 made 3x+ on SPANKMAS." -> extract "SPANKMAS"
        # Example: "@Lutherrachcalls made 2x+ on BEARCOIN from dip." -> extract "BEARCOIN"
        # Pattern: Extract token name (alphanumeric) before "from" or period
        kolscope_match = re.search(r'made\s+\d+x\+?\s+on\s+([A-Za-z0-9\-]+)', text, re.IGNORECASE)
        if kolscope_match:
            token_name = kolscope_match.group(1).strip()
            if token_name and len(token_name) >= 1 and len(token_name) <= 50:
                return token_name.upper()
        
        # Method 0.5: Extract from Solana Early Trending format "🔥 TOKEN_NAME New Trending" (PRIORITY)
        solana_early_match = re.search(r'🔥\s*‎?([^\n]+?)\s+New\s+Trending', text, re.IGNORECASE)
        if solana_early_match:
            token_name = solana_early_match.group(1).strip().strip(' ‎')
            if token_name and len(token_name) >= 1 and len(token_name) <= 50:
                return token_name.upper()
        
        # Method 0.6: Extract from Solana Early Trending format "📈 TOKEN is up X.Xx" (PRIORITY)
        # Example: "📈 ‎SUNABOZU is up 3.1X 📈"
        solana_early_up_match = re.search(r'📈\s*‎?([A-Za-z0-9\-]+)\s+is\s+up\s+[\d.]+[Xx]', text, re.IGNORECASE)
        if solana_early_up_match:
            token_name = solana_early_up_match.group(1).strip().strip(' ‎')
            if token_name and len(token_name) >= 1 and len(token_name) <= 50:
                return token_name.upper()
        
        # Method 1: Extract from "💰 TOKEN ($X.XK)" format (Large Buys Tracker)
        # Example: "💰 E91 ($49.2K) - 10.65 SOL BUY"
        # Example: "[botted] 💰 HOUSEMAID ($24.4K) - 5.87 SOL BUY"
        large_buys_match = re.search(r'💰\s*([A-Za-z0-9\-]+)\s*\(', text)
        if large_buys_match:
            token_name = large_buys_match.group(1).strip()
            if token_name and len(token_name) >= 1 and len(token_name) <= 20:
                return token_name.upper()
        
        # Method 2: Extract from Momentum Tracker format "⚡ TOKEN ($X.XK)"
        # Example: "⚡ likely ($13.4K)  - ⏫ 41.06% in 1.5s"
        momentum_match = re.search(r'⚡\s*([A-Za-z0-9\-]+)\s*\(', text)
        if momentum_match:
            token_name = momentum_match.group(1).strip()
            if token_name and len(token_name) >= 1 and len(token_name) <= 20:
                return token_name.upper()
        
        # Method 3: Extract from "Swapped X TOKEN for Y #TOKEN" format (PRIORITY - token being bought)
        # Pattern: Swapped X ANY_TOKEN for Y #TOKEN - token name is AFTER "for"
        # Example: "Swapped 1 #SOL ($128.37) for 14,312,725.39 #SLIDING On #Jupiter"
        # Example: "Swapped 51.55 #USD1 ($51.55) for 9,703,079.87 #1Dog On #Raydium"
        # The token name is "#SLIDING" or "#1Dog" (not the first #SOL or #USD1)
        # IMPORTANT: Skip if there's a "#$TOKEN" format before "On" (that's handled by Method 0.3)
        # IMPORTANT: Skip exchange names that come AFTER "On" (FLASH, Jupiter, etc.)
        # Match: Swapped [amount] [#?ANY_TOKEN] [anything] for [amount] #TOKEN (but not #$TOKEN or exchange names)
        swapped_match = re.search(r'Swapped\s+[\d,.]+(?:\s*\([^)]+\))?\s+#?[A-Za-z0-9]+\s+[^#]*for\s+[\d,.]+\s+#([A-Za-z0-9™©®]+)', text, re.IGNORECASE)
        if swapped_match:
            token_name = swapped_match.group(1).strip()
            # Skip exchange names (FLASH, Jupiter, Raydium, etc.) - these come AFTER "On", not after "for"
            if token_name.upper() in ['FLASH', 'JUPITER', 'RAYDIUM', 'PUMPFUN', 'PUMPSWAP', 'BINANCE', 'MAESTRO', 'CHART', 'BUY']:
                pass  # Skip exchange names
            else:
                # Remove any trailing words like "On", "@", "#", or exchange names
                token_name = re.sub(r'\s+(On|@|#|PumpFun|PumpSwap|Raydium|Binance|Jupiter|MAESTRO|CHART|BUY).*$', '', token_name, flags=re.IGNORECASE)
                # Remove special characters like ™ but keep the base token name
                token_name = re.sub(r'[™©®]', '', token_name).strip()
                if token_name and len(token_name) >= 1 and len(token_name) <= 20:  # Allow tokens like "1Dog"
                    return token_name.upper()
        
        # Method 4: Extract from XTRACK format "TOKEN did 👉 Xx"
        xtrack_match = re.search(r'([A-Za-z0-9]+)\s+did\s+👉', text, re.IGNORECASE)
        if xtrack_match:
            symbol = xtrack_match.group(1).strip().upper()
            if len(symbol) >= 2 and len(symbol) <= 20:
                return symbol
        
        # Method 5: Extract from CALLERS format "⚪ TOKEN (#TOKEN)"
        callers_match = re.search(r'⚪\s*([^(]+?)\s*\(#([^)]+)\)', text)
        if callers_match:
            # Prefer the symbol in parentheses
            symbol = callers_match.group(2).strip().upper()
            if len(symbol) >= 2 and len(symbol) <= 20:
                return symbol
        
        # Method 6: Extract from CALL ALERT format
        call_alert_match = re.search(r'CALL ALERT:\s*([A-Za-z0-9\-]+)', text, re.IGNORECASE)
        if call_alert_match:
            symbol = call_alert_match.group(1).strip().upper()
            if len(symbol) >= 2 and len(symbol) <= 20:
                return symbol
        
        # Method 5: Extract from spydefi "call on TOKEN"
        spydefi_match = re.search(r'call on\s+([A-Za-z0-9\-]+)', text, re.IGNORECASE)
        if spydefi_match:
            symbol = spydefi_match.group(1).strip().upper()
            if len(symbol) >= 2 and len(symbol) <= 20:
                return symbol
        
        # Method 8: Extract from #TOKEN format (but skip if message has "Swapped" and it's at start - that's trader ID)
        has_swapped = 'Swapped' in text
        if not has_swapped:
            # Look for #TOKEN at the very start of the message (only if not a Swapped message)
            start_hash_match = re.search(r'^#([A-Za-z0-9]+(?:\.\.\.[A-Za-z0-9]+)?)', text)
            if start_hash_match:
                token_name = start_hash_match.group(1).strip()
                # Handle ellipsis format - take first part before ...
                if '...' in token_name:
                    token_name = token_name.split('...')[0]
                if len(token_name) >= 2 and len(token_name) <= 20:
                    return token_name.upper()
        
        # Method 7: Extract from any #TOKEN format (fallback, but skip if it's at start and message has Swapped)
        # IMPORTANT: Skip exchange names that come AFTER "On" (FLASH, Jupiter, etc.) - these are not tokens
        all_hash_matches = list(re.finditer(r'#([A-Za-z0-9]+(?:\.\.\.[A-Za-z0-9]+)?)', text))
        if all_hash_matches:
            # If message has "Swapped", skip the first match (it's the trader ID like #SOL)
            # Otherwise, use the first match
            start_idx = 1 if has_swapped and len(all_hash_matches) > 1 else 0
            if start_idx < len(all_hash_matches):
                token_name = all_hash_matches[start_idx].group(1).strip()
                # Handle ellipsis format
                if '...' in token_name:
                    token_name = token_name.split('...')[0]
                # Skip exchange names (FLASH, Jupiter, etc.) - these come AFTER "On", not tokens
                if token_name.upper() in ['FLASH', 'JUPITER', 'RAYDIUM', 'PUMPFUN', 'PUMPSWAP', 'BINANCE', 'MAESTRO', 'CHART', 'BUY']:
                    # Skip this match, try next one if available
                    if start_idx + 1 < len(all_hash_matches):
                        token_name = all_hash_matches[start_idx + 1].group(1).strip()
                        if '...' in token_name:
                            token_name = token_name.split('...')[0]
                    else:
                        token_name = None
                if token_name and len(token_name) >= 2 and len(token_name) <= 20:
                    return token_name.upper()
        
        # Method 10: Extract from $TOKEN format (but skip pure numbers from market cap like $24.4K or $170K)
        dollar_match = re.search(r'\$([A-Za-z0-9]+)', text)
        if dollar_match:
            symbol = dollar_match.group(1).strip().upper()
            # Don't match if it's just numbers (like "24" from "$24.4K", "49" from "$49.2K", or "170" from "$170K")
            # Also skip if it ends with K or M (market cap indicators)
            if symbol and not symbol.replace('.', '').isdigit() and not symbol.endswith(('K', 'M')) and len(symbol) >= 2 and len(symbol) <= 20:
                return symbol
            else:
                    pass
        
        return None
    
    @staticmethod
    def parse_market_cap(text: str) -> Optional[float]:
        """Parse market cap (e.g., $53.8k, $1.5M, $51,398)"""
        if not text:
            return None
        
        # XTRACK format with arrow: "MC: $23.1k 👉 $69.2k" (take current = second value)
        arrow_mcap = re.findall(r'MC:\s*\$([\d,\.]+[KMkm]?)', text, re.IGNORECASE)
        if arrow_mcap and len(arrow_mcap) >= 2:
            mc_str = arrow_mcap[-1].replace(',', '').upper()
            try:
                if mc_str.endswith('K'):
                    return float(mc_str[:-1]) * 1000
                if mc_str.endswith('M'):
                    return float(mc_str[:-1]) * 1_000_000
                return float(mc_str)
            except Exception:
                pass

        # PFBF format: "MC: $51,398" or "MC: $36,908" - HIGHEST PRIORITY  
        # Pattern: Match "MC:" followed by "$" and number with commas
        # PFBF format has commas in number (like $36,908)
        pfbf_match = re.search(r'MC:\s+\$([\d,]+)', text, re.IGNORECASE)
        if pfbf_match:
            num_str = pfbf_match.group(1)
            # If number has commas, it's PFBF format
            if ',' in num_str:
                mc_str = num_str.strip().replace(',', '')
                try:
                    return float(mc_str)
                except:
                    pass
        
        # WhaleBuy format: "MCP $15K" or "MCP $441.1M" - extract MCAP from MCP field
        # Example: "🟢Buy 2.91 SOL 23.6M [Asgore💊] $0.00001 MCP $15K" -> extract $15K
        # Example: "🟢Buy 6K USDC 13.6K [pippin💊] $0.44116 MCP $441.1M" -> extract $441.1M
        # Pattern: MCP followed by space and $, then number with K or M suffix
        # Try more flexible pattern that handles any whitespace
        whalebuy_mcp_match = re.search(r'MCP\s+\$([\d,\.]+)([KMkm])', text, re.IGNORECASE)
        if whalebuy_mcp_match:
            mc_str = whalebuy_mcp_match.group(1).strip().replace(',', '')
            suffix = whalebuy_mcp_match.group(2).upper()
            try:
                value = float(mc_str)
                if suffix == 'K':
                    return value * 1000
                elif suffix == 'M':
                    return value * 1000000
                else:
                    return value
            except Exception:
                pass
        
        # KOLscope format: "$17.2K ⮕ $34.5K" - extract the SECOND value (current MCAP after arrow)
        # If "made" is present, the second value after ⮕ is the current MCAP
        # Example: "$17.2K ⮕ $34.5K" -> extract $34.5K (current MCAP)
        if 'made' in text:  # KOLscope multiplier messages
            # Find all "$XK" or "$XM" or "$X.XK" patterns (handles decimals like $17.2K)
            all_mcaps = re.findall(r'\$([\d,\.]+[KMkm])', text, re.IGNORECASE)
            if all_mcaps and len(all_mcaps) >= 2:
                # Take the second one (current MCAP after the arrow)
                mc_str = all_mcaps[1].strip().upper().replace(',', '')
                try:
                    if 'K' in mc_str:
                        result = float(mc_str.replace('K', '')) * 1000
                        return result
                    elif 'M' in mc_str:
                        result = float(mc_str.replace('M', '')) * 1000000
                        return result
                except Exception:
                    pass
        
        # SOL_SB_MB format: "MC: $227.92K" - extract MCAP with K/M suffix and decimals
        # Example: "MC: $227.92K" -> extract $227.92K = 227920
        sol_sb_mb_mc_match = re.search(r'MC[:\s]+\$([\d,\.]+)([KMkm])', text, re.IGNORECASE)
        if sol_sb_mb_mc_match:
            mc_str = sol_sb_mb_mc_match.group(1).strip().replace(',', '')
            suffix = sol_sb_mb_mc_match.group(2).upper()
            try:
                value = float(mc_str)
                if suffix == 'K':
                    return value * 1000
                elif suffix == 'M':
                    return value * 1000000
                else:
                    return value
            except Exception:
                pass
        
        patterns = [
            r'💰\s*MC:\s*\$?([\d,]+)',  # Solana Early Trending: 💰 MC: $54,726 (prioritize this)
            r'MC[:\s]+\$?([\d,\.]+[KMkm]?)\s*👉',
            r'MCap[:\s]+\$?([\d,\.]+[KMkm]?)',
            r'Market\s+Cap[:\s]+\$?([\d,\.]+[KMkm]?)',
            r'MC[:\s]+\$([\d,\.]+[KMkm]?)',  # General MC: $X format (must have $ to avoid partial matches)
            r'💰\s*MC:\s*\$?([\d,\.]+[KMkm]?)',
            r'\(\$([\d,\.]+[KMkm]?)\)',
            r'Current MCap:\s*\$?([\d,\.]+[KMkm]?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                mc_str = match.group(1).strip().upper()
                try:
                    # Remove commas first
                    mc_str = mc_str.replace(',', '')
                    # Handle Solana Early Trending format (no K/M suffix, just number)
                    if 'K' in mc_str:
                        return float(mc_str.replace('K', '')) * 1000
                    elif 'M' in mc_str:
                        return float(mc_str.replace('M', '')) * 1000000
                    elif 'B' in mc_str:
                        return float(mc_str.replace('B', '')) * 1000000000
                    else:
                        # Direct number (Solana Early Trending format like "54726" or PFBF like "51398")
                        return float(mc_str)
                except:
                    continue
        
        return None
    
    @staticmethod
    def parse_liquidity(text: str) -> Optional[float]:
        """Parse liquidity"""
        if not text:
            return None
        
        patterns = [
            r'LIQ[:\s]+\$?([\d,\.]+[KMkm]?)',
            r'Liquidity[:\s]+\$?([\d,\.]+[KMkm]?)',
            r'💧\s*LIQ[:\s]+\$?([\d,\.]+[KMkm]?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                liq_str = match.group(1).strip().upper()
                try:
                    liq_str = liq_str.replace(',', '')
                    if 'K' in liq_str:
                        return float(liq_str.replace('K', '')) * 1000
                    elif 'M' in liq_str:
                        return float(liq_str.replace('M', '')) * 1000000
                    else:
                        return float(liq_str)
                except:
                    continue
        
        return None
    
    @staticmethod
    def parse_buy_size_sol(text: str) -> Optional[float]:
        """Parse buy size in SOL"""
        if not text:
            return None
        
        patterns = [
            # WhaleBuy format: "🟢Buy X SOL" or "Buy X SOL" or "Buy X WSOL" (PRIORITY - highest)
            r'🟢Buy\s+(\d+\.?\d*)\s*(?:SOL|WSOL)',
            r'Buy\s+(\d+\.?\d*)\s*(?:SOL|WSOL)',
            # SOL_SB_MB format: "swapped 3.93 SOL for" (PRIORITY - high)
            r'swapped\s+(\d+\.?\d*)\s*SOL\s+for',
            # Large Buys Tracker format: "💰 TOKEN ($X.XK) - Y SOL BUY"
            r'💰\s*[A-Za-z0-9\-]+\s*\(\$[\d,\.]+[KMkm]?\)\s*-\s*(\d+\.?\d*)\s*SOL',
            # General formats
            r'(\d+\.?\d*)\s*SOL\s*BUY',
            r'Swapped\s+(\d+\.?\d*)\s*#?SOL',
            r'(\d+\.?\d*)\s*SOL\s*for',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except:
                    continue
        
        return None
    
    @staticmethod
    def parse_xtrack_multiplier(text: str) -> Optional[float]:
        """Parse XTRACK multiplier"""
        if not text:
            return None
        
        patterns = [
            r'did\s+👉\s*(\d+x)',
            r'(\d+x\+?)',
            r'(\d+\.?\d*x)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                mult_str = match.group(1).replace('x', '').replace('+', '')
                try:
                    return float(mult_str)
                except:
                    continue
        
        return None
    
    @staticmethod
    def parse_glydo_symbols(text: str) -> List[str]:
        """Parse Glydo message to extract token symbols (trending list)"""
        if not text:
            return []
        
        symbols = []
        # Pattern: "1. $SYMBOL" or "1. #SYMBOL" or just "$SYMBOL"
        patterns = [
            r'\d+\.\s*\$?([A-Za-z0-9]+)',  # "1. $PP" or "1. PP"
            r'\d+\.\s*#([A-Za-z0-9]+)',   # "1. #Probable"
            r'\$\s*([A-Za-z0-9]+)',       # "$PP" standalone
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if match and len(match) >= 1:
                    symbols.append(match.upper())
        
        return symbols
    
    @classmethod
    def diagnose_failure(cls, msg: Dict, source: str) -> str:
        """Return a reason code when parse_message() returns None."""
        try:
            content = msg.get("content", "") or msg.get("text", "") or ""
            entities = msg.get("entities", []) or []
            if not content:
                return "empty_content"

            if source == "glydo":
                syms = cls.parse_glydo_symbols(content)
                return "glydo_no_symbol" if not syms else "glydo_symbol_only"

            # SpyDefi ETH CA present (not supported in this Solana system)
            if re.search(r'spydefi_bot\?start=0x[a-fA-F0-9]{40}', content):
                return "eth_ca_present"

            ca = cls.extract_contract_address(content, entities)
            if not ca:
                return "no_ca"
            if not cls.is_valid_solana_address(ca):
                return "invalid_ca"

            sym = cls.extract_symbol(content)
            if not sym:
                return "no_symbol"
            if sym == "UNKNOWN":
                return "symbol_unknown"

            return "other"
        except Exception:
            return "exception"

    @classmethod
    def parse_message(cls, msg: Dict, source: str) -> Optional[ParsedMessage]:
        """Parse a message and extract token data"""
        # Normalize common source aliases
        src = source
        if source.startswith('xtrack'):
            src = 'xtrack'
        elif source.startswith('glydo'):
            src = 'glydo'
        elif source.startswith('sol_sb_mb'):
            src = 'sol_sb_mb'
        elif source.startswith('sol_sb1'):
            src = 'sol_sb1'
        elif source.startswith('whalebuy'):
            src = 'whalebuy'
        elif source.startswith('momentum'):
            src = 'momentum_tracker'
        elif source.startswith('large_buys'):
            src = 'large_buys_tracker'
        elif source.startswith('pfbf'):
            src = 'pfbf_volume_alert'
        elif source.startswith('call_analyzer'):
            src = 'call_analyzer'
        elif source.startswith('kolscope'):
            src = 'kolscope'
        elif source.startswith('spydefi'):
            src = 'spydefi'
        elif source.startswith('solana_early'):
            src = 'solana_early_trending'
        source = src

        content = msg.get('content', '') or msg.get('text', '')
        if not content:
            return None
        
        # Special handling for Glydo (symbol-only, no contract address)
        if source == 'glydo':
            symbols = cls.parse_glydo_symbols(content)
            if not symbols:
                return None
            
            # Extract timestamp
            timestamp_str = msg.get('date_utc', '')
            if not timestamp_str:
                timestamp = datetime.now(timezone.utc)
            else:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('+00:00', '+00:00'))
                except:
                    timestamp = datetime.now(timezone.utc)
            
            # Return first symbol (Glydo messages can have multiple, we'll handle matching separately)
            # Use placeholder contract address that will be matched later
            return ParsedMessage(
                symbol=symbols[0],  # Take first symbol
                contract_address=f'GLYDO_{symbols[0]}',  # Placeholder for matching
                source=source,
                timestamp=timestamp,
                buy_size_sol=None,
                market_cap=None,
                liquidity=None,
                xtrack_multiplier=None
            )
        
        # For all other sources, contract address is REQUIRED
        contract_address = cls.extract_contract_address(content, msg.get('entities', []))
        if not contract_address:
            return None  # Must have contract address
        
        # Validate contract address format
        if not cls.is_valid_solana_address(contract_address):
            return None  # Invalid contract address format
        
        # Extract symbol
        symbol = cls.extract_symbol(content)
        if not symbol:
            symbol = "UNKNOWN"
        
        # Extract timestamp
        timestamp_str = msg.get('date_utc', '')
        if not timestamp_str:
            timestamp = datetime.now(timezone.utc)
        else:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('+00:00', '+00:00'))
            except:
                timestamp = datetime.now(timezone.utc)
        
        # Extract metrics
        buy_size_sol = cls.parse_buy_size_sol(content)
        market_cap = cls.parse_market_cap(content)
        liquidity = cls.parse_liquidity(content)
        xtrack_multiplier = cls.parse_xtrack_multiplier(content) if source == 'xtrack' else None
        
        return ParsedMessage(
            symbol=symbol,
            contract_address=contract_address,
            source=source,
            timestamp=timestamp,
            buy_size_sol=buy_size_sol,
            market_cap=market_cap,
            liquidity=liquidity,
            xtrack_multiplier=xtrack_multiplier
        )

