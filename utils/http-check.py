#!/usr/bin/env python3

import os
import sys
import json
import asyncio
import aiohttp

# ======================================
# CONFIG
# ======================================

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIR = os.path.join(ROOT_DIR, "output")

DNS_FILE = os.path.join(OUTPUT_DIR, "dns-output.json")
HTTP_OUTPUT = os.path.join(OUTPUT_DIR, "http-output.json")

WORKERS = 60
TIMEOUT = 25

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# ======================================
# LOAD DNS + DOMAINS
# ======================================

def load_dns():
    if not os.path.exists(DNS_FILE):
        print("dns-output.json not found")
        sys.exit(1)

    with open(DNS_FILE, "r") as f:
        dns_data = json.load(f)

    domains = [
        d for d, r in dns_data.items()
        if r.get("A") or r.get("AAAA") or r.get("CNAME")
    ]

    return domains, dns_data

# ======================================
# CONNECTOR
# ======================================

def make_connector(limit):
    return aiohttp.TCPConnector(
        limit=limit,
        limit_per_host=6,
        ttl_dns_cache=600,
        ssl=False,
        enable_cleanup_closed=True
    )

# ======================================
# FULL FETCH PHASE (NO HEAD, NO FILTER)
# ======================================

async def status_phase(domains, dns_data):

    results = {}

    connector = make_connector(WORKERS)
    timeout = aiohttp.ClientTimeout(total=TIMEOUT)
    sem = asyncio.Semaphore(WORKERS)

    async with aiohttp.ClientSession(
        connector=connector,
        timeout=timeout
    ) as session:

        async def worker(domain, proto):

            async with sem:

                try:
                    records = dns_data.get(domain, {})
                    ips = records.get("A") or records.get("AAAA")

                    if not ips:
                        return domain, proto, {
                            "status": None,
                            "body": "NO_IP"
                        }

                    ip = ips[0]
                    url = f"{proto}://{ip}"

                    headers = HEADERS.copy()
                    headers["Host"] = domain

                    async with session.get(
                        url,
                        headers=headers,
                        allow_redirects=True
                    ) as r:

                        body = await r.read()

                        return domain, proto, {
                            "status": r.status,
                            "body": body.decode(errors="ignore")
                        }

                except Exception as e:
                    return domain, proto, {
                        "status": None,
                        "body": f"ERROR:{type(e).__name__}"
                    }

        tasks = []

        for domain in domains:
            tasks.append(worker(domain, "https"))
            tasks.append(worker(domain, "http"))

        total = len(tasks)

        for i, coro in enumerate(asyncio.as_completed(tasks), 1):
            domain, proto, data = await coro

            if domain not in results:
                results[domain] = {}

            results[domain][proto] = data

            print(f"\r[FETCH] {i}/{total}", end="", flush=True)

        print()

    return results

# ======================================
# SAVE
# ======================================

def save_output(data):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(HTTP_OUTPUT, "w") as f:
        json.dump(data, f, indent=4)

# ======================================
# MAIN
# ======================================

def main():

    domains, dns_data = load_dns()

    if not domains:
        print("No resolved domains.")
        return

    print(f"Loaded {len(domains)} domains")

    results = asyncio.run(status_phase(domains, dns_data))

    save_output(results)

    print("Done.")

if __name__ == "__main__":
    main()