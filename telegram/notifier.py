#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Telegram Notifier for Vecna Takeover Alerts
- Minimal output: only a progress counter (e.g., [5/22]) that updates in-place.
- Falls back to text-only if photo sending fails.
"""

import os
import json
import time
import requests
from datetime import datetime, timezone
from pathlib import Path

# ======================================
# Constants & Paths
# ======================================

ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT_DIR / "configs" / "telegram-settings.json"
FINAL_FILE = ROOT_DIR / "found" / "final.json"
POC_DIR = ROOT_DIR / "poc"

TIMEOUT = 15
SEND_DELAY = 0.7
MAX_RETRIES = 5
MAX_NETWORK_UNREACHABLE_RETRIES = 10
MAX_CAPTION_LENGTH = 900          # Safe limit (Telegram max 1024)
PHOTO_MAX_SIZE = 10 * 1024 * 1024  # 10 MB

# ======================================
# Config Loader
# ======================================

def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# ======================================
# Safe Poster with Retry (silent, only logs via return)
# ======================================

def safe_post(url, data=None, files=None, max_retries=MAX_RETRIES):
    """
    Send request with retries. Returns True on success, False on failure.
    All prints are suppressed; only the final return indicates outcome.
    """
    attempts = 0
    network_unreachable_count = 0

    while attempts < max_retries:
        attempts += 1
        try:
            if files:
                response = requests.post(url, data=data, files=files, timeout=TIMEOUT)
            else:
                response = requests.post(url, json=data, timeout=TIMEOUT)

            if response.status_code == 200:
                return True

            if response.status_code == 429:
                retry_after = response.json().get("parameters", {}).get("retry_after", 5)
                time.sleep(retry_after)
                continue

            # Other errors: wait and retry
            time.sleep(5)

        except requests.RequestException as e:
            if "Network is unreachable" in str(e):
                network_unreachable_count += 1
                if network_unreachable_count >= MAX_NETWORK_UNREACHABLE_RETRIES:
                    return False
                time.sleep(5)
                continue
            else:
                time.sleep(5)

    return False

# ======================================
# Telegram Senders (silent)
# ======================================

def send_message(token, chat_id, text, topic_id=None):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    if topic_id:
        payload["message_thread_id"] = int(topic_id)
    return safe_post(url, data=payload)

def send_photo(token, chat_id, photo_path, caption, topic_id=None):
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    with open(photo_path, "rb") as photo_file:
        files = {"photo": photo_file}
        data = {
            "chat_id": chat_id,
            "caption": caption[:MAX_CAPTION_LENGTH],
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        if topic_id:
            data["message_thread_id"] = int(topic_id)
        return safe_post(url, data=data, files=files)

# ======================================
# Smart Alert Sender (Photo with Fallback to Text)
# ======================================

def send_alert(token, chat_id, message_text, screenshot_path, topic_id=None):
    """Try photo, fallback to text if photo fails or is invalid."""
    if screenshot_path and os.path.exists(screenshot_path):
        file_size = os.path.getsize(screenshot_path)
        if file_size <= PHOTO_MAX_SIZE:
            success = send_photo(token, chat_id, screenshot_path, message_text, topic_id)
            if success:
                return True
    # Fallback to text-only
    return send_message(token, chat_id, message_text, topic_id)

# ======================================
# Load Final Report
# ======================================

def load_final():
    if not FINAL_FILE.exists():
        return []
    with open(FINAL_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# ======================================
# Message Builder
# ======================================

def severity_emoji(severity):
    return {
        "critical": "💀",
        "high": "🔥",
        "medium": "⚠️",
        "low": "🔎"
    }.get(str(severity).lower(), "ℹ️")

def build_message(entry):
    domain = entry.get("domain", "unknown")
    services = ", ".join(entry.get("services", []))
    engines = ", ".join(entry.get("engines", []))
    confidence = entry.get("confidence", 0)
    severity = entry.get("severity", "low")
    discussions = entry.get("discussion")

    emoji = severity_emoji(severity)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    lines = [
        f"{emoji} *VECNA TAKEOVER DETECTED* {emoji}",
        "",
        f"🎯 *Target:* `{domain}`",
        f"🧩 *Service(s):* `{services}`",
        f"🧠 *Engine(s):* `{engines}`",
        "",
        f"📊 *Severity:* *{severity.upper()}*",
        f"📈 *Confidence:* `{confidence}%`"
    ]

    if discussions:
        lines.append("")
        lines.append("📚 *References:*")
        if isinstance(discussions, list):
            for d in discussions:
                lines.append(f"- {d}")
        else:
            lines.append(f"- {discussions}")

    lines.append("")
    lines.append(f"⏱ `{now}`")

    full_text = "\n".join(lines)
    # Trim if excessively long (safety)
    if len(full_text) > MAX_CAPTION_LENGTH * 2:
        full_text = full_text[:MAX_CAPTION_LENGTH * 2 - 50] + "\n... (trimmed)"
    return full_text

# ======================================
# Main
# ======================================

def main():
    config = load_config()
    if not config.get("TELEGRAM_ENABLED", False):
        return

    token = config["TELEGRAM_TOKEN"]
    chat_id = config["TELEGRAM_CHAT_ID"]
    topic_id = config.get("TELEGRAM_TOPIC_ID")

    entries = load_final()
    if not entries:
        return

    total = len(entries)
    sent = 0

    # Print initial progress (0/total)
    print(f"\r[{sent}/{total}]", end='', flush=True)

    for idx, entry in enumerate(entries, start=1):
        domain = entry.get("domain", f"entry_{idx}")
        message_text = build_message(entry)
        screenshot_path = POC_DIR / domain / "screenshot.png"

        success = send_alert(token, chat_id, message_text, screenshot_path, topic_id)
        if success:
            sent += 1

        # Update progress in-place
        print(f"\r[{sent}/{total}]", end='', flush=True)

        # Small delay between messages (except last)
        if idx < total:
            time.sleep(SEND_DELAY)

    # Final newline and summary
    print()  # newline after progress
    print(f"Done: {sent} of {total} alerts sent.")

if __name__ == "__main__":
    main()
