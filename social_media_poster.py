#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
social_media_poster.py

Posts Tier 1 alerts to Twitter using Twitter API v1.1.
"""

import os
from typing import Dict, Optional

# Twitter API (using tweepy)
try:
    import tweepy
    TWITTER_AVAILABLE = True
except ImportError:
    TWITTER_AVAILABLE = False
    print("⚠️ tweepy not installed. Install with: pip install tweepy")

# ========== CONFIG ==========
# Twitter API v1.1 credentials
TWITTER_API_KEY = "MAq2wDIG92oJdpp1LZEoFGOT4"
TWITTER_API_SECRET = "Hy0kt1kl4kBrKdnxVqCCto47h1jnxJwIdAA3tPbI0UhI2XrjHZ"
TWITTER_ACCESS_TOKEN = "1483338975062675460-Zy5j6uhG1WY3hR0evpoMUZF7LcyJw3"
TWITTER_ACCESS_TOKEN_SECRET = "kRJzxp3LybaGbqgJH53ld6zvUA1lfo0r4OGM0g74uYOsr"
# ============================

class SocialMediaPoster:
    """Handle posting to Twitter"""
    
    def __init__(self):
        self.twitter_client = None
        self.twitter_enabled = False
        
        # Initialize Twitter
        if TWITTER_AVAILABLE and self._validate_twitter_credentials():
            try:
                # Use OAuth 1.0a for posting (v1.1 API)
                auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
                auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
                self.twitter_client = tweepy.API(auth, wait_on_rate_limit=True)
                self.twitter_enabled = True
                print("✅ Twitter API initialized")
            except Exception as e:
                print(f"⚠️ Twitter API initialization failed: {e}")
                import traceback
                traceback.print_exc()
        else:
            if not TWITTER_AVAILABLE:
                print("⚠️ tweepy not installed - Twitter posting disabled")
            else:
                print("⚠️ Twitter credentials not configured - Twitter posting disabled")
    
    def _validate_twitter_credentials(self) -> bool:
        """Validate Twitter credentials are set"""
        return all([
            TWITTER_API_KEY,
            TWITTER_API_SECRET,
            TWITTER_ACCESS_TOKEN,
            TWITTER_ACCESS_TOKEN_SECRET
        ])
    
    def format_twitter_alert(self, alert: Dict) -> str:
        """Format alert for Twitter (280 char limit)"""
        token = alert.get("token", "UNKNOWN")
        contract = alert.get("contract", "")
        tier = alert.get("tier", 1)
        multiplier = alert.get("cohort_multiplier", 2)
        current_mc = alert.get("mc_usd", 0)
        
        # Format market cap
        if current_mc:
            if current_mc >= 1_000_000:
                mc_str = f"${current_mc/1_000_000:.1f}M"
            elif current_mc >= 1_000:
                mc_str = f"${current_mc/1_000:.0f}K"
            else:
                mc_str = f"${current_mc:.0f}"
        else:
            mc_str = "N/A"
        
        # Build compact message
        contract_short = contract[:8] + "..." if contract and len(contract) > 8 else (contract if contract else "N/A")
        
        # Try to fit everything in 280 chars
        # Format: 🚀 TIER 1 ALERT 🚀\n\n{token} hit {multiplier}x on XTRACK\nMC: {mc}\nCA: {contract_short}\n\n📊 Chart link
        
        base_msg = f"🚀 TIER 1 ALERT 🚀\n\n{token} hit {multiplier}x on XTRACK\nMC: {mc_str}\nCA: {contract_short}"
        
        # Add DexScreener link if we have contract
        if contract:
            dexscreener_link = f"\n\n📊 https://dexscreener.com/solana/{contract}"
            if len(base_msg + dexscreener_link) <= 280:
                base_msg += dexscreener_link
        
        # Truncate if still too long
        if len(base_msg) > 280:
            # Remove some parts to fit
            base_msg = f"🚀 TIER 1 🚀\n{token} {multiplier}x XTRACK\nMC: {mc_str}\nCA: {contract_short}"
            if contract and len(base_msg + f"\n📊 https://dexscreener.com/solana/{contract}") <= 280:
                base_msg += f"\n📊 https://dexscreener.com/solana/{contract}"
        
        return base_msg[:280]
    
    async def post_to_twitter(self, alert: Dict) -> bool:
        """Post alert to Twitter"""
        if not self.twitter_enabled or not self.twitter_client:
            return False
        
        try:
            tweet_text = self.format_twitter_alert(alert)
            
            # Post tweet
            response = self.twitter_client.update_status(tweet_text)
            print(f"✅ Posted to Twitter: Tweet ID {response.id}")
            print(f"   Tweet: {tweet_text[:100]}...")
            return True
        except tweepy.TooManyRequests:
            print("⚠️ Twitter rate limit exceeded - skipping post")
            return False
        except tweepy.TweepyException as e:
            print(f"❌ Twitter API error: {e}")
            return False
        except Exception as e:
            print(f"❌ Error posting to Twitter: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def post_tier1_alert(self, alert: Dict) -> Dict[str, bool]:
        """Post Tier 1 alert to Twitter"""
        results = {
            "twitter": False
        }
        
        # Only post if it's actually Tier 1
        if alert.get("tier") != 1:
            print(f"⚠️ Alert is not Tier 1 (tier={alert.get('tier')}) - skipping Twitter post")
            return results
        
        print(f"\n📱 Posting Tier 1 alert to Twitter...")
        
        # Post to Twitter
        if self.twitter_enabled:
            results["twitter"] = await self.post_to_twitter(alert)
        
        return results




