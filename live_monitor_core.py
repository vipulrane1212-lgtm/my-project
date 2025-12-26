"""
live_monitor_core.py

End-to-end Live Memecoin Monitoring pipeline:
- Normalizes parsed messages into events
- Dedupe + cursor tracking
- Cohort detection (first XTRACK 2x/3x)
- Scoring engine (confirmation + tail windows)
- MCAP merge rules with Glydo fallback
- Alert routing (returns alert payloads for caller to send)
"""

from __future__ import annotations

import math
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from live_config import load_channels, load_config
from live_store import LiveStore
from tiered_strategy_engine import TieredStrategyEngine


def _to_datetime(ts: str | datetime) -> datetime:
    if isinstance(ts, datetime):
        return ts.astimezone(timezone.utc)
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)


def _ts(dt: datetime) -> float:
    return dt.timestamp()


def parse_callers_subs(text: str) -> Tuple[Optional[int], Optional[int]]:
    callers = None
    subs = None
    if text:
        c_match = re.search(r"Callers:\s*([0-9]+)", text, re.IGNORECASE)
        s_match = re.search(r"Subs:\s*([0-9]+)", text, re.IGNORECASE)
        if c_match:
            try:
                callers = int(c_match.group(1))
            except Exception:
                pass
        if s_match:
            try:
                subs = int(s_match.group(1))
            except Exception:
                pass
    return callers, subs


class LiveMemecoinMonitor:
    """Core monitor that can run in backtest or live mode."""

    def __init__(
        self,
        config_path: str = "automation_rules.json",
        channels_path: str = "channels.json",
        redis_url: Optional[str] = None,
    ):
        self.config = load_config(config_path)
        self.channels = load_channels(channels_path)
        
        # Validate configuration
        self._validate_config()
        
        # Initialize store with error handling
        try:
            self.store = LiveStore(use_redis_url=redis_url)
        except Exception as e:
            print(f"⚠️  Warning: Redis store initialization failed: {e}. Using in-memory store.")
            self.store = LiveStore(use_redis_url=None)  # Fallback to in-memory

        # Support both old and new config structures
        if "timers" in self.config:
            self.confirm_window = timedelta(minutes=self.config["timers"]["confirm_window_minutes"])
            self.tail_window = timedelta(hours=self.config["timers"]["tail_window_hours"])
        else:
            self.confirm_window = timedelta(minutes=self.config.get("confirm_window_minutes", 30))
            self.tail_window = timedelta(hours=self.config.get("tail_window_hours", 6))
        
        self.retention = self.config.get("retention", {})
        
        # Support both old and new weight structures
        if "scoring" in self.config:
            self.weights = {}  # Legacy access - will use scoring structure directly
        else:
            self.weights = self.config.get("weights", {})
        
        # Support both old and new threshold structures
        if "thresholds" in self.config and isinstance(self.config["thresholds"], dict):
            if "high_alert" in self.config["thresholds"]:
                # Old structure (has high_alert, medium_alert, etc.)
                self.thresholds = self.config["thresholds"]
            elif "high" in self.config["thresholds"]:
                # New structure (has high, medium, watch)
                self.thresholds = {
                    "high_alert": self.config["thresholds"].get("high", 70),
                    "medium_alert": self.config["thresholds"].get("medium", 50),
                    "watch_alert": self.config["thresholds"].get("watch", 30),
                    "liq_min_usd": self.config.get("thresholds", {}).get("liq_min_usd", 5000),
                    "mc_min_usd": self.config.get("thresholds", {}).get("mc_min_usd", 5000),
                }
            else:
                self.thresholds = self.config["thresholds"]
        else:
            self.thresholds = self.config.get("thresholds", {})
        
        # Add liq_min_usd and mc_min_usd if missing (for backward compatibility)
        if "liq_min_usd" not in self.thresholds:
            self.thresholds["liq_min_usd"] = 5000
        if "mc_min_usd" not in self.thresholds:
            self.thresholds["mc_min_usd"] = 5000
        
        # Ensure high_alert and medium_alert exist (defaults for multiplicative strategy)
        if "high_alert" not in self.thresholds:
            self.thresholds["high_alert"] = 5.0
        if "medium_alert" not in self.thresholds:
            self.thresholds["medium_alert"] = 3.0
        
        self.mcap_fallback = self.config.get("mcap_fallback", {"glydo_use_previous": True, "previous_mcap_ttl_minutes": 60})
        
        # Initialize tiered strategy engine
        self.strategy_engine = TieredStrategyEngine()
        
        # Alert rate tracking for dynamic thresholding
        self._alert_timestamps: List[float] = []  # Track HIGH alert timestamps
        
        # Track recent alerts by token to prevent duplicates
        self._recent_alerts_by_token: Dict[str, float] = {}  # token -> last_alert_timestamp

    def _validate_config(self) -> None:
        """Validate configuration structure - HARD REQUIRE scoring structure."""
        if not isinstance(self.config, dict):
            raise ValueError("Config must be a dictionary")

        # HARD REQUIRE: Must have scoring structure
        if "scoring" not in self.config:
            raise ValueError("Config must contain 'scoring' section - legacy weights not supported")

        # HARD REQUIRE: Must have thresholds structure
        if "thresholds" not in self.config:
            raise ValueError("Config must contain 'thresholds' section")

        # HARD REQUIRE: Must have timers structure
        if "timers" not in self.config:
            raise ValueError("Config must contain 'timers' section")

        # Validate scoring structure
        scoring = self.config["scoring"]
        required_scoring_keys = ["base", "sources", "meta"]
        for key in required_scoring_keys:
            if key not in scoring:
                raise ValueError(f"scoring section must contain '{key}'")

        # Validate thresholds structure
        thresholds = self.config["thresholds"]
        required_threshold_keys = ["high", "medium"]
        for key in required_threshold_keys:
            if key not in thresholds:
                raise ValueError(f"thresholds section must contain '{key}'")
            
            # Validate cap
            cap = scoring.get("cap", 100)
            if not isinstance(cap, (int, float)) or cap <= 0:
                raise ValueError(f"Invalid score cap: {cap} (must be > 0)")
            
            # Validate weights are numeric
            if "sources" in scoring:
                for source, weight in scoring["sources"].items():
                    if not isinstance(weight, (int, float)):
                        raise ValueError(f"Invalid weight for {source}: {weight} (must be numeric)")

    def _get_recent_alert_rate(self) -> int:
        """F: Get recent HIGH alert rate (alerts per day)."""
        now = _ts(datetime.now(timezone.utc))
        day_ago = now - (24 * 3600)
        
        # Clean old timestamps
        self._alert_timestamps = [ts for ts in self._alert_timestamps if ts > day_ago]
        
        return len(self._alert_timestamps)

    # -----------------------------
    # Normalization helpers
    # -----------------------------
    def normalize_event(
        self,
        feed_name: str,
        message_id: str,
        timestamp: datetime,
        token: str,
        contract: Optional[str],
        raw_text: str,
        multiplier: Optional[float] = None,
        mc_usd: Optional[float] = None,
        liquidity_usd: Optional[float] = None,
        buy_size_sol: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Build normalized event schema from parsed message data."""
        # Validate inputs
        if not token or not isinstance(token, str):
            raise ValueError(f"Invalid token: {token}")
        
        if not feed_name or not isinstance(feed_name, str):
            raise ValueError(f"Invalid feed_name: {feed_name}")
        
        # Validate numeric fields
        if multiplier is not None:
            try:
                multiplier = float(multiplier)
                if multiplier < 0:
                    multiplier = None
            except (ValueError, TypeError):
                multiplier = None
        
        if mc_usd is not None:
            try:
                mc_usd = float(mc_usd)
                if mc_usd < 0:
                    mc_usd = None
            except (ValueError, TypeError):
                mc_usd = None
        
        if liquidity_usd is not None:
            try:
                liquidity_usd = float(liquidity_usd)
                if liquidity_usd < 0:
                    liquidity_usd = None
            except (ValueError, TypeError):
                liquidity_usd = None
        
        if buy_size_sol is not None:
            try:
                buy_size_sol = float(buy_size_sol)
                if buy_size_sol < 0:
                    buy_size_sol = None
            except (ValueError, TypeError):
                buy_size_sol = None
        
        # Validate timestamp
        try:
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            timestamp = timestamp.astimezone(timezone.utc)
        except Exception:
            timestamp = datetime.now(timezone.utc)
        
        callers, subs = parse_callers_subs(raw_text or "")

        # Try to fill missing contract from cache (with error handling)
        cached_contract = None
        if not contract and token:
            try:
                cached_contract = self.store.get_symbol_contract(token)
            except Exception:
                pass  # Graceful degradation if cache fails

        event = {
            "feed_name": feed_name,
            "message_id": str(message_id),
            "timestamp_utc": timestamp.isoformat(),
            "timestamp_ts": _ts(timestamp),
            "token": token,
            "contract": contract or cached_contract,
            "multiplier": multiplier,
            "mc_usd": mc_usd,
            "mc_source": feed_name if mc_usd is not None else None,
            "liquidity_usd": liquidity_usd,
            "buy_size_sol": buy_size_sol,  # Store buy size in SOL
            "callers": callers,
            "subs": subs,
            "holders": None,
            "raw_text": raw_text or "",
            "parsed_at": datetime.now(timezone.utc).isoformat(),
        }
        return event

    # -----------------------------
    # Cohort + scoring
    # -----------------------------
    def _ensure_cohort(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create cohort on first XTRACK 2x/3x signal."""
        token = event["token"]
        existing = self.store.get_cohort(token)
        if existing:
            return existing

        if event["feed_name"].startswith("xtrack") and event.get("multiplier"):
            mult = float(event["multiplier"])
            if mult >= 2.0:
                # Support both old and new weight structures
                if "scoring" in self.config:
                    base_config = self.config["scoring"]["base"]
                    base_weight = float(base_config.get("3x", 20)) if mult >= 3.0 else float(base_config.get("2x", 12))
                else:
                    base_weight = float(self.weights.get("base_3x", 20)) if mult >= 3.0 else float(self.weights.get("base_2x", 12))
                cohort = {
                    "token": token,
                    "contract": event.get("contract"),
                    "cohort_start": event["timestamp_utc"],
                    "cohort_ts": event["timestamp_ts"],
                    "base_multiplier": mult,
                    "base_weight": base_weight,
                    "feed_name": event["feed_name"],
                    "message_id": event["message_id"],
                    "alert_level": None,
                    "first_seen_ts": event["timestamp_ts"],  # Track first appearance for early bonus
                    "entry_mc": event.get("mc_usd"),  # Store entry MC from XTRACK event
                }
                self.store.set_cohort(token, cohort, self.retention["cohort_ttl_hours"])
                return cohort
        return existing

    def _latest_metric(self, events: List[Dict[str, Any]], key: str, at_ts: float) -> Tuple[Optional[float], Optional[str], Optional[datetime]]:
        """Pick latest value for a metric at or before at_ts."""
        candidate = None
        source = None
        when = None
        for ev in events:
            ts = ev.get("timestamp_ts", 0)
            if ts <= at_ts and ev.get(key) is not None:
                if candidate is None or ts > _ts(when):  # type: ignore[arg-type]
                    candidate = ev[key]
                    source = ev.get("mc_source") if key == "mc_usd" else ev.get("feed_name")
                    when = datetime.fromtimestamp(ts, tz=timezone.utc)
        return candidate, source, when

    def _resolve_mcap(self, token: str, at_ts: float, events: List[Dict[str, Any]]) -> Tuple[Optional[float], str]:
        """MCAP merge with prioritized fallback order: dexscreener_live → gmgn → sources → cache → glydo_72h"""
        # Priority order: dexscreener_live → gmgn → kolscope/spydefi/momentum → symbol→CA cache → glydo_fallback_72h
        
        # 1. dexscreener_live (from mc_source field)
        for ev in events:
            ts = ev.get("timestamp_ts", 0)
            if ts <= at_ts and ev.get("mc_usd") is not None:
                mc_source = ev.get("mc_source") or ""
                if "dexscreener" in mc_source.lower() or mc_source == "dexscreener_live":
                    return ev["mc_usd"], "dexscreener_live"
        
        # 2. gmgn (from mc_source field)
        for ev in events:
            ts = ev.get("timestamp_ts", 0)
            if ts <= at_ts and ev.get("mc_usd") is not None:
                mc_source = ev.get("mc_source") or ""
                if "gmgn" in mc_source.lower():
                    return ev["mc_usd"], "gmgn"
        
        # 3. kolscope/spydefi/momentum (from feed_name or mc_source)
        priority_sources = ["kolscope", "spydefi", "momentum_tracker"]
        for source_name in priority_sources:
            for ev in events:
                ts = ev.get("timestamp_ts", 0)
                if ts <= at_ts and ev.get("mc_usd") is not None:
                    feed = ev.get("feed_name") or ""
                    mc_source = ev.get("mc_source") or ""
                    if source_name in feed or source_name in mc_source:
                        return ev["mc_usd"], f"cached_{source_name}"
        
        # 4. Any other source from events (latest value)
        mc, source, _ = self._latest_metric(events, "mc_usd", at_ts)
        if mc is not None and source:
            # Mark as cached if not already marked
            if not source.startswith("cached_") and source not in ["dexscreener_live", "gmgn", "glydo_fallback_72h"]:
                return mc, f"cached_{source}"
            return mc, source

        # 5. TTL cache (symbol→CA cache)
        last_mc = self.store.get_last_mcap(token)
        if last_mc:
            cached_source = last_mc.get("source", "cached")
            if not cached_source.startswith("cached_"):
                cached_source = f"cached_{cached_source}"
            return last_mc.get("mc_usd"), cached_source

        # 6. 72h Glydo fallback
        glydo_ago = at_ts - 72 * 3600
        glydo_mc = None
        glydo_ts = 0
        for ev in events:
            ts = ev.get("timestamp_ts", 0)
            if glydo_ago <= ts <= at_ts and ev.get("feed_name") == "glydo" and ev.get("mc_usd") is not None:
                if ts > glydo_ts:  # Get latest glydo value
                    glydo_mc = ev["mc_usd"]
                    glydo_ts = ts
        if glydo_mc is not None:
            return glydo_mc, "glydo_fallback_72h"

        return None, "unknown"

    def _check_churn_penalty(self, cohort: Dict[str, Any], events: List[Dict[str, Any]]) -> float:
        """C: Check for churn penalty - repeated cohorts without >4x peak."""
        token = cohort.get("token")
        if not token:
            return 0.0
        
        churn_window_hours = self.thresholds.get("churn_window_hours", 48)
        churn_penalty = float(self.thresholds.get("churn_penalty", 6))
        churn_peak_threshold = float(self.thresholds.get("churn_peak_threshold", 4.0))
        
        # Check for previous cohorts in the window
        cohort_ts = cohort.get("cohort_ts", 0)
        window_start = cohort_ts - (churn_window_hours * 3600)
        
        # Look for previous cohorts in events (check XTRACK multipliers after previous cohorts)
        previous_cohorts = []
        for ev in events:
            ev_ts = ev.get("timestamp_ts", 0)
            if ev_ts < window_start or ev_ts >= cohort_ts:
                continue
            if ev.get("feed_name", "").startswith("xtrack") and ev.get("multiplier"):
                try:
                    mult = float(ev.get("multiplier", 0))
                    if mult >= 2.0:  # Previous cohort trigger
                        previous_cohorts.append((ev_ts, mult))
                except (ValueError, TypeError):
                    pass
        
        if not previous_cohorts:
            return 0.0
        
        # Check if any previous cohort reached >4x peak
        for prev_ts, prev_mult in previous_cohorts:
            # Check for peak multiplier after this cohort
            for ev in events:
                ev_ts = ev.get("timestamp_ts", 0)
                if ev_ts < prev_ts:
                    continue
                if ev.get("feed_name", "").startswith("xtrack") and ev.get("multiplier"):
                    try:
                        peak_mult = float(ev.get("multiplier", 0))
                        if peak_mult >= churn_peak_threshold:
                            return 0.0  # Found a winner, no penalty
                    except (ValueError, TypeError):
                        pass
        
        # No >4x peak found for previous cohorts - apply penalty
        return churn_penalty

    def _score_signals(self, cohort: Dict[str, Any], events: List[Dict[str, Any]]) -> Tuple[float, List[str], Dict[str, Any]]:
        """Compute score using multiplicative scoring system (automation strategy)."""
        import math
        
        cohort_ts = cohort["cohort_ts"]
        confirm_end = cohort_ts + self.confirm_window.total_seconds()
        tail_end = cohort_ts + self.tail_window.total_seconds()
        # Look BACKWARDS 6 hours to capture signals that appeared BEFORE the XTRACK event
        # Signals (SB1, SB_MB, Glydo, Whalebuy) typically appear before the cohort trigger
        window_start = cohort_ts - self.tail_window.total_seconds()  # 6 hours before cohort

        # Check if using new scoring structure or legacy weights structure
        use_new_structure = "scoring" in self.config
        if use_new_structure:
            # New structure (additive) - keep for backward compatibility
            scoring = self.config["scoring"]
            base_config = scoring["base"]
            sources_config = scoring["sources"]
            meta_config = scoring["meta"]
            callers_tiers_config = scoring.get("callers_tiers", {})
            subs_tiers_config = scoring.get("subs_tiers", {})
            buy_size_config = scoring.get("buy_size", {})
            score_cap = scoring.get("cap", 100)
        else:
            # Legacy weights structure (multiplicative) - this is the automation strategy
            base_config = None
            sources_config = None
            meta_config = None
            callers_tiers_config = None
            subs_tiers_config = None
            buy_size_config = None
            score_cap = None

        # Start with base multiplier (multiplicative scoring)
        base_mult = cohort.get("base_multiplier", 2.0)
        if use_new_structure:
            # New structure: additive scoring
            if base_mult >= 3.0:
                score = float(base_config.get("3x", 20))
            else:
                score = float(base_config.get("2x", 12))
        else:
            # Legacy structure: multiplicative scoring
            if base_mult >= 3.0:
                score = float(self.weights.get("base_3x", 1.8))
            else:
                score = float(self.weights.get("base_2x", 1.0))

        matched: List[str] = []
        seen_sources: set[str] = set()  # Dedupe: same source only counts once per cohort
        latest_liq = None
        latest_callers = None
        latest_subs = None
        buy_sizes: List[float] = []  # Track buy sizes for boosts

        # Process events with time decay
        for ev in events:
            ts = ev.get("timestamp_ts", 0)
            # Include events from 6 hours before cohort to 6 hours after
            if ts < window_start or ts > tail_end:
                continue

            # Time decay: full weight in 0-30m, 50% in 30m-6h
            # Events BEFORE cohort_ts get full weight (they're early signals)
            # Events AFTER cohort_ts get time decay
            if ts <= cohort_ts:
                weight_factor = 1.0  # Early signals get full weight
            elif ts <= confirm_end:
                weight_factor = 1.0  # Full weight in 0-30m after cohort
            else:
                weight_factor = 0.5  # 50% in 30m-6h after cohort
            
            feed = ev.get("feed_name")
            signal = None
            if feed == "glydo":
                signal = "glydo"
            elif feed == "sol_sb1":
                signal = "sol_sb1"
            elif feed == "sol_sb_mb":
                signal = "sol_sb_mb"
            elif feed == "kolscope":
                signal = "kolscope"
            elif feed == "solana_early_trending":
                signal = "solana_early_trending"
            elif feed == "large_buys_tracker":
                signal = "large_buy"
            elif feed == "momentum_tracker":
                signal = "momentum_tracker"
            elif feed == "pfbf_volume_alert":
                signal = "pfbf_volume"
            elif feed == "spydefi":
                signal = "spydefi"
            elif feed == "whalebuy":
                signal = "whalebuy"

            # Apply signal multiplier (dedupe: same source only counts once)
            if signal and signal not in seen_sources:
                seen_sources.add(signal)
                matched.append(signal)
                if use_new_structure:
                    # New structure: additive scoring
                    source_key_map = {
                        "sol_sb1": "sol_sb1",
                        "sol_sb_mb": "sol_sb_mb",
                        "glydo": "glydo",
                        "kolscope": "kolscope",
                        "whalebuy": "whalebuy",
                        "large_buy": "large_buy",
                        "momentum_tracker": "momentum_tracker",
                        "solana_early_trending": "solana_early_trending",
                        "spydefi": "spydefi",
                        "pfbf_volume": "pfbf_volume",
                    }
                    source_key = source_key_map.get(signal, "other")
                    signal_weight = float(sources_config.get(source_key, sources_config.get("other", 2)))
                    score += signal_weight * weight_factor
                else:
                    # Legacy structure: multiplicative scoring
                    # Map signal names to weight keys
                    weight_key_map = {
                        "sol_sb1": "sol_sb1",
                        "sol_sb_mb": "sol_sb_mb",
                        "glydo": "glydo",
                        "kolscope": "kolscope",
                        "whalebuy": "whalebuy",
                        "large_buy": "large_buy",
                        "momentum_tracker": "momentum",
                        "solana_early_trending": "early_trending",
                        "spydefi": "spydefi",
                        "pfbf_volume": "pfbf_volume",
                    }
                    weight_key = weight_key_map.get(signal, None)
                    if weight_key:
                        signal_multiplier = float(self.weights.get(weight_key, 1.0))
                        # Apply time decay to multiplier (interpolate between 1.0 and signal_multiplier)
                        # Full weight = signal_multiplier, decayed = closer to 1.0
                        if weight_factor < 1.0:
                            # Interpolate: 1.0 + (signal_multiplier - 1.0) * weight_factor
                            effective_multiplier = 1.0 + (signal_multiplier - 1.0) * weight_factor
                        else:
                            effective_multiplier = signal_multiplier
                        score *= effective_multiplier

            # Track latest liquidity / callers / subs for downstream fields
            if ev.get("liquidity_usd") is not None:
                latest_liq = ev["liquidity_usd"]
            if ev.get("callers") is not None:
                latest_callers = ev["callers"]
            if ev.get("subs") is not None:
                latest_subs = ev["subs"]

            # Extract buy sizes from events
            buy_size = ev.get("buy_size_sol") or ev.get("buy_size") or ev.get("buy_amount_sol")
            if buy_size is not None:
                try:
                    buy_size_float = float(buy_size)
                    if buy_size_float > 0:
                        buy_sizes.append(buy_size_float)
                except (ValueError, TypeError):
                    pass

        # Meta multipliers (multiplicative scoring)
        # Contract present
        if use_new_structure:
            # New structure: additive
            if cohort.get("contract"):
                score += float(meta_config.get("contract_present", 10))
        else:
            # Legacy structure: multiplicative
            if cohort.get("contract"):
                contract_mult = float(self.weights.get("contract_present", 0.8))
                score *= contract_mult

        # MCAP sweet spot (10K-500K)
        mc_usd, mc_src = self._resolve_mcap(cohort["token"], tail_end, events)
        if mc_usd and 10000 <= mc_usd <= 500000:
            if use_new_structure:
                score += float(meta_config.get("mc_sweet_spot", 6))
            else:
                mc_mult = float(self.weights.get("mc_sweet_spot", 1.0))
                score *= mc_mult

        # Liquidity OK
        if latest_liq is None:
            latest_liq, _, _ = self._latest_metric(events, "liquidity_usd", tail_end)
        liq_min = self.thresholds.get("liq_min_usd", 5000) if not use_new_structure else self.thresholds.get("low_liq_threshold_usd", 5000)
        if latest_liq is not None and latest_liq >= liq_min:
            if use_new_structure:
                score += float(meta_config.get("liq_ok", 4))
            else:
                liq_mult = float(self.weights.get("liq_ok", 0.5))
                score *= liq_mult

        # Callers boost (multiplicative: callers_boost_factor * log10(callers + 1))
        callers_for_boost = latest_callers
        if callers_for_boost is None:
            callers_for_boost, _, _ = self._latest_metric(events, "callers", tail_end)
        if callers_for_boost is not None and callers_for_boost > 0:
            if use_new_structure:
                # New structure: additive tiers
                if callers_for_boost >= 20:
                    score += float(callers_tiers_config.get(">=20", 22))
                elif callers_for_boost >= 10:
                    score += float(callers_tiers_config.get("10-19", 14))
                elif callers_for_boost >= 5:
                    score += float(callers_tiers_config.get("5-9", 8))
                elif callers_for_boost >= 1:
                    score += float(callers_tiers_config.get("1-4", 4))
            else:
                # Legacy structure: multiplicative boost
                callers_boost_factor = float(self.weights.get("callers_boost_factor", 1.2))
                callers_multiplier = callers_boost_factor * math.log10(callers_for_boost + 1)
                score *= callers_multiplier

        # No subs tiers, buy size boosts, churn penalty, or low liq penalty in multiplicative strategy
        # Score is already multiplicative, no need to cap (thresholds are low: 5.0/3.0)
        
        # Get subs for meta (not used in scoring for multiplicative strategy)
        subs_for_meta = latest_subs
        if subs_for_meta is None:
            subs_for_meta, _, _ = self._latest_metric(events, "subs", tail_end)

        meta = {
            "mc_usd": mc_usd,
            "mc_source": mc_src,
            "liquidity_usd": latest_liq,
            "callers": callers_for_boost,
            "subs": subs_for_meta,
            "matched_signals": matched,
            "last_buy_sol": buy_sizes[-1] if buy_sizes else None,
            "top_buy_sol": max(buy_sizes) if buy_sizes else None,
        }
        return score, matched, meta

    def _build_alert(
        self,
        cohort: Dict[str, Any],
        score: float,
        meta: Dict[str, Any],
        level: str,
        events: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        cohort_dt = _to_datetime(cohort["cohort_start"])
        alert_id = f"{cohort['token']}:{cohort['cohort_start']}:{level}"
        
        # Use buy sizes from meta (already extracted in _score_signals)
        # Fallback to extraction if not in meta
        last_buy_sol = meta.get("last_buy_sol")
        top_buy_sol = meta.get("top_buy_sol")
        
        if last_buy_sol is None or top_buy_sol is None:
            # Fallback: extract from events if not in meta
            if events:
                buy_sizes = []
                buy_timestamps = []
                for ev in events:
                    # Check for buy size in various fields
                    buy_size = ev.get("buy_size_sol") or ev.get("buy_size") or ev.get("buy_amount_sol")
                    if buy_size:
                        try:
                            buy_size_float = float(buy_size)
                            if buy_size_float > 0:
                                buy_sizes.append(buy_size_float)
                                # Track timestamp for last buy
                                ev_ts = ev.get("timestamp_ts") or ev.get("timestamp_utc")
                                if ev_ts:
                                    buy_timestamps.append((buy_size_float, ev_ts))
                        except (ValueError, TypeError):
                            pass
                
                if buy_sizes:
                    if last_buy_sol is None:
                        # Most recent buy (by timestamp if available, else last in list)
                        if buy_timestamps:
                            buy_timestamps.sort(key=lambda x: x[1], reverse=True)
                            last_buy_sol = buy_timestamps[0][0]
                        else:
                            last_buy_sol = buy_sizes[-1]
                    if top_buy_sol is None:
                        top_buy_sol = max(buy_sizes)
        
        alert_dict = {
            "alert_id": alert_id,
            "level": level,
            "token": cohort["token"],
            "contract": cohort.get("contract"),
            "score": round(score, 2),
            "cohort_start_utc": cohort_dt.isoformat(),
            "cohort_start_ist": (cohort_dt + timedelta(hours=5, minutes=30)).isoformat(),
            "mc_usd": meta.get("mc_usd"),
            "mc_source": meta.get("mc_source"),
            "liq_usd": meta.get("liquidity_usd"),
            "callers": meta.get("callers"),
            "subs": meta.get("subs"),
            "matched_signals": sorted(set(meta.get("matched_signals", []))),
            "time_since_cohort_seconds": int(_ts(datetime.now(timezone.utc)) - _ts(cohort_dt)),
            "cohort_multiplier": cohort.get("base_multiplier"),
            "last_buy_sol": last_buy_sol,
            "top_buy_sol": top_buy_sol,
        }
        
        # Add tiered strategy fields if available
        if meta.get("tier"):
            alert_dict["tier"] = meta.get("tier")
        if meta.get("glydo_in_top5") is not None:
            alert_dict["glydo_in_top5"] = meta.get("glydo_in_top5")
        if meta.get("hot_list") is not None:
            alert_dict["hot_list"] = meta.get("hot_list")
        if meta.get("confirmations"):
            alert_dict["confirmations"] = meta.get("confirmations")
        if cohort.get("entry_mc"):
            alert_dict["entry_mc"] = cohort.get("entry_mc")
        
        return alert_dict

    def ingest_event(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Ingest event with error handling."""
        try:
            return self._ingest_event_internal(event)
        except Exception as e:
            print(f"⚠️  Error ingesting event: {str(e)}")
            return []  # Return empty list on error
    
    def _ingest_event_internal(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Main entrypoint: ingest normalized event, return generated alerts."""
        feed = event["feed_name"]
        mid = str(event["message_id"])

        # Dedupe
        if self.store.is_processed(feed, mid):
            return []
        self.store.mark_processed(feed, mid, self.retention["raw_feed_ttl_hours"])

        # Persist event
        ev_key = f"event:{feed}:{mid}"
        self.store.store_event(ev_key, event, self.retention["raw_feed_ttl_hours"])
        if event.get("mc_usd") is not None:
            self.store.set_last_mcap(
                event.get("token") or event.get("contract") or "unknown",
                event["mc_usd"],
                event.get("mc_source") or feed,
                ttl_minutes=self.mcap_fallback.get("previous_mcap_ttl_minutes", 60),
            )

        # Ensure cohort if applicable
        cohort = self._ensure_cohort(event)
        if not cohort:
            return []

        # Update strategy engine with Glydo messages
        if event.get("feed_name") == "glydo":
            self.strategy_engine.update_glydo_cache(event)

        # Gather events for token
        token_events = self.store.get_events_for_token(cohort["token"])

        # Get entry MC from cohort or resolve
        entry_mc = cohort.get("entry_mc")
        if not entry_mc:
            entry_mc, mc_source = self._resolve_mcap(cohort["token"], cohort["cohort_ts"], token_events)
            if entry_mc:
                cohort["entry_mc"] = entry_mc
        else:
            mc_source = "cohort"  # MC came from cohort creation

        # Evaluate using tiered strategy
        opportunity = self.strategy_engine.evaluate_opportunity(cohort, token_events)
        
        # Determine alert level based on tier
        level = "IGNORE"
        if opportunity:
            tier = opportunity["tier"]
            if tier == 1:
                level = "HIGH"
            elif tier == 2:
                level = "MEDIUM"
            elif tier == 3:
                level = "MEDIUM"  # Tier 3 also goes to MEDIUM for now
        else:
            # No tier match - use old scoring as fallback for compatibility
            score, matched, meta = self._score_signals(cohort, token_events)
            if score >= self.thresholds.get("high", 75):
                level = "HIGH"
            elif score >= self.thresholds.get("medium", 55):
                level = "MEDIUM"

        # Build meta for alert (use opportunity data if available)
        if opportunity:
            meta = {
                "mc_usd": entry_mc,
                "mc_source": mc_source,
                "matched_signals": opportunity["confirmations"]["details"],
                "tier": opportunity["tier"],
                "glydo_in_top5": opportunity["glydo_in_top5"],
                "hot_list": opportunity["hot_list"],
                "confirmations": opportunity["confirmations"]
            }
            # Get latest callers/subs from events
            latest_callers = None
            latest_subs = None
            for ev in token_events:
                if ev.get("callers"):
                    latest_callers = ev.get("callers")
                if ev.get("subs"):
                    latest_subs = ev.get("subs")
            meta["callers"] = latest_callers
            meta["subs"] = latest_subs
        else:
            # Fallback to old scoring meta
            score, matched, meta = self._score_signals(cohort, token_events)

        # Hard cap: MCAP > $500k forces WATCH (not HIGH/MEDIUM)
        mc_usd = meta.get("mc_usd")
        if mc_usd and mc_usd > 500000 and level in {"HIGH", "MEDIUM"}:
            level = "WATCH"

        # Only send alert for HIGH/MEDIUM; WATCH/IGNORE are logged but not sent
        # Use tier as score for compatibility with alert formatter
        if opportunity:
            score = opportunity.get("tier", 0) * 25
        else:
            score, _, _ = self._score_signals(cohort, token_events)
        alert = self._build_alert(cohort, score, meta, level, events=token_events)
        
        # Enhanced deduplication: Check exact alert_id first
        if self.store.get_alert(alert["alert_id"]):
            return []
        
        # Additional check: Has an alert been sent for this token in the last 10 minutes?
        # This prevents duplicate alerts even if cohort_start timestamps differ slightly
        token = cohort['token']
        now_ts = _ts(datetime.now(timezone.utc))
        last_alert_ts = self._recent_alerts_by_token.get(token, 0)
        time_since_last_alert = now_ts - last_alert_ts
        
        if time_since_last_alert < 600:  # 10 minutes = 600 seconds
            print(f"⚠️ Skipping duplicate alert for {token} - last alert sent {int(time_since_last_alert)}s ago")
            return []
        
        # Store alert and update tracking
        self.store.store_alert(alert["alert_id"], alert, self.retention["alerts_ttl_hours"])
        self._recent_alerts_by_token[token] = now_ts
        
        # Cleanup old entries (older than 1 hour)
        cutoff = now_ts - 3600
        self._recent_alerts_by_token = {k: v for k, v in self._recent_alerts_by_token.items() if v > cutoff}
        
        # Track HIGH alerts for dynamic thresholding
        if level == "HIGH":
            self._alert_timestamps.append(now_ts)
        
        return [alert] if level in {"HIGH", "MEDIUM"} else []


__all__ = ["LiveMemecoinMonitor", "parse_callers_subs"]

