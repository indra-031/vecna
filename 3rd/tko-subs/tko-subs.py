#!/usr/bin/env python3

import os
import sys
import json
import csv
import re
from urllib.parse import urlparse
from datetime import datetime, timezone

# =========================================================
# Paths
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "../.."))

DNS_FILE = os.path.join(ROOT_DIR, "output", "dns-output.json")
HTTP_FILE = os.path.join(ROOT_DIR, "output", "http-output.json")

CSV_FILE = os.path.join(BASE_DIR, "providers-data.csv")

FOUND_DIR = os.path.join(ROOT_DIR, "found")
OUTPUT_FILE = os.path.join(FOUND_DIR, "tkosubs.json")

# =========================================================
# Helpers
# =========================================================

def normalize_target(target: str):
    target = target.strip()
    if not target:
        return None

    if not target.startswith(("http://", "https://")):
        target = "http://" + target

    parsed = urlparse(target)
    return parsed.netloc.lower()

def read_targets(arg: str):
    if os.path.isfile(arg):
        with open(arg, "r") as f:
            return [normalize_target(line) for line in f if line.strip()]
    return [normalize_target(arg)]

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)

def load_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def get_full_body(domain_http):
    for proto in ["http", "https"]:
        pdata = domain_http.get(proto, {})
        body = (
            pdata.get("body")
            or pdata.get("body_preview")
            or pdata.get("body_snippet")
        )
        if body:
            return body.lower()
    return ""

def get_domain_cnames(domain, dns_data):
    domain_dns = dns_data.get(domain, {})
    cnames = domain_dns.get("CNAME", [])
    return [c.lower().rstrip(".") for c in cnames]

def text_matches(body, pattern):
    try:
        return re.search(pattern, body, re.IGNORECASE) is not None
    except re.error:
        return pattern.lower() in body

# =========================================================
# Core Logic
# =========================================================

def match_tkosubs(domain, dns_data, http_data, providers):

    results = []

    body = get_full_body(http_data.get(domain, {}))
    cnames = get_domain_cnames(domain, dns_data)

    for row in providers:

        service = row.get("name", "").strip()
        cname_pattern = row.get("cname", "").strip().lower()
        fingerprint = row.get("string", "").strip()
        http_required = row.get("http", "false").strip().lower() == "true"

        # -----------------------------
        # CNAME match (required)
        # -----------------------------

        cname_match = False

        for cname in cnames:
            if cname_pattern and cname_pattern in cname:
                cname_match = True
                break

        if not cname_match:
            continue

        # -----------------------------
        # HTTP requirement logic
        # -----------------------------

        if http_required and not body:
            continue

        # -----------------------------
        # Body fingerprint match
        # -----------------------------

        if fingerprint:
            if not body:
                continue

            if not text_matches(body, fingerprint):
                continue

        # -----------------------------
        # Matched
        # -----------------------------

        results.append({
            "domain": domain,
            "engine": "tkosubs",
            "service": service,
            "type": "fingerprint",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    return results

# =========================================================
# Main
# =========================================================

def main():

    if len(sys.argv) != 2:
        print("Usage: python tkosubs.py domains.txt")
        sys.exit(1)

    targets = read_targets(sys.argv[1])

    dns_data = load_json(DNS_FILE)
    http_data = load_json(HTTP_FILE)
    providers = load_csv(CSV_FILE)

    all_findings = []

    for domain in targets:
        if not domain:
            continue

        findings = match_tkosubs(domain, dns_data, http_data, providers)
        all_findings.extend(findings)

    if all_findings:
        os.makedirs(FOUND_DIR, exist_ok=True)

        with open(OUTPUT_FILE, "w") as f:
            json.dump(all_findings, f, indent=4)

        print(f"[+] Found {len(all_findings)} vulnerable target(s) via TKO-SUBS.")
    else:
        print("[-] No TKO-SUBS matches found.")

if __name__ == "__main__":
    main()