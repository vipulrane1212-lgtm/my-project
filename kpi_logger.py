#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kpi_logger.py

KPI tracking and logging for live monitoring system.
Tracks precision, recall, false positives, and alert metrics.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict

class KPILogger:
    """Track KPIs for live monitoring system."""
    
    def __init__(self, log_file: str = "kpi_logs.json"):
        self.log_file = Path(log_file)
        self.alerts: List[Dict] = []
        self.false_positives: List[Dict] = []
        self.true_positives: List[Dict] = []
        self.load_logs()
    
    def load_logs(self):
        """Load existing logs from file."""
        if self.log_file.exists():
            try:
                data = json.loads(self.log_file.read_text())
                self.alerts = data.get("alerts", [])
                self.false_positives = data.get("false_positives", [])
                self.true_positives = data.get("true_positives", [])
            except Exception:
                pass
    
    def save_logs(self):
        """Save logs to file with atomic write and error handling."""
        data = {
            "alerts": self.alerts,
            "false_positives": self.false_positives,
            "true_positives": self.true_positives,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        
        # Atomic write: write to temp file first, then rename
        # This prevents corruption if the process crashes during write
        temp_file = self.log_file.with_suffix('.json.tmp')
        try:
            # Write to temporary file first
            json_str = json.dumps(data, indent=2, ensure_ascii=False)
            temp_file.write_text(json_str, encoding='utf-8')
            
            # Atomic rename (works on most filesystems)
            temp_file.replace(self.log_file)
            
            # Verify the file was written correctly
            if not self.log_file.exists():
                raise IOError(f"Failed to save {self.log_file} - file does not exist after write")
            
        except Exception as e:
            # If temp file exists, try to clean it up
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except:
                    pass
            # Re-raise the exception so caller can handle it
            raise IOError(f"Failed to save logs to {self.log_file}: {e}") from e
    
    def log_alert(self, alert: Dict, level: str):
        """Log an alert with metadata.
        
        CRITICAL: This method MUST always succeed - alerts must be saved to JSON
        even if there are errors. This ensures the API always has the latest alerts.
        """
        try:
            # CRITICAL: Save the "Current MCAP" that was shown in the Telegram post
            # This is different from entry_mc (which is the MCAP when alert was triggered)
            # The Telegram post shows "Current MC: $142.0K" - this is what users see
            current_mcap_shown = alert.get("current_mcap")
            if current_mcap_shown is None:
                # Fallback: use entry_mc or mc_usd if current_mcap not available
                current_mcap_shown = alert.get("entry_mc") or alert.get("mc_usd") or alert.get("live_mcap")
            
            # Also save entry_mc separately (the MCAP when alert was triggered)
            entry_mc = alert.get("entry_mc")
            
            alert_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": level,
                "token": alert.get("token"),
                "contract": alert.get("contract"),
                "score": alert.get("score"),
                "callers": alert.get("callers"),
                "subs": alert.get("subs"),
                "liq_usd": alert.get("liq_usd"),
                "mc_usd": current_mcap_shown,  # Save the CURRENT MCAP that was shown in the Telegram post
                "current_mcap": current_mcap_shown,  # Explicit field for current MCAP from post
                "entry_mc": entry_mc,  # Save entry_mc separately (MCAP when alert was triggered)
                "last_buy_sol": alert.get("last_buy_sol"),
                "top_buy_sol": alert.get("top_buy_sol"),
                "matched_signals": alert.get("matched_signals", []),
                "tags": self._generate_tags(alert),
                # Add tiered strategy fields for API server
                "tier": alert.get("tier"),
                "glydo_in_top5": alert.get("glydo_in_top5"),
                "hot_list": alert.get("hot_list"),  # Save hot_list dict or bool
                "hot_list_status": alert.get("hot_list_status"),  # Alternative field name
                "confirmations": alert.get("confirmations"),  # Save confirmations for API
            }
            self.alerts.append(alert_entry)
            
            # CRITICAL: Save logs immediately - don't batch, ensure persistence
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self.save_logs()
                    print(f"✅ Alert saved to kpi_logs.json: {alert.get('token')} (Tier {alert.get('tier')}, Current MC ${current_mcap_shown:,.0f})")
                    break  # Success - exit retry loop
                except Exception as save_error:
                    if attempt < max_retries - 1:
                        print(f"⚠️ Save attempt {attempt + 1} failed: {save_error}, retrying...")
                        import time
                        time.sleep(0.2 * (attempt + 1))  # Exponential backoff
                    else:
                        # Last attempt failed - this is critical
                        print(f"❌ CRITICAL: Failed to save alert after {max_retries} attempts: {save_error}")
                        print(f"   Alert data: token={alert.get('token')}, tier={alert.get('tier')}")
                        # Try one more time with a different approach - direct write
                        try:
                            import shutil
                            # Create backup of current file
                            if self.log_file.exists():
                                backup_file = self.log_file.with_suffix('.json.backup')
                                shutil.copy2(self.log_file, backup_file)
                            
                            # Direct write as last resort
                            json_str = json.dumps({
                                "alerts": self.alerts,
                                "false_positives": self.false_positives,
                                "true_positives": self.true_positives,
                                "last_updated": datetime.now(timezone.utc).isoformat(),
                            }, indent=2, ensure_ascii=False)
                            self.log_file.write_text(json_str, encoding='utf-8')
                            print(f"✅ Emergency save succeeded for {alert.get('token')}")
                        except Exception as emergency_error:
                            print(f"❌ EMERGENCY SAVE ALSO FAILED: {emergency_error}")
                            import traceback
                            traceback.print_exc()
            
            return alert_entry
        except Exception as e:
            # CRITICAL: Never fail silently - log the error but don't crash
            print(f"❌ CRITICAL ERROR in log_alert: {e}")
            print(f"   Alert data: token={alert.get('token')}, tier={alert.get('tier')}")
            import traceback
            traceback.print_exc()
            # Return None to indicate failure, but don't raise exception
            return None
    
    def _generate_tags(self, alert: Dict) -> List[str]:
        """Generate tags for false positive analysis."""
        tags = []
        
        if not alert.get("contract"):
            tags.append("no_ca")
        
        liq = alert.get("liq_usd", 0) or 0
        if liq < 5000:
            tags.append("low_liq")
        
        matched = alert.get("matched_signals", [])
        if "sol_sb1" in matched:
            tags.append("has_sb1")
        if "glydo" in matched:
            tags.append("has_glydo")
        
        last_buy = alert.get("last_buy_sol", 0) or 0
        top_buy = alert.get("top_buy_sol", 0) or 0
        if last_buy < 5 and top_buy < 5:
            tags.append("tiny_buy")
        
        callers = alert.get("callers", 0) or 0
        subs = alert.get("subs", 0) or 0
        if callers < 20 or subs < 100000:
            tags.append("weak_social")
        
        return tags
    
    def mark_false_positive(self, alert_entry: Dict, reason: str):
        """Mark an alert as false positive."""
        fp_entry = {
            **alert_entry,
            "fp_reason": reason,
            "marked_at": datetime.now(timezone.utc).isoformat(),
        }
        self.false_positives.append(fp_entry)
        self.save_logs()
    
    def mark_true_positive(self, alert_entry: Dict, peak_multiplier: float, time_to_peak_minutes: float):
        """Mark an alert as true positive with peak data."""
        tp_entry = {
            **alert_entry,
            "peak_multiplier": peak_multiplier,
            "time_to_peak_minutes": time_to_peak_minutes,
            "marked_at": datetime.now(timezone.utc).isoformat(),
        }
        self.true_positives.append(tp_entry)
        self.save_logs()
    
    def get_daily_stats(self, days: int = 1) -> Dict:
        """Get daily statistics."""
        cutoff = datetime.now(timezone.utc).timestamp() - (days * 24 * 3600)
        
        recent_alerts = [a for a in self.alerts if datetime.fromisoformat(a["timestamp"]).timestamp() > cutoff]
        recent_fps = [fp for fp in self.false_positives if datetime.fromisoformat(fp["marked_at"]).timestamp() > cutoff]
        recent_tps = [tp for tp in self.true_positives if datetime.fromisoformat(tp["marked_at"]).timestamp() > cutoff]
        
        high_alerts = [a for a in recent_alerts if a["level"] == "HIGH"]
        medium_alerts = [a for a in recent_alerts if a["level"] == "MEDIUM"]
        
        # False positive breakdown
        fp_causes = defaultdict(int)
        for fp in recent_fps:
            for tag in fp.get("tags", []):
                if tag in ["no_ca", "low_liq", "has_sb1", "has_glydo", "tiny_buy", "weak_social"]:
                    fp_causes[tag] += 1
        
        # Precision
        high_precision = len(recent_tps) / len(high_alerts) if high_alerts else 0.0
        
        return {
            "period_days": days,
            "high_alerts": len(high_alerts),
            "medium_alerts": len(medium_alerts),
            "total_alerts": len(recent_alerts),
            "false_positives": len(recent_fps),
            "true_positives": len(recent_tps),
            "high_precision": high_precision,
            "fp_breakdown": dict(fp_causes),
        }
    
    def print_stats(self, days: int = 1):
        """Print statistics to console."""
        stats = self.get_daily_stats(days)
        print("\n" + "=" * 80)
        print(f"KPI STATISTICS (Last {days} day(s))")
        print("=" * 80)
        print(f"HIGH Alerts: {stats['high_alerts']}")
        print(f"MEDIUM Alerts: {stats['medium_alerts']}")
        print(f"Total Alerts: {stats['total_alerts']}")
        print(f"\nTrue Positives: {stats['true_positives']}")
        print(f"False Positives: {stats['false_positives']}")
        print(f"HIGH Precision: {stats['high_precision']:.2%}")
        print(f"\nFalse Positive Breakdown:")
        for cause, count in stats['fp_breakdown'].items():
            print(f"  {cause}: {count}")
        print("=" * 80 + "\n")


__all__ = ["KPILogger"]






