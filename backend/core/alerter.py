"""
DisasterMind — Telegram Alert System
Sends formatted government-style alerts when risk thresholds are crossed.
Token and chat ID loaded from .env — never hardcoded.
"""

import os
from datetime import datetime, timezone
from typing import Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# Risk level icons
RISK_ICONS = {
    "CRITICAL": "🔴",
    "HIGH":     "🟠",
    "MODERATE": "🟡",
    "LOW":      "🟢",
}

TREND_ICONS = {
    "ESCALATING": "📈",
    "STABLE":     "➡️",
    "IMPROVING":  "📉",
    "NEW":        "🆕",
}


def _is_configured() -> bool:
    return bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)


async def send_alert(
    cell_name: str,
    state: str,
    risk_level: str,
    risk_score: int,
    trend: str,
    consecutive_hrs: int,
    flood_prob: float,
    hotspot_count: int,
    rainfall_d1: float,
    summary: str,
    escalation_risk: str = "",
    lat: float = 0.0,
    lon: float = 0.0,
) -> bool:
    """
    Send a formatted threat alert to Telegram.
    Returns True on success, False on failure.
    """
    if not _is_configured():
        print("[Alerter] Telegram not configured — skipping alert")
        return False

    risk_icon  = RISK_ICONS.get(risk_level, "⚪")
    trend_icon = TREND_ICONS.get(trend, "➡️")
    now        = datetime.now(timezone.utc).strftime("%d %b %Y  %H:%M UTC")

    def _escape_md(text: str) -> str:
        return str(text).replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace('`', '\\`')

    # Build message
    lines = [
        f"{risk_icon} *DISASTERMIND ALERT*",
        f"━━━━━━━━━━━━━━━━━━━━━━",
        f"📍 *{_escape_md(cell_name)}*, {_escape_md(state)}",
        f"🕒 {now}",
        f"",
        f"*Risk Level:*  {risk_level}  ({risk_score}/10)",
        f"*Trend:*  {trend_icon} {trend}",
        f"*Active for:*  {consecutive_hrs} hour(s)",
        f"",
        f"📡 *Live Readings*",
        f"• Hotspots (FIRMS): {hotspot_count}",
        f"• Flood probability: {flood_prob:.0%}",
        f"• Rainfall (D1): {rainfall_d1:.1f} mm",
        f"",
        f"📋 *Situation*",
        f"{summary[:400] if summary else 'Autonomous scan detected elevated risk.'}",
    ]

    if escalation_risk:
        lines += ["", f"⚠️ *Escalation Risk*", escalation_risk[:200]]

    if lat and lon:
        lines += [
            "",
            f"🗺 Coordinates: {lat:.2f}°N, {lon:.2f}°E",
            f"[View on map](https://maps.google.com/?q={lat},{lon})",
        ]

    lines += [
        "",
        "━━━━━━━━━━━━━━━━━━━━━━",
        "_Sent autonomously by DisasterMind AI_",
        "_National Disaster Intelligence System_",
    ]

    message = "\n".join(lines)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id":    TELEGRAM_CHAT_ID,
                    "text":       message,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": False,
                },
            )
            if r.status_code == 200:
                print(f"[Alerter] Alert sent: {cell_name} — {risk_level}")
                return True
            else:
                print(f"[Alerter] Telegram error {r.status_code}: {r.text[:200]}")
                return False
    except Exception as e:
        print(f"[Alerter] Failed to send alert: {e}")
        return False


async def send_national_summary(
    active_threats: int,
    critical_count: int,
    high_count: int,
    escalating_count: int,
    top_threat: Optional[str],
    cells_scanned: int,
    scan_duration_s: float,
) -> bool:
    """
    Send hourly national scan summary to Telegram.
    Only sent when there are active threats.
    """
    if not _is_configured():
        return False
    if active_threats == 0:
        return True  # no message needed for all-clear

    now   = datetime.now(timezone.utc).strftime("%d %b %Y  %H:%M UTC")
    icon  = "🔴" if critical_count > 0 else "🟠" if high_count > 0 else "🟡"

    lines = [
        f"{icon} *NATIONAL SCAN COMPLETE*",
        f"━━━━━━━━━━━━━━━━━━━━━━",
        f"🕒 {now}",
        f"",
        f"🇮🇳 *India Threat Summary*",
        f"• Cells scanned: {cells_scanned}",
        f"• Active threats: {active_threats}",
        f"• Critical zones: {critical_count}",
        f"• High risk zones: {high_count}",
        f"• Escalating: {escalating_count}",
    ]

    if top_threat:
        lines += ["", f"🔺 *Highest threat:* {top_threat}"]

    lines += [
        "",
        f"⏱ Scan completed in {scan_duration_s:.1f}s",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━",
        "_DisasterMind Autonomous Monitor_",
    ]

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id":    TELEGRAM_CHAT_ID,
                    "text":       "\n".join(lines),
                    "parse_mode": "Markdown",
                },
            )
            return r.status_code == 200
    except Exception as e:
        print(f"[Alerter] Summary send failed: {e}")
        return False


async def test_connection() -> bool:
    """Test Telegram bot connectivity. Called at startup."""
    if not _is_configured():
        print("[Alerter] Telegram not configured (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID missing)")
        return False
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{TELEGRAM_API}/getMe")
            if r.status_code == 200:
                bot_name = r.json().get("result", {}).get("username", "unknown")
                print(f"[Alerter] Telegram connected — bot: @{bot_name}")
                return True
            return False
    except Exception as e:
        print(f"[Alerter] Telegram connection test failed: {e}")
        return False
