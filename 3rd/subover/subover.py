#!/usr/bin/env python3

import os
import sys
import json
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

PROVIDERS_FILE = os.path.join(BASE_DIR, "providers.json")

FOUND_DIR = os.path.join(ROOT_DIR, "found")
OUTPUT_FILE = os.path.join(FOUND_DIR, "subover.json")

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

def ensure_list(value):
    if not value:
        return []
    if isinstance(value, list):
        return value
    return [value]

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
# Core Matching Logic
# =========================================================

def match_subover(domain, dns_data, http_data, providers):

    results = []

    domain_dns = dns_data.get(domain, {})
    domain_http = http_data.get(domain, {})

    body = get_full_body(domain_http)
    cnames = get_domain_cnames(domain, dns_data)

    for provider in providers:

        service = provider.get("name", "unknown")
        cname_patterns = [c.lower() for c in ensure_list(provider.get("cname"))]
        body_patterns = ensure_list(provider.get("response"))

        # -----------------------------
        # CNAME Match (required)
        # -----------------------------

        cname_match = False

        if cname_patterns:
            for expected in cname_patterns:
                for actual in cnames:
                    if expected in actual:
                        cname_match = True
                        break
                if cname_match:
                    break

        if not cname_match:
            continue

        # -----------------------------
        # Body Match
        # -----------------------------

        if not body:
            continue

        body_match = False

        for pattern in body_patterns:
            if text_matches(body, pattern):
                body_match = True
                break

        if not body_match:
            continue

        # -----------------------------
        # Matched
        # -----------------------------

        results.append({
            "domain": domain,
            "engine": "subover",
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
        print("Usage: python subover.py domains.txt")
        sys.exit(1)

    targets = read_targets(sys.argv[1])

    dns_data = load_json(DNS_FILE)
    http_data = load_json(HTTP_FILE)
    providers = load_json(PROVIDERS_FILE)

    all_findings = []

    for domain in targets:
        if not domain:
            continue

        findings = match_subover(domain, dns_data, http_data, providers)
        all_findings.extend(findings)

    if all_findings:
        os.makedirs(FOUND_DIR, exist_ok=True)

        with open(OUTPUT_FILE, "w") as f:
            json.dump(all_findings, f, indent=4)

        print(f"[+] Found {len(all_findings)} vulnerable target(s) via Subover.")
    else:
        print("[-] No Subover matches found.")

if __name__ == "__main__":
    main()