#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
telegram_monitor_new.py

Live Telegram monitoring system using cohort-based scoring:
- Uses MessageParser for extraction
- Normalizes events and forwards to LiveMemecoinMonitor
- Scoring/alerts handled by live_monitor_core (2x/3x cohorts + corroboration)
"""

import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Dict, Optional

from telethon import TelegramClient, events
from telethon.errors import FloodWaitError, RPCError
from telethon.tl.types import ChannelParticipantsAdmins
from telethon.tl.custom import Button

from message_parser import MessageParser
from live_monitor_core import LiveMemecoinMonitor
from live_alert_formatter import format_alert
from dexscreener_fetcher import enrich_alert_with_live_data
from kpi_logger import KPILogger

# Debug logging helper (only logs if DEBUG_LOG_PATH is set)
def debug_log(data: dict):
    """Optional debug logging - only writes if DEBUG_LOG_PATH environment variable is set"""
    debug_log_path = os.getenv('DEBUG_LOG_PATH')
    if debug_log_path:
        try:
            with open(debug_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(data) + "\n")
        except Exception:
            pass  # Silently fail if can't write debug log

# ========== CONFIG ==========
API_ID = int(os.getenv('API_ID', '25177061'))
API_HASH = os.getenv('API_HASH', 'c11ea2f1db2aa742144dfa2a30448408')
SESSION_NAME = os.getenv('SESSION_NAME', 'blackhat_empire_session')

# Forum topics to monitor
FORUM_TOPICS = [
    {
        'group_id': -1002134751475,
        'group_title': 'Blackhat SOL Alerts',
        'thread_id': 3285418,
        'name': 'SOL SB1',
        'source': 'sol_sb1'
    },
    {
        'group_id': -1002134751475,
        'group_title': 'Blackhat SOL Alerts',
        'thread_id': 3285420,
        'name': 'SOL SB/MB',
        'source': 'sol_sb_mb'
    },
    {
        'group_id': -1002134751475,
        'group_title': 'Blackhat SOL Alerts',
        'thread_id': 3285422,
        'name': 'WhaleBuy',
        'source': 'whalebuy'
    },
    {
        'group_id': -1002134751475,
        'group_title': 'Blackhat SOL Alerts',
        'thread_id': 3791791,  # updated per link https://t.me/c/2134751475/3791791
        'name': 'XTRACK SOL NEW',
        'source': 'xtrack'
    },
    {
        'group_id': -1002195249735,
        'group_title': 'Orion Tracker',
        'thread_id': 8037,
        'name': 'Momentum Tracker',
        'source': 'momentum_tracker'
    },
    {
        'group_id': -1002195249735,
        'group_title': 'Orion Tracker',
        'thread_id': 8047,
        'name': 'Large Buys Tracker',
        'source': 'large_buys_tracker'
    },
]

# Channels to monitor
CHANNELS = [
    {
        'channel_id': -1002782074434,
        'channel_name': 'Glydo Alerts',
        'source': 'glydo'
    },
    {
        'channel_id': -1002225558516,
        'channel_name': 'pfbf volume alert',
        'source': 'pfbf_volume_alert'
    },
    {
        'channel_id': -1002050218130,
        'channel_name': 'call analyzer',
        'source': 'call_analyzer'
    },
    {
        'channel_id': -1002397610468,
        'channel_name': 'kolscope',
        'source': 'kolscope'
    },
    {
        'channel_id': -1001960616143,
        'channel_name': 'spydefi',
        'source': 'spydefi'
    },
    {
        'channel_id': -1002093384030,
        'channel_name': 'Solana Early Trending',
        'source': 'solana_early_trending'
    },
]

# Output files
STATE_FILE = "token_states.json"
AUTO_BUY_LOG = "auto_buy_signals.json"
SUBSCRIPTIONS_FILE = "subscriptions.json"  # Store subscribed user IDs

# Bot configuration for sending alerts
BOT_TOKEN = os.getenv('BOT_TOKEN', '8231103146:AAElHbn-WfOfafitmPGnDZ2WeA61HaAlXUA')  # Bot token for sending alerts
ALERT_CHAT_ID = None  # TODO: Set your chat/group ID here (see instructions below)

# To get your chat ID:
# 1. Add your bot to a group/channel
# 2. Send a message in that group/channel
# 3. Visit: https://api.telegram.org/bot<BOT_TOKEN>/getUpdates
# 4. Look for "chat":{"id":-1001234567890} - that's your ALERT_CHAT_ID
# OR use @userinfobot in the group to get the chat ID
# ============================

class TelegramMonitorNew:
    """New simplified Telegram monitor"""
    
    def __init__(self, client: TelegramClient, bot_client: TelegramClient = None, enrich_with_live_mcap: bool = True):
        self.client = client
        self.bot_client = bot_client  # Optional bot for sending alerts
        self.parser = MessageParser()
        self.monitor = LiveMemecoinMonitor()
        self.processed_messages = 0
        self.processed_message_ids = set()
        self.alert_chat_id = ALERT_CHAT_ID  # Keep for backward compatibility
        self.alert_groups = set()  # Set of group chat IDs to send alerts to
        self.subscribed_users = set()  # User IDs subscribed to alerts
        self.user_tier_preferences = {}  # Dict: user_id -> set of tiers they want (None = all tiers)
        self.group_tier_preferences = {}  # Dict: group_id -> set of tiers they want (None = all tiers)
        self.recent_alerts = {}  # Track recent alerts to prevent duplicates: (token, tier) -> timestamp
        self.enrich_with_live_mcap = enrich_with_live_mcap  # Enable live MCAP enrichment via DexScreener
        self.kpi_logger = KPILogger()  # KPI tracking
        self.load_subscriptions()
        self.load_alert_groups()  # Load saved group IDs
        self.load_user_preferences()  # Load user tier preferences
        self.load_group_preferences()  # Load group/channel tier preferences
    
    def message_to_dict(self, message) -> Dict:
        """Convert Telethon message to dict"""
        content = message.message or ''
        
        # Extract URLs from entities
        urls_from_entities = []
        if hasattr(message, 'entities') and message.entities:
            from telethon.tl.types import MessageEntityUrl, MessageEntityTextUrl
            for entity_obj in message.entities:
                if isinstance(entity_obj, MessageEntityUrl):
                    url = content[entity_obj.offset:entity_obj.offset + entity_obj.length]
                    urls_from_entities.append(url)
                elif isinstance(entity_obj, MessageEntityTextUrl):
                    urls_from_entities.append(entity_obj.url)

        # Extract URLs from inline buttons (SpyDefi often uses buttons)
        urls_from_buttons = []
        try:
            if getattr(message, "buttons", None):
                for row in message.buttons:
                    for btn in row:
                        btn_url = getattr(btn, "url", None)
                        if btn_url:
                            urls_from_buttons.append(btn_url)
        except Exception:
            pass

        # Also extract URLs from reply_markup (sometimes buttons aren't exposed via .buttons)
        urls_from_reply_markup = []
        try:
            rm = getattr(message, "reply_markup", None)
            if rm and getattr(rm, "rows", None):
                for row in rm.rows:
                    for btn in getattr(row, "buttons", []) or []:
                        btn_url = getattr(btn, "url", None)
                        if btn_url:
                            urls_from_reply_markup.append(btn_url)
        except Exception:
            pass
        
        # Combine text with URLs
        all_urls = []
        if urls_from_entities:
            all_urls.extend(urls_from_entities)
        if urls_from_buttons:
            all_urls.extend(urls_from_buttons)
        if urls_from_reply_markup:
            all_urls.extend(urls_from_reply_markup)
        if all_urls:
            content += '\n' + ' '.join(all_urls)
        
        # Build entities list
        entities = []
        if hasattr(message, 'entities') and message.entities:
            for entity_obj in message.entities:
                entity_dict = {
                    'type': type(entity_obj).__name__,
                    'offset': entity_obj.offset,
                    'length': entity_obj.length
                }
                if hasattr(entity_obj, 'url'):
                    entity_dict['url'] = entity_obj.url
                entities.append(entity_dict)
        
        msg_date = message.date
        if msg_date and msg_date.tzinfo is None:
            msg_date = msg_date.replace(tzinfo=timezone.utc)
        
        return {
            'id': message.id,
            'date_utc': msg_date.isoformat() if msg_date else datetime.now(timezone.utc).isoformat(),
            'content': content,
            'text': content,
            'entities': entities,
            'sender_id': message.sender_id,
        }
    
    async def process_message(self, message, source: str):
        """Process incoming message"""
        # #region agent log
        debug_log({"sessionId":"debug-session","runId":"run1","hypothesisId":"H1","location":"telegram_monitor_new.py:231","message":"process_message called","data":{"message_id":message.id,"source":source,"already_processed":message.id in self.processed_message_ids},"timestamp":int(datetime.now(timezone.utc).timestamp()*1000)})
        # #endregion
        # Canonicalize source names to match scoring engine
        def canonical(src: str) -> str:
            if src.startswith('xtrack'):
                return 'xtrack'
            if src.startswith('glydo'):
                return 'glydo'
            if src.startswith('sol_sb_mb'):
                return 'sol_sb_mb'
            if src.startswith('sol_sb1'):
                return 'sol_sb1'
            if src.startswith('whalebuy'):
                return 'whalebuy'
            if src.startswith('momentum'):
                return 'momentum_tracker'
            if src.startswith('large_buys'):
                return 'large_buys_tracker'
            if src.startswith('pfbf'):
                return 'pfbf_volume_alert'
            if src.startswith('call_analyzer'):
                return 'call_analyzer'
            if src.startswith('kolscope'):
                return 'kolscope'
            if src.startswith('spydefi'):
                return 'spydefi'
            if src.startswith('solana_early'):
                return 'solana_early_trending'
            return src
        source = canonical(source)
        # Skip if already processed
        if message.id in self.processed_message_ids:
            return
        
        self.processed_message_ids.add(message.id)
        self.processed_messages += 1
        
        # Convert to dict
        msg_dict = self.message_to_dict(message)
        content = msg_dict.get('content', '') or ''
        content_preview = content[:150] if content else '(empty)'
        
        # Log every message received
        print(f"\n[{source.upper():<15}] 📨 Message #{self.processed_messages} received")
        print(f"    Content: {content_preview}...")
        
        # Parse message with error handling
        try:
            parsed = self.parser.parse_message(msg_dict, source)
            if not parsed:
                reason_code = self.parser.diagnose_failure(msg_dict, source)
                print(f"[{source.upper():<15}] ❌ [PARSE FAILED:{reason_code}]")
                return
        except Exception as e:
            print(f"[{source.upper():<15}] ❌ [PARSE ERROR] {str(e)}")
            return

        # Validate parsed data
        if not parsed.symbol or parsed.symbol == "UNKNOWN":
            print(f"[{source.upper():<15}] ❌ [VALIDATION FAILED] Invalid symbol")
            return
        
        # Handle contract address validation
        contract = None
        if parsed.contract_address and not str(parsed.contract_address).startswith("GLYDO_"):
            if self.parser.is_valid_solana_address(parsed.contract_address):
                contract = parsed.contract_address
            else:
                print(f"[{source.upper():<15}] ⚠️  [INVALID CA] {parsed.contract_address[:20]}...")

        ca_short = contract[:8] + '...' if contract and len(contract) > 8 else (parsed.contract_address[:8] + '...' if parsed.contract_address else 'N/A')
        print(f"[{source.upper():<15}] ✅ [PARSED] {parsed.symbol} | CA: {ca_short}")

        info_parts = []
        if parsed.buy_size_sol:
            info_parts.append(f"Buy: {parsed.buy_size_sol:.2f} SOL")
        if parsed.market_cap:
            info_parts.append(f"MC: ${parsed.market_cap:,.0f}")
        if parsed.liquidity:
            info_parts.append(f"LP: ${parsed.liquidity:,.0f}")
        if parsed.xtrack_multiplier:
            info_parts.append(f"XTRACK: {parsed.xtrack_multiplier}x")
        if info_parts:
            print(f"    Details: {' | '.join(info_parts)}")

        # Normalize and ingest into new live monitor with error handling
        try:
            event = self.monitor.normalize_event(
                feed_name=source,
                message_id=str(message.id),
                timestamp=parsed.timestamp,
                token=parsed.symbol,
                contract=contract,
                raw_text=content,
                multiplier=parsed.xtrack_multiplier,
                mc_usd=parsed.market_cap,
                liquidity_usd=parsed.liquidity,
                buy_size_sol=parsed.buy_size_sol,  # Pass buy size from parsed message
            )
        except Exception as e:
            print(f"[{source.upper():<15}] ❌ [NORMALIZE ERROR] {str(e)}")
            return

        try:
            alerts = self.monitor.ingest_event(event)
            # #region agent log
            debug_log({"sessionId":"debug-session","runId":"run1","hypothesisId":"H1,H2","location":"telegram_monitor_new.py:335","message":"ingest_event returned alerts","data":{"alert_count":len(alerts),"message_id":message.id,"source":source,"alerts_tiers":[a.get("tier") for a in alerts]},"timestamp":int(datetime.now(timezone.utc).timestamp()*1000)})
            # #endregion
        except Exception as e:
            print(f"[{source.upper():<15}] ❌ [INGEST ERROR] {str(e)}")
            return
        for alert in alerts:
            # Deduplication: Check if we've sent this exact alert recently (same token + tier)
            token = alert.get("token") or "UNKNOWN"
            tier = alert.get("tier")
            alert_key = (token, tier)
            current_time = datetime.now(timezone.utc).timestamp()
            # #region agent log
            debug_log({"sessionId":"debug-session","runId":"run1","hypothesisId":"H2,H7,H10","location":"telegram_monitor_new.py:343","message":"Alert before deduplication check","data":{"token":token,"tier":tier,"alert_key":str(alert_key),"alert_id":alert.get("alert_id"),"alert_keys":list(alert.keys())},"timestamp":int(current_time*1000)})
            # #endregion
            
            # Check if we sent this alert in the last 5 minutes
            if alert_key in self.recent_alerts:
                last_sent = self.recent_alerts[alert_key]
                time_diff = current_time - last_sent
                if time_diff < 300:  # 5 minutes = 300 seconds
                    print(f"⚠️ Skipping duplicate alert for {token} TIER {tier} - sent {int(time_diff)}s ago")
                    # #region agent log
                    debug_log({"sessionId":"debug-session","runId":"run1","hypothesisId":"H1,H5","location":"telegram_monitor_new.py:351","message":"Duplicate alert detected and skipped","data":{"token":token,"tier":tier,"time_diff":time_diff,"alert_key":str(alert_key)},"timestamp":int(current_time*1000)})
                    # #endregion
                    continue
            
            # Mark this alert as sent
            self.recent_alerts[alert_key] = current_time
            # #region agent log
            debug_log({"sessionId":"debug-session","runId":"run1","hypothesisId":"H1","location":"telegram_monitor_new.py:355","message":"Alert marked as sent in recent_alerts","data":{"token":token,"tier":tier,"alert_key":str(alert_key),"recent_alerts_count":len(self.recent_alerts)},"timestamp":int(current_time*1000)})
            # #endregion
            
            # Cleanup old entries (older than 1 hour)
            cutoff = current_time - 3600
            self.recent_alerts = {k: v for k, v in self.recent_alerts.items() if v > cutoff}
            
            # Enrich with live MCAP/symbol from DexScreener if enabled
            current_mcap = None
            if self.enrich_with_live_mcap and alert.get("contract"):
                try:
                    enriched = enrich_alert_with_live_data(alert)
                    # Update alert with live data if available
                    if enriched.get("live_mcap") is not None:
                        current_mcap = enriched["live_mcap"]
                        alert["mc_usd"] = current_mcap
                        alert["mc_source"] = "dexscreener_live"
                        print(f"[DexScreener] Updated MCAP for {alert.get('token')}: ${current_mcap:,.2f}")
                    if enriched.get("live_symbol") and not alert.get("token"):
                        alert["token"] = enriched["live_symbol"]
                        print(f"[DexScreener] Updated symbol: {enriched['live_symbol']}")
                    if enriched.get("live_liquidity") is not None:
                        alert["liq_usd"] = enriched["live_liquidity"]
                except Exception as e:
                    # Don't fail alerts if DexScreener API fails
                    print(f"[DexScreener] Warning: Could not enrich alert: {e}")
            
            # MCAP Filter: Skip alerts if current MCAP > 500k
            if current_mcap is None:
                # Fallback to alert's MCAP if enrichment failed
                current_mcap = alert.get("mc_usd") or alert.get("market_cap")
            
            if current_mcap and current_mcap > 500000:  # 500k threshold
                print(f"⏭️ Skipping alert for {token} - Current MCAP ${current_mcap:,.0f} exceeds 500k threshold")
                continue  # Skip this alert
            
            # CRITICAL: Get the Current MCAP that will be shown in the Telegram post
            # This must be done BEFORE formatting the message, so we save the correct value
            # The format_alert function uses _get_current_mc() which prefers live_mcap -> mc_usd -> entry_mc
            from live_alert_formatter import _get_current_mc
            current_mc_shown = _get_current_mc(alert)  # This is what will be displayed in Telegram
            if current_mc_shown is not None:
                alert["current_mcap"] = current_mc_shown  # Save the MCAP that will be shown
                alert["current_mcap_source"] = alert.get("mc_source", "unknown")  # Track source
                print(f"📊 Current MCAP ({alert.get('current_mcap_source', 'unknown')}): ${current_mc_shown:,.0f}")
            
            # Log alert for KPI tracking (NOW with correct current_mcap)
            level = alert.get("level", "MEDIUM")
            self.kpi_logger.log_alert(alert, level)
            
            # Pass weights for tagline selection
            weights = self.monitor.weights if hasattr(self.monitor, 'weights') else None
            alert_message = format_alert(alert, weights=weights)
            print(f"\n{'='*80}")
            print(alert_message)
            print(f"{'='*80}\n")
            if self.bot_client:
                # #region agent log
                debug_log({"sessionId":"debug-session","runId":"run1","hypothesisId":"H3","location":"telegram_monitor_new.py:390","message":"Calling send_telegram_alert","data":{"token":token,"tier":tier,"alert_id":alert.get("alert_id")},"timestamp":int(datetime.now(timezone.utc).timestamp()*1000)})
                # #endregion
                await self.send_telegram_alert(alert_message, alert=alert)
    
    async def send_telegram_alert(self, alert_message: str, alert: Dict = None):
        """Send formatted alert to Telegram with tier filtering"""
        if not self.bot_client:
            print("⚠️ Bot client not initialized - alert not sent")
            return
        
        # Extract tier from alert if provided
        alert_tier = None
        if alert:
            alert_tier = alert.get("tier")
        # #region agent log
        debug_log({"sessionId":"debug-session","runId":"run1","hypothesisId":"H7,H10","location":"telegram_monitor_new.py:401","message":"send_telegram_alert entry","data":{"alert_tier":alert_tier,"alert_keys":list(alert.keys()) if alert else None,"alert_meta_tier":alert.get("meta",{}).get("tier") if alert and isinstance(alert.get("meta"),dict) else None},"timestamp":int(datetime.now(timezone.utc).timestamp()*1000)})
        # #endregion
        
        sent_count = 0
        
        # Send to configured alert groups/channels with tier filtering
        if self.alert_groups:
            for group_id in self.alert_groups:
                # Check if group/channel has tier preferences
                group_tiers = self.group_tier_preferences.get(group_id)
                # #region agent log
                debug_log({"sessionId":"debug-session","runId":"run1","hypothesisId":"H6,H8,H9","location":"telegram_monitor_new.py:409","message":"Checking group tier preferences","data":{"group_id":group_id,"group_tiers":list(group_tiers) if group_tiers else None,"alert_tier":alert_tier,"all_group_prefs":{str(k):list(v) if v else None for k,v in self.group_tier_preferences.items()}},"timestamp":int(datetime.now(timezone.utc).timestamp()*1000)})
                # #endregion
                
                # STRICT FILTERING: If group has preferences set, ONLY send alerts matching those tiers
                # Alerts without a tier (alert_tier is None) should be filtered out if preferences are set
                should_send = True
                if group_tiers is not None and len(group_tiers) > 0:
                    # Group has specific tier preferences - STRICT MODE
                    # Only send if alert has a tier AND tier is in group's preferences
                    if alert_tier is None or alert_tier not in group_tiers:
                        should_send = False
                # #region agent log
                debug_log({"sessionId":"debug-session","runId":"run1","hypothesisId":"H9","location":"telegram_monitor_new.py:417","message":"Group tier filtering decision","data":{"group_id":group_id,"should_send":should_send,"alert_tier":alert_tier,"group_tiers":list(group_tiers) if group_tiers else None},"timestamp":int(datetime.now(timezone.utc).timestamp()*1000)})
                # #endregion
                
                if should_send:
                    try:
                        # #region agent log
                        debug_log({"sessionId":"debug-session","runId":"run1","hypothesisId":"H3,H4","location":"telegram_monitor_new.py:421","message":"Sending alert to group","data":{"group_id":group_id,"alert_tier":alert_tier,"token":alert.get("token") if alert else None},"timestamp":int(datetime.now(timezone.utc).timestamp()*1000)})
                        # #endregion
                        await self.bot_client.send_message(
                            group_id,
                            alert_message,
                            parse_mode='Markdown',
                            link_preview=False
                        )
                        sent_count += 1
                        print(f"✅ Alert sent to group/channel {group_id}")
                    except Exception as e:
                        print(f"❌ Failed to send to group {group_id}: {e}")
                        # Remove invalid group (bot removed or no permission)
                        self.alert_groups.discard(group_id)
                        self.save_alert_groups()
                else:
                    print(f"⏭️ Skipped group/channel {group_id} - tier {alert_tier} not in preferences {group_tiers}")
        
        # Send to subscribed users with tier filtering
        # IMPORTANT: Skip users who are in groups that already received the alert to prevent duplicates
        if self.subscribed_users:
            for user_id in self.subscribed_users:
                # Check if this user is in any of the alert groups (to prevent duplicate alerts)
                # If the alert was already sent to a group the user is in, skip sending to user
                user_in_group = False
                if self.alert_groups:
                    # Note: We can't easily check if user is in group without API call
                    # Instead, we'll rely on the user to not be subscribed if they're in a group
                    # But we can add a check: if user_id matches a group_id (shouldn't happen, but safety check)
                    if user_id in self.alert_groups:
                        user_in_group = True
                
                # Skip if user is in a group that already received the alert
                # (This prevents duplicate alerts when user is both subscribed and in a group)
                if user_in_group:
                    # #region agent log
                    debug_log({"sessionId":"debug-session","runId":"run1","hypothesisId":"H4","location":"telegram_monitor_new.py:491","message":"Skipping user - already in group that received alert","data":{"user_id":user_id,"alert_tier":alert_tier},"timestamp":int(datetime.now(timezone.utc).timestamp()*1000)})
                    # #endregion
                    continue
                
                # Check if user has tier preferences
                user_tiers = self.user_tier_preferences.get(user_id)
                # #region agent log
                debug_log({"sessionId":"debug-session","runId":"run1","hypothesisId":"H6,H8,H9","location":"telegram_monitor_new.py:500","message":"Checking user tier preferences","data":{"user_id":user_id,"user_tiers":list(user_tiers) if user_tiers else None,"alert_tier":alert_tier,"all_user_prefs":{str(k):list(v) if v else None for k,v in self.user_tier_preferences.items()}},"timestamp":int(datetime.now(timezone.utc).timestamp()*1000)})
                # #endregion
                
                # STRICT FILTERING: If user has preferences set, ONLY send alerts matching those tiers
                # Alerts without a tier (alert_tier is None) should be filtered out if preferences are set
                should_send = True
                if user_tiers is not None and len(user_tiers) > 0:
                    # User has specific tier preferences - STRICT MODE
                    # Only send if alert has a tier AND tier is in user's preferences
                    if alert_tier is None or alert_tier not in user_tiers:
                        should_send = False
                # #region agent log
                debug_log({"sessionId":"debug-session","runId":"run1","hypothesisId":"H9","location":"telegram_monitor_new.py:512","message":"User tier filtering decision","data":{"user_id":user_id,"should_send":should_send,"alert_tier":alert_tier,"user_tiers":list(user_tiers) if user_tiers else None},"timestamp":int(datetime.now(timezone.utc).timestamp()*1000)})
                # #endregion
                
                if should_send:
                    try:
                        # #region agent log
                        debug_log({"sessionId":"debug-session","runId":"run1","hypothesisId":"H3,H4","location":"telegram_monitor_new.py:516","message":"Sending alert to user","data":{"user_id":user_id,"alert_tier":alert_tier,"token":alert.get("token") if alert else None},"timestamp":int(datetime.now(timezone.utc).timestamp()*1000)})
                        # #endregion
                        await self.bot_client.send_message(
                            user_id,
                            alert_message,
                            parse_mode='Markdown',
                            link_preview=False
                        )
                        sent_count += 1
                    except Exception as e:
                        print(f"❌ Failed to send to user {user_id}: {e}")
                        # Remove invalid user from subscriptions
                        self.subscribed_users.discard(user_id)
                        self.save_subscriptions()
        
        if sent_count > 0:
            print(f"✅ Alert sent to {sent_count} destination(s) ({len(self.alert_groups)} groups, {len(self.subscribed_users)} users)")
        
        if sent_count == 0:
            print("⚠️ No valid alert destinations - alert not sent")
            print("   Add bot to a group as admin, or use /subscribe to receive alerts")
    
    def load_subscriptions(self):
        """Load subscribed users from file"""
        if os.path.exists(SUBSCRIPTIONS_FILE):
            try:
                with open(SUBSCRIPTIONS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.subscribed_users = set(data.get('users', []))
                    print(f"📋 Loaded {len(self.subscribed_users)} subscribed user(s)")
            except Exception as e:
                print(f"⚠️ Failed to load subscriptions: {e}")
                self.subscribed_users = set()
        else:
            self.subscribed_users = set()
    
    def save_subscriptions(self):
        """Save subscribed users to file"""
        try:
            with open(SUBSCRIPTIONS_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    'last_updated': datetime.now(timezone.utc).isoformat(),
                    'users': list(self.subscribed_users)
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Failed to save subscriptions: {e}")
    
    def load_user_preferences(self):
        """Load user tier preferences from file"""
        PREFERENCES_FILE = "user_preferences.json"
        if os.path.exists(PREFERENCES_FILE):
            try:
                with open(PREFERENCES_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Convert stored lists back to sets
                    for user_id_str, tiers_list in data.get('preferences', {}).items():
                        user_id = int(user_id_str)
                        if tiers_list is None:
                            self.user_tier_preferences[user_id] = None  # All tiers
                        else:
                            self.user_tier_preferences[user_id] = set(tiers_list)
                    print(f"📋 Loaded tier preferences for {len(self.user_tier_preferences)} user(s)")
            except Exception as e:
                print(f"⚠️ Failed to load user preferences: {e}")
                self.user_tier_preferences = {}
        else:
            self.user_tier_preferences = {}
    
    def save_user_preferences(self):
        """Save user tier preferences to file"""
        PREFERENCES_FILE = "user_preferences.json"
        try:
            # Convert sets to lists for JSON serialization
            preferences_dict = {}
            for user_id, tiers_set in self.user_tier_preferences.items():
                if tiers_set is None:
                    preferences_dict[str(user_id)] = None
                else:
                    preferences_dict[str(user_id)] = list(tiers_set)
            
            with open(PREFERENCES_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    'last_updated': datetime.now(timezone.utc).isoformat(),
                    'preferences': preferences_dict
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Failed to save user preferences: {e}")
    
    def load_group_preferences(self):
        """Load group/channel tier preferences from file"""
        GROUP_PREFERENCES_FILE = "group_preferences.json"
        if os.path.exists(GROUP_PREFERENCES_FILE):
            try:
                with open(GROUP_PREFERENCES_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Convert stored lists back to sets
                    for group_id_str, tiers_list in data.get('preferences', {}).items():
                        group_id = int(group_id_str)
                        if tiers_list is None:
                            self.group_tier_preferences[group_id] = None  # All tiers
                        else:
                            self.group_tier_preferences[group_id] = set(tiers_list)
                    print(f"📋 Loaded tier preferences for {len(self.group_tier_preferences)} group/channel(s)")
            except Exception as e:
                print(f"⚠️ Failed to load group preferences: {e}")
                self.group_tier_preferences = {}
        else:
            self.group_tier_preferences = {}
        
        # MIGRATION: Check if any group IDs are in user_preferences.json and move them
        # This fixes the bug where group preferences were saved to the wrong file
        PREFERENCES_FILE = "user_preferences.json"
        if os.path.exists(PREFERENCES_FILE):
            try:
                with open(PREFERENCES_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    preferences = data.get('preferences', {})
                    migrated = False
                    # Check each preference - if the key is a group ID (negative number), migrate it
                    for key_str, tiers_list in list(preferences.items()):
                        try:
                            key_id = int(key_str)
                            # Group IDs are typically negative (e.g., -1001449259153)
                            # User IDs are typically positive
                            if key_id < 0 and key_id not in self.group_tier_preferences:
                                # This is a group ID in user_preferences - migrate it
                                if tiers_list is None:
                                    self.group_tier_preferences[key_id] = None
                                else:
                                    self.group_tier_preferences[key_id] = set(tiers_list)
                                # Remove from user_preferences
                                del preferences[key_str]
                                migrated = True
                                print(f"📋 Migrated group preference for {key_id} from user_preferences.json to group_preferences.json")
                        except (ValueError, TypeError):
                            pass
                    
                    # Save updated user_preferences if migration occurred
                    if migrated:
                        with open(PREFERENCES_FILE, 'w', encoding='utf-8') as f:
                            json.dump({
                                'last_updated': datetime.now(timezone.utc).isoformat(),
                                'preferences': preferences
                            }, f, indent=2, ensure_ascii=False)
                        # Save group preferences
                        self.save_group_preferences()
            except Exception as e:
                print(f"⚠️ Failed to migrate group preferences: {e}")
    
    def save_group_preferences(self):
        """Save group/channel tier preferences to file"""
        GROUP_PREFERENCES_FILE = "group_preferences.json"
        try:
            # Convert sets to lists for JSON serialization
            preferences_dict = {}
            for group_id, tiers_set in self.group_tier_preferences.items():
                if tiers_set is None:
                    preferences_dict[str(group_id)] = None
                else:
                    preferences_dict[str(group_id)] = list(tiers_set)
            
            with open(GROUP_PREFERENCES_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    'last_updated': datetime.now(timezone.utc).isoformat(),
                    'preferences': preferences_dict
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Failed to save group preferences: {e}")
    
    def load_alert_groups(self):
        """Load alert group chat IDs from file"""
        ALERT_GROUPS_FILE = "alert_groups.json"
        if os.path.exists(ALERT_GROUPS_FILE):
            try:
                with open(ALERT_GROUPS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.alert_groups = set(data.get('groups', []))
                    print(f"📋 Loaded {len(self.alert_groups)} alert group(s)")
            except Exception as e:
                print(f"⚠️ Failed to load alert groups: {e}")
                self.alert_groups = set()
        else:
            self.alert_groups = set()
        
        # Also add the hardcoded ALERT_CHAT_ID if set (for backward compatibility)
        if self.alert_chat_id:
            self.alert_groups.add(self.alert_chat_id)
    
    def save_alert_groups(self):
        """Save alert group chat IDs to file"""
        ALERT_GROUPS_FILE = "alert_groups.json"
        try:
            with open(ALERT_GROUPS_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    'last_updated': datetime.now(timezone.utc).isoformat(),
                    'groups': list(self.alert_groups)
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Failed to save alert groups: {e}")
    
    async def setup_bot_handlers(self):
        """Setup bot command handlers for subscriptions"""
        if not self.bot_client:
            print("⚠️ Bot client not available - command handlers not set up")
            return

        # Handle all incoming messages and check for commands
        @self.bot_client.on(events.NewMessage(incoming=True))
        async def command_handler(event):
            message_text = (event.message.message or "").strip()
            if not message_text.startswith('/'):
                return  # Not a command, skip
            
            # Extract command (handle /command@botname format)
            command = message_text.split()[0].split('@')[0].lower()
            
            try:
                print(f"📥 [BOT] Received command '{command}' from user {event.sender_id} in chat {event.chat_id}")
                
                if command == '/start':
                    print(f"📥 [BOT] Processing /start from user {event.sender_id}")
                    welcome_msg = (
                        "🚀 **@solboy_calls**\n\n"
                        
                        "**About me:**\n"
                        "Been in the Solana memecoin space since the early days. I've seen the cycles, the pumps, the rugs, and everything in between. Over time, I've built a system that filters through the noise to find real opportunities.\n\n"
                        
                        "**My approach:**\n"
                        "I don't call everything. I wait for multiple sources to align — when XTRACK, Glydo, whale wallets, and momentum all point in the same direction. That's when I know it's worth your attention.\n\n"
                        
                        "**What you'll get:**\n"
                        "• **TIER 1 ULTRA** 🚀 — My highest conviction plays\n"
                        "• **TIER 2 HIGH** 🔥 — Strong setups with solid confirmations\n"
                        "• **TIER 3 MEDIUM** ⚡ — Good opportunities worth watching\n\n"
                        
                        "📖 **Complete Trading Guide:**\n"
                        "[Read the Alert Pipeline Guide](https://telegra.ph/Solboy-Alert-Pipeline--Complete-Trading-Guide-12-23)\n\n"
                        
                        "**Quick Actions:**\n"
                        "Use the buttons below to subscribe or add your group/channel to receive alerts.\n\n"
                        
                        "— [Join my channel](https://t.me/solboy_calls)"
                    )
                    # Create inline keyboard buttons
                    buttons = [
                        [Button.inline("✅ Subscribe", b"subscribe"),
                         Button.inline("❌ Unsubscribe", b"unsubscribe")],
                        [Button.inline("➕ Add Group", b"add_group"),
                         Button.inline("➕ Add Channel", b"add_channel")],
                        [Button.inline("📋 My Groups/Channels", b"list_groups"),
                         Button.inline("ℹ️ Help", b"help")]
                    ]
                    await event.respond(welcome_msg, parse_mode='Markdown', link_preview=False, buttons=buttons)
                    return
                
                elif command == '/subscribe':
                    user_id = event.sender_id
                    print(f"📥 [BOT] Processing /subscribe from user {user_id}")
                    if user_id in self.subscribed_users:
                        await event.respond("✅ You're already subscribed! You'll receive all alerts.", parse_mode='Markdown')
                    else:
                        self.subscribed_users.add(user_id)
                        self.save_subscriptions()
                        await event.respond(
                            "✅ **Subscribed!**\n\n"
                            "You'll now receive real-time trading alerts when high-quality signals are detected.\n\n"
                            "Use /unsubscribe to stop receiving alerts.",
                            parse_mode='Markdown'
                        )
                        print(f"📝 User {user_id} subscribed to alerts (total: {len(self.subscribed_users)})")
                    return
                
                elif command == '/unsubscribe':
                    user_id = event.sender_id
                    if user_id in self.subscribed_users:
                        self.subscribed_users.discard(user_id)
                        self.save_subscriptions()
                        await event.respond("❌ **Unsubscribed.**\n\nYou won't receive alerts anymore. Use /subscribe to re-enable.", parse_mode='Markdown')
                        print(f"📝 User {user_id} unsubscribed from alerts")
                    else:
                        await event.respond("ℹ️ You're not subscribed. Use /subscribe to start receiving alerts.", parse_mode='Markdown')
                    return
                
                elif command == '/status':
                    user_id = event.sender_id
                    if user_id in self.subscribed_users:
                        # Get tier preferences
                        user_tiers = self.user_tier_preferences.get(user_id)
                        tier_emojis = {1: "🚀", 2: "🔥", 3: "⚡"}
                        
                        if user_tiers is None or len(user_tiers) == 0:
                            tier_info = "All tiers (TIER 1 🚀, TIER 2 🔥, TIER 3 ⚡)"
                        else:
                            tier_names = []
                            for t in sorted(user_tiers):
                                tier_names.append(f"TIER {t} {tier_emojis.get(t, '')}")
                            tier_info = ", ".join(tier_names)
                        
                        await event.respond(
                            f"✅ **Status: Subscribed**\n\n"
                            f"You're receiving alerts.\n"
                            f"**Tier preferences:** {tier_info}\n\n"
                            f"Total subscribers: {len(self.subscribed_users)}\n\n"
                            f"Use `/set all` to receive all tiers, or `/set t1,t2` to customize.\n"
                            f"Use /unsubscribe to stop.",
                            parse_mode='Markdown'
                        )
                    else:
                        await event.respond(
                            "❌ **Status: Not Subscribed**\n\n"
                            "Use /subscribe to start receiving alerts.",
                            parse_mode='Markdown'
                        )
                    return
                
                elif command == '/help':
                    welcome_msg = (
                        "🚀 **@solboy_calls**\n\n"
                        
                        "**About me:**\n"
                        "Been in the Solana memecoin space since the early days. I've seen the cycles, the pumps, the rugs, and everything in between. Over time, I've built a system that filters through the noise to find real opportunities.\n\n"
                        
                        "**My approach:**\n"
                        "I don't call everything. I wait for multiple sources to align — when XTRACK, Glydo, whale wallets, and momentum all point in the same direction. That's when I know it's worth your attention.\n\n"
                        
                        "**What you'll get:**\n"
                        "• **TIER 1 ULTRA** 🚀 — My highest conviction plays\n"
                        "• **TIER 2 HIGH** 🔥 — Strong setups with solid confirmations\n"
                        "• **TIER 3 MEDIUM** ⚡ — Good opportunities worth watching\n\n"
                        
                        "**⚡ Commands:**\n"
                        "`/subscribe` — Get my alerts\n"
                        "`/unsubscribe` — Stop alerts\n"
                        "`/status` — Check subscription\n"
                        "`/addgroup` — Add group (admin only)\n"
                        "`/addchannel` — Add channel (admin only)\n"
                        "`/removegroup` — Remove group/channel (admin only)\n"
                        "`/groups` — List alert groups/channels\n"
                        "`/help` — Show this again\n\n"
                        
                        "📖 **Complete Trading Guide:**\n"
                        "[Read the Alert Pipeline Guide](https://telegra.ph/Solboy-Alert-Pipeline--Complete-Trading-Guide-12-23)\n\n"
                        
                        "**💡 Quick Actions:**\n"
                        "Use the buttons below for quick access.\n\n"
                        
                        "— [Join my channel](https://t.me/solboy_calls)"
                    )
                    # Create inline keyboard buttons
                    buttons = [
                        [Button.inline("✅ Subscribe", b"subscribe"),
                         Button.inline("❌ Unsubscribe", b"unsubscribe")],
                        [Button.inline("➕ Add Group", b"add_group"),
                         Button.inline("➕ Add Channel", b"add_channel")],
                        [Button.inline("📋 My Groups/Channels", b"list_groups"),
                         Button.inline("ℹ️ Help", b"help")]
                    ]
                    await event.respond(welcome_msg, parse_mode='Markdown', link_preview=False, buttons=buttons)
                    return
                
                elif command == '/addgroup':
                    chat_id = event.chat_id
                    chat = await event.get_chat()
                    
                    # Only works in groups
                    is_group = hasattr(chat, 'megagroup') or (hasattr(chat, 'broadcast') and not chat.broadcast)
                    if not is_group:
                        await event.respond("❌ This command only works in groups. Use /addchannel for channels.", parse_mode='Markdown')
                        return
                    
                    # Check if user is admin
                    try:
                        admins = await self.bot_client.get_participants(chat, filter=ChannelParticipantsAdmins)
                        user_is_admin = any(p.id == event.sender_id for p in admins)
                        if not user_is_admin:
                            await event.respond("❌ Only group admins can use this command.", parse_mode='Markdown')
                            return
                    except:
                        pass  # Allow if can't check
                    
                    if chat_id not in self.alert_groups:
                        self.alert_groups.add(chat_id)
                        self.save_alert_groups()
                        chat_title = getattr(chat, 'title', f'Group {chat_id}')
                        await event.respond(
                            f"✅ **Group Added!**\n\n"
                            f"Alerts will now be sent to this group: {chat_title}\n\n"
                            f"Use /removegroup to stop alerts.",
                            parse_mode='Markdown'
                        )
                        print(f"📝 Group {chat_id} ({chat_title}) added to alert destinations")
                    else:
                        await event.respond("ℹ️ This group is already receiving alerts.", parse_mode='Markdown')
                    return
                
                elif command == '/addchannel':
                    chat_id = event.chat_id
                    chat = await event.get_chat()
                    
                    # Only works in channels
                    is_channel = hasattr(chat, 'broadcast') and chat.broadcast
                    if not is_channel:
                        await event.respond("❌ This command only works in channels. Use /addgroup for groups.", parse_mode='Markdown')
                        return
                    
                    # Check if user is admin
                    try:
                        admins = await self.bot_client.get_participants(chat, filter=ChannelParticipantsAdmins)
                        user_is_admin = any(p.id == event.sender_id for p in admins)
                        if not user_is_admin:
                            await event.respond("❌ Only channel admins can use this command.", parse_mode='Markdown')
                            return
                    except:
                        pass  # Allow if can't check
                    
                    if chat_id not in self.alert_groups:
                        self.alert_groups.add(chat_id)
                        self.save_alert_groups()
                        chat_title = getattr(chat, 'title', f'Channel {chat_id}')
                        await event.respond(
                            f"✅ **Channel Added!**\n\n"
                            f"Alerts will now be sent to this channel: {chat_title}\n\n"
                            f"Use /removegroup to stop alerts.",
                            parse_mode='Markdown'
                        )
                        print(f"📝 Channel {chat_id} ({chat_title}) added to alert destinations")
                    else:
                        await event.respond("ℹ️ This channel is already receiving alerts.", parse_mode='Markdown')
                    return
                
                elif command == '/removegroup':
                    chat_id = event.chat_id
                    chat = await event.get_chat()
                    
                    if chat_id in self.alert_groups:
                        self.alert_groups.discard(chat_id)
                        self.save_alert_groups()
                        chat_title = getattr(chat, 'title', f'Group {chat_id}')
                        await event.respond(
                            f"❌ **Group Removed**\n\n"
                            f"This group will no longer receive alerts.\n\n"
                            f"Use /addgroup to re-enable.",
                            parse_mode='Markdown'
                        )
                        print(f"📝 Group {chat_id} ({chat_title}) removed from alert destinations")
                    else:
                        await event.respond("ℹ️ This group is not receiving alerts.", parse_mode='Markdown')
                    return
                
                elif command == '/groups':
                    if not self.alert_groups:
                        await event.respond(
                            "📋 **Alert Groups:**\n\n"
                            "No groups configured.\n\n"
                            "Add bot to a group as admin, or use /addgroup in a group.",
                            parse_mode='Markdown'
                        )
                    else:
                        groups_list = []
                        for group_id in self.alert_groups:
                            try:
                                chat = await self.bot_client.get_entity(group_id)
                                title = getattr(chat, 'title', f'Group {group_id}')
                                groups_list.append(f"• {title} (ID: {group_id})")
                            except:
                                groups_list.append(f"• Group {group_id} (unknown)")
                        
                        await event.respond(
                            f"📋 **Alert Groups ({len(self.alert_groups)}):**\n\n" + "\n".join(groups_list),
                            parse_mode='Markdown'
                        )
                    return
                
                elif command.startswith('/set'):
                    user_id = event.sender_id
                    chat_id = event.chat_id
                    chat = await event.get_chat()
                    
                    # Check if command is from a group/channel or private chat
                    is_group = hasattr(chat, 'megagroup') or (hasattr(chat, 'broadcast') and not chat.broadcast)
                    is_channel = hasattr(chat, 'broadcast') and chat.broadcast
                    is_private = not is_group and not is_channel
                    
                    # Parse command: /set t1 or /set t1,t2 or /set all
                    parts = message_text.split()
                    if len(parts) < 2:
                        if is_private:
                            await event.respond(
                                "❌ **Invalid format.**\n\n"
                                "**Usage:**\n"
                                "`/set 1` or `/set t1` — Receive only TIER 1 alerts\n"
                                "`/set 2` or `/set t2` — Receive only TIER 2 alerts\n"
                                "`/set 3` or `/set t3` — Receive only TIER 3 alerts\n"
                                "`/set 1,2` or `/set t1,t2` — Receive TIER 1 and TIER 2 alerts\n"
                                "`/set all` — Receive all tier alerts (default)\n\n"
                                "**Examples:**\n"
                                "`/set 1` or `/set t1`\n"
                                "`/set 1,2` or `/set t1,t2`\n"
                                "`/set all`",
                                parse_mode='Markdown'
                            )
                        else:
                            await event.respond(
                                "❌ **Invalid format.**\n\n"
                                "**Usage:**\n"
                                "`/set 1` or `/set t1` — This group/channel receives only TIER 1 alerts\n"
                                "`/set 1,2` or `/set t1,t2` — This group/channel receives TIER 1 and TIER 2 alerts\n"
                                "`/set all` — This group/channel receives all tier alerts (default)\n\n"
                                "**Note:** Only admins can set tier preferences for groups/channels.",
                                parse_mode='Markdown'
                            )
                        return
                    
                    tier_arg = parts[1].lower().strip()
                    
                    # Handle group/channel tier preferences
                    if is_group or is_channel:
                        # Check if group/channel is added first
                        if chat_id not in self.alert_groups:
                            await event.respond(
                                "❌ **This group/channel is not receiving alerts.**\n\n"
                                "Use `/addgroup` or `/addchannel` first, then set tier preferences.",
                                parse_mode='Markdown'
                            )
                            return
                        
                        # If group is already added, allow tier preferences to be set
                        # (More lenient - if someone added the group, they can set preferences)
                        # Only check admin if we can, but don't block if check fails
                        user_is_admin = False
                        try:
                            admins = await self.bot_client.get_participants(chat, filter=ChannelParticipantsAdmins)
                            user_is_admin = any(p.id == user_id for p in admins)
                        except Exception as e:
                            # If we can't check admins (permission issue, etc.), allow the command
                            print(f"⚠️ Could not check admin status for user {user_id} in chat {chat_id}: {e}")
                            user_is_admin = True  # Allow if check fails
                        
                        # Only deny if we successfully checked AND user is not admin
                        # If check failed, we allow (more lenient)
                        if not user_is_admin:
                            # Try one more time with a different method
                            try:
                                # Check if bot is admin and can see admins
                                bot_me = await self.bot_client.get_me()
                                bot_admins = await self.bot_client.get_participants(chat, filter=ChannelParticipantsAdmins)
                                user_is_admin = any(p.id == user_id for p in bot_admins)
                                if not user_is_admin:
                                    await event.respond("❌ Only admins can set tier preferences for groups/channels.", parse_mode='Markdown')
                                    return
                            except:
                                # If all checks fail, allow anyway (user added the group, so they should be able to set preferences)
                                print(f"⚠️ Admin check failed for user {user_id}, but allowing since group is already added")
                                pass  # Allow the command
                        
                        # Parse tier preferences for group/channel
                        if tier_arg == 'all':
                            # Remove preferences (get all alerts)
                            if chat_id in self.group_tier_preferences:
                                del self.group_tier_preferences[chat_id]
                            self.save_group_preferences()
                            chat_title = getattr(chat, 'title', f'Group/Channel {chat_id}')
                            await event.respond(
                                f"✅ **Tier preference updated for {chat_title}!**\n\n"
                                f"This group/channel will now receive **all tier alerts** (TIER 1, 2, and 3).",
                                parse_mode='Markdown'
                            )
                        else:
                            # Parse tier numbers
                            tier_numbers = []
                            for part in tier_arg.split(','):
                                part = part.strip()
                                if part.startswith('t'):
                                    try:
                                        tier_num = int(part[1:])
                                        if tier_num in [1, 2, 3]:
                                            tier_numbers.append(tier_num)
                                    except ValueError:
                                        pass
                            
                            if not tier_numbers:
                                await event.respond(
                                    "❌ **Invalid tier format.**\n\n"
                                    "**Usage:**\n"
                                    "`/set t1` — Receive only TIER 1 alerts\n"
                                    "`/set t1,t2` — Receive TIER 1 and TIER 2 alerts\n"
                                    "`/set all` — Receive all tier alerts",
                                    parse_mode='Markdown'
                                )
                                return
                            
                            # Save preferences
                            self.group_tier_preferences[chat_id] = set(tier_numbers)
                            self.save_group_preferences()
                            
                            tier_names = []
                            tier_emojis = {1: "🚀", 2: "🔥", 3: "⚡"}
                            for t in sorted(tier_numbers):
                                tier_names.append(f"TIER {t} {tier_emojis.get(t, '')}")
                            
                            chat_title = getattr(chat, 'title', f'Group/Channel {chat_id}')
                            await event.respond(
                                f"✅ **Tier preference updated for {chat_title}!**\n\n"
                                f"This group/channel will now receive only: {', '.join(tier_names)}\n\n"
                                f"Use `/set all` to receive all tier alerts again.",
                                parse_mode='Markdown'
                            )
                            print(f"📝 Group/Channel {chat_id} ({chat_title}) set tier preferences: {tier_numbers}")
                    else:
                        # Handle user tier preferences (private chat)
                        # Check if user is subscribed
                        if user_id not in self.subscribed_users:
                            await event.respond(
                                "❌ **You're not subscribed.**\n\n"
                                "Use `/subscribe` first, then set your tier preferences.",
                                parse_mode='Markdown'
                            )
                            return
                        
                        # Parse tier preferences
                        if tier_arg == 'all':
                            # Remove preferences (get all alerts)
                            if user_id in self.user_tier_preferences:
                                del self.user_tier_preferences[user_id]
                            self.save_user_preferences()
                            await event.respond(
                                "✅ **Tier preference updated!**\n\n"
                                "You'll now receive **all tier alerts** (TIER 1, 2, and 3).",
                                parse_mode='Markdown'
                            )
                        else:
                            # Parse tier numbers - support both /set 1 and /set t1 formats
                            tier_numbers = []
                            for part in tier_arg.split(','):
                                part = part.strip()
                                # Support both formats: "t1" or just "1"
                                if part.startswith('t'):
                                    try:
                                        tier_num = int(part[1:])
                                        if tier_num in [1, 2, 3]:
                                            tier_numbers.append(tier_num)
                                    except ValueError:
                                        pass
                                else:
                                    # Direct number format: "1", "2", "3"
                                    try:
                                        tier_num = int(part)
                                        if tier_num in [1, 2, 3]:
                                            tier_numbers.append(tier_num)
                                    except ValueError:
                                        pass
                            
                            if not tier_numbers:
                                await event.respond(
                                    "❌ **Invalid tier format.**\n\n"
                                    "**Usage:**\n"
                                    "`/set 1` or `/set t1` — Receive only TIER 1 alerts\n"
                                    "`/set 1,2` or `/set t1,t2` — Receive TIER 1 and TIER 2 alerts\n"
                                    "`/set all` — Receive all tier alerts",
                                    parse_mode='Markdown'
                                )
                                return
                            
                            # Save preferences
                            self.user_tier_preferences[user_id] = set(tier_numbers)
                            self.save_user_preferences()
                            
                            tier_names = []
                            tier_emojis = {1: "🚀", 2: "🔥", 3: "⚡"}
                            for t in sorted(tier_numbers):
                                tier_names.append(f"TIER {t} {tier_emojis.get(t, '')}")
                            
                            await event.respond(
                                f"✅ **Tier preference updated!**\n\n"
                                f"You'll now receive only: {', '.join(tier_names)}\n\n"
                                f"Use `/set all` to receive all tier alerts again.",
                                parse_mode='Markdown'
                            )
                            print(f"📝 User {user_id} set tier preferences: {tier_numbers}")
                    return
                
            except Exception as e:
                print(f"❌ Error in command handler: {e}")
                import traceback
                traceback.print_exc()
        
        # Handle inline button callbacks
        @self.bot_client.on(events.CallbackQuery)
        async def callback_handler(event):
            """Handle inline button clicks"""
            try:
                data = event.data.decode('utf-8') if isinstance(event.data, bytes) else event.data
                user_id = event.sender_id
                chat_id = event.chat_id
                
                print(f"📥 [BOT] Received callback '{data}' from user {user_id}")
                
                # Acknowledge the callback first
                await event.answer()
                
                if data == "subscribe":
                    if user_id in self.subscribed_users:
                        try:
                            await event.edit("✅ You're already subscribed! You'll receive all alerts.", parse_mode='Markdown')
                        except:
                            await self.bot_client.send_message(user_id, "✅ You're already subscribed! You'll receive all alerts.", parse_mode='Markdown')
                    else:
                        self.subscribed_users.add(user_id)
                        self.save_subscriptions()
                        try:
                            await event.edit(
                                "✅ **Subscribed!**\n\n"
                                "You'll now receive real-time trading alerts when high-quality signals are detected.\n\n"
                                "Use /unsubscribe to stop receiving alerts.",
                                parse_mode='Markdown'
                            )
                        except:
                            await self.bot_client.send_message(
                                user_id,
                                "✅ **Subscribed!**\n\n"
                                "You'll now receive real-time trading alerts when high-quality signals are detected.\n\n"
                                "Use /unsubscribe to stop receiving alerts.",
                                parse_mode='Markdown'
                            )
                        print(f"📝 User {user_id} subscribed to alerts (total: {len(self.subscribed_users)})")
                
                elif data == "unsubscribe":
                    if user_id in self.subscribed_users:
                        self.subscribed_users.discard(user_id)
                        self.save_subscriptions()
                        try:
                            await event.edit("❌ **Unsubscribed.**\n\nYou won't receive alerts anymore. Use /subscribe to re-enable.", parse_mode='Markdown')
                        except:
                            await self.bot_client.send_message(user_id, "❌ **Unsubscribed.**\n\nYou won't receive alerts anymore. Use /subscribe to re-enable.", parse_mode='Markdown')
                        print(f"📝 User {user_id} unsubscribed from alerts")
                    else:
                        try:
                            await event.edit("ℹ️ You're not subscribed. Use /subscribe to start receiving alerts.", parse_mode='Markdown')
                        except:
                            await self.bot_client.send_message(user_id, "ℹ️ You're not subscribed. Use /subscribe to start receiving alerts.", parse_mode='Markdown')
                
                elif data == "add_group":
                    # This should be called from within a group
                    try:
                        # Get the chat where the button was clicked
                        msg = await event.get_message()
                        chat = await msg.get_chat()
                        current_chat_id = chat.id
                        is_group = hasattr(chat, 'megagroup') or (hasattr(chat, 'broadcast') and not chat.broadcast)
                        
                        if not is_group:
                            # Try to send a message explaining
                            try:
                                await event.edit(
                                    "❌ **This button only works in groups.**\n\n"
                                    "1. Add me to your group as admin\n"
                                    "2. Use this button again in the group\n\n"
                                    "Or use `/addgroup` command in the group.",
                                    parse_mode='Markdown'
                                )
                            except:
                                await self.bot_client.send_message(
                                    user_id,
                                    "❌ **This button only works in groups.**\n\n"
                                    "1. Add me to your group as admin\n"
                                    "2. Use this button again in the group\n\n"
                                    "Or use `/addgroup` command in the group.",
                                    parse_mode='Markdown'
                                )
                            return
                        
                        # Check if user is admin
                        try:
                            admins = await self.bot_client.get_participants(chat, filter=ChannelParticipantsAdmins)
                            user_is_admin = any(p.id == user_id for p in admins)
                            if not user_is_admin:
                                try:
                                    await event.edit("❌ Only group admins can add groups.", parse_mode='Markdown')
                                except:
                                    await self.bot_client.send_message(user_id, "❌ Only group admins can add groups.", parse_mode='Markdown')
                                return
                        except:
                            pass  # Allow if can't check
                        
                        if current_chat_id not in self.alert_groups:
                            self.alert_groups.add(current_chat_id)
                            self.save_alert_groups()
                            chat_title = getattr(chat, 'title', f'Group {current_chat_id}')
                            try:
                                await event.edit(
                                    f"✅ **Group Added!**\n\n"
                                    f"Alerts will now be sent to this group: {chat_title}\n\n"
                                    f"Use /removegroup to stop alerts.",
                                    parse_mode='Markdown'
                                )
                            except:
                                await self.bot_client.send_message(
                                    current_chat_id,
                                    f"✅ **Group Added!**\n\n"
                                    f"Alerts will now be sent to this group: {chat_title}\n\n"
                                    f"Use /removegroup to stop alerts.",
                                    parse_mode='Markdown'
                                )
                            print(f"📝 Group {current_chat_id} ({chat_title}) added to alert destinations")
                        else:
                            try:
                                await event.edit("ℹ️ This group is already receiving alerts.", parse_mode='Markdown')
                            except:
                                await self.bot_client.send_message(user_id, "ℹ️ This group is already receiving alerts.", parse_mode='Markdown')
                    except Exception as e:
                        try:
                            await event.edit(
                                f"❌ **Error adding group:**\n\n"
                                f"Make sure:\n"
                                f"1. I'm added to the group as admin\n"
                                f"2. You're an admin of the group\n"
                                f"3. Use this button from within the group\n\n"
                                f"Or use `/addgroup` command in the group.",
                                parse_mode='Markdown'
                            )
                        except:
                            await self.bot_client.send_message(
                                user_id,
                                f"❌ **Error adding group:**\n\n"
                                f"Make sure:\n"
                                f"1. I'm added to the group as admin\n"
                                f"2. You're an admin of the group\n"
                                f"3. Use this button from within the group\n\n"
                                f"Or use `/addgroup` command in the group.",
                                parse_mode='Markdown'
                            )
                        print(f"❌ Error in add_group callback: {e}")
                
                elif data == "add_channel":
                    # This should be called from within a channel
                    try:
                        # Get the chat where the button was clicked
                        msg = await event.get_message()
                        chat = await msg.get_chat()
                        current_chat_id = chat.id
                        is_channel = hasattr(chat, 'broadcast') and chat.broadcast
                        
                        if not is_channel:
                            # Try to send a message explaining
                            try:
                                await event.edit(
                                    "❌ **This button only works in channels.**\n\n"
                                    "1. Add me to your channel as admin\n"
                                    "2. Use this button again in the channel\n\n"
                                    "Or use `/addchannel` command in the channel.",
                                    parse_mode='Markdown'
                                )
                            except:
                                await self.bot_client.send_message(
                                    user_id,
                                    "❌ **This button only works in channels.**\n\n"
                                    "1. Add me to your channel as admin\n"
                                    "2. Use this button again in the channel\n\n"
                                    "Or use `/addchannel` command in the channel.",
                                    parse_mode='Markdown'
                                )
                            return
                        
                        # Check if user is admin
                        try:
                            admins = await self.bot_client.get_participants(chat, filter=ChannelParticipantsAdmins)
                            user_is_admin = any(p.id == user_id for p in admins)
                            if not user_is_admin:
                                try:
                                    await event.edit("❌ Only channel admins can add channels.", parse_mode='Markdown')
                                except:
                                    await self.bot_client.send_message(user_id, "❌ Only channel admins can add channels.", parse_mode='Markdown')
                                return
                        except:
                            pass  # Allow if can't check
                        
                        if current_chat_id not in self.alert_groups:
                            self.alert_groups.add(current_chat_id)
                            self.save_alert_groups()
                            chat_title = getattr(chat, 'title', f'Channel {current_chat_id}')
                            try:
                                await event.edit(
                                    f"✅ **Channel Added!**\n\n"
                                    f"Alerts will now be sent to this channel: {chat_title}\n\n"
                                    f"Use /removegroup to stop alerts.",
                                    parse_mode='Markdown'
                                )
                            except:
                                await self.bot_client.send_message(
                                    current_chat_id,
                                    f"✅ **Channel Added!**\n\n"
                                    f"Alerts will now be sent to this channel: {chat_title}\n\n"
                                    f"Use /removegroup to stop alerts.",
                                    parse_mode='Markdown'
                                )
                            print(f"📝 Channel {current_chat_id} ({chat_title}) added to alert destinations")
                        else:
                            try:
                                await event.edit("ℹ️ This channel is already receiving alerts.", parse_mode='Markdown')
                            except:
                                await self.bot_client.send_message(user_id, "ℹ️ This channel is already receiving alerts.", parse_mode='Markdown')
                    except Exception as e:
                        try:
                            await event.edit(
                                f"❌ **Error adding channel:**\n\n"
                                f"Make sure:\n"
                                f"1. I'm added to the channel as admin\n"
                                f"2. You're an admin of the channel\n"
                                f"3. Use this button from within the channel\n\n"
                                f"Or use `/addchannel` command in the channel.",
                                parse_mode='Markdown'
                            )
                        except:
                            await self.bot_client.send_message(
                                user_id,
                                f"❌ **Error adding channel:**\n\n"
                                f"Make sure:\n"
                                f"1. I'm added to the channel as admin\n"
                                f"2. You're an admin of the channel\n"
                                f"3. Use this button from within the channel\n\n"
                                f"Or use `/addchannel` command in the channel.",
                                parse_mode='Markdown'
                            )
                        print(f"❌ Error in add_channel callback: {e}")
                
                elif data == "list_groups":
                    if not self.alert_groups:
                        try:
                            await event.edit(
                                "📋 **Alert Groups/Channels:**\n\n"
                                "No groups or channels configured.\n\n"
                                "Add me to a group/channel as admin, then use the buttons or commands to add them.",
                                parse_mode='Markdown'
                            )
                        except:
                            await self.bot_client.send_message(
                                user_id,
                                "📋 **Alert Groups/Channels:**\n\n"
                                "No groups or channels configured.\n\n"
                                "Add me to a group/channel as admin, then use the buttons or commands to add them.",
                                parse_mode='Markdown'
                            )
                    else:
                        groups_list = []
                        for group_id in self.alert_groups:
                            try:
                                chat = await self.bot_client.get_entity(group_id)
                                title = getattr(chat, 'title', f'Group/Channel {group_id}')
                                chat_type = "Channel" if (hasattr(chat, 'broadcast') and chat.broadcast) else "Group"
                                groups_list.append(f"• {chat_type}: {title} (ID: {group_id})")
                            except:
                                groups_list.append(f"• Group/Channel {group_id} (unknown)")
                        
                        response_text = f"📋 **Alert Groups/Channels ({len(self.alert_groups)}):**\n\n" + "\n".join(groups_list)
                        try:
                            await event.edit(response_text, parse_mode='Markdown')
                        except:
                            await self.bot_client.send_message(user_id, response_text, parse_mode='Markdown')
                
                elif data == "help":
                    welcome_msg = (
                        "🚀 **@solboy_calls**\n\n"
                        
                        "**About me:**\n"
                        "Been in the Solana memecoin space since the early days. I've seen the cycles, the pumps, the rugs, and everything in between. Over time, I've built a system that filters through the noise to find real opportunities.\n\n"
                        
                        "**My approach:**\n"
                        "I don't call everything. I wait for multiple sources to align — when XTRACK, Glydo, whale wallets, and momentum all point in the same direction. That's when I know it's worth your attention.\n\n"
                        
                        "**What you'll get:**\n"
                        "• **TIER 1 ULTRA** 🚀 — My highest conviction plays\n"
                        "• **TIER 2 HIGH** 🔥 — Strong setups with solid confirmations\n"
                        "• **TIER 3 MEDIUM** ⚡ — Good opportunities worth watching\n\n"
                        
                        "**⚡ Commands:**\n"
                        "`/subscribe` — Get my alerts\n"
                        "`/unsubscribe` — Stop alerts\n"
                        "`/status` — Check subscription\n"
                        "`/set t1` — Receive only TIER 1 alerts\n"
                        "`/set t1,t2` — Receive specific tier alerts\n"
                        "`/set all` — Receive all tier alerts (default)\n"
                        "`/addgroup` — Add group (admin only)\n"
                        "`/addchannel` — Add channel (admin only)\n"
                        "`/removegroup` — Remove group/channel (admin only)\n"
                        "`/groups` — List alert groups/channels\n"
                        "`/help` — Show this again\n\n"
                        
                        "📖 **Complete Trading Guide:**\n"
                        "[Read the Alert Pipeline Guide](https://telegra.ph/Solboy-Alert-Pipeline--Complete-Trading-Guide-12-23)\n\n"
                        
                        "**💡 Quick Actions:**\n"
                        "Use the buttons below for quick access.\n\n"
                        
                        "— [Join my channel](https://t.me/solboy_calls)"
                    )
                    buttons = [
                        [Button.inline("✅ Subscribe", b"subscribe"),
                         Button.inline("❌ Unsubscribe", b"unsubscribe")],
                        [Button.inline("➕ Add Group", b"add_group"),
                         Button.inline("➕ Add Channel", b"add_channel")],
                        [Button.inline("📋 My Groups/Channels", b"list_groups"),
                         Button.inline("ℹ️ Help", b"help")]
                    ]
                    try:
                        await event.edit(welcome_msg, parse_mode='Markdown', link_preview=False, buttons=buttons)
                    except:
                        await self.bot_client.send_message(user_id, welcome_msg, parse_mode='Markdown', link_preview=False, buttons=buttons)
                
            except Exception as e:
                print(f"❌ Error in callback handler: {e}")
                import traceback
                traceback.print_exc()
                try:
                    await event.answer("❌ An error occurred. Please try again.")
                except:
                    pass
        
        # Handle bot being added to groups/channels
        @self.bot_client.on(events.ChatAction)
        async def chat_action_handler(event):
            """Detect when bot is added to a group or channel"""
            try:
                # Check if bot was added to a group/channel
                if event.user_added or event.user_joined:
                    # Check if the added user is the bot itself
                    bot_me = await self.bot_client.get_me()
                    if event.user_id and event.user_id == bot_me.id:
                        chat_id = event.chat_id
                        chat = await event.get_chat()
                        
                        # Check if it's a group or channel
                        is_group = hasattr(chat, 'megagroup') or (hasattr(chat, 'broadcast') and not chat.broadcast)
                        is_channel = hasattr(chat, 'broadcast') and chat.broadcast
                        
                        if is_group or is_channel:
                            # Check if bot is admin (can send messages)
                            try:
                                # Try to get bot's permissions
                                participants = await self.bot_client.get_participants(chat)
                                # If we can get participants, we likely have access
                                
                                if chat_id not in self.alert_groups:
                                    self.alert_groups.add(chat_id)
                                    self.save_alert_groups()
                                    
                                    chat_title = getattr(chat, 'title', f'Group/Channel {chat_id}')
                                    chat_type = "channel" if is_channel else "group"
                                    print(f"✅ Bot added to {chat_type}: {chat_title} (ID: {chat_id})")
                                    print(f"   Alerts will now be sent to this {chat_type}")
                                    
                                    # Send welcome message to group/channel
                                    try:
                                        welcome_text = (
                                            "✅ **Bot Added!**\n\n"
                                            f"I'll now send trading alerts to this {chat_type}.\n\n"
                                            "Use /start for more information.\n\n"
                                            "📖 **Complete Trading Guide:**\n"
                                            "[Read the Alert Pipeline Guide](https://telegra.ph/Solboy-Alert-Pipeline--Complete-Trading-Guide-12-23)"
                                        )
                                        await self.bot_client.send_message(
                                            chat_id,
                                            welcome_text,
                                            parse_mode='Markdown',
                                            link_preview=False
                                        )
                                    except:
                                        pass  # Silent fail if can't send welcome
                            except Exception as e:
                                print(f"⚠️ Could not verify admin status for {chat_type} {chat_id}: {e}")
            except Exception as e:
                print(f"❌ Error in chat action handler: {e}")
                import traceback
                traceback.print_exc()
        
        # Add logging to verify handlers are being called
        print(f"   📝 Registered command handlers:")
        print(f"      - /start, /help")
        print(f"      - /subscribe, /unsubscribe")
        print(f"      - /status, /set (tier filtering)")
        print(f"      - /addgroup, /addchannel, /removegroup, /groups")
        print(f"   🔘 Inline buttons enabled:")
        print(f"      - Subscribe/Unsubscribe")
        print(f"      - Add Group/Add Channel")
        print(f"      - My Groups/Channels, Help")
        
        # Test bot connection
        try:
            bot_me = await self.bot_client.get_me()
            print(f"   ✅ Bot verified: @{bot_me.username} (ID: {bot_me.id})")
            print(f"   💡 Send /start or /subscribe to @{bot_me.username} in a private chat")
        except Exception as e:
            print(f"   ⚠️ Warning: Could not verify bot connection: {e}")
        
        
        print("✅ Bot command handlers setup complete")
        print(f"   Bot is ready to receive commands. Try /start or /subscribe")
        
        # Test bot connection
        try:
            bot_me = await self.bot_client.get_me()
            print(f"   Bot username: @{bot_me.username}")
            print(f"   Bot ID: {bot_me.id}")
        except Exception as e:
            print(f"   ⚠️ Warning: Could not verify bot connection: {e}")
    
    async def setup_handlers(self):
        """Setup message handlers for all sources"""
        
        # Collect all monitored chat IDs
        monitored_chat_ids = set()
        for topic in FORUM_TOPICS:
            monitored_chat_ids.add(topic['group_id'])
        for channel in CHANNELS:
            monitored_chat_ids.add(channel['channel_id'])
        
        # Single handler for all messages (like old script)
        @self.client.on(events.NewMessage(chats=list(monitored_chat_ids)))
        async def message_handler(event):
            try:
                message = event.message
                chat_id = event.chat_id
                
                # Check if it's a forum group
                is_forum_group = any(chat_id == topic['group_id'] for topic in FORUM_TOPICS)
                
                if is_forum_group:
                    # Extract topic ID from message (multiple methods)
                    topic_id = None
                    
                    # Method 1: Check reply_to for forum topic messages
                    if hasattr(message, 'reply_to') and message.reply_to:
                        reply_to = message.reply_to
                        # Try to get topic ID (reply_to_top_id for forum topics)
                        topic_id = getattr(reply_to, 'reply_to_top_id', None)
                        # Also try reply_to_msg_id (sometimes topic ID is here)
                        if not topic_id:
                            topic_id = getattr(reply_to, 'reply_to_msg_id', None)
                    
                    # Method 2: Check message_thread_id directly on the message
                    if not topic_id:
                        topic_id = getattr(message, 'message_thread_id', None)
                    
                    # Only process if we have a topic_id AND it matches one of our monitored topics
                    if topic_id:
                        for topic in FORUM_TOPICS:
                            if (chat_id == topic['group_id'] and 
                                topic_id == topic['thread_id']):
                                await self.process_message(message, topic['source'])
                                return
                        # Topic ID exists but doesn't match any monitored topic - skip silently
                        return
                    else:
                        # No topic_id detected - skip silently (likely from another topic or general chat)
                        return
                
                # Check if message is from a channel we're monitoring
                for channel in CHANNELS:
                    if chat_id == channel['channel_id']:
                        await self.process_message(message, channel['source'])
                        return
                        
            except Exception as e:
                print(f"❌ Error in message handler: {e}")
                import traceback
                traceback.print_exc()
        
        # Print monitoring status
        for topic in FORUM_TOPICS:
            print(f"📡 Monitoring forum topic: {topic['name']} (thread {topic['thread_id']})")
        
        for channel in CHANNELS:
            print(f"📡 Monitoring channel: {channel['channel_name']}")
    
    async def start(self):
        """Start monitoring"""
        print(f"\n{'='*80}")
        print("TELEGRAM MONITOR - NEW SYSTEM")
        print(f"{'='*80}")
        print(f"Forum topics: {len(FORUM_TOPICS)}")
        print(f"Channels: {len(CHANNELS)}")
        print(f"{'='*80}\n")
        
        # Setup message monitoring handlers
        await self.setup_handlers()
        
        # Setup bot command handlers (after monitoring handlers)
        if self.bot_client:
            await self.setup_bot_handlers()
        
        print(f"\n✅ Monitoring started. Waiting for messages...")
        print(f"📊 Subscribed users: {len(self.subscribed_users)}")
        print(f"📢 Alert groups: {len(self.alert_groups)}")
        if self.enrich_with_live_mcap:
            print(f"🔄 Live MCAP enrichment: ENABLED (DexScreener API)")
        else:
            print(f"🔄 Live MCAP enrichment: DISABLED")
        if self.alert_groups:
            for group_id in self.alert_groups:
                try:
                    if self.bot_client:
                        chat = await self.bot_client.get_entity(group_id)
                        title = getattr(chat, 'title', f'Group {group_id}')
                        print(f"   - {title} (ID: {group_id})")
                    else:
                        print(f"   - Group ID: {group_id}")
                except:
                    print(f"   - Group ID: {group_id} (unknown)")
        if self.bot_client:
            try:
                bot_me = await self.bot_client.get_me()
                print(f"🤖 Bot ready: @{bot_me.username} (ID: {bot_me.id})")
                print(f"   Send /start or /subscribe to the bot in a private chat")
                print(f"   Or add bot to a group and use /addgroup")
            except Exception as e:
                print(f"⚠️ Could not get bot info: {e}")
        else:
            print("⚠️ Bot client not initialized - commands will not work")
        print()
        
        # Keep running (both clients will stay connected)
        # Use asyncio.gather to keep both clients running
        if self.bot_client:
            await asyncio.gather(
                self.client.run_until_disconnected(),
                self.bot_client.run_until_disconnected(),
                return_exceptions=True
            )
        else:
            await self.client.run_until_disconnected()

async def connect_with_retry(client: TelegramClient, max_attempts: int = 5, is_bot: bool = False, bot_token: str = None):
    """Connect to Telegram with retry logic and exponential backoff"""
    from telethon.errors import AuthKeyDuplicatedError
    import sys
    
    # Check if session file exists (for non-bot connections) before attempting connection
    if not is_bot:
        session_file = f"{SESSION_NAME}.session"
        # Check multiple possible locations
        possible_paths = [
            session_file,  # Current directory
            f"/app/{session_file}",  # Railway /app directory
            os.path.join(os.getcwd(), session_file),  # Absolute path from current dir
        ]
        
        session_found = False
        actual_path = None
        for path in possible_paths:
            if os.path.exists(path):
                session_found = True
                actual_path = path
                break
        
        if not session_found:
            # Last resort: Check if file exists in current directory (Railway might deploy it there)
            current_dir_files = os.listdir('.')
            session_files = [f for f in current_dir_files if f.endswith('.session')]
            
            print("\n" + "=" * 80)
            print("⚠️  SESSION FILE NOT FOUND")
            print("=" * 80)
            print(f"Session file '{session_file}' does not exist in any expected location.")
            print(f"Checked paths: {possible_paths}")
            print(f"Current working directory: {os.getcwd()}")
            print(f"All .session files in current directory: {session_files}")
            print(f"All files in current directory (first 20): {current_dir_files[:20]}")
            
            # If we find ANY session file, try to use it as a last resort
            if session_files:
                print(f"\n⚠️  Found other session files: {session_files}")
                print("   Trying to use the first one as fallback...")
                fallback_session = session_files[0]
                try:
                    import shutil
                    shutil.copy2(fallback_session, session_file)
                    print(f"✅ Copied {fallback_session} to {session_file}")
                    actual_path = session_file
                    session_found = True
                except Exception as e:
                    print(f"❌ Could not copy fallback session: {e}")
            
            if not session_found:
                print("\n🔧 SOLUTION:")
                print("1. The session file should be in GitHub and deployed automatically")
                print(f"2. Verify '{session_file}' is in your GitHub repository")
                print("3. Check Railway Dashboard → Deployments → Latest deployment logs")
                print("4. If file is missing, ensure it's committed to Git and not in .gitignore")
                print("5. Redeploy on Railway after ensuring file is in GitHub")
                print("\nSee RAILWAY_SESSION_SETUP.md for detailed instructions")
                print("=" * 80 + "\n")
                raise FileNotFoundError(f"Session file '{session_file}' not found. Please ensure it's in GitHub and Railway has deployed it.")
        
        if session_found:
            print(f"✅ Found session file at: {actual_path}")
    
    for attempt in range(1, max_attempts + 1):
        try:
            print(f"Attempt {attempt} at connecting{' bot' if is_bot else ''}...")
            
            if is_bot and bot_token:
                await client.start(bot_token=bot_token)
            else:
                await client.start()
            
            print(f"✅ Connection successful{' (bot)' if is_bot else ''}!")
            return True
        except AuthKeyDuplicatedError as e:
            # CRITICAL: Session file is being used from multiple IPs
            session_name = client.session.filename if hasattr(client.session, 'filename') else SESSION_NAME
            print("\n" + "=" * 80)
            print("❌ AUTH KEY DUPLICATED ERROR")
            print("=" * 80)
            print(f"The session file '{session_name}.session' is being used from multiple IP addresses.")
            print("This happens when the bot runs locally AND on Railway simultaneously.")
            print("\n🔧 FIX:")
            print("1. Stop the bot on your local machine (if running)")
            print("2. Delete the session file on Railway:")
            print(f"   - Go to Railway dashboard → Your service → Files")
            print(f"   - Delete: {session_name}.session")
            print("3. OR delete the session file locally if you want to run on Railway only:")
            print(f"   - Delete: {session_name}.session from your local directory")
            print("4. Create a new session and upload to Railway")
            print("\n💡 TIP: Only run the bot in ONE place at a time!")
            print("   - Either locally OR on Railway, not both")
            print("=" * 80 + "\n")
            raise  # Don't retry - this needs manual intervention
        except EOFError as e:
            # Non-interactive environment (Railway) trying to prompt for phone number
            print("\n" + "=" * 80)
            print("❌ AUTHENTICATION ERROR - NON-INTERACTIVE ENVIRONMENT")
            print("=" * 80)
            print("Railway cannot prompt for phone number interactively.")
            print("The session file must be uploaded to Railway.")
            print("\n🔧 SOLUTION:")
            print("1. Create session file locally first:")
            print("   - Run the bot locally: python telegram_monitor_new.py")
            print("   - Enter your phone number and authentication code")
            print(f"   - This creates: {SESSION_NAME}.session")
            print("\n2. Upload session file to Railway:")
            print("   - Go to Railway dashboard → Your service → Files tab")
            print(f"   - Click 'Upload' and select: {SESSION_NAME}.session")
            print("\n3. Redeploy on Railway")
            print("\n4. See RAILWAY_SESSION_SETUP.md for detailed instructions")
            print("=" * 80 + "\n")
            raise  # Don't retry - needs manual intervention
        except FileNotFoundError as e:
            # Session file missing (should be caught earlier, but handle just in case)
            print("\n" + "=" * 80)
            print("⚠️  SESSION FILE NOT FOUND")
            print("=" * 80)
            print(f"Session file '{SESSION_NAME}.session' does not exist.")
            print("\n🔧 SOLUTION:")
            print("1. Create session file locally first:")
            print("   - Run the bot locally: python telegram_monitor_new.py")
            print("   - Enter your phone number and authentication code")
            print(f"   - This creates: {SESSION_NAME}.session")
            print("\n2. Upload session file to Railway:")
            print("   - Go to Railway dashboard → Your service → Files tab")
            print(f"   - Click 'Upload' and select: {SESSION_NAME}.session")
            print("\n3. Redeploy on Railway")
            print("\n4. See RAILWAY_SESSION_SETUP.md for detailed instructions")
            print("=" * 80 + "\n")
            raise  # Don't retry - needs manual intervention
        except Exception as e:
            if attempt < max_attempts:
                wait_time = min(2 ** attempt, 30)  # Exponential backoff, max 30 seconds
                print(f"   ⚠️ Connection failed: {type(e).__name__}: {str(e)}")
                print(f"   Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
            else:
                print(f"   ❌ Failed after {max_attempts} attempts: {type(e).__name__}: {str(e)}")
                raise
    return False

async def run_api_server():
    """Run the API server in background"""
    try:
        import uvicorn
        from api_server import app
        # Railway uses PORT environment variable, fallback to 5000 for local dev
        port = int(os.getenv("PORT", "5000"))
        config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
        server = uvicorn.Server(config)
        print("🚀 Starting SolBoy Alerts API Server...")
        print(f"📡 API will be available at: http://0.0.0.0:{port}")
        print(f"📖 API docs at: http://0.0.0.0:{port}/docs")
        print(f"💚 Health check: http://0.0.0.0:{port}/api/health")
        await server.serve()
    except Exception as e:
        print(f"⚠️ Warning: Could not start API server: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main function"""
    # CRITICAL: Ensure session file is in the right location for Railway
    # If session file exists in current directory but not in /app/, copy it
    session_file = f"{SESSION_NAME}.session"
    if os.path.exists(session_file) and not os.path.exists(f"/app/{session_file}"):
        try:
            import shutil
            # Ensure /app directory exists
            os.makedirs("/app", exist_ok=True)
            # Copy session file to /app/ for Railway
            shutil.copy2(session_file, f"/app/{session_file}")
            print(f"✅ Copied session file to /app/{session_file}")
        except Exception as e:
            print(f"⚠️  Could not copy session file to /app/: {e}")
            # Continue anyway - might work from current directory
    
    # TelegramClient will create the session file on first run if it doesn't exist
    # The user will be prompted to authenticate via phone number
    # Increase connection timeout and add connection retry settings
    client = TelegramClient(
        SESSION_NAME, 
        API_ID, 
        API_HASH,
        connection_retries=5,
        retry_delay=2,
        timeout=30
    )
    bot_client = None
    
    # Initialize bot client if token is provided
    if BOT_TOKEN:
        try:
            bot_client = TelegramClient(
                'bot_session', 
                API_ID, 
                API_HASH,
                connection_retries=5,
                retry_delay=2,
                timeout=30
            )
            await connect_with_retry(bot_client, max_attempts=5, is_bot=True, bot_token=BOT_TOKEN)
            bot_me = await bot_client.get_me()
            print(f"✅ Bot client connected: @{bot_me.username} ({bot_me.first_name})")
            print(f"   Bot ID: {bot_me.id}")
            print(f"   Bot username: @{bot_me.username}")
            if ALERT_CHAT_ID:
                print(f"✅ Alert destination: {ALERT_CHAT_ID}")
            else:
                print("⚠️  ALERT_CHAT_ID not set - alerts will only print to console")
                print("   Set ALERT_CHAT_ID in telegram_monitor_new.py to enable Telegram alerts")
            print()
        except Exception as e:
            print(f"❌ Warning: Could not start bot client: {e}")
            print(f"   Error details: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            print("   Alerts will only be logged to console\n")
            bot_client = None
    
    try:
        await connect_with_retry(client, max_attempts=5, is_bot=False)
        me = await client.get_me()
        print(f"Connected as: {me.first_name} (@{me.username or 'N/A'})\n")
        
        monitor = TelegramMonitorNew(client, bot_client=bot_client)
        
        # Start API server and monitor concurrently
        await asyncio.gather(
            run_api_server(),
            monitor.start(),
            return_exceptions=True
        )
        
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            await client.disconnect()
            if bot_client:
                await bot_client.disconnect()
        except:
            pass

if __name__ == '__main__':
    asyncio.run(main())
