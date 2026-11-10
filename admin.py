#!/usr/bin/env python3
"""
VoiceIQ India — Terminal Admin & Voice Intelligence Hub CLI (Python)

Usage:
    python admin.py
    python admin.py --watch
    python admin.py --db
"""
import sys
import os
import time
import argparse
from datetime import datetime

# Enable UTF-8 for Windows PowerShell / Command Prompt
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ANSI Colors
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ORANGE = "\033[38;5;208m"
YELLOW = "\033[38;5;220m"
AMBER = "\033[38;5;214m"
GREEN = "\033[38;5;42m"
RED = "\033[38;5;196m"
CYAN = "\033[38;5;51m"
WHITE = "\033[38;5;15m"
GRAY = "\033[38;5;244m"
DARK_GRAY = "\033[38;5;238m"

# Ensure backend package is in python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

def render_bar(value: int, max_val: int, width: int = 22, color: str = ORANGE) -> str:
    safe_max = max(1, max_val)
    ratio = min(1.0, max(0.0, value / safe_max))
    filled = int(round(ratio * width))
    empty = width - filled
    bar = "█" * filled + "░" * empty
    pct = f"{int(round(ratio * 100)):3d}%"
    return f"{color}{bar}{RESET} {WHITE}{pct}{RESET}"

def format_inr(amount: float) -> str:
    return f"₹{amount:,.2f}"

def fetch_data_from_db():
    try:
        from app.core.database import SessionLocal, init_db
        from app.services.ecommerce_service import ECommerceService
        from app.repositories.conversation_repo import conversation_repo

        init_db()
        db = SessionLocal()
        try:
            store_stats = ECommerceService.get_store_analytics(db)
            conv_stats = conversation_repo.get_dashboard_stats(db)
            recent_convs, _ = conversation_repo.get_multi(db, skip=0, limit=5)

            # Convert ORM objects to dicts for display
            recent_list = []
            for c in recent_convs:
                recent_list.append({
                    "id": c.id,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                    "language_code": c.language_code,
                    "status": c.status,
                    "transcript": c.transcript,
                })

            return {
                "store": store_stats,
                "support": {
                    "total_conversations": conv_stats.total_conversations,
                    "completed_conversations": conv_stats.completed_conversations,
                    "success_rate_percentage": conv_stats.success_rate_percentage,
                },
                "recent_conversations": recent_list,
                "source": "Direct SQLite Database (voiceiq.db)"
            }
        finally:
            db.close()
    except Exception as e:
        return {"error": str(e)}

def fetch_data_from_api():
    try:
        import urllib.request
        import json
        req = urllib.request.Request(
            "http://127.0.0.1:8000/api/admin/analytics",
            headers={"User-Agent": "VoiceIQ-Terminal-Admin"}
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            data["source"] = "FastAPI Backend (http://127.0.0.1:8000)"
            return data
    except Exception:
        # Fallback to direct DB access
        return fetch_data_from_db()

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def render_dashboard(is_watch=False, force_db=False):
    if is_watch:
        clear_screen()

    if force_db:
        data = fetch_data_from_db()
    else:
        data = fetch_data_from_api()

    now = datetime.now().strftime("%I:%M:%S %p")

    print(f"\n{ORANGE}{BOLD}  ╔════════════════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{ORANGE}{BOLD}  ║      VOICEIQ INDIA — ADMIN & VOICE INTELLIGENCE TERMINAL HUB        ║{RESET}")
    print(f"{ORANGE}{BOLD}  ╚════════════════════════════════════════════════════════════════════════════╝{RESET}")
    source_label = data.get("source", "Live Database")
    print(f"  {GRAY}Source: {WHITE}{source_label}{GRAY}  •  Refreshed: {WHITE}{now}{RESET} {GREEN + '[LIVE WATCH]' + RESET if is_watch else ''}\n")

    if "error" in data:
        print(f"  {RED}{BOLD}⚠ Unable to load analytics: {data['error']}{RESET}\n")
        return

    store = data.get("store", {})
    recent_convs = data.get("recent_conversations", [])

    # Top Key Metrics
    print(f"  {BOLD}KEY PERFORMANCE METRICS{RESET}")
    print(f"  {DARK_GRAY}{'─' * 74}{RESET}")

    c1 = f"{GRAY}Total Orders:{RESET}    {WHITE}{BOLD}{store.get('total_orders', 0)}{RESET} ({GREEN}{store.get('active_orders', 0)} active{RESET})"
    c2 = f"{GRAY}Simulated Rev:{RESET}   {ORANGE}{BOLD}{format_inr(store.get('simulated_revenue', 0))}{RESET}"
    c3 = f"{GRAY}Voice Queries:{RESET}   {WHITE}{BOLD}{store.get('voice_conversations_count', 0)}{RESET} ({GREEN}{store.get('transcription_success_rate', 100)}% accuracy{RESET})"
    c4 = f"{GRAY}7-Day Returns:{RESET}   {YELLOW}{BOLD}{store.get('total_returns', 0)} requests{RESET} ({GREEN}{store.get('delivered_orders', 0)} delivered{RESET})"

    print(f"  {c1:<44} {c2}")
    print(f"  {c3:<44} {c4}")
    print(f"  {DARK_GRAY}{'─' * 74}{RESET}\n")

    # Intent Breakdown
    intents = store.get("intent_distribution", {})
    print(f"  {AMBER}{BOLD}📊 CUSTOMER VOICE INTENTS BREAKDOWN{RESET}")
    if not intents:
        print(f"  {GRAY}No voice intents logged yet. Ask queries in the Voice Assistant!{RESET}")
    else:
        max_intent = max(intents.values()) if intents else 1
        for intent, count in intents.items():
            label = intent.replace("_", " ").upper()
            bar = render_bar(count, max_intent, 20, ORANGE)
            print(f"  {WHITE}{label:<22}{RESET} {bar} {GRAY}({count}){RESET}")
    print("")

    # Multilingual Audio Distribution
    langs = store.get("language_distribution", {})
    print(f"  {YELLOW}{BOLD}🌐 MULTILINGUAL INDIAN AUDIO DISTRIBUTION (BCP-47){RESET}")
    if not langs:
        print(f"  {GRAY}Languages will populate as voice sessions are processed.{RESET}")
    else:
        max_lang = max(langs.values()) if langs else 1
        for lang, count in langs.items():
            bar = render_bar(count, max_lang, 20, YELLOW)
            print(f"  {WHITE}{lang:<22}{RESET} {bar} {GRAY}({count} recordings){RESET}")
    print("")

    # Recent Voice Support Logs
    print(f"  {CYAN}{BOLD}🎙 RECENT CUSTOMER VOICE SUPPORT LOGS{RESET}")
    if not recent_convs:
        print(f"  {GRAY}No voice conversations logged in SQLite database yet.{RESET}")
    else:
        print(f"  {GRAY}{'TIMESTAMP':<18} {'LANG':<10} {'STATUS':<12} TRANSCRIPT{RESET}")
        print(f"  {DARK_GRAY}{'─' * 74}{RESET}")
        for c in recent_convs[:5]:
            created = c.get("created_at") or "Recent"
            if "T" in created:
                created = created.split("T")[0] + " " + created.split("T")[1][:5]
            lang = (c.get("language_code") or "en-IN")[:8]
            st = c.get("status") or "completed"
            st_color = GREEN if st == "completed" else (RED if st == "failed" else YELLOW)
            transcript = c.get("transcript") or "(Speech processed via Gnani Prisma)"
            if len(transcript) > 36:
                transcript = transcript[:33] + "..."
            print(f"  {WHITE}{created:<18}{RESET} {CYAN}{lang:<10}{RESET} {st_color}{st.upper():<12}{RESET} {WHITE}\"{transcript}\"{RESET}")

    print(f"  {DARK_GRAY}{'─' * 74}{RESET}")
    if is_watch:
        print(f"\n  {GRAY}Press {WHITE}Ctrl+C{GRAY} to stop live watch mode.{RESET}\n")
    else:
        print(f"\n  {GRAY}Tip: Run with {WHITE}--watch{GRAY} for live auto-updating dashboard.{RESET}\n")

def main():
    parser = argparse.ArgumentParser(description="VoiceIQ India — Terminal Admin & Voice Intelligence Hub")
    parser.add_argument("--watch", "-w", action="store_true", help="Continuously refresh the dashboard every 3 seconds")
    parser.add_argument("--db", action="store_true", help="Directly query SQLite database instead of HTTP API")
    args = parser.parse_args()

    try:
        if args.watch:
            while True:
                render_dashboard(is_watch=True, force_db=args.db)
                time.sleep(3)
        else:
            render_dashboard(is_watch=False, force_db=args.db)
    except KeyboardInterrupt:
        print(f"\n{GRAY}Admin Hub closed.{RESET}\n")

if __name__ == "__main__":
    main()
