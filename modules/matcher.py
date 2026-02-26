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
# Utils
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
            return [normalize_target(x) for x in f if x.strip()]
    return [normalize_target(arg)]

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)

def ensure_list(v):
    if not v:
        return []
    if isinstance(v, list):
        return v
    return [v]

# =========================================================
# DNS Match
# =========================================================

def match_dns(domain_dns, dns_conditions):

    cname_records = [
        c.lower() for c in domain_dns.get("CNAME", [])
    ]

    keywords = [
        k.lower() for k in ensure_list(
            dns_conditions.get("cname_contains")
        )
    ]

    if not cname_records or not keywords:
        return False

    return any(
        kw in cname
        for cname in cname_records
        for kw in keywords
    )

# =========================================================
# HTTP Match (Strict + Per-Protocol)
# =========================================================

def match_http(domain_http, http_conditions, match_logic="AND"):

    for proto in ["http", "https"]:

        pdata = domain_http.get(proto, {})
        status = pdata.get("status")
        body = (pdata.get("body") or "").lower()
        headers = {
            k.lower(): v.lower()
            for k, v in pdata.get("headers", {}).items()
        }

        checks = []

        # ---- STATUS ----
        status_in = ensure_list(http_conditions.get("status_in"))
        if status_in:
            checks.append(status in status_in)

        # ---- BODY ----
        body_keywords = [
            k.lower() for k in ensure_list(
                http_conditions.get("body_contains_any")
            )
        ]
        if body_keywords:
            checks.append(
                any(kw in body for kw in body_keywords)
            )

        # ---- HEADER ----
        header_conditions = http_conditions.get("header_contains", {})
        if header_conditions:
            header_match = False
            for hk, hv in header_conditions.items():
                hk = hk.lower()
                hv = hv.lower()
                if hk in headers and hv in headers[hk]:
                    header_match = True
            checks.append(header_match)

        if not checks:
            continue

        if match_logic == "AND":
            if all(checks):
                return True
        else:  # OR
            if any(checks):
                return True

    return False

# =========================================================
# Core
# =========================================================

def match_domain(domain, dns_data, http_data, signatures):

    results = []

    domain_dns = dns_data.get(domain, {})
    domain_http = http_data.get(domain, {})

    for sig in signatures:

        if not sig.get("enabled", True):
            continue

        conditions = sig.get("conditions", {})
        dns_conditions = conditions.get("dns", {})
        http_conditions = conditions.get("http", {})

        if not dns_conditions or not http_conditions:
            continue

        match_logic = sig.get("match_logic", "AND")

        dns_match = match_dns(domain_dns, dns_conditions)
        if not dns_match:
            continue

        http_match = match_http(
            domain_http,
            http_conditions,
            match_logic
        )
        if not http_match:
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

        findings = match_domain(
            domain,
            dns_data,
            http_data,
            signatures
        )

        all_findings.extend(findings)

    if all_findings:
        os.makedirs(FOUND_DIR, exist_ok=True)
        with open(OUTPUT_FILE, "w") as f:
            json.dump(all_findings, f, indent=4)

    print(f"[+] Found {len(all_findings)} vulnerable target(s).")

if __name__ == "__main__":
    main()