#!/usr/bin/env python3

import os
import json
import time
import requests
from datetime import datetime, timezone

# ======================================
# Paths
# ======================================

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_FILE = os.path.join(ROOT_DIR, "configs", "telegram-settings.json")
FINAL_FILE = os.path.join(ROOT_DIR, "found", "final.json")
POC_DIR = os.path.join(ROOT_DIR, "poc")

TIMEOUT = 10
SEND_DELAY = 0.7
MAX_NETWORK_UNREACHABLE_RETRIES = 10   # only for "Network is unreachable"

# ======================================
# Config
# ======================================

def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

# ======================================
# Telegram Senders
# ======================================

def send_message(token, chat_id, message, topic_id=None):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    if topic_id:
        payload["message_thread_id"] = int(topic_id)
    return safe_post(url, payload)


def send_photo(token, chat_id, photo_path, caption, topic_id=None):
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    with open(photo_path, "rb") as photo:
        files = {"photo": photo}
        data = {
            "chat_id": chat_id,
            "caption": caption,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        if topic_id:
            data["message_thread_id"] = int(topic_id)
        return safe_post(url, data, files=files)


def safe_post(url, data, files=None):
    """
    - 429: indefinite retry with retry_after (silent)
    - Network unreachable: max 10 retries then fail (silent)
    - Other errors: indefinite retry with 5s sleep (silent)
    """
    network_unreachable_count = 0

    while True:
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

            # Other status codes → indefinite retry
            time.sleep(5)

        except requests.RequestException as e:
            # Specific "Network is unreachable" error
            if "Network is unreachable" in str(e):
                network_unreachable_count += 1
                if network_unreachable_count >= MAX_NETWORK_UNREACHABLE_RETRIES:
                    return False
                time.sleep(5)
                continue

            # Other network errors → indefinite retry
            time.sleep(5)

# ======================================
# Load Final Report
# ======================================

def load_final():
    if not os.path.exists(FINAL_FILE):
        return []
    with open(FINAL_FILE, "r") as f:
        return json.load(f)

# ======================================
# Severity Styling
# ======================================

def severity_emoji(severity):
    return {
        "critical": "💀",
        "high": "🔥",
        "medium": "⚠️",
        "low": "🔎"
    }.get(str(severity).lower(), "ℹ️")

# ======================================
# Message Builder
# ======================================

def build_message(entry):
    domain = entry.get("domain")
    services = ", ".join(entry.get("services", []))
    engines = ", ".join(entry.get("engines", []))
    confidence = entry.get("confidence", 0)
    severity = entry.get("severity", "low")
    discussions = entry.get("discussion")

    emoji = severity_emoji(severity)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    message = f"""
{emoji} *VECNA TAKEOVER DETECTED* {emoji}

🎯 *Target:* `{domain}`
🧩 *Service(s):* `{services}`
🧠 *Engine(s):* `{engines}`

📊 *Severity:* *{severity.upper()}*
📈 *Confidence:* `{confidence}%`
"""

    if discussions:
        message += "\n📚 *References:*\n"
        if isinstance(discussions, list):
            for d in discussions:
                message += f"- {d}\n"
        else:
            message += f"- {discussions}\n"

    message += f"\n⏱ `{now}`\n"
    return message.strip()

# ======================================
# Main
# ======================================

def main():
    config = load_config()

    if not config.get("TELEGRAM_ENABLED", False):
        print("[-] Telegram disabled.")
        return

    token = config["TELEGRAM_TOKEN"]
    chat_id = config["TELEGRAM_CHAT_ID"]
    topic_id = config.get("TELEGRAM_TOPIC_ID")

    entries = load_final()

    if not entries:
        print("[-] No entries found.")
        return

    sent = 0

    for entry in entries:
        domain = entry.get("domain")
        message = build_message(entry)
        screenshot_path = os.path.join(POC_DIR, domain, "screenshot.png")

        if os.path.exists(screenshot_path):
            success = send_photo(token, chat_id, screenshot_path, message, topic_id)
        else:
            success = send_message(token, chat_id, message, topic_id)

        if success:
            sent += 1
            time.sleep(SEND_DELAY)
        # if not sent, nothing printed (silent retry already handled)

    # Final summary
    if sent == 0 and entries:
        print("[!] Unable to send Telegram alerts due to network error.")
    else:
        print(f"[+] Sent {sent} Telegram alert(s).")

# ======================================

if __name__ == "__main__":
    main()
