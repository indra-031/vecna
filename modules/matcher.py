#!/usr/bin/env python3

import os
import sys
import json
from urllib.parse import urlparse

# =========================================================
# Paths
# =========================================================

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

DNS_FILE = os.path.join(ROOT_DIR, "output", "dns-output.json")
HTTP_FILE = os.path.join(ROOT_DIR, "output", "http-output.json")
SIGNATURE_FILE = os.path.join(ROOT_DIR, "configs", "signatures.json")

FOUND_DIR = os.path.join(ROOT_DIR, "found")
OUTPUT_FILE = os.path.join(FOUND_DIR, "internal.json")

# =========================================================
# Utilities
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

# =========================================================
# Core Matching Logic
# =========================================================

def extract_http_data(domain_http):
    statuses = []
    bodies = []
    headers_list = []

    for proto in ["http", "https"]:
        pdata = domain_http.get(proto, {})

        if "status" in pdata:
            statuses.append(pdata["status"])

        if "body_snippet" in pdata:
            bodies.append(pdata["body_snippet"].lower())

        if "headers" in pdata:
            headers_list.append({
                k.lower(): v.lower()
                for k, v in pdata["headers"].items()
            })

    return statuses, bodies, headers_list

def match_dns(cname_records, dns_conditions):
    cname_keywords = [
        k.lower() for k in ensure_list(dns_conditions.get("cname_contains"))
    ]

    if not cname_keywords:
        return False

    if not cname_records:
        return False

    return any(
        keyword in cname
        for cname in cname_records
        for keyword in cname_keywords
    )

def match_http(statuses, bodies, headers, http_conditions):

    expected_status = ensure_list(http_conditions.get("status"))
    if expected_status:
        if not any(s in expected_status for s in statuses):
            return False

    body_keywords = [
        k.lower() for k in ensure_list(http_conditions.get("body_contains"))
    ]

    if body_keywords:
        if not any(
            keyword in body
            for body in bodies
            for keyword in body_keywords
        ):
            return False

    header_conditions = http_conditions.get("header_contains", {})
    if header_conditions:
        matched = False
        for hdr in headers:
            for hk, hv in header_conditions.items():
                if hk.lower() in hdr and hv.lower() in hdr[hk.lower()]:
                    matched = True
        if not matched:
            return False

    return True

def match_domain(domain, dns_data, http_data, signatures):

    results = []

    domain_dns = dns_data.get(domain, {})
    domain_http = http_data.get(domain, {})

    cname_records = [
        c.lower() for c in domain_dns.get("CNAME", [])
    ]

    statuses, bodies, headers = extract_http_data(domain_http)

    for sig in signatures:

        if not sig.get("enabled", True):
            continue

        conditions = sig.get("conditions", {})
        dns_conditions = conditions.get("dns", {})
        http_conditions = conditions.get("http", {})

        if not match_dns(cname_records, dns_conditions):
            continue

        if not match_http(statuses, bodies, headers, http_conditions):
            continue

        results.append({
            "domain": domain,
            "signature": sig.get("id"),
            "service": sig.get("service"),
            "severity": sig.get("severity"),
            "confidence": sig.get("confidence")
        })

    return results

# =========================================================
# Main
# =========================================================

def main():

    if len(sys.argv) != 2:
        print("Usage:")
        print(" python matcher.py domain.com")
        print(" python matcher.py domains.txt")
        sys.exit(1)

    targets = read_targets(sys.argv[1])

    dns_data = load_json(DNS_FILE)
    http_data = load_json(HTTP_FILE)
    signatures = load_json(SIGNATURE_FILE)

    all_findings = []

    for domain in targets:
        if not domain:
            continue

        findings = match_domain(domain, dns_data, http_data, signatures)
        all_findings.extend(findings)

    if all_findings:
        os.makedirs(FOUND_DIR, exist_ok=True)

        with open(OUTPUT_FILE, "w") as f:
            json.dump(all_findings, f, indent=4)

    print(f"[+] Found {len(all_findings)} vulnerable target(s).")

if __name__ == "__main__":
    main()