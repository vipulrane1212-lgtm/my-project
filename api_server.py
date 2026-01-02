#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SolBoy Alerts API Server
Provides REST API endpoints for the website to consume real-time statistics and alert data.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import os
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
from pathlib import Path
from collections import defaultdict

# Import formatter functions for description and hotlist
try:
    from live_alert_formatter import _get_hot_list_status, _get_spicy_intro, _build_confirmation_lines, _build_glydo_line
except ImportError:
    # Fallback if import fails
    def _get_hot_list_status(alert: Dict) -> str:
        hot_list = alert.get("hot_list") or alert.get("hot_list_status", {})
        if isinstance(hot_list, bool):
            return "🟢 Yes" if hot_list else "🔴 No"
        elif isinstance(hot_list, dict):
            was_in_hot_list = hot_list.get("was_in_hot_list", False)
            return "🟢 Yes" if was_in_hot_list else "🔴 No"
        return "🔴 No"
    
    def _get_spicy_intro(alert: Dict, confirmation_lines: List[str], glydo_line: str) -> str:
        return "Alert description not available"
    
    def _build_confirmation_lines(alert: Dict) -> List[str]:
        return []
    
    def _build_glydo_line(alert: Dict) -> str:
        return ""

app = FastAPI(
    title="SolBoy Alerts API",
    description="API for SolBoy Alerts website - Real-time statistics and alert data",
    version="1.0.0"
)

# Enable CORS for Next.js website
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your website domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# File paths
BASE_DIR = Path(__file__).parent

# CRITICAL: Check for Railway persistent volume first (same logic as kpi_logger)
# This ensures API reads from the same file that the bot writes to
data_dir = Path("/data")
if data_dir.exists() and data_dir.is_dir():
    # Use persistent volume if available (Railway)
    KPI_LOGS_FILE = data_dir / "kpi_logs.json"
else:
    # Fallback to local file (local dev or Railway without volumes)
    KPI_LOGS_FILE = BASE_DIR / "kpi_logs.json"

# #region agent log
try:
    with open(r'c:\Users\Admin\Desktop\amaverse\.cursor\debug.log', 'a', encoding='utf-8') as f:
        import json as json_lib
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        log_entry = {
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": "H1,H2",
            "location": "api_server.py:68",
            "message": "API server init - KPI_LOGS_FILE path determined",
            "data": {
                "kpi_logs_file_path": str(KPI_LOGS_FILE),
                "data_dir_exists": data_dir.exists(),
                "file_exists": KPI_LOGS_FILE.exists(),
                "file_size": KPI_LOGS_FILE.stat().st_size if KPI_LOGS_FILE.exists() else 0,
                "base_dir": str(BASE_DIR)
            },
            "timestamp": int(now.timestamp() * 1000)
        }
        f.write(json_lib.dumps(log_entry) + '\n')
except Exception:
    pass
# #endregion

SUBSCRIPTIONS_FILE = BASE_DIR / "subscriptions.json"
ALERT_GROUPS_FILE = BASE_DIR / "alert_groups.json"
USER_PREFERENCES_FILE = BASE_DIR / "user_preferences.json"

# In-memory cache for kpi_data (refreshes every 30 seconds or when file changes)
_kpi_data_cache = None
_cache_timestamp = None
_cache_file_mtime = None
CACHE_TTL_SECONDS = 30


def get_cached_kpi_data() -> Dict:
    """Get kpi_data from cache or load from file if cache is stale.
    
    Cache refreshes:
    - Every 30 seconds (CACHE_TTL_SECONDS)
    - When kpi_logs.json file modification time changes
    
    Returns full kpi_data dict with alerts, true_positives, false_positives.
    """
    global _kpi_data_cache, _cache_timestamp, _cache_file_mtime
    
    now = datetime.now(timezone.utc)
    
    # #region agent log
    try:
        with open(r'c:\Users\Admin\Desktop\amaverse\.cursor\debug.log', 'a', encoding='utf-8') as f:
            import json as json_lib
            log_entry = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "H1,H2,H3",
                "location": "api_server.py:70",
                "message": "get_cached_kpi_data entry",
                "data": {
                    "cache_exists": _kpi_data_cache is not None,
                    "cache_timestamp": str(_cache_timestamp) if _cache_timestamp else None,
                    "file_path": str(KPI_LOGS_FILE),
                    "file_exists": KPI_LOGS_FILE.exists(),
                    "file_size": KPI_LOGS_FILE.stat().st_size if KPI_LOGS_FILE.exists() else 0,
                    "data_dir_exists": data_dir.exists(),
                    "now": now.isoformat()
                },
                "timestamp": int(now.timestamp() * 1000)
            }
            f.write(json_lib.dumps(log_entry) + '\n')
    except Exception:
        pass
    # #endregion
    
    # Check if cache is valid
    cache_valid = False
    if _kpi_data_cache is not None and _cache_timestamp is not None:
        # CRITICAL: Always check file modification time FIRST (most reliable)
        try:
            current_mtime = KPI_LOGS_FILE.stat().st_mtime if KPI_LOGS_FILE.exists() else 0
            if _cache_file_mtime is not None and current_mtime > 0:
                # File was modified - invalidate cache immediately
                if current_mtime != _cache_file_mtime:
                    cache_valid = False
                else:
                    # File not modified - check TTL
                    age_seconds = (now - _cache_timestamp).total_seconds()
                    if age_seconds < CACHE_TTL_SECONDS:
                        cache_valid = True
            else:
                # Fallback to TTL check if mtime unavailable
                age_seconds = (now - _cache_timestamp).total_seconds()
                if age_seconds < CACHE_TTL_SECONDS:
                    cache_valid = True
        except Exception:
            # Fallback to TTL check on error
            age_seconds = (now - _cache_timestamp).total_seconds()
            if age_seconds < CACHE_TTL_SECONDS:
                cache_valid = True
    
    # #region agent log
    try:
        with open(r'c:\Users\Admin\Desktop\amaverse\.cursor\debug.log', 'a', encoding='utf-8') as f:
            import json as json_lib
            log_entry = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "H1,H2",
                "location": "api_server.py:95",
                "message": "cache validity check",
                "data": {
                    "cache_valid": cache_valid,
                    "age_seconds": age_seconds if _cache_timestamp else None,
                    "current_mtime": KPI_LOGS_FILE.stat().st_mtime if KPI_LOGS_FILE.exists() else 0,
                    "cached_mtime": _cache_file_mtime
                },
                "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000)
            }
            f.write(json_lib.dumps(log_entry) + '\n')
    except Exception:
        pass
    # #endregion
    
    # Load from file if cache is invalid
    if not cache_valid:
        # #region agent log
        try:
            with open(r'c:\Users\Admin\Desktop\amaverse\.cursor\debug.log', 'a', encoding='utf-8') as f:
                import json as json_lib
                log_entry = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H3,H4",
                    "location": "api_server.py:157",
                    "message": "cache invalid - loading from file",
                    "data": {
                        "file_path": str(KPI_LOGS_FILE),
                        "file_exists": KPI_LOGS_FILE.exists(),
                        "file_size": KPI_LOGS_FILE.stat().st_size if KPI_LOGS_FILE.exists() else 0
                    },
                    "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000)
                }
                f.write(json_lib.dumps(log_entry) + '\n')
        except Exception:
            pass
        # #endregion
        
        _kpi_data_cache = load_json_file(KPI_LOGS_FILE, {"alerts": [], "true_positives": [], "false_positives": []})
        _cache_timestamp = now
        try:
            _cache_file_mtime = KPI_LOGS_FILE.stat().st_mtime if KPI_LOGS_FILE.exists() else 0
        except Exception:
            _cache_file_mtime = 0
        
        # #region agent log
        try:
            with open(r'c:\Users\Admin\Desktop\amaverse\.cursor\debug.log', 'a', encoding='utf-8') as f:
                import json as json_lib
                alerts = _kpi_data_cache.get("alerts", [])
                latest_alert = max(alerts, key=lambda x: x.get("timestamp", "")) if alerts else None
                log_entry = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H3",
                    "location": "api_server.py:180",
                    "message": "cache loaded from file",
                    "data": {
                        "alert_count": len(alerts),
                        "latest_token": latest_alert.get("token") if latest_alert else None,
                        "latest_timestamp": latest_alert.get("timestamp") if latest_alert else None,
                        "file_mtime": _cache_file_mtime
                    },
                    "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000)
                }
                f.write(json_lib.dumps(log_entry) + '\n')
        except Exception:
            pass
        # #endregion
    
    return _kpi_data_cache


def get_cached_alerts() -> List[Dict]:
    """Get alerts from cache (convenience function)."""
    kpi_data = get_cached_kpi_data()
    return kpi_data.get("alerts", [])


def invalidate_cache():
    """Force cache invalidation (call after updates)."""
    global _kpi_data_cache, _cache_timestamp, _cache_file_mtime
    _kpi_data_cache = None
    _cache_timestamp = None
    _cache_file_mtime = None


def load_json_file(file_path: Path, default: dict = None) -> dict:
    """Safely load JSON file with retry logic."""
    if default is None:
        default = {}
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data
            return default
        except json.JSONDecodeError as e:
            # JSON decode error - file might be corrupted or being written
            if attempt < max_retries - 1:
                import time
                time.sleep(0.1 * (attempt + 1))  # Brief delay before retry
                print(f"⚠️ JSON decode error (attempt {attempt + 1}/{max_retries}), retrying...")
            else:
                print(f"❌ Error loading {file_path}: JSON decode error: {e}")
                # Try to load backup file if main file is corrupted
                backup_file = file_path.with_suffix('.json.backup')
                if backup_file.exists():
                    try:
                        print(f"⚠️ Attempting to load backup file: {backup_file}")
                        with open(backup_file, 'r', encoding='utf-8') as f:
                            return json.load(f)
                    except Exception as backup_error:
                        print(f"❌ Backup file also failed: {backup_error}")
                return default
        except Exception as e:
            if attempt < max_retries - 1:
                import time
                time.sleep(0.1 * (attempt + 1))
                print(f"⚠️ Error loading {file_path} (attempt {attempt + 1}/{max_retries}): {e}, retrying...")
            else:
                print(f"❌ Error loading {file_path} after {max_retries} attempts: {e}")
                return default
    
    return default


def get_tier_from_level(level: str, alert_tier: Optional[int] = None, alert: Optional[Dict] = None) -> int:
    """Convert alert level to tier number.
    
    CRITICAL: The tier field comes DIRECTLY from the Telegram alert post.
    If the Telegram post says "TIER 1", the tier field MUST be 1.
    If the Telegram post says "TIER 2", the tier field MUST be 2.
    If the Telegram post says "TIER 3", the tier field MUST be 3.
    
    THE TELEGRAM POST IS THE SOURCE OF TRUTH - NO HEURISTICS WHEN TIER FIELD EXISTS!
    
    IMPORTANT: 
    - Tier 1 alerts are stored as level="HIGH"
    - Tier 2 and Tier 3 alerts are both stored as level="MEDIUM"
    - We can't distinguish Tier 2 from Tier 3 without the tier field
    
    PRIORITY (STRICT):
    1. Use alert_tier if available (from the tier field - this is EXACTLY what was shown in Telegram post)
    2. ONLY use heuristics if tier field is missing (for old alerts before tier field was added)
    """
    # PRIORITY 1: If tier is explicitly provided, use it DIRECTLY (this is EXACTLY what was shown in Telegram post)
    # NO HEURISTICS - THE TELEGRAM POST DECIDES THE TIER!
    if alert_tier is not None and alert_tier in [1, 2, 3]:
        return alert_tier
    
    level_upper = level.upper()
    
    # Explicit tier strings
    if level_upper in ["ULTRA", "TIER 1", "TIER1", "1"]:
        return 1
    elif level_upper in ["TIER 2", "TIER2", "2"]:
        return 2
    elif level_upper in ["TIER 3", "TIER3", "3"]:
        return 3
    
    # CRITICAL FIX: Tier 1 alerts are stored as level="HIGH"
    if "HIGH" in level_upper:
        return 1  # Tier 1 uses HIGH
    
    # PROBLEM: Both Tier 2 and Tier 3 use MEDIUM level
    # We need to use heuristics to distinguish them when tier field is missing
    elif "MEDIUM" in level_upper:
        if alert:
            # Try to infer tier from alert data
            # Tier 2: Has Glydo top 5 + confirmations
            # Tier 3: No Glydo top 5 OR delayed Glydo OR multiple non-Glydo confirmations
            
            glydo_in_top5 = alert.get("glydo_in_top5", False)
            hot_list = alert.get("hot_list")
            if isinstance(hot_list, dict):
                was_in_hot_list = hot_list.get("was_in_hot_list", False)
            else:
                was_in_hot_list = bool(hot_list)
            
            # If has Glydo top 5, more likely Tier 2
            if glydo_in_top5 or was_in_hot_list:
                # Check confirmations - Tier 2 needs at least 1 confirmation
                confirmations = alert.get("confirmations", {})
                if isinstance(confirmations, dict):
                    total_confirmations = confirmations.get("total", 0)
                    strong_confirmations = confirmations.get("strong_total", 0)
                    if total_confirmations >= 1 or strong_confirmations >= 1:
                        return 2  # Tier 2: Glydo top 5 + confirmations
            
            # Default MEDIUM to Tier 3 (more common, and safer default)
            return 3
        
        # No alert data available - default MEDIUM to Tier 3
        # (Tier 3 is more common than Tier 2, so safer default)
        return 3
    
    return 3  # Default to tier 3


@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "message": "SolBoy Alerts API",
        "version": "1.0.0",
        "endpoints": {
            "/api/stats": "Get real-time statistics",
            "/api/alerts/recent": "Get recent alerts",
            "/api/subscribers": "Get subscriber count",
            "/api/health": "Health check"
        }
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    # Get latest alert info for debugging
    latest_alert = None
    alert_count = 0
    try:
        # Use cached alerts for better performance
        alerts = get_cached_alerts()
        alert_count = len(alerts)
        if alerts:
            # Get most recent alert
            alerts_sorted = sorted(
                alerts,
                key=lambda x: datetime.fromisoformat(x.get("timestamp", "2000-01-01")).replace(tzinfo=timezone.utc),
                reverse=True
            )
            latest = alerts_sorted[0]
            latest_alert = {
                "token": latest.get("token"),
                "timestamp": latest.get("timestamp"),
                "tier": latest.get("tier"),
            }
    except Exception as e:
        print(f"Error getting latest alert info: {e}")
    
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "files": {
            "subscriptions": SUBSCRIPTIONS_FILE.exists(),
            "kpi_logs": KPI_LOGS_FILE.exists(),
            "alert_groups": ALERT_GROUPS_FILE.exists(),
            "user_preferences": USER_PREFERENCES_FILE.exists(),
        },
        "alerts": {
            "total": alert_count,
            "latest": latest_alert
        }
    }


@app.get("/api/stats")
async def get_stats():
    """Get real-time statistics for the website."""
    try:
        # Load data (use cached kpi_data for better performance)
        subscriptions_data = load_json_file(SUBSCRIPTIONS_FILE, {"users": []})
        kpi_data = get_cached_kpi_data()
        alert_groups_data = load_json_file(ALERT_GROUPS_FILE, {"groups": []})
        
        alerts = kpi_data.get("alerts", [])
        true_positives = kpi_data.get("true_positives", [])
        false_positives = kpi_data.get("false_positives", [])
        
        # Count subscribers (users + groups)
        user_count = len(subscriptions_data.get("users", []))
        group_count = len(alert_groups_data.get("groups", []))
        total_subscribers = user_count + group_count
        
        # Count alerts by tier
        tier_counts = {1: 0, 2: 0, 3: 0}
        for alert in alerts:
            level = alert.get("level", "MEDIUM")
            # CRITICAL: Use tier field DIRECTLY from Telegram post - this is the source of truth
            alert_tier = alert.get("tier")
            if alert_tier is not None and alert_tier in [1, 2, 3]:
                # Tier field exists - use it directly (this is EXACTLY what was shown in Telegram post)
                tier = alert_tier
            else:
                # Only use heuristics if tier field is missing (for old alerts)
                tier = get_tier_from_level(level, alert_tier, alert)
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
        
        # Calculate win rate (true positives / total alerts)
        total_alerts = len(alerts)
        tp_count = len(true_positives)
        win_rate = (tp_count / total_alerts * 100) if total_alerts > 0 else 0.0
        
        # Get recent alerts (last 24 hours)
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
        recent_alerts = [
            a for a in alerts
            if datetime.fromisoformat(a.get("timestamp", "2000-01-01")).replace(tzinfo=timezone.utc) > cutoff_time
        ]
        
        # Get alerts from last 7 days
        week_cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        week_alerts = [
            a for a in alerts
            if datetime.fromisoformat(a.get("timestamp", "2000-01-01")).replace(tzinfo=timezone.utc) > week_cutoff
        ]
        
        return {
            "totalSubscribers": total_subscribers,
            "userSubscribers": user_count,
            "groupSubscribers": group_count,
            "totalAlerts": total_alerts,
            "tier1Alerts": tier_counts[1],
            "tier2Alerts": tier_counts[2],
            "tier3Alerts": tier_counts[3],
            "winRate": round(win_rate, 1),
            "recentAlerts24h": len(recent_alerts),
            "recentAlerts7d": len(week_alerts),
            "truePositives": len(true_positives),
            "falsePositives": len(false_positives),
            "lastUpdated": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        print(f"Error in get_stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")


@app.get("/api/alerts/recent")
async def get_recent_alerts(limit: int = 20, tier: Optional[int] = None, dedupe: bool = True):
    """Get recent alerts.
    
    Args:
        limit: Number of alerts to return (default: 20)
        tier: Filter by tier (1, 2, or 3) - optional
        dedupe: If True, show only latest alert per token (default: True)
    """
    try:
        # Use cached alerts for better performance
        alerts = get_cached_alerts()
        
        # #region agent log
        try:
            with open(r'c:\Users\Admin\Desktop\amaverse\.cursor\debug.log', 'a', encoding='utf-8') as f:
                import json as json_lib
                now = datetime.now(timezone.utc)
                latest_alert = max(alerts, key=lambda x: x.get("timestamp", "")) if alerts else None
                log_entry = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H3,H5",
                    "location": "api_server.py:378",
                    "message": "get_recent_alerts entry",
                    "data": {
                        "total_alerts": len(alerts),
                        "latest_token": latest_alert.get("token") if latest_alert else None,
                        "latest_timestamp": latest_alert.get("timestamp") if latest_alert else None,
                        "limit": limit,
                        "dedupe": dedupe
                    },
                    "timestamp": int(now.timestamp() * 1000)
                }
                f.write(json_lib.dumps(log_entry) + '\n')
        except Exception:
            pass
        # #endregion
        
        # Sort by timestamp (newest first)
        alerts.sort(
            key=lambda x: datetime.fromisoformat(x.get("timestamp", "2000-01-01")).replace(tzinfo=timezone.utc),
            reverse=True
        )
        
        # Deduplicate: Keep only the latest alert per token (if dedupe=True)
        # BUT: Only dedupe if there are multiple alerts for the same token within a short time window
        # This ensures recent alerts are never hidden
        if dedupe:
            seen_tokens = {}
            deduplicated = []
            for alert in alerts:
                token = alert.get("token", "").upper()
                if not token:
                    deduplicated.append(alert)  # Keep alerts without token
                    continue
                
                # Get alert timestamp
                try:
                    alert_time = datetime.fromisoformat(alert.get("timestamp", "2000-01-01")).replace(tzinfo=timezone.utc)
                except:
                    alert_time = datetime.now(timezone.utc)
                
                # If we've seen this token before, check if this alert is newer
                if token in seen_tokens:
                    existing_alert, existing_time = seen_tokens[token]
                    # Only replace if this alert is newer (within last 24 hours)
                    time_diff = (alert_time - existing_time).total_seconds()
                    if time_diff > 0 and time_diff < 86400:  # 24 hours
                        # This alert is newer - replace the old one
                        deduplicated.remove(existing_alert)
                        deduplicated.append(alert)
                        seen_tokens[token] = (alert, alert_time)
                    # If older than 24 hours, treat as separate alert (token relaunched)
                    elif time_diff >= 86400:
                        deduplicated.append(alert)
                        seen_tokens[token] = (alert, alert_time)
                else:
                    # First time seeing this token
                    seen_tokens[token] = (alert, alert_time)
                    deduplicated.append(alert)
            
            # Sort again after deduplication (newest first)
            deduplicated.sort(
                key=lambda x: datetime.fromisoformat(x.get("timestamp", "2000-01-01")).replace(tzinfo=timezone.utc),
                reverse=True
            )
            alerts = deduplicated
        
        # Filter by tier if specified
        if tier:
            filtered_alerts = []
            for alert in alerts:
                level = alert.get("level", "MEDIUM")
                # CRITICAL: Use tier field DIRECTLY from Telegram post - this is the source of truth
                alert_tier_field = alert.get("tier")
                if alert_tier_field is not None and alert_tier_field in [1, 2, 3]:
                    # Tier field exists - use it directly (this is EXACTLY what was shown in Telegram post)
                    alert_tier = alert_tier_field
                else:
                    # Only use heuristics if tier field is missing (for old alerts)
                    alert_tier = get_tier_from_level(level, alert_tier_field, alert)
                if alert_tier == tier:
                    filtered_alerts.append(alert)
            alerts = filtered_alerts
        
        # Limit results
        alerts = alerts[:limit]
        
        # #region agent log
        try:
            with open(r'c:\Users\Admin\Desktop\amaverse\.cursor\debug.log', 'a', encoding='utf-8') as f:
                import json as json_lib
                now = datetime.now(timezone.utc)
                returned_tokens = [a.get("token") for a in alerts[:5]]
                log_entry = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H5",
                    "location": "api_server.py:390",
                    "message": "alerts after filtering/limiting",
                    "data": {
                        "alerts_returned": len(alerts),
                        "first_5_tokens": returned_tokens,
                        "first_alert_timestamp": alerts[0].get("timestamp") if alerts else None
                    },
                    "timestamp": int(now.timestamp() * 1000)
                }
                f.write(json_lib.dumps(log_entry) + '\n')
        except Exception:
            pass
        # #endregion
        
        # Format alerts for frontend
        formatted_alerts = []
        for alert in alerts:
            level = alert.get("level", "MEDIUM")
            # CRITICAL: Use tier field DIRECTLY from Telegram post - this is the source of truth
            # If Telegram post says "TIER 1", tier field is 1. If it says "TIER 2", tier field is 2.
            # NO HEURISTICS - THE TELEGRAM POST DECIDES THE TIER!
            alert_tier_field = alert.get("tier")
            if alert_tier_field is not None and alert_tier_field in [1, 2, 3]:
                # Tier field exists - use it directly (this is EXACTLY what was shown in Telegram post)
                tier_num = alert_tier_field
            else:
                # Only use heuristics if tier field is missing (for old alerts)
                tier_num = get_tier_from_level(level, alert_tier_field, alert)
            
            # Get hotlist status
            try:
                hotlist_status = _get_hot_list_status(alert)
                # Extract just "Yes" or "No" for cleaner API response
                hotlist = "Yes" if "🟢" in hotlist_status or "Yes" in hotlist_status else "No"
            except Exception:
                hotlist = "No"
            
            # Get description (spicy intro)
            try:
                # Build confirmation lines and glydo line for intro generation
                confirmation_lines = _build_confirmation_lines(alert)
                glydo_line = _build_glydo_line(alert)
                description = _get_spicy_intro(alert, confirmation_lines, glydo_line)
            except Exception as e:
                # Fallback description based on matched signals
                matched = alert.get("matched_signals", [])
                if matched:
                    description = f"Alert triggered by: {', '.join(matched)}"
                else:
                    description = "Alert description not available"
            
            # CRITICAL: "Entry MCAP" = The MCAP that was shown in the Telegram post at the time it was posted
            # This is what the user sees as "Current MC" in the Telegram post
            # This is considered the "entry" MCAP because it's the MCAP at the time of the alert posting
            # Priority: current_mcap (from post) > mc_usd (saved current MC) > entry_mc (fallback)
            entry_mcap = None
            
            # First try current_mcap field (this is the MCAP that was shown in the Telegram post)
            current_mcap_field = alert.get("current_mcap")
            if current_mcap_field is not None:
                try:
                    entry_mcap = float(current_mcap_field)
                except (ValueError, TypeError):
                    pass
            
            # If no current_mcap field, try mc_usd (this should be the current MCAP from the post)
            if entry_mcap is None:
                mc_usd = alert.get("mc_usd")
                if mc_usd is not None:
                    try:
                        entry_mcap = float(mc_usd)
                    except (ValueError, TypeError):
                        pass
            
            # Fallback: try entry_mc (old field name, but might have the value we need)
            if entry_mcap is None:
                entry_mc_old = alert.get("entry_mc")
                if entry_mc_old is not None:
                    try:
                        entry_mcap = float(entry_mc_old)
                    except (ValueError, TypeError):
                        pass
            
            # Last resort: try other field names
            if entry_mcap is None:
                other_fields = ["live_mcap", "market_cap", "mcap"]
                for field in other_fields:
                    value = alert.get(field)
                    if value is not None:
                        try:
                            entry_mcap = float(value)
                            break
                        except (ValueError, TypeError):
                            continue
            
            # Get confirmation count
            confirmation_count = 0
            confirmations = alert.get("confirmations")
            if isinstance(confirmations, dict):
                confirmation_count = confirmations.get("total", 0)
            elif isinstance(confirmations, (int, float)):
                confirmation_count = int(confirmations)
            else:
                # Fallback: count matched signals
                matched_signals = alert.get("matched_signals", [])
                confirmation_count = len(matched_signals)
            
            # Get cohort time relative (e.g., "0s ago", "5m ago")
            cohort_time_relative = None
            try:
                cohort_start = alert.get("cohort_start_utc") or alert.get("cohort_start_ist")
                if cohort_start:
                    if isinstance(cohort_start, str):
                        cohort_dt = datetime.fromisoformat(cohort_start.replace("Z", "+00:00"))
                    else:
                        cohort_dt = cohort_start
                    
                    if cohort_dt.tzinfo is None:
                        cohort_dt = cohort_dt.replace(tzinfo=timezone.utc)
                    
                    now = datetime.now(timezone.utc)
                    delta = now - cohort_dt
                    
                    if delta.total_seconds() >= 0:
                        total_seconds = int(delta.total_seconds())
                        if total_seconds < 60:
                            cohort_time_relative = f"{total_seconds}s ago"
                        else:
                            minutes = total_seconds // 60
                            seconds = total_seconds % 60
                            if minutes < 60:
                                if seconds > 0:
                                    cohort_time_relative = f"{minutes}m {seconds}s ago"
                                else:
                                    cohort_time_relative = f"{minutes}m ago"
                            else:
                                hours = minutes // 60
                                minutes = minutes % 60
                                if hours < 24:
                                    if minutes > 0:
                                        cohort_time_relative = f"{hours}h {minutes}m ago"
                                    else:
                                        cohort_time_relative = f"{hours}h ago"
                                else:
                                    days = hours // 24
                                    hours = hours % 24
                                    if days < 7:
                                        if hours > 0:
                                            cohort_time_relative = f"{days}d {hours}h ago"
                                        else:
                                            cohort_time_relative = f"{days}d ago"
                                    else:
                                        cohort_time_relative = f"{days}d ago"
            except Exception:
                pass  # Silently fail if cohort time calculation fails
            
            formatted_alert = {
                "id": alert.get("contract", "")[:8] + "_" + alert.get("timestamp", "")[:10],
                "token": alert.get("token", "UNKNOWN"),
                "tier": tier_num,
                "level": level,
                "timestamp": alert.get("timestamp"),
                "contract": alert.get("contract"),
                "score": alert.get("score"),
                "liquidity": alert.get("liq_usd"),
                "callers": alert.get("callers"),
                "subs": alert.get("subs"),
                "matchedSignals": alert.get("matched_signals", []),
                "tags": alert.get("tags", []),
                "hotlist": hotlist,
                "description": description,
                "entryMc": entry_mcap,  # Entry MCAP = MCAP shown in Telegram post at time of posting (this is the "Current MC" from the post)
                "confirmationCount": confirmation_count,  # Number of confirmations
                "cohortTime": cohort_time_relative  # Relative time like "0s ago"
            }
            formatted_alerts.append(formatted_alert)
        
        return {
            "alerts": formatted_alerts,
            "count": len(formatted_alerts),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        print(f"Error in get_recent_alerts: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching alerts: {str(e)}")


@app.get("/api/subscribers")
async def get_subscribers():
    """Get subscriber information."""
    try:
        subscriptions_data = load_json_file(SUBSCRIPTIONS_FILE, {"users": []})
        alert_groups_data = load_json_file(ALERT_GROUPS_FILE, {"groups": []})
        user_prefs_data = load_json_file(USER_PREFERENCES_FILE, {"preferences": {}})
        
        return {
            "totalSubscribers": len(subscriptions_data.get("users", [])) + len(alert_groups_data.get("groups", [])),
            "userSubscribers": len(subscriptions_data.get("users", [])),
            "groupSubscribers": len(alert_groups_data.get("groups", [])),
            "usersWithPreferences": len(user_prefs_data.get("preferences", {})),
            "lastUpdated": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        print(f"Error in get_subscribers: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching subscribers: {str(e)}")


@app.get("/api/alerts/tiers")
async def get_tier_breakdown():
    """Get alert breakdown by tier."""
    try:
        # Use cached alerts for better performance
        alerts = get_cached_alerts()
        
        tier_breakdown = {
            1: {"count": 0, "alerts": []},
            2: {"count": 0, "alerts": []},
            3: {"count": 0, "alerts": []}
        }
        
        for alert in alerts:
            level = alert.get("level", "MEDIUM")
            # CRITICAL: Use tier field DIRECTLY from Telegram post - this is the source of truth
            alert_tier_field = alert.get("tier")
            if alert_tier_field is not None and alert_tier_field in [1, 2, 3]:
                # Tier field exists - use it directly (this is EXACTLY what was shown in Telegram post)
                tier = alert_tier_field
            else:
                # Only use heuristics if tier field is missing (for old alerts)
                tier = get_tier_from_level(level, alert_tier_field, alert)
            tier_breakdown[tier]["count"] += 1
            
            # Add to recent alerts for this tier (last 10)
            if len(tier_breakdown[tier]["alerts"]) < 10:
                tier_breakdown[tier]["alerts"].append({
                    "token": alert.get("token"),
                    "timestamp": alert.get("timestamp"),
                    "contract": alert.get("contract")
                })
        
        return {
            "tier1": tier_breakdown[1],
            "tier2": tier_breakdown[2],
            "tier3": tier_breakdown[3],
            "total": len(alerts)
        }
    except Exception as e:
        print(f"Error in get_tier_breakdown: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching tier breakdown: {str(e)}")


@app.get("/api/alerts/stats/daily")
async def get_daily_stats(days: int = 7):
    """Get daily statistics for charts."""
    try:
        # Use cached alerts for better performance
        alerts = get_cached_alerts()
        
        # Group alerts by date
        daily_stats = defaultdict(lambda: {"total": 0, "tier1": 0, "tier2": 0, "tier3": 0})
        
        for alert in alerts:
            try:
                alert_time = datetime.fromisoformat(alert.get("timestamp", "2000-01-01")).replace(tzinfo=timezone.utc)
                days_ago = (datetime.now(timezone.utc) - alert_time).days
                
                if days_ago <= days:
                    date_key = alert_time.strftime("%Y-%m-%d")
                    daily_stats[date_key]["total"] += 1
                    
                    level = alert.get("level", "MEDIUM")
                    # CRITICAL: Use tier field DIRECTLY from Telegram post - this is the source of truth
                    alert_tier_field = alert.get("tier")
                    if alert_tier_field is not None and alert_tier_field in [1, 2, 3]:
                        # Tier field exists - use it directly (this is EXACTLY what was shown in Telegram post)
                        tier = alert_tier_field
                    else:
                        # Only use heuristics if tier field is missing (for old alerts)
                        tier = get_tier_from_level(level, alert_tier_field, alert)
                    daily_stats[date_key][f"tier{tier}"] += 1
            except Exception:
                continue
        
        # Convert to list format for charts
        chart_data = []
        for i in range(days):
            date = (datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d")
            stats = daily_stats.get(date, {"total": 0, "tier1": 0, "tier2": 0, "tier3": 0})
            chart_data.append({
                "date": date,
                **stats
            })
        
        chart_data.reverse()  # Oldest to newest
        
        return {
            "period": days,
            "data": chart_data
        }
    except Exception as e:
        print(f"Error in get_daily_stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching daily stats: {str(e)}")


@app.post("/api/cache/refresh")
async def refresh_cache():
    """Force cache refresh (admin endpoint)."""
    invalidate_cache()
    return {"status": "success", "message": "Cache invalidated, will refresh on next request"}


if __name__ == "__main__":
    import uvicorn
    # Railway uses PORT environment variable, fallback to 5000 for local dev
    port = int(os.getenv("PORT", "5000"))
    
    # CRITICAL: Invalidate cache on startup to ensure fresh data
    invalidate_cache()
    
    # Log file path being used
    print("🚀 Starting SolBoy Alerts API Server...")
    print(f"📁 Reading alerts from: {KPI_LOGS_FILE}")
    print(f"   File exists: {KPI_LOGS_FILE.exists()}")
    if KPI_LOGS_FILE.exists():
        file_size = KPI_LOGS_FILE.stat().st_size
        print(f"   File size: {file_size:,} bytes")
    
    print(f"📡 API will be available at: http://0.0.0.0:{port}")
    print(f"📖 API docs at: http://0.0.0.0:{port}/docs")
    print(f"💚 Health check: http://0.0.0.0:{port}/api/health")
    print(f"🔄 Cache refresh: http://0.0.0.0:{port}/api/cache/refresh")
    uvicorn.run(app, host="0.0.0.0", port=port)



