#!/usr/bin/env python3

import json
import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INPUT_FILE = os.path.join(ROOT_DIR, "output", "dns-output.json")
OUTPUT_FILE = os.path.join(ROOT_DIR, "output", "alive-domains.txt")

def main():

    if not os.path.exists(INPUT_FILE):
        print("dns-output.json not found")
        sys.exit(1)

    with open(INPUT_FILE, "r") as f:
        dns_data = json.load(f)

    alive = []

    for domain, records in dns_data.items():

        if not isinstance(records, dict):
            continue

        has_a = records.get("A")
        has_aaaa = records.get("AAAA")
        has_cname = records.get("CNAME")

        if has_a or has_aaaa or has_cname:
            alive.append(domain)

    alive = sorted(set(alive))

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    with open(OUTPUT_FILE, "w") as f:
        for d in alive:
            f.write(d.strip() + "\n")

    print(f"[✓] Extract {len(alive)} alive domains")

if __name__ == "__main__":
    main()