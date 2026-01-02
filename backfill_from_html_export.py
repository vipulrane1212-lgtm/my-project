"""
Backfill missing alerts from Telegram HTML export.
This works without needing a Telegram session, perfect for Railway deployment.
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from html import unescape
import shutil

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

KPI_LOGS_FILE = Path("kpi_logs.json")
LICO_CONTRACT = "678QT3ZQCCBLJJZB5IC5FVMAV94AYRIWSZ3FUYSRVYNC"


def parse_alert_from_html_message(text: str, message_date: datetime) -> Optional[Dict]:
    """Parse alert data from HTML message text."""
    try:
        # Clean HTML entities
        text = unescape(text)
        text = re.sub(r'<br\s*/?>', '\n', text)
        text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags
        
        # Check if this is an alert message
        is_confirmation = "CONFIRMATION ALERT" in text or "ALPHA INCOMING" in text
        is_watchlist = "WATCHLIST ALERT" in text
        
        if not (is_confirmation or is_watchlist):
            return None
        
        # Extract tier (from "TIER X LOCKED" or default to 3)
        tier_match = re.search(r'TIER\s+(\d+)', text, re.IGNORECASE)
        tier = int(tier_match.group(1)) if tier_match else 3
        
        # Extract token name
        token_match = re.search(r'TOKEN[:\s]+([A-Z0-9]+)', text, re.IGNORECASE) or \
                      re.search(r'Token[:\s]+([A-Z0-9]+)', text, re.IGNORECASE) or \
                      re.search(r'🔥\s*\*\*([A-Z0-9]+)\*\*', text) or \
                      re.search(r'\*\*([A-Z0-9]+)\*\*', text)
        token = token_match.group(1) if token_match else None
        
        # Extract contract address
        contract_match = re.search(r'<code>([A-Za-z0-9]{32,44})</code>', text) or \
                        re.search(r'`([A-Za-z0-9]{32,44})`', text) or \
                        re.search(r'Contract[:\s]+([A-Za-z0-9]{32,44})', text, re.IGNORECASE)
        contract = contract_match.group(1) if contract_match else None
        
        # Extract market cap
        mcap = None
        mcap_match = re.search(r'Market Cap[:\s]+\$?([0-9,.]+\.?[0-9]*)\s*([KMkm]?)', text, re.IGNORECASE) or \
                    re.search(r'Current MC[:\s]+\$?([0-9,.]+\.?[0-9]*)\s*([KMkm]?)', text, re.IGNORECASE)
        if mcap_match:
            mcap_str = mcap_match.group(1).replace(',', '').upper()
            mcap_unit = (mcap_match.group(2) or '').upper()
            mcap = float(mcap_str)
            if mcap_unit == 'K':
                mcap *= 1000
            elif mcap_unit == 'M':
                mcap *= 1000000
        
        # Extract callers and subs
        callers = None
        subs = None
        callers_match = re.search(r'Callers[:\s]+(\d+)', text, re.IGNORECASE)
        if callers_match:
            callers = int(callers_match.group(1))
        
        subs_match = re.search(r'Subs[:\s]+([0-9,]+)', text, re.IGNORECASE)
        if subs_match:
            subs = int(subs_match.group(1).replace(',', ''))
        
        # Extract level
        level = "HIGH" if tier == 1 else "MEDIUM"
        
        # Extract confirmations
        confirmations = {}
        if "Glydo" in text:
            confirmations["glydo"] = True
        if "Momentum" in text:
            confirmations["momentum"] = True
        if "Smart Money" in text or "Large Buy" in text:
            confirmations["smart_money"] = True
        if "Volume" in text:
            confirmations["volume"] = True
        
        if not token or not contract:
            return None
        
        return {
            "timestamp": message_date.isoformat(),
            "level": level,
            "token": token,
            "contract": contract,
            "mc_usd": mcap,
            "current_mcap": mcap,
            "entry_mc": mcap,
            "tier": tier,
            "confirmations": confirmations,
            "callers": callers,
            "subs": subs,
            "matched_signals": list(confirmations.keys()) if confirmations else [],
            "source": "html_export_backfill",
        }
    except Exception as e:
        return None


def parse_html_export(html_file: Path) -> List[Dict]:
    """Parse alerts from Telegram HTML export file."""
    print(f"📄 Parsing HTML export: {html_file}")
    
    if not html_file.exists():
        print(f"❌ File not found: {html_file}")
        return []
    
    alerts = []
    
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all message divs with date and text
        # Pattern: <div class="pull_right date details" title="DATE">...</div> ... <div class="text">TEXT</div>
        message_blocks = re.finditer(
            r'<div class="pull_right date details"[^>]*title="([^"]+)"[^>]*>.*?</div>.*?<div class="text">(.*?)</div>',
            content,
            re.DOTALL
        )
        
        for match in message_blocks:
            date_str = match.group(1)
            text = match.group(2)
            
            # Parse date (format: "08.12.2025 21:31:24 UTC+05:30" or "26.12.2025 10:50:00 UTC+05:30")
            try:
                # Extract date and time parts
                date_match = re.search(r'(\d{2})\.(\d{2})\.(\d{4})\s+(\d{2}):(\d{2}):(\d{2})', date_str)
                if date_match:
                    day, month, year, hour, minute, second = date_match.groups()
                    # Convert to UTC (subtract 5:30 hours from IST)
                    message_date = datetime(
                        int(year), int(month), int(day),
                        int(hour), int(minute), int(second),
                        tzinfo=timezone.utc
                    )
                    # Adjust for UTC+05:30 timezone (subtract 5:30)
                    from datetime import timedelta
                    message_date = message_date - timedelta(hours=5, minutes=30)
                    
                    alert = parse_alert_from_html_message(text, message_date)
                    if alert:
                        alerts.append(alert)
            except Exception as e:
                continue
        
        print(f"✅ Parsed {len(alerts)} alerts from HTML export")
        return alerts
    
    except Exception as e:
        print(f"❌ Error parsing HTML: {e}")
        import traceback
        traceback.print_exc()
        return []


def load_kpi_logs() -> Dict:
    """Load existing kpi_logs from file."""
    if KPI_LOGS_FILE.exists():
        try:
            with open(KPI_LOGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading kpi_logs.json: {e}")
            return {"alerts": []}
    return {"alerts": []}


def save_kpi_logs(data: Dict):
    """Save kpi_logs to file."""
    try:
        # Create backup
        if KPI_LOGS_FILE.exists():
            backup_file = KPI_LOGS_FILE.with_suffix('.json.backup')
            shutil.copy2(KPI_LOGS_FILE, backup_file)
            print(f"✅ Created backup: {backup_file}")
        
        with open(KPI_LOGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved updated kpi_logs.json with {len(data.get('alerts', []))} alerts.")
    except Exception as e:
        print(f"❌ Error saving kpi_logs.json: {e}")


def find_existing_alert(telegram_alert: Dict, existing_alerts: List[Dict]) -> Optional[Dict]:
    """Find matching alert in existing alerts."""
    tg_contract = telegram_alert.get("contract")
    tg_token = telegram_alert.get("token")
    tg_timestamp = datetime.fromisoformat(telegram_alert.get("timestamp", "2000-01-01").replace("Z", "+00:00"))
    
    if not tg_contract and not tg_token:
        return None
    
    for ex_alert in existing_alerts:
        ex_contract = ex_alert.get("contract")
        ex_token = ex_alert.get("token")
        
        # Match by contract (most reliable)
        if tg_contract and ex_contract and tg_contract == ex_contract:
            ex_timestamp = datetime.fromisoformat(ex_alert.get("timestamp", "2000-01-01").replace("Z", "+00:00"))
            if abs((tg_timestamp - ex_timestamp).total_seconds()) < 300:  # 5 min window
                return ex_alert
        
        # Fallback to token + timestamp
        if not tg_contract and tg_token and ex_token and tg_token == ex_token:
            try:
                ex_timestamp = datetime.fromisoformat(ex_alert.get("timestamp", "2000-01-01").replace("Z", "+00:00"))
                if abs((tg_timestamp - ex_timestamp).total_seconds()) < 300:
                    return ex_alert
            except:
                pass
    
    return None


def main():
    """Main backfill function."""
    print("="*80)
    print("BACKFILL FROM HTML EXPORT")
    print("="*80)
    
    # Find HTML export file (try both locations)
    html_file = Path(r"c:\Users\Admin\Downloads\Telegram Desktop\ChatExport_2026-01-02 (2)\messages.html")
    if not html_file.exists():
        html_file = Path(r"c:\Users\Admin\Downloads\Telegram Desktop\ChatExport_2026-01-02\messages.html")
    if not html_file.exists():
        print(f"❌ HTML export not found at: {html_file}")
        print("   Please provide the path to your Telegram HTML export file.")
        return
    
    # Load existing alerts
    kpi_data = load_kpi_logs()
    existing_alerts = kpi_data.get("alerts", [])
    print(f"\n📋 Current alerts in kpi_logs.json: {len(existing_alerts)}")
    
    # Find LICO alert timestamp
    lico_time = None
    for alert in existing_alerts:
        if alert.get("contract") == LICO_CONTRACT or alert.get("token") == "LICO":
            lico_time = datetime.fromisoformat(alert.get("timestamp", "").replace("Z", "+00:00"))
            print(f"   ✅ Found LICO alert: {alert.get('token')} at {lico_time.strftime('%Y-%m-%d %H:%M:%S')}")
            break
    
    if not lico_time:
        print("   ⚠️  LICO alert not found, will backfill all alerts from HTML")
        lico_time = datetime(2025, 12, 26, 10, 50, 0, tzinfo=timezone.utc)
    
    # Parse HTML export
    html_alerts = parse_html_export(html_file)
    
    if not html_alerts:
        print("❌ No alerts found in HTML export")
        return
    
    # Filter alerts after LICO
    alerts_after_lico = []
    for a in html_alerts:
        alert_time = datetime.fromisoformat(a.get("timestamp", "2000-01-01").replace("Z", "+00:00"))
        if alert_time > lico_time:
            alerts_after_lico.append(a)
            print(f"  Found alert after LICO: {a.get('token')} at {alert_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\n📊 Found {len(alerts_after_lico)} alerts after LICO in HTML export")
    
    # Find missing alerts
    new_alerts = []
    for tg_alert in alerts_after_lico:
        existing = find_existing_alert(tg_alert, existing_alerts)
        if not existing:
            new_alerts.append(tg_alert)
    
    print(f"\n✨ Found {len(new_alerts)} new alerts to add")
    
    if not new_alerts:
        print("✅ All alerts already in kpi_logs.json!")
        return
    
    # Show preview
    print("\nNew alerts to add:")
    for i, alert in enumerate(new_alerts[:10], 1):
        token = alert.get("token", "UNKNOWN")
        tier = alert.get("tier", "?")
        timestamp = alert.get("timestamp", "")[:19]
        print(f"  {i}. {token} - Tier {tier} - {timestamp}")
    
    if len(new_alerts) > 10:
        print(f"  ... and {len(new_alerts) - 10} more")
    
    # Add new alerts
    all_alerts = existing_alerts + new_alerts
    
    # Sort by timestamp (newest first)
    all_alerts.sort(
        key=lambda x: datetime.fromisoformat(x.get("timestamp", "2000-01-01").replace("Z", "+00:00")),
        reverse=True
    )
    
    kpi_data["alerts"] = all_alerts
    kpi_data["last_updated"] = datetime.now(timezone.utc).isoformat()
    
    # Save
    save_kpi_logs(kpi_data)
    
    print(f"\n✅ Backfill complete! Added {len(new_alerts)} alerts")
    print(f"Total alerts now: {len(all_alerts)}")
    print("\nNext step: Commit to Git and push:")
    print("   git add kpi_logs.json")
    print("   git commit -m 'Backfill alerts from HTML export'")
    print("   git push origin main")


if __name__ == "__main__":
    main()

