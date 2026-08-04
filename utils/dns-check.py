#!/usr/bin/env python3

import sys
import os
import json
import dns.resolver
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

# ========= Paths ========= #

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIR = os.path.join(ROOT_DIR, "output")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "dns-output.json")

# ========= DNS Resolver (Global for speed) ========= #

resolver = dns.resolver.Resolver()
resolver.timeout = 2
resolver.lifetime = 3

RECORD_TYPES = ["A", "AAAA", "CNAME", "MX", "NS"]

# ========= Helpers ========= #

def normalize_target(target: str):
    target = target.strip()
    if not target:
        return None

    if not target.startswith(("http://", "https://")):
        target = "http://" + target

    parsed = urlparse(target)
    return parsed.netloc.lower()

def read_input(arg: str):
    if os.path.isfile(arg):
        with open(arg, "r") as f:
            return [normalize_target(line) for line in f if line.strip()]
    else:
        return [normalize_target(arg)]

def get_dns_records(domain: str):
    records = {}

    for rtype in RECORD_TYPES:
        try:
            answers = resolver.resolve(domain, rtype)
            records[rtype] = [r.to_text() for r in answers]
        except Exception:
            records[rtype] = []

    return domain, records

def save_output(all_results: dict):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(all_results, f, indent=4)

# ========= Main ========= #

def main():
    if len(sys.argv) != 2:
        print("Usage:")
        print(" python dns-check.py target.com")
        print(" python dns-check.py domains.txt")
        sys.exit(1)

    targets = [t for t in read_input(sys.argv[1]) if t]
    total = len(targets)

    all_results = {}

    # 🔥 Parallel DNS
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(get_dns_records, domain) for domain in targets]

        for index, future in enumerate(as_completed(futures), start=1):
            domain, dns_data = future.result()
            all_results[domain] = dns_data
            print(f"\r[DNS] Completed {index}/{total}", end="", flush=True)

    print()
    save_output(all_results)

if __name__ == "__main__":
    main()