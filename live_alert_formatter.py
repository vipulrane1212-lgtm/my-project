"""
live_alert_formatter.py

New professional-yet-spicy Telegram alert template
Alpha channel style with tier-based formatting
Themed intro paragraphs for dynamic, engaging alerts
"""

from __future__ import annotations

import random
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, List

# Tier emoji mapping
TIER_EMOJIS = {
    1: "🚀",
    2: "🔥",
    3: "⚡",
}

# Tier names
TIER_NAMES = {
    1: "ULTRA",
    2: "HIGH",
    3: "MEDIUM",
}

# Theme 1: Glydo Heatmap Dominance (Pure volume/trending fire — 10 templates)
GLYDO_INTROS = [
    "Bro, this one's lighting up Glydo like a Solana bonfire—top 5 heat just exploded while smart money circles. {token_symbol} isn't whispering; it's screaming breakout. Eyes on that early pump leg, degens—cohort hit and it's already cooking. Hot List? Locked in before we blinked. Don't chase; this is the entry window. LFG, or watch from the sidelines.",
    "Glydo's top 5 just crowned {token_symbol} the volume king—trending harder than a cat meme in bull season. Whispers from the heatmap say it's got legs for days. Cohort dropped, and the chart's already curving up. If Hot List says yes, that's your green light. Size it smart; this smells like alpha harvest.",
    "Heatmap alert: {token_symbol} stormed Glydo's elite top 5, pulling eyes and volume like gravity. Not some flash-in-pan; this is sustained buzz turning to buys. XTRACK cohort nailed the timing—early enough to ride the wave. Hot List warmed it up perfectly. Pro tip: Enter now, exit on euphoria.",
    "{token_symbol} just hijacked Glydo's trending throne—top 5 glow-up means real talk, not hype. Volume's stacking, discussions popping; it's the quiet before the rocket. Cohort timestamp? Fresh as hell. Hot List badge? Earned. This is where legends load—don't be the one FOMOing later.",
    "Picture this: Glydo heatmap turns crimson on {token_symbol}, top 5 domination in under 20 mins. That's not luck; that's liquidity flooding in. Cohort syncs perfectly—XTRACK called it clean. Hot List pre-heat? Chef's kiss. Degens, this is your \"I told you so\" setup. Bag it before the herd.",
    "Glydo just flexed: {token_symbol} owns top 5, heatmap screaming \"all eyes here.\" From whisper to wildfire in cohort minutes. Smart plays incoming—volume doesn't lie. Hot List status? Prepped and primed. This one's built different; trade it like you mean it.",
    "Top 5 takeover on Glydo—{token_symbol}'s heatmap is straight fire, pulling degens like moths. Cohort hit the sweet spot; early momentum's locked. No fluff, just facts: Trending = buying pressure. Hot List? Activated. Enter the matrix, anon—upside's calling.",
    "{token_symbol} crashed Glydo's top 5 party, heatmap peaking like a full moon pump. This ain't random; it's coordinated chaos turning to gains. Cohort fresh, confirms stacking. Hot List green? That's your unfair advantage. Pro degen move: Position now, profit later.",
    "Glydo whispers turned to roars—{token_symbol} claims top 5, volume validating every tick. Cohort's the spark; this is the explosion waiting. Hot List history? Check. Eyes emoji for the chart curve. Not advice, but... you see it too, right?",
    "Heatmap royalty: {token_symbol} dethroned the pack on Glydo top 5. Trending metrics don't bluff—buys are brewing. XTRACK cohort timed it gold. Hot List? Warmed to perfection. This is alpha in plain sight; grab the wheel before it accelerates.",
]

# Theme 2: Momentum Spike Mania (Fast pumps, % surges — 10 templates)
MOMENTUM_INTROS = [
    "{token_symbol}'s chart just yeeted +{momentum_pct}% in seconds—momentum tracker lit up like a casino win. This isn't a tick; it's a tremor before the quake. Cohort dropped right into the surge; pure rocket fuel. Hot List? Fueling the fire. Degens, strap in—this leg's just starting.",
    "Spike alert: {token_symbol} surged {momentum_pct}% faster than a Solana tx—momentum's screaming \"go time.\" No slow build; this is instant alpha. Cohort synced the chaos perfectly. Hot List status? Primed for blast-off. LFG, or regret scrolling past.",
    "Holy velocity: {token_symbol} clocked +{momentum_pct}% in a heartbeat—trackers are buzzing. That's not noise; it's narrative shifting to pump. Cohort nailed the entry; confirms piling. Hot List? Yes, please. This one's got that viral velocity—ride it.",
    "{token_symbol} just momentum-mooned {momentum_pct}%—spike so sharp it cut through resistance. Tracker confirmed: Real buyers, not bots. Cohort fresh as the surge. Hot List greenlight? Absolute. Pro play: Catch the wave, surf to 5x.",
    "Momentum meltdown: {token_symbol}'s up {momentum_pct}% in seconds—trackers can't keep up. This is the spark igniting the room. Cohort timed it flawless. Hot List? Heated entry. Don't overthink; this velocity validates itself.",
    "{token_symbol} velocity hit: +{momentum_pct}% spike that's got trackers trembling. From flatline to fireworks—cohort caught the fuse. Hot List status? Lit. Smart money's whispering; listen close, anon.",
    "Surge city: {token_symbol} blasted {momentum_pct}%—momentum's the megaphone for incoming volume. No fakeout; this is foundation building. Cohort locked the door. Hot List? Open sesame. Enter now; exit on headlines.",
    "{token_symbol}'s spike game: {momentum_pct}% in a flash—trackers yelling \"all in.\" That's the sound of liquidity loving life. Cohort perfect pitch. Hot List? VIP pass. This momentum? It's money talking.",
    "Fast & furious: {momentum_pct}% momentum rip on {token_symbol}—spike so clean it's surgical. Cohort synced the speedrun. Hot List green? Go mode. Degens, this is your adrenaline alert.",
    "{token_symbol} just spiked {momentum_pct}%—momentum tracker's in love. Velocity vector points moon. Cohort captured the climb. Hot List? Co-sign. Pure pump poetry; recite with bags.",
]

# Theme 3: Smart Money Snipes (Large/Whale/Multi Buys — 10 templates)
SMART_MONEY_INTROS = [
    "Whale watch: {token_symbol} just got sniped by a tracked wallet dropping {buy_sol} SOL—heavy hitters loading early. This isn't retail noise; it's institutional degen. Cohort confirms the conviction. Hot List? Whale-approved. Bags filling; join the pod.",
    "Snipe squad: {token_symbol}'s seeing multi-wallet action—{multi_wallets} degens coordinating {total_sol} SOL buys. Smart money's stacking, not yapping. Cohort hit the honey pot. Hot List status? Sweet. This cluster? Your cue to cluster in.",
    "{token_symbol} whale dive: {whale_sol} SOL from a big fish—trackers lit, liquidity loves it. Not a dip buy; this is directional. Cohort timed the splash. Hot List? Deep end ready. Dive in before the surface ripples.",
    "Multi-buy madness: {token_symbol}'s got {multi_wallets} wallets tag-teaming {total_sol} SOL—coordinated alpha drop. Whales don't FOMO; they front-run. Cohort nailed it. Hot List green? Herd incoming. Position like a pro.",
    "Tracked snipe: {buy_sol} SOL wallet just aped {token_symbol}—smart money's map says treasure here. Volume validating the vision. Cohort fresh print. Hot List? Mapped out. Follow the footprints to gains.",
    "{token_symbol} whale whisper: {whale_sol} SOL entry from the deep—trackers trembling. This is quiet conviction turning loud. Cohort caught the current. Hot List? Oceanic. Swim with the big fish, anon.",
    "Buy cluster alert: {token_symbol}'s pulling {multi_wallets} snipers with {total_sol} SOL—teamwork makes the dream work. Not solo; symphony of buys. Cohort conducted it. Hot List? In tune. Harmonize your portfolio.",
    "{token_symbol} heavy artillery: {buy_sol} SOL tracked buy just landed—smart money's betting the farm. Impact? Immediate upside. Cohort zeroed in. Hot List? Locked target. Fire when ready.",
    "Whale pod assemble: {token_symbol}'s got multi {multi_wallets} dropping {total_sol} SOL—collective conviction. Whales hunt in packs for a reason. Cohort led the charge. Hot List? Pack leader. Run with 'em.",
    "Snipe supreme: {buy_sol} SOL from a shadow wallet on {token_symbol}—trackers say it's the vanguard. Early buys build empires. Cohort vanguard too. Hot List? Empire state. Claim your plot.",
]

# Theme 4: Early Trending + Mixed Confirms (Wildcard hype, KOL/volume vibes — 10 templates)
MIXED_INTROS = [
    "Trending takeover: {token_symbol} just popped on Early Trending—early birds getting the worm before XTRACK even blinked. Volume's validating the vibe. Cohort sealed the story. Hot List? Bird's eye view. Fly high, degen.",
    "KOL echo: {token_symbol}'s getting SpyDefi/KOLscope nods—whispers turning to calls. Not hype; harmonic convergence. Cohort amplified it. Hot List green? Echo chamber of gains. Amplify your stack.",
    "Volume vault: {token_symbol}'s PFBF volume alert hit—buys stacking like pancakes. Early trending co-signs the stack. Cohort flipped the switch. Hot List? Breakfast club. Eat good.",
    "{token_symbol} trending tide: Early signals + volume surge—tide's turning, and you're on the crest. KOLscope's watching too. Cohort rode the wave. Hot List? Tidal lock. Surf's up.",
    "Mixed magic: {token_symbol}'s blending Early Trending with multi-confirms—recipe for rocket sauce. Not one-note; full orchestra. Cohort conducted. Hot List? VIP seats. Encore with profits.",
    "Volume + vibe: {token_symbol}'s PFBF buys + trending buzz—vibe check passed with flying colors. KOLscope's in the mix. Cohort vibe'd it. Hot List? Color-coded green. Paint the town red with gains.",
    "Early echo chamber: {token_symbol} trending early, KOLs echoing—chamber's filling with buy pressure. Volume's the bass drop. Cohort dropped the beat. Hot List? Front row. Drop in.",
    "{token_symbol} wildcard win: Trending post + volume spike—wild card turning ace. Confirms stacking like chips. Cohort cashed in. Hot List? Royal flush. Bet big.",
    "Buzz build: {token_symbol}'s Early Trending lit the fuse, volume's the boom. KOLscope co-producer. Cohort directed the scene. Hot List? Blockbuster. Cut to credits with bags.",
    "Hybrid heat: {token_symbol}'s trending + mixed confirms—heat from all angles, no cold spots. Early signals set the stage. Cohort stole the show. Hot List? Standing ovation. Applaud with apes.",
]


def _format_money(val: Optional[float]) -> str:
    """Format USD value with K/M suffixes."""
    if val is None:
        return "—"
    if val >= 1_000_000:
        return f"${val/1_000_000:.2f}M"
    if val >= 1_000:
        return f"${val/1_000:.1f}K"
    return f"${val:,.0f}"


def _format_cohort_time_relative(alert: Dict) -> str:
    """Format cohort time as relative (e.g., '1s ago', '1m 5s ago', '1h 5m ago')."""
    cohort_start = alert.get("cohort_start_utc") or alert.get("cohort_start_ist")
    if not cohort_start:
        return "—"
    
    try:
        if isinstance(cohort_start, str):
            dt = datetime.fromisoformat(cohort_start.replace("Z", "+00:00"))
        else:
            dt = cohort_start
        
        # Ensure timezone aware
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        now = datetime.now(timezone.utc)
        delta = now - dt
        
        if delta.total_seconds() < 0:
            return "just now"
        
        total_seconds = int(delta.total_seconds())
        
        if total_seconds < 60:
            return f"{total_seconds}s ago"
        
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        
        if minutes < 60:
            if seconds > 0:
                return f"{minutes}m {seconds}s ago"
            return f"{minutes}m ago"
        
        hours = minutes // 60
        minutes = minutes % 60
        
        if hours < 24:
            if minutes > 0:
                return f"{hours}h {minutes}m ago"
            return f"{hours}h ago"
        
        days = hours // 24
        hours = hours % 24
        
        if days < 7:
            if hours > 0:
                return f"{days}d {hours}h ago"
            return f"{days}d ago"
        
        return f"{days}d ago"
    except:
        return "—"


def _get_multiplier(alert: Dict) -> float:
    """Get current multiplier from alert."""
    # Try cohort multiplier first
    mult = alert.get("cohort_multiplier") or alert.get("base_multiplier")
    if mult:
        return float(mult)
    
    # Fallback: try to infer from score (legacy)
    score = alert.get("score", 0)
    if score >= 20:
        return 3.0
    elif score >= 12:
        return 2.0
    
    return 2.0  # Default


def _get_current_mc(alert: Dict) -> Optional[float]:
    """Get current MC (prefer live, fallback to entry)."""
    # Prefer live MC from DexScreener
    live_mc = alert.get("live_mcap") or alert.get("mc_usd")
    if live_mc:
        return float(live_mc)
    
    # Fallback to entry MC
    entry_mc = alert.get("entry_mc")
    if entry_mc:
        return float(entry_mc)
    
    return None


def _build_glydo_line(alert: Dict) -> str:
    """Build Glydo top 5 line if present."""
    glydo_in_top5 = alert.get("glydo_in_top5") or False
    if glydo_in_top5:
        return "🌡️ Glydo Top 5 Heatmap — trending hard right now"
    return ""


def _build_confirmation_lines(alert: Dict) -> List[str]:
    """Build confirmation lines from alert data (deduplicated)."""
    lines = []
    seen = set()  # Track seen confirmation types to avoid duplicates
    confirmations = alert.get("confirmations", {})
    
    # Handle both dict format (from tiered strategy) and list format (from old system)
    if isinstance(confirmations, dict):
        # New tiered strategy format
        details = confirmations.get("details", [])
        
        # Parse details to extract specific info
        for detail in details:
            detail_lower = detail.lower()
            
            # Deduplicate by type
            if "momentum" in detail_lower and "momentum" not in seen:
                seen.add("momentum")
                # Try to extract percentage
                pct_match = re.search(r'(\d+(?:\.\d+)?)%', detail)
                if pct_match:
                    lines.append(f"🟢 Momentum spike: +{pct_match.group(1)}% in seconds")
                else:
                    lines.append("🟢 Momentum spike detected")
            
            elif ("large buy" in detail_lower or "tracked wallet" in detail_lower) and "large_buy" not in seen:
                seen.add("large_buy")
                # Try to extract SOL amount
                sol_match = re.search(r'(\d+(?:\.\d+)?)\s*SOL', detail)
                if sol_match:
                    lines.append(f"💰 Tracked wallet sniped {sol_match.group(1)} SOL")
                else:
                    lines.append("💰 Large buy detected")
            
            elif "whale" in detail_lower and "whale" not in seen:
                seen.add("whale")
                sol_match = re.search(r'(\d+(?:\.\d+)?)\s*SOL', detail)
                if sol_match:
                    lines.append(f"🐳 Whale buy confirmed ({sol_match.group(1)} SOL)")
                else:
                    lines.append("🐳 Whale buy confirmed")
            
            elif ("pfbf" in detail_lower or "volume" in detail_lower) and "volume" not in seen:
                seen.add("volume")
                lines.append("📊 Volume spike detected")
            
            elif ("early trending" in detail_lower or "early" in detail_lower) and "early_trending" not in seen:
                seen.add("early_trending")
                lines.append("📈 Early Trending posted")
            
            elif "multi" in detail_lower and "multi_buy" not in seen:
                seen.add("multi_buy")
                multi_count = confirmations.get("multi_buy", 0)
                if multi_count > 0:
                    lines.append(f"👥 Multi-buy detected ({multi_count} wallets)")
                else:
                    lines.append("👥 Multi-buy detected")
        
        # Also check direct confirmation counts if details are empty
        if not lines:
            if confirmations.get("momentum_spike", 0) > 0 and "momentum" not in seen:
                seen.add("momentum")
                lines.append("🟢 Momentum spike detected")
            
            if confirmations.get("large_buy", 0) > 0 and "large_buy" not in seen:
                seen.add("large_buy")
                buy_size = alert.get("last_buy_sol") or alert.get("top_buy_sol")
                if buy_size:
                    lines.append(f"💰 Tracked wallet sniped {buy_size:.1f} SOL")
                else:
                    lines.append("💰 Large buy detected")
            
            if confirmations.get("whale_buy", 0) > 0 and "whale" not in seen:
                seen.add("whale")
                lines.append("🐳 Whale buy confirmed")
            
            if confirmations.get("multi_buy", 0) > 0 and "multi_buy" not in seen:
                seen.add("multi_buy")
                multi_count = confirmations.get("multi_buy", 0)
                lines.append(f"👥 Multi-buy detected ({multi_count} wallets)")
            
            if confirmations.get("early_trending", 0) > 0 and "early_trending" not in seen:
                seen.add("early_trending")
                lines.append("📈 Early Trending posted")
    
    else:
        # Old format - matched_signals list
        matched = alert.get("matched_signals", [])
        for sig in matched:
            if sig == "momentum_tracker" and "momentum" not in seen:
                seen.add("momentum")
                lines.append("🟢 Momentum spike detected")
            elif sig == "large_buys_tracker" and "large_buy" not in seen:
                seen.add("large_buy")
                buy_size = alert.get("last_buy_sol") or alert.get("top_buy_sol")
                if buy_size:
                    lines.append(f"💰 Tracked wallet sniped {buy_size:.1f} SOL")
                else:
                    lines.append("💰 Large buy detected")
            elif sig == "whalebuy" and "whale" not in seen:
                seen.add("whale")
                lines.append("🐳 Whale buy confirmed")
            elif sig == "pfbf_volume_alert" and "volume" not in seen:
                seen.add("volume")
                lines.append("📊 Volume spike detected")
            elif sig == "solana_early_trending" and "early_trending" not in seen:
                seen.add("early_trending")
                lines.append("📈 Early Trending posted")
    
    return lines


def _build_trigger_reason(alert: Dict, confirmation_count: int) -> str:
    """Build explanation of why this tier was triggered."""
    tier = alert.get("tier")
    if not tier or tier not in [1, 2, 3]:
        return ""
    
    confirmations = alert.get("confirmations", {})
    entry_mc = alert.get("entry_mc") or alert.get("mc_usd")
    glydo_in_top5 = alert.get("glydo_in_top5", False)
    
    reasons = []
    tier_badge = TIER_EMOJIS.get(tier, "⚡")
    
    # Build tier badge line
    tier_name_display = TIER_NAMES.get(tier, f"TIER {tier}")
    reasons.append(f"{tier_badge} **TIER {tier}**")
    
    # Add Glydo if present
    if glydo_in_top5:
        reasons.append("✓ Glydo Top 5 (±20min)")
    
    # Add confirmation count
    if confirmation_count > 0:
        if confirmation_count == 1:
            reasons.append(f"✓ {confirmation_count} confirmation(s)")
        else:
            reasons.append(f"✓ {confirmation_count} confirmation(s)")
    else:
        # Fallback for tier 3
        if tier == 3:
            delayed_glydo = False
            if isinstance(confirmations, dict):
                glydo_data = alert.get("glydo_data", {})
                delayed_glydo = glydo_data.get("delayed_appearance", False)
            if delayed_glydo:
                reasons.append("✓ Delayed Glydo appearance")
            else:
                reasons.append("✓ Multiple signals confirmed")
    
    # Entry MC removed per user request - only current MCAP should be present
    
    if reasons:
        return "\n".join(reasons)
    return ""


def _get_hot_list_status(alert: Dict) -> str:
    """Get Hot List status string."""
    hot_list = alert.get("hot_list") or alert.get("hot_list_status", {})
    
    # Handle both bool and dict format
    if isinstance(hot_list, bool):
        return "🟢 Yes" if hot_list else "🔴 No"
    elif isinstance(hot_list, dict):
        was_in_hot_list = hot_list.get("was_in_hot_list", False)
        return "🟢 Yes" if was_in_hot_list else "🔴 No"
    
    return "🔴 No"


def _extract_dynamic_variables(alert: Dict) -> Dict[str, str]:
    """Extract dynamic variables from alert for intro template substitution."""
    token_symbol = alert.get("token") or "UNKNOWN"
    confirmations = alert.get("confirmations", {})
    details = confirmations.get("details", []) if isinstance(confirmations, dict) else []
    
    vars_dict = {
        "token_symbol": token_symbol,
        "momentum_pct": "50",  # Default fallback
        "buy_sol": "20",  # Default fallback
        "whale_sol": "50",  # Default fallback
        "multi_wallets": "3",  # Default fallback
        "total_sol": "100",  # Default fallback
    }
    
    # Extract momentum percentage
    for detail in details:
        detail_lower = detail.lower()
        if "momentum" in detail_lower:
            pct_match = re.search(r'(\d+(?:\.\d+)?)%', detail)
            if pct_match:
                vars_dict["momentum_pct"] = pct_match.group(1)
                break
    
    # Extract buy sizes (SOL amounts)
    buy_sizes = []
    for detail in details:
        detail_lower = detail.lower()
        if "buy" in detail_lower or "wallet" in detail_lower or "whale" in detail_lower:
            sol_matches = re.findall(r'(\d+(?:\.\d+)?)\s*SOL', detail)
            buy_sizes.extend([float(m) for m in sol_matches])
    
    # Also check alert data directly
    if not buy_sizes:
        buy_size = alert.get("last_buy_sol") or alert.get("top_buy_sol") or alert.get("buy_size_sol")
        if buy_size:
            buy_sizes.append(float(buy_size))
    
    if buy_sizes:
        # Use largest buy for whale_sol, first for buy_sol
        vars_dict["whale_sol"] = str(max(buy_sizes))
        vars_dict["buy_sol"] = str(buy_sizes[0])
        vars_dict["total_sol"] = str(sum(buy_sizes))
    
    # Extract multi-wallet count
    if isinstance(confirmations, dict):
        multi_count = confirmations.get("multi_buy", 0)
        if multi_count > 0:
            vars_dict["multi_wallets"] = str(multi_count)
        else:
            # Try to infer from details
            for detail in details:
                if "multi" in detail.lower():
                    multi_match = re.search(r'(\d+)\s*(?:wallet|buy)', detail, re.IGNORECASE)
                    if multi_match:
                        vars_dict["multi_wallets"] = multi_match.group(1)
                        break
    
    # Try to get total SOL from alert data if available
    total_buy_sol = alert.get("total_buy_sol") or alert.get("total_prex_buy_sol")
    if total_buy_sol and float(total_buy_sol) > 0:
        vars_dict["total_sol"] = f"{float(total_buy_sol):.1f}"
    
    # Try to get buy count for multi_wallets if not already set
    if vars_dict["multi_wallets"] == "3":  # Still default
        buy_count = alert.get("buy_count") or alert.get("buy_event_count")
        if buy_count and buy_count > 1:
            vars_dict["multi_wallets"] = str(buy_count)
    
    return vars_dict


def _select_intro_theme(alert: Dict, confirmation_lines: List[str], glydo_line: str) -> List[str]:
    """Select appropriate intro theme based on confirmations and triggers."""
    confirmations = alert.get("confirmations", {})
    details = confirmations.get("details", []) if isinstance(confirmations, dict) else []
    glydo_in_top5 = alert.get("glydo_in_top5", False)
    
    # Check for momentum
    has_momentum = any("momentum" in line.lower() for line in confirmation_lines) or \
                   any("momentum" in str(d).lower() for d in details)
    
    # Check for smart money (whale/large buys)
    has_smart_money = any("whale" in line.lower() or "large buy" in line.lower() or 
                         "tracked wallet" in line.lower() for line in confirmation_lines) or \
                     any("whale" in str(d).lower() or "large buy" in str(d).lower() or 
                         "tracked wallet" in str(d).lower() for d in details)
    
    # Check for multi-buy
    has_multi_buy = any("multi" in line.lower() for line in confirmation_lines) or \
                   any("multi" in str(d).lower() for d in details)
    
    # Check for early trending / mixed
    has_early_trending = any("early trending" in line.lower() for line in confirmation_lines) or \
                        any("early trending" in str(d).lower() for d in details)
    has_volume = any("volume" in line.lower() or "pfbf" in line.lower() for line in confirmation_lines) or \
                any("volume" in str(d).lower() or "pfbf" in str(d).lower() for d in details)
    has_kol = any("kol" in line.lower() or "spydefi" in line.lower() for line in confirmation_lines) or \
             any("kol" in str(d).lower() or "spydefi" in str(d).lower() for d in details)
    
    # Priority selection logic:
    # 1. Glydo + Momentum → Glydo theme
    # 2. Glydo + Smart Money → Glydo theme
    # 3. Pure Glydo → Glydo theme
    # 4. Momentum (standalone) → Momentum theme
    # 5. Smart Money (whale/large/multi) → Smart Money theme
    # 6. Early Trending + Mixed → Mixed theme
    # 7. Default → Random from all themes
    
    if glydo_in_top5:
        # Glydo takes priority
        return GLYDO_INTROS
    elif has_momentum and not has_smart_money:
        # Pure momentum
        return MOMENTUM_INTROS
    elif has_smart_money or has_multi_buy:
        # Smart money theme
        return SMART_MONEY_INTROS
    elif has_early_trending or has_volume or has_kol:
        # Mixed theme
        return MIXED_INTROS
    else:
        # Default: random selection from all themes
        all_intros = GLYDO_INTROS + MOMENTUM_INTROS + SMART_MONEY_INTROS + MIXED_INTROS
        return all_intros


def _get_spicy_intro(alert: Dict, confirmation_lines: List[str], glydo_line: str) -> str:
    """Get themed spicy intro paragraph based on alert triggers."""
    # Select theme
    theme_intros = _select_intro_theme(alert, confirmation_lines, glydo_line)
    
    # Pick random intro from selected theme
    intro_template = random.choice(theme_intros)
    
    # Extract dynamic variables
    vars_dict = _extract_dynamic_variables(alert)
    
    # Substitute variables in template - handle missing variables gracefully
    try:
        intro = intro_template.format(**vars_dict)
    except KeyError as e:
        # Fallback: replace missing variables with defaults
        missing_var = str(e).strip("'\"")
        default_value = vars_dict.get(missing_var, "N/A")
        intro = intro_template.replace(f"{{{missing_var}}}", default_value)
        print(f"⚠️ Warning: Missing variable {missing_var} in intro template, using default: {default_value}")
    except Exception as e:
        # Ultimate fallback: use template as-is if formatting completely fails
        print(f"⚠️ Warning: Error formatting intro template: {e}")
        intro = intro_template
        # Try to at least replace token_symbol
        intro = intro.replace("{token_symbol}", vars_dict.get("token_symbol", "UNKNOWN"))
    
    return intro


def format_alert(alert: Dict[str, any], weights: Optional[Dict] = None) -> str:
    """
    Format alert using new alpha channel template with themed spicy intros.
    
    New Template Structure:
    🚨 **ALPHA INCOMING — TIER {tier} LOCKED** {tier_emoji} {tier_name}
    **{token_symbol}** just crossed **{multiplier}x** on XTRACK
    🔥 Current MC: **${current_mc}**
    CA: `{contract_address}`
    
    [SPICY INTRO PARAGRAPH HERE — 5-6 LINES, THEMED TO TRIGGERS]
    
    Why it triggered:
    {tier_badge} **TIER {tier}**
    ✓ Glydo Top 5 (±20min)
    ✓ {confirm_count} confirmation(s)
    ✓ Entry MC: **${entry_mc}** ({range_text})
    
    {confirmation_bullets}
    
    ⏰ Cohort: {cohort_time_ago}
    💧 Hot List: {hot_list_emoji} {hot_list_status}
    
    📊 Chart • 🎯 GMGN • 🔍 Rugcheck
    
    — Monitored by solboy {tier_name}
    """
    token = alert.get("token") or "UNKNOWN"
    contract = alert.get("contract")
    tier = alert.get("tier")
    
    # Ensure tier is valid (default to 3 if missing but alert exists)
    if tier is None or tier not in [1, 2, 3]:
        tier = 3  # Default fallback
        print(f"⚠️ Warning: Invalid tier in alert, defaulting to 3")
    
    # Validate contract address is present
    if not contract:
        # Try to get from alert data
        contract = alert.get("contract_address")
    
    # Get multiplier
    multiplier = _get_multiplier(alert)
    
    # Get current MC (prefer live from DexScreener)
    current_mc = _get_current_mc(alert)
    current_mc_str = _format_money(current_mc) if current_mc else "—"
    
    # Get entry MC for trigger reason
    entry_mc = alert.get("entry_mc") or alert.get("mc_usd")
    entry_mc_str = _format_money(entry_mc) if entry_mc else "—"
    
    # Get tier emoji and name
    tier_emoji = TIER_EMOJIS.get(tier, "⚡")
    tier_name = TIER_NAMES.get(tier, f"TIER {tier}")
    
    # Build Glydo line
    glydo_line = _build_glydo_line(alert)
    
    # Build confirmation lines (deduplicated)
    confirmation_lines = _build_confirmation_lines(alert)
    
    # Count actual confirmation lines (including Glydo if present)
    confirmation_count = len(confirmation_lines)
    if glydo_line:
        confirmation_count += 1  # Glydo counts as a confirmation
    
    # Get spicy intro paragraph
    spicy_intro = _get_spicy_intro(alert, confirmation_lines, glydo_line)
    
    # Build trigger reason (use actual confirmation count)
    trigger_reason = _build_trigger_reason(alert, confirmation_count)
    
    # Get cohort time as relative
    cohort_time_relative = _format_cohort_time_relative(alert)
    
    # Get Hot List status
    hot_list_status = _get_hot_list_status(alert)
    
    # Build the alert with new template structure
    text = f"🚨 **ALPHA INCOMING — TIER {tier} LOCKED** {tier_emoji} {tier_name}\n\n"
    
    # Token info (🔥 token name, then MC, then CA on separate line in code block)
    text += f"🔥 **{token}**\n"
    text += f"Current MC: **{current_mc_str}**\n"
    
    # Contract address on next line in code block for easy copying
    if contract:
        text += f"\n`{contract}`\n\n"
    else:
        text += "\n⚠️ No contract address\n\n"
    
    # Spicy intro paragraph
    text += f"{spicy_intro}\n\n"
    
    # Why it triggered section
    if trigger_reason:
        text += f"Why it triggered:\n{trigger_reason}\n\n"
    
    # Confirmation bullets
    confirmation_bullets = []
    if glydo_line:
        confirmation_bullets.append(glydo_line)
    if confirmation_lines:
        confirmation_bullets.extend(confirmation_lines)
    
    # Only show confirmation bullets if there are actual confirmations
    # Skip if it would only be "📊 Signal confirmed" (single line, not informative)
    if confirmation_bullets:
        text += "\n".join(confirmation_bullets) + "\n\n"
    # If no confirmations, skip the "📊 Signal confirmed" line entirely
    
    # Metadata
    text += f"⏰ Cohort: {cohort_time_relative}\n"
    text += f"💧 Hot List: {hot_list_status}\n"
    
    # Links (embedded, no preview) - all on one line - BELOW Cohort/Hot List
    if contract:
        text += f"\n[📊 Chart](https://dexscreener.com/solana/{contract}) • [🎯 GMGN](https://gmgn.ai/sol/token/{contract}) • [🔍 Rugcheck](https://rugcheck.xyz/t/{contract})\n"
    else:
        text += "\n📊 Chart: — (no CA) • 🎯 GMGN: — (no CA) • 🔍 Rugcheck: — (no CA)\n"
    
    # Footer - entire text as clickable link
    text += f"\n[— Monitored by solboy](https://t.me/solboy_calls)"
    
    return text


__all__ = ["format_alert"]
