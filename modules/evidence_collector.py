#!/usr/bin/env python3

import os
import json
import traceback
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright

# =========================================================
# Paths
# =========================================================

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

FINAL_FILE = os.path.join(ROOT_DIR, "found", "final.json")
DNS_FILE = os.path.join(ROOT_DIR, "output", "dns-output.json")
HTTP_FILE = os.path.join(ROOT_DIR, "output", "http-output.json")

POC_DIR = os.path.join(ROOT_DIR, "poc")

# =========================================================
# Config
# =========================================================

PAGE_TIMEOUT = 8000
BROWSER_TIMEOUT = 60000
RESTART_BROWSER_EVERY = 50  

# =========================================================
# Utils
# =========================================================

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

def has_dns_records(dns_data):
    return bool(dns_data)

# =========================================================
# Screenshot Safe Wrapper
# =========================================================

def safe_screenshot(browser, domain, screenshot_path):

    try:
        page = browser.new_page()
        page.set_default_navigation_timeout(PAGE_TIMEOUT)

        page.goto(
            f"http://{domain}",
            timeout=PAGE_TIMEOUT,
            wait_until="domcontentloaded"
        )

        page.screenshot(path=screenshot_path, full_page=True)
        page.close()
        return True

    except Exception:
        try:
            page.close()
        except:
            pass
        return False

# =========================================================
# Evidence Builder
# =========================================================

def collect_for_domain(entry, browser, dns_all, http_all, stats):

    domain = entry.get("domain")
    if not domain:
        return

    try:

        domain_dir = os.path.join(POC_DIR, domain)

        if os.path.exists(domain_dir):
            stats["skipped"] += 1
            return

        os.makedirs(domain_dir, exist_ok=True)

        dns_data = dns_all.get(domain, {})
        http_data = http_all.get(domain, {})

        save_json(os.path.join(domain_dir, "dns.json"), dns_data)
        save_json(os.path.join(domain_dir, "http.json"), http_data)

        # -------------------------
        # RAW HTTP
        # -------------------------

        raw_path = os.path.join(domain_dir, "raw_http.txt")

        with open(raw_path, "w") as f:
            for proto in ["http", "https"]:
                pdata = http_data.get(proto, {})
                if "body_preview" in pdata:
                    f.write(f"\n===== {proto.upper()} =====\n")
                    f.write(pdata["body_preview"])
                    f.write("\n")

        # -------------------------
        # Screenshot
        # -------------------------

        screenshot_taken = False

        if has_dns_records(dns_data):
            screenshot_path = os.path.join(domain_dir, "screenshot.png")
            screenshot_taken = safe_screenshot(browser, domain, screenshot_path)

            if screenshot_taken:
                stats["screenshots"] += 1
            else:
                stats["errors"] += 1
        else:
            stats["nxdomain"] += 1

        # -------------------------
        # Final Report
        # -------------------------

        report = {
            "domain": domain,
            "services": entry.get("services", []),
            "engines": entry.get("engines", []),
            "confidence": entry.get("confidence"),
            "severity": entry.get("severity"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "evidence_files": {
                "dns": "dns.json",
                "http": "http.json",
                "raw_http": "raw_http.txt",
                "screenshot": "screenshot.png" if screenshot_taken else None
            }
        }

        save_json(os.path.join(domain_dir, "report.json"), report)

        stats["processed"] += 1

    except Exception:
        stats["errors"] += 1
        traceback.print_exc()

# =========================================================
# Browser Launcher (Safe)
# =========================================================

def launch_browser(p):
    return p.chromium.launch(
        headless=True,
        timeout=BROWSER_TIMEOUT,
        args=[
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-setuid-sandbox",
        ]
    )

# =========================================================
# Main
# =========================================================

def main():

    if not os.path.exists(FINAL_FILE):
        print("[-] final.json not found.")
        return

    final_data = load_json(FINAL_FILE)

    if not final_data:
        print("[-] No entries inside final.json")
        return

    total = len(final_data)
    print(f"[+] Domains to process: {total}")

    os.makedirs(POC_DIR, exist_ok=True)

    dns_all = load_json(DNS_FILE)
    http_all = load_json(HTTP_FILE)

    stats = {
        "processed": 0,
        "skipped": 0,
        "screenshots": 0,
        "errors": 0,
        "nxdomain": 0
    }

    with sync_playwright() as p:

        browser = launch_browser(p)

        for i, entry in enumerate(final_data, 1):

            print(f"\r[+] Processing {i}/{total}", end="", flush=True)

            try:
                collect_for_domain(entry, browser, dns_all, http_all, stats)
            except Exception:
                stats["errors"] += 1

            if i % RESTART_BROWSER_EVERY == 0:
                try:
                    browser.close()
                except:
                    pass
                browser = launch_browser(p)

        try:
            browser.close()
        except:
            pass

    print("\n")
    print(f"   Total Domains   : {total}")
    print(f"   Processed       : {stats['processed']}")
    print(f"   Skipped (exist) : {stats['skipped']}")
    print(f"   Screenshots     : {stats['screenshots']}")
    print(f"   Errors          : {stats['errors']}")
    print(f"   NXDOMAIN        : {stats['nxdomain']}")

# =========================================================

if __name__ == "__main__":
    main()
