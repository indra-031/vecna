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

STATUS_WORKERS = 60
BODY_WORKERS = 20

STATUS_TIMEOUT = 8
BODY_TIMEOUT = 25

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
# CONNECTOR (REUSED)
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
# STATUS PHASE
# ======================================

async def status_phase(domains):

    results = {}
    body_targets = []

    connector = make_connector(STATUS_WORKERS)
    timeout = aiohttp.ClientTimeout(total=STATUS_TIMEOUT)

    sem = asyncio.Semaphore(STATUS_WORKERS)

    async with aiohttp.ClientSession(
        connector=connector,
        timeout=timeout
    ) as session:

        async def worker(domain):

            async with sem:

                async def check(url):
                    try:
                        async with session.get(
                            url,
                            headers=HEADERS,
                            allow_redirects=False
                        ) as r:
                            return r.status
                    except:
                        return "error"

                https_status, http_status = await asyncio.gather(
                    check(f"https://{domain}"),
                    check(f"http://{domain}")
                )

                results[domain] = {
                    "https": {"status": https_status},
                    "http": {"status": http_status}
                }

                if https_status in (403, 404):
                    body_targets.append((domain, "https"))

                if http_status in (403, 404):
                    body_targets.append((domain, "http"))

        tasks = [worker(d) for d in domains]

        total = len(tasks)

        for i, coro in enumerate(asyncio.as_completed(tasks), 1):
            await coro
            print(f"\r[STATUS] {i}/{total}", end="", flush=True)

    print()
    print(f"Found {len(body_targets)} targets (403/404)")
    return results, body_targets


# ======================================
# BODY PHASE (NO DNS RE-RESOLVE)
# ======================================

async def body_phase(results, targets, dns_data):

    if not targets:
        return results

    print("Saving bodies...")

    connector = make_connector(BODY_WORKERS)
    timeout = aiohttp.ClientTimeout(total=BODY_TIMEOUT)

    sem = asyncio.Semaphore(BODY_WORKERS)

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
                        results[domain][proto]["body"] = "NO_IP"
                        return

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

                        results[domain][proto]["status"] = r.status
                        results[domain][proto]["body"] = body.decode(errors="ignore")

                except Exception as e:
                    results[domain][proto]["body"] = f"BODY_ERROR:{type(e).__name__}"

        tasks = [
            worker(d, p)
            for d, p in targets
        ]

        total = len(tasks)

        for i, coro in enumerate(asyncio.as_completed(tasks), 1):
            await coro
            print(f"\r[BODY] {i}/{total}", end="", flush=True)

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

    results, body_targets = asyncio.run(status_phase(domains))

    results = asyncio.run(
        body_phase(results, body_targets, dns_data)
    )

    save_output(results)

    print("Done.")


if __name__ == "__main__":
    main()