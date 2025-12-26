"""
live_config.py

Config loader for the Live Memecoin Monitor.
- Provides sane defaults from the Live Strategy README.
- Allows overriding via JSON files:
    * automation_rules.json  (weights / thresholds / windows / retention)
    * channels.json          (alert routing targets)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

DEFAULT_CONFIG: Dict[str, Any] = {
    "confirm_window_minutes": 30,
    "tail_window_hours": 6,
    "mcap_fallback": {
        "glydo_use_previous": True,
        "previous_mcap_ttl_minutes": 60,
    },
    "weights": {
        "base_2x": 1.0,
        "base_3x": 1.8,
        "glydo": 1.5,
        "sol_sb1": 2.5,
        "sol_sb_mb": 2.1,
        "kolscope": 1.5,
        "early_trending": 1.0,
        "large_buy": 0.8,
        "momentum": 0.8,
        "pfbf_volume": 0.8,
        "spydefi": 0.8,
        "whalebuy": 0.8,
        "contract_present": 0.8,
        "mc_sweet_spot": 1.0,
        "liq_ok": 0.5,
        "callers_boost_factor": 1.2,
    },
    "thresholds": {
        "high_alert": 5.0,
        "medium_alert": 3.0,
        "liq_min_usd": 5000,
        "mc_min_usd": 5000,
    },
    "retention": {
        "raw_feed_ttl_hours": 168,  # 7 days
        "cohort_ttl_hours": 720,    # 30 days
        "alerts_ttl_hours": 168,    # 7 days
        "cursor_ttl_hours": 8760,   # 365 days
    },
}

DEFAULT_CHANNELS: Dict[str, Any] = {
    "channels": {
        "alerts_high": {"chat_id": None, "name": "alerts_high", "notify_webhook": None},
        "alerts_medium": {"chat_id": None, "name": "alerts_medium", "notify_webhook": None},
        "ingest_errors": {"chat_id": None, "name": "ingest_errors", "notify_webhook": None},
        "ops": {"chat_id": None, "name": "ops", "notify_webhook": None},
    }
}


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def load_config(config_path: str | Path = "automation_rules.json") -> Dict[str, Any]:
    """Load automation config with defaults applied."""
    config_path = Path(config_path)
    user_cfg = _load_json(config_path)

    merged = DEFAULT_CONFIG.copy()
    for key, val in DEFAULT_CONFIG.items():
        if isinstance(val, dict):
            merged[key] = {**val, **user_cfg.get(key, {})}
    # top-level overrides
    for k, v in user_cfg.items():
        if k not in merged:
            merged[k] = v
    return merged


def load_channels(channels_path: str | Path = "channels.json") -> Dict[str, Any]:
    """Load channel routing config with defaults applied."""
    channels_path = Path(channels_path)
    user_cfg = _load_json(channels_path)
    merged = DEFAULT_CHANNELS.copy()
    merged["channels"] = {**DEFAULT_CHANNELS["channels"], **user_cfg.get("channels", {})}
    return merged


__all__ = ["load_config", "load_channels", "DEFAULT_CONFIG", "DEFAULT_CHANNELS"]

