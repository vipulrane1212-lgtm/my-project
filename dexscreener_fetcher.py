"""
dexscreener_fetcher.py

Utility to fetch live MCAP, symbol, and liquidity from DexScreener public API.
No authentication required - free public API.
"""

from __future__ import annotations

import time
from typing import Optional, Dict, Tuple
import requests

# Rate limiting: DexScreener allows ~200 requests/minute
# We'll add a simple rate limiter
_last_request_time = 0
_min_request_interval = 0.3  # 300ms between requests (200/min = 3/sec max)


def fetch_token_data(contract_address: str, timeout: int = 10) -> Optional[Dict]:
    """
    Fetch token data from DexScreener API.
    
    Args:
        contract_address: Solana contract address
        timeout: Request timeout in seconds
        
    Returns:
        Dict with API response or None if error
    """
    global _last_request_time
    
    # Simple rate limiting
    elapsed = time.time() - _last_request_time
    if elapsed < _min_request_interval:
        time.sleep(_min_request_interval - elapsed)
    _last_request_time = time.time()
    
    url = f"https://api.dexscreener.com/latest/dex/tokens/{contract_address}"
    
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"[DexScreener] Request error for {contract_address}: {e}")
        return None
    except Exception as e:
        print(f"[DexScreener] Error fetching {contract_address}: {e}")
        return None


def extract_token_info(data: Dict, contract_address: str) -> Tuple[Optional[str], Optional[float], Optional[float], Optional[str]]:
    """
    Extract symbol, MCAP, liquidity, and price from DexScreener response.
    
    Returns:
        (symbol, mcap_usd, liquidity_usd, price_usd)
    """
    if not data or "pairs" not in data:
        return None, None, None, None
    
    pairs = data.get("pairs", [])
    if not pairs:
        return None, None, None, None
    
    # Find the pair with the highest liquidity (usually the main pair)
    main_pair = None
    max_liquidity = 0
    
    for pair in pairs:
        if pair.get("chainId") == "solana":
            liq = pair.get("liquidity", {})
            if isinstance(liq, dict):
                liq_usd = liq.get("usd", 0) or 0
            else:
                liq_usd = float(liq) if liq else 0
            
            if liq_usd > max_liquidity:
                max_liquidity = liq_usd
                main_pair = pair
    
    if not main_pair:
        # Fallback to first Solana pair
        for pair in pairs:
            if pair.get("chainId") == "solana":
                main_pair = pair
                break
        if not main_pair:
            main_pair = pairs[0]
    
    # Extract data
    base_token = main_pair.get("baseToken", {})
    symbol = base_token.get("symbol")
    name = base_token.get("name")
    
    # Clean symbol/name
    if symbol:
        symbol = symbol.strip()
    if name:
        name = name.strip()
        
    # Prefer name if symbol is emoji or just numbers and name is better
    # But for now, let's just make sure we return the best possible identifier
    if not symbol and name:
        symbol = name
    elif symbol and symbol.replace('.', '').isdigit() and name and not name.replace('.', '').isdigit():
        # If symbol is just numbers but name is text, use name
        symbol = name
        
    # MCAP: prefer marketCap, fallback to fdv
    mcap = main_pair.get("marketCap")
    if mcap is None:
        mcap = main_pair.get("fdv")  # Fully diluted valuation
    
    # Liquidity
    liquidity = main_pair.get("liquidity", {})
    if isinstance(liquidity, dict):
        liquidity_usd = liquidity.get("usd")
    else:
        liquidity_usd = float(liquidity) if liquidity else None
    
    # Price
    price_usd = main_pair.get("priceUsd")
    if price_usd:
        try:
            price_usd = float(price_usd)
        except (ValueError, TypeError):
            price_usd = None
    
    return symbol, mcap, liquidity_usd, price_usd


def get_live_mcap_and_symbol(contract_address: str) -> Tuple[Optional[str], Optional[float], Optional[float], Optional[str]]:
    """
    Convenience function to get live token data.
    
    Args:
        contract_address: Solana contract address
        
    Returns:
        (symbol, mcap_usd, liquidity_usd, price_usd)
    """
    data = fetch_token_data(contract_address)
    if not data:
        return None, None, None, None
    
    return extract_token_info(data, contract_address)


def enrich_alert_with_live_data(alert: Dict) -> Dict:
    """
    Enrich alert with live MCAP and symbol from DexScreener.
    
    Args:
        alert: Alert dictionary with contract address
        
    Returns:
        Updated alert dict with live_mcap, live_symbol, live_liquidity if available
    """
    contract = alert.get("contract")
    if not contract:
        return alert
    
    symbol, mcap, liquidity, price = get_live_mcap_and_symbol(contract)
    
    # Update alert with live data (don't overwrite existing if live data is None)
    if symbol:
        alert["live_symbol"] = symbol
    if mcap is not None:
        alert["live_mcap"] = mcap
    if liquidity is not None:
        alert["live_liquidity"] = liquidity
    if price is not None:
        alert["live_price"] = price
    
    return alert


# Test function
if __name__ == "__main__":
    test_contracts = [
        "13EHWUDMRTQ4LXYBFF7JNHNQGCZXZYYO8IUAGATAPUMP",
        "4MKRVMH7CDEWSRXTEWBZ61RRJNAITFGKA6FZHZM2PUMP"
    ]
    
    print("=" * 80)
    print("DexScreener Live Data Fetcher - Test")
    print("=" * 80)
    print()
    
    for contract in test_contracts:
        print(f"Contract: {contract}")
        symbol, mcap, liquidity, price = get_live_mcap_and_symbol(contract)
        
        print(f"  Symbol: {symbol or 'N/A'}")
        print(f"  MCAP: ${mcap:,.2f}" if mcap else "  MCAP: N/A")
        print(f"  Liquidity: ${liquidity:,.2f}" if liquidity else "  Liquidity: N/A")
        print(f"  Price: ${price}" if price else "  Price: N/A")
        print()

