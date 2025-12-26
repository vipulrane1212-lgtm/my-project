#!/usr/bin/env python3
"""
Tiered Strategy Engine for Live Telegram Monitoring
Implements the proven tiered strategy from backtest analysis
"""

import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

class TieredStrategyEngine:
    """Implements the tiered strategy logic for live monitoring"""
    
    def __init__(self):
        self.glydo_cache = []  # Cache recent Glydo messages for top 5 tracking
        self.hot_list = set()  # Tokens currently in Glydo top 5
        
    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol: uppercase, strip #/$ prefixes"""
        if not symbol:
            return symbol
        return symbol.strip('#$').upper()
    
    def symbols_match(self, symbol1: str, symbol2: str) -> bool:
        """Check if two symbols match, handling variations"""
        if not symbol1 or not symbol2:
            return False
        
        s1 = self.normalize_symbol(symbol1)
        s2 = self.normalize_symbol(symbol2)
        
        # Exact match
        if s1 == s2:
            return True
        
        # Handle known variations
        variations = {
            'SNOC': ['SNOWBALL', 'SNOW'],
            'SNOWBALL': ['SNOC', 'SNOW'],
            'FIREBALL': ['FIRE'],
            'BOBO': ['BOBO SHOW', 'BOBOSHOW'],
            'BOBO SHOW': ['BOBO', 'BOBOSHOW'],
            'YETI': ['YETI'],
            'LEGENDARY': ['LEGEND'],
            'NEURVONA': ['NEURONA', 'NEURON'],
        }
        
        # Check if either symbol is a variation of the other
        for base, variants in variations.items():
            if s1 == base and s2 in variants:
                return True
            if s2 == base and s1 in variants:
                return True
            if s1 in variants and s2 in variants:
                return True
        
        # Partial match (one contains the other, min 4 chars)
        if len(s1) >= 4 and len(s2) >= 4:
            if s1 in s2 or s2 in s1:
                return True
        
        return False
    
    def update_glydo_cache(self, message: Dict):
        """Update Glydo cache with new message"""
        if message.get('feed_name') != 'glydo':
            return
        
        timestamp = self._parse_timestamp(message.get('timestamp_utc'))
        content = message.get('raw_text', '')
        
        # Extract top 5 symbols
        matches = re.findall(r'\d+\.\s*[#$]?([A-Za-z0-9]+)', content)
        symbols = [self.normalize_symbol(match) for match in matches[:5]]
        
        self.glydo_cache.append({
            'timestamp': timestamp,
            'symbols': symbols,
            'content': content
        })
        
        # Update hot list
        self.hot_list = set()
        for entry in self.glydo_cache[-10:]:  # Last 10 Glydo messages
            self.hot_list.update(entry['symbols'])
        
        # Clean old entries (keep last 50 messages)
        if len(self.glydo_cache) > 50:
            self.glydo_cache = self.glydo_cache[-50:]
    
    def _parse_timestamp(self, ts: str | datetime) -> datetime:
        """Parse timestamp to datetime"""
        if isinstance(ts, datetime):
            return ts.astimezone(timezone.utc)
        try:
            return datetime.fromisoformat(str(ts).replace("Z", "+00:00")).astimezone(timezone.utc)
        except:
            return datetime.now(timezone.utc)
    
    def check_glydo_top5(self, token: str, cohort_timestamp: datetime) -> Dict:
        """Check if token appears in Glydo top 5 within ±20 minutes"""
        time_minus_20m = cohort_timestamp - timedelta(minutes=20)
        time_plus_20m = cohort_timestamp + timedelta(minutes=20)
        
        glydo_symbols = set()
        for entry in self.glydo_cache:
            if time_minus_20m <= entry['timestamp'] <= time_plus_20m:
                glydo_symbols.update(entry['symbols'])
        
        # Check if token appears in top 5
        in_top5 = any(self.symbols_match(token, gs) for gs in glydo_symbols)
        
        return {
            'in_top5_window': in_top5,
            'glydo_symbols': list(glydo_symbols),
            'delayed_appearance': self._check_delayed_glydo(token, cohort_timestamp)
        }
    
    def _check_delayed_glydo(self, token: str, cohort_timestamp: datetime) -> bool:
        """Check if token appears in Glydo after 30 minutes"""
        time_plus_30m = cohort_timestamp + timedelta(minutes=30)
        time_plus_2h = cohort_timestamp + timedelta(hours=2)
        
        for entry in self.glydo_cache:
            if time_plus_30m <= entry['timestamp'] <= time_plus_2h:
                if any(self.symbols_match(token, s) for s in entry['symbols']):
                    return True
        return False
    
    def count_confirmations(self, token: str, cohort_timestamp: datetime, events: List[Dict]) -> Dict:
        """Count confirmation signals within ±30 minutes"""
        time_minus_30m = cohort_timestamp - timedelta(minutes=30)
        time_plus_30m = cohort_timestamp + timedelta(minutes=30)
        
        confirmations = {
            'momentum_spike': 0,  # >25% in <30s
            'large_buy': 0,  # >5 SOL single buy
            'multi_buy': 0,
            'whale_buy': 0,
            'pfbf_volume': 0,
            'early_trending': 0,
            'total': 0,
            'strong_total': 0,  # Strong confirmations only
            'details': []
        }
        
        for event in events:
            event_time = self._parse_timestamp(event.get('timestamp_utc'))
            if not (time_minus_30m <= event_time <= time_plus_30m):
                continue
            
            source = event.get('feed_name', '')
            
            # Momentum spike
            if source == 'momentum_tracker':
                # Check if momentum > 25% (would need to extract from raw_text or add field)
                confirmations['momentum_spike'] += 1
                confirmations['strong_total'] += 1
                confirmations['details'].append("Momentum spike")
            
            # Large buy
            buy_size = event.get('buy_size_sol', 0) or 0
            if buy_size > 5:
                confirmations['large_buy'] += 1
                confirmations['strong_total'] += 1
                confirmations['details'].append(f"Large buy: {buy_size} SOL")
            
            # Whale buy
            if source == 'whalebuy':
                confirmations['multi_buy'] += 1
                confirmations['whale_buy'] += 1
                confirmations['strong_total'] += 1
                confirmations['details'].append("Whale buy")
            
            # PFBF volume
            if source == 'pfbf_volume_alert':
                confirmations['multi_buy'] += 1
                confirmations['pfbf_volume'] += 1
                confirmations['details'].append("PFBF volume alert")
            
            # Early trending
            if source == 'solana_early_trending':
                confirmations['early_trending'] += 1
                confirmations['strong_total'] += 1
                confirmations['details'].append("Early trending")
        
        confirmations['total'] = (confirmations['momentum_spike'] + confirmations['large_buy'] +
                                confirmations['multi_buy'] + confirmations['early_trending'])
        
        return confirmations
    
    def check_hot_list(self, token: str) -> bool:
        """Check if token is currently in Hot List (Glydo top 5)"""
        return any(self.symbols_match(token, hl) for hl in self.hot_list)
    
    def determine_tier(self, entry_mc: float, glydo_data: Dict, confirmations: Dict) -> Optional[int]:
        """Determine strategy tier based on criteria"""
        
        in_top5 = glydo_data['in_top5_window']
        strong_confirmations = confirmations['strong_total']
        total_confirmations = confirmations['total']
        delayed_glydo = glydo_data['delayed_appearance']
        
        # Tier 1: XTRACK ≥2x + Glydo top 5 (±20 min) + ≥1 strong confirmation + MC 40k-100k
        if (in_top5 and strong_confirmations >= 1 and 40000 <= entry_mc <= 100000):
            return 1
        
        # Tier 2: XTRACK ≥2x + Glydo top 5 (±20 min) + ≥1 confirmation + MC 30k-120k
        if (in_top5 and total_confirmations >= 1 and 30000 <= entry_mc <= 120000):
            return 2
        
        # Tier 3: XTRACK ≥2x + (≥2 non-Glydo confirmations OR delayed Glydo)
        if total_confirmations >= 2 or delayed_glydo:
            return 3
        
        return None
    
    def evaluate_opportunity(self, cohort: Dict, events: List[Dict]) -> Optional[Dict]:
        """Evaluate if cohort qualifies for any tier"""
        
        token = cohort.get('token')
        cohort_timestamp = self._parse_timestamp(cohort.get('cohort_start'))
        entry_mc = cohort.get('entry_mc')
        
        # Apply MC filters
        if not entry_mc or entry_mc < 30000 or entry_mc > 150000:
            return None
        
        # Check Glydo appearances
        glydo_data = self.check_glydo_top5(token, cohort_timestamp)
        
        # Count confirmations
        confirmations = self.count_confirmations(token, cohort_timestamp, events)
        
        # Check Hot List
        in_hot_list = self.check_hot_list(token)
        
        # Determine tier
        tier = self.determine_tier(entry_mc, glydo_data, confirmations)
        
        if tier:
            return {
                'tier': tier,
                'glydo_in_top5': glydo_data['in_top5_window'],
                'confirmations': confirmations,
                'hot_list': in_hot_list,
                'entry_mc': entry_mc
            }
        
        return None






