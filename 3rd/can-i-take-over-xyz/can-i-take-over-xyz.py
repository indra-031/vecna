#!/usr/bin/env python3

import os
import sys
import json
import re
from datetime import datetime, timezone

# ======================================
# Paths
# ======================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "../.."))

HTTP_FILE = os.path.join(ROOT_DIR, "output", "http-output.json")
DNS_FILE = os.path.join(ROOT_DIR, "output", "dns-output.json")

FINGERPRINT_FILE = os.path.join(BASE_DIR, "fingerprints.json")

FOUND_DIR = os.path.join(ROOT_DIR, "found")
OUTPUT_FILE = os.path.join(FOUND_DIR, "can-i-take-over-xyz.json")

# ======================================
# Helpers
# ======================================

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)

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

def calculate_severity(fp):
    if fp.get("vulnerable") is True:
        return "high"

    if str(fp.get("status", "")).lower() == "edge case":
        return "medium"

    return "info"

def text_matches(body, pattern):
    try:
        return re.search(pattern, body, re.IGNORECASE) is not None
    except re.error:
        return pattern.lower() in body

def cname_matches(domain_cnames, expected_cnames):
    if not expected_cnames:
        return True

    for expected in expected_cnames:
        expected = expected.lower()
        for actual in domain_cnames:
            if expected in actual:
                return True
    return False

# ======================================
# Core Matcher
# ======================================

def match_domain(domain, http_data, dns_data, fingerprints):

    results = []

    domain_http = http_data.get(domain)
    if not domain_http:
        return results

    body = get_full_body(domain_http)
    if not body:
        return results

    domain_cnames = get_domain_cnames(domain, dns_data)

    for fp in fingerprints:

        service = fp.get("service", "unknown")
        fingerprint = fp.get("fingerprint")

        if not fingerprint:
            continue

        expected_cnames = fp.get("cname", [])

        if not cname_matches(domain_cnames, expected_cnames):
            continue

        if not text_matches(body, fingerprint):
            continue

        results.append({
            "domain": domain,
            "engine": "can-i-take-over-xyz",
            "service": service,
            "severity": calculate_severity(fp),
            "matched_on": "body_text",
            "fingerprint": fingerprint,
            "discussion": fp.get("discussion"),
            "documentation": fp.get("documentation"),
            "cname": expected_cnames,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    return results

# ======================================
# Main
# ======================================

def main():

    if len(sys.argv) != 2:
        print("Usage: python can-i-take-over-xyz.py domains.txt")
        sys.exit(1)

    if os.path.isfile(sys.argv[1]):
        with open(sys.argv[1], "r") as f:
            targets = [line.strip() for line in f if line.strip()]
    else:
        targets = [sys.argv[1]]

    http_data = load_json(HTTP_FILE)
    dns_data = load_json(DNS_FILE)
    fingerprints = load_json(FINGERPRINT_FILE)

    if not http_data:
        print("[-] No HTTP results found.")
        return

    if not dns_data:
        print("[-] No DNS results found.")
        return

    if not fingerprints:
        print("[-] No fingerprints loaded.")
        return

    all_findings = []

    for domain in targets:
        findings = match_domain(domain, http_data, dns_data, fingerprints)
        all_findings.extend(findings)

    if all_findings:
        os.makedirs(FOUND_DIR, exist_ok=True)

        with open(OUTPUT_FILE, "w") as f:
            json.dump(all_findings, f, indent=4)

        print(f"[+] Saved {len(all_findings)} findings")
    else:
        print("[-] No third-party matches found.")

if __name__ == "__main__":
    main()