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
SUBSCRIPTIONS_FILE = BASE_DIR / "subscriptions.json"
KPI_LOGS_FILE = BASE_DIR / "kpi_logs.json"
ALERT_GROUPS_FILE = BASE_DIR / "alert_groups.json"
USER_PREFERENCES_FILE = BASE_DIR / "user_preferences.json"


def load_json_file(file_path: Path, default: dict = None) -> dict:
    """Safely load JSON file."""
    if default is None:
        default = {}
    try:
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return default
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return default


def get_tier_from_level(level: str, alert_tier: Optional[int] = None, alert: Optional[Dict] = None) -> int:
    """Convert alert level to tier number.
    
    IMPORTANT: 
    - Tier 1 alerts are stored as level="HIGH"
    - Tier 2 and Tier 3 alerts are both stored as level="MEDIUM"
    - We can't distinguish Tier 2 from Tier 3 without the tier field or additional data
    
    Use alert_tier if available (from the tier field in the alert), otherwise infer from level and alert data.
    """
    # If tier is explicitly provided, use it (most reliable)
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
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "files": {
            "subscriptions": SUBSCRIPTIONS_FILE.exists(),
            "kpi_logs": KPI_LOGS_FILE.exists(),
            "alert_groups": ALERT_GROUPS_FILE.exists(),
            "user_preferences": USER_PREFERENCES_FILE.exists(),
        }
    }


@app.get("/api/stats")
async def get_stats():
    """Get real-time statistics for the website."""
    try:
        # Load data
        subscriptions_data = load_json_file(SUBSCRIPTIONS_FILE, {"users": []})
        kpi_data = load_json_file(KPI_LOGS_FILE, {"alerts": [], "true_positives": [], "false_positives": []})
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
            alert_tier = alert.get("tier")  # Use tier field if available
            tier = get_tier_from_level(level, alert_tier, alert)  # Pass alert for heuristics
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
        kpi_data = load_json_file(KPI_LOGS_FILE, {"alerts": []})
        alerts = kpi_data.get("alerts", [])
        
        # Sort by timestamp (newest first)
        alerts.sort(
            key=lambda x: datetime.fromisoformat(x.get("timestamp", "2000-01-01")).replace(tzinfo=timezone.utc),
            reverse=True
        )
        
        # Deduplicate: Keep only the latest alert per token (if dedupe=True)
        if dedupe:
            seen_tokens = set()
            deduplicated = []
            for alert in alerts:
                token = alert.get("token", "").upper()
                if token and token not in seen_tokens:
                    seen_tokens.add(token)
                    deduplicated.append(alert)
            alerts = deduplicated
        
        # Filter by tier if specified
        if tier:
            filtered_alerts = []
            for alert in alerts:
                level = alert.get("level", "MEDIUM")
                alert_tier_field = alert.get("tier")  # Use tier field if available
                alert_tier = get_tier_from_level(level, alert_tier_field, alert)  # Pass alert for heuristics
                if alert_tier == tier:
                    filtered_alerts.append(alert)
            alerts = filtered_alerts
        
        # Limit results
        alerts = alerts[:limit]
        
        # Format alerts for frontend
        formatted_alerts = []
        for alert in alerts:
            level = alert.get("level", "MEDIUM")
            alert_tier_field = alert.get("tier")  # Use tier field if available (most reliable)
            tier_num = get_tier_from_level(level, alert_tier_field, alert)  # Pass alert for heuristics
            
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
            
            # Get market cap that was shown in the Telegram post
            # This should be the entry MC (market cap at alert time), not current live MC
            # Priority: entry_mc (alert time) > mc_usd (from when logged) > live_mcap (enriched)
            current_mcap = None
            
            # First try entry_mc (market cap at the time alert was triggered)
            entry_mc = alert.get("entry_mc")
            if entry_mc is not None:
                try:
                    current_mcap = float(entry_mc)
                except (ValueError, TypeError):
                    pass
            
            # If no entry_mc, try mc_usd (this is what was shown in the post)
            if current_mcap is None:
                mc_usd = alert.get("mc_usd")
                if mc_usd is not None:
                    try:
                        current_mcap = float(mc_usd)
                    except (ValueError, TypeError):
                        pass
            
            # Last resort: try other field names (but these are less reliable)
            if current_mcap is None:
                other_fields = ["live_mcap", "market_cap", "mcap"]
                for field in other_fields:
                    value = alert.get(field)
                    if value is not None:
                        try:
                            current_mcap = float(value)
                            break
                        except (ValueError, TypeError):
                            continue
            
            # For existing alerts without saved mcap, try to get from live store
            # This gets the mcap that was stored when the alert was created
            if current_mcap is None:
                try:
                    from live_store import LiveStore
                    store = LiveStore()
                    token = alert.get("token") or alert.get("contract")
                    if token:
                        last_mcap_data = store.get_last_mcap(token)
                        if last_mcap_data:
                            # get_last_mcap returns dict: {"mc_usd": value, "source": str, "ts": float}
                            if isinstance(last_mcap_data, dict):
                                mcap_value = last_mcap_data.get("mc_usd")
                                if mcap_value:
                                    current_mcap = float(mcap_value)
                except Exception:
                    pass  # Silently fail if store not available
            
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
                "currentMcap": current_mcap
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
        kpi_data = load_json_file(KPI_LOGS_FILE, {"alerts": []})
        alerts = kpi_data.get("alerts", [])
        
        tier_breakdown = {
            1: {"count": 0, "alerts": []},
            2: {"count": 0, "alerts": []},
            3: {"count": 0, "alerts": []}
        }
        
        for alert in alerts:
            level = alert.get("level", "MEDIUM")
            alert_tier_field = alert.get("tier")  # Use tier field if available
            tier = get_tier_from_level(level, alert_tier_field, alert)  # Pass alert for heuristics
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
        kpi_data = load_json_file(KPI_LOGS_FILE, {"alerts": []})
        alerts = kpi_data.get("alerts", [])
        
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
                    alert_tier_field = alert.get("tier")  # Use tier field if available
                    tier = get_tier_from_level(level, alert_tier_field, alert)  # Pass alert for heuristics
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


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting SolBoy Alerts API Server...")
    print("📡 API will be available at: http://localhost:5000")
    print("📖 API docs at: http://localhost:5000/docs")
    print("💚 Health check: http://localhost:5000/api/health")
    uvicorn.run(app, host="0.0.0.0", port=5000)



