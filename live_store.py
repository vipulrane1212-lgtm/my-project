"""
live_store.py

TTL-aware in-memory store with optional Redis backing for:
- parsed events
- cohorts
- alerts
- dedupe sets and cursors
"""

from __future__ import annotations

import json
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None


def _now_ts() -> float:
    return time.time()


@dataclass
class StoredItem:
    value: Any
    expires_at: float


class InMemoryTTLStore:
    """Simple in-memory TTL store (fallback when Redis is unavailable)."""

    def __init__(self):
        self._items: Dict[str, StoredItem] = {}
        self._events_by_token: defaultdict[str, List[Tuple[float, Dict[str, Any]]]] = defaultdict(list)

    def _cleanup(self):
        now = _now_ts()
        expired_keys = [k for k, v in self._items.items() if v.expires_at <= now]
        for k in expired_keys:
            self._items.pop(k, None)

        # Cleanup per-token indexes
        for token, events in list(self._events_by_token.items()):
            filtered = [(ts, ev) for ts, ev in events if ts > now]
            if filtered:
                self._events_by_token[token] = filtered
            else:
                self._events_by_token.pop(token, None)

    def set_json(self, key: str, value: Any, ttl_seconds: int):
        self._cleanup()
        self._items[key] = StoredItem(value=value, expires_at=_now_ts() + ttl_seconds)

    def get_json(self, key: str) -> Optional[Any]:
        self._cleanup()
        item = self._items.get(key)
        if not item:
            return None
        if item.expires_at <= _now_ts():
            self._items.pop(key, None)
            return None
        return item.value

    def add_event_for_token(self, token: str, timestamp_ts: float, event_key: str, ttl_seconds: int):
        self._cleanup()
        # Store expiry alongside the event key for cleanup
        self._events_by_token[token].append((timestamp_ts + ttl_seconds, event_key))

    def get_event_keys_for_token(self, token: str) -> List[str]:
        self._cleanup()
        return [ev_key for _exp, ev_key in self._events_by_token.get(token, [])]


class RedisTTLStore:
    """Redis-backed store (uses JSON serialization)."""

    def __init__(self, redis_url: str):
        if redis is None:
            raise RuntimeError("redis package not installed")
        self.client = redis.from_url(redis_url, decode_responses=True)

    def set_json(self, key: str, value: Any, ttl_seconds: int):
        self.client.setex(key, ttl_seconds, json.dumps(value, default=str))

    def get_json(self, key: str) -> Optional[Any]:
        raw = self.client.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return None

    # For Redis we use sorted sets to index events by token
    def add_event_for_token(self, token: str, timestamp_ts: float, event_key: str, ttl_seconds: int):
        pipe = self.client.pipeline()
        pipe.zadd(f"events_by_token:{token}", {event_key: timestamp_ts})
        pipe.expire(f"events_by_token:{token}", ttl_seconds)
        pipe.execute()

    def get_event_keys_for_token(self, token: str) -> List[str]:
        return self.client.zrange(f"events_by_token:{token}", 0, -1)


class LiveStore:
    """
    Thin wrapper that abstracts storage backend.
    Exposes the minimal set of operations needed by the monitor.
    """

    def __init__(self, use_redis_url: Optional[str] = None):
        if use_redis_url:
            self.backend = RedisTTLStore(use_redis_url)
        else:
            self.backend = InMemoryTTLStore()

    # Generic key helpers
    def set(self, key: str, value: Any, ttl_hours: float):
        self.backend.set_json(key, value, int(ttl_hours * 3600))

    def get(self, key: str) -> Optional[Any]:
        return self.backend.get_json(key)

    # Dedupe
    def is_processed(self, feed: str, message_id: str) -> bool:
        return self.get(f"processed:{feed}:{message_id}") is not None

    def mark_processed(self, feed: str, message_id: str, ttl_hours: float):
        self.set(f"processed:{feed}:{message_id}", True, ttl_hours)

    # Events
    def store_event(self, event_key: str, event: Dict[str, Any], ttl_hours: float):
        self.set(event_key, event, ttl_hours)
        token = event.get("token") or event.get("contract") or "unknown"
        ts = event.get("timestamp_ts") or _now_ts()
        self.backend.add_event_for_token(token, ts, event_key, int(ttl_hours * 3600))
        # cache symbol->contract for future matching
        if event.get("token") and event.get("contract"):
            self.set_symbol_contract(event["token"], event["contract"], ttl_hours)

    def get_event(self, event_key: str) -> Optional[Dict[str, Any]]:
        return self.get(event_key)

    def get_events_for_token(self, token: str) -> List[Dict[str, Any]]:
        events: List[Dict[str, Any]] = []
        for ev_key in self.backend.get_event_keys_for_token(token):
            ev = self.get(ev_key)
            if ev:
                events.append(ev)
        # Sort by timestamp
        return sorted(events, key=lambda e: e.get("timestamp_ts", 0))

    # Cohorts
    def get_cohort(self, token: str) -> Optional[Dict[str, Any]]:
        return self.get(f"cohort:{token}")

    def set_cohort(self, token: str, cohort: Dict[str, Any], ttl_hours: float):
        self.set(f"cohort:{token}", cohort, ttl_hours)

    # Alerts
    def store_alert(self, alert_id: str, alert: Dict[str, Any], ttl_hours: float):
        self.set(f"alert:{alert_id}", alert, ttl_hours)

    def get_alert(self, alert_id: str) -> Optional[Dict[str, Any]]:
        return self.get(f"alert:{alert_id}")

    # MCAP cache (for fallback)
    def set_last_mcap(self, token: str, mc_value: float, source: str, ttl_minutes: int):
        payload = {"mc_usd": mc_value, "source": source, "ts": _now_ts()}
        self.backend.set_json(f"last_mcap:{token}", payload, ttl_minutes * 60)

    def get_last_mcap(self, token: str) -> Optional[Dict[str, Any]]:
        return self.backend.get_json(f"last_mcap:{token}")

    # Symbol -> contract cache (for Glydo / CA-missing)
    def set_symbol_contract(self, symbol: str, contract: str, ttl_hours: float):
        key = f"symbol_contract:{symbol.upper()}"
        self.backend.set_json(key, {"contract": contract}, int(ttl_hours * 3600))

    def get_symbol_contract(self, symbol: str) -> Optional[str]:
        key = f"symbol_contract:{symbol.upper()}"
        val = self.backend.get_json(key)
        if isinstance(val, dict):
            return val.get("contract")
        return None

    # Cursor
    def get_cursor(self, feed_name: str) -> Optional[Dict[str, Any]]:
        return self.get(f"cursor:{feed_name}")

    def set_cursor(self, feed_name: str, cursor: Dict[str, Any], ttl_hours: float):
        self.set(f"cursor:{feed_name}", cursor, ttl_hours)


__all__ = ["LiveStore"]

