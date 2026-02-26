#!/usr/bin/env python3

import subprocess
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
FOUND_DIR = ROOT_DIR / "found"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

NUCLEI_CONCURRENCY = 150
NUCLEI_RATE_LIMIT = 300

def normalize_domains(domains_file):
    normalized_file = ROOT_DIR / "output" / "normalized-nuclei.txt"
    normalized_file.parent.mkdir(exist_ok=True)

    with open(domains_file, "r") as infile, open(normalized_file, "w") as outfile:
        for line in infile:
            domain = line.strip()
            if not domain:
                continue

            if not domain.startswith(("http://", "https://")):
                domain = "https://" + domain

            outfile.write(domain + "\n")

    return normalized_file

def run_nuclei(target_file):
    print("[+] Running Nuclei (takeover templates only)...")

    cmd = [
        "nuclei",
        "-silent",
        "-duc",
        "-j",
        "-c", str(NUCLEI_CONCURRENCY),
        "-rl", str(NUCLEI_RATE_LIMIT),
        "-t", str(TEMPLATES_DIR),
        "-l", str(target_file),
    ]

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=1,
            text=True
        )
    except FileNotFoundError:
        print("[-] nuclei binary not found.")
        sys.exit(1)

    findings = []

    for line in process.stdout:
        line = line.strip()
        if not line:
            continue

        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue

        findings.append({
            "engine": "nuclei",
            "domain": data.get("host"),
            "template": data.get("template-id"),
            "severity": data.get("info", {}).get("severity"),
            "name": data.get("info", {}).get("name"),
            "matched_at": data.get("matched-at"),
            "type": "takeover"
        })

    process.wait()
    return findings

def save_findings(findings):
    if not findings:
        print("[-] No takeover findings from nuclei.")
        return

    FOUND_DIR.mkdir(exist_ok=True)
    output_file = FOUND_DIR / "nuclei.json"

    with open(output_file, "w") as f:
        json.dump(findings, f, indent=4)

    print(f"[+] Saved {len(findings)} nuclei findings")

def main():
    domains_file = ROOT_DIR / "output" / "alive-domains.txt"

    if not domains_file.exists():
        print("[-] alive-domains.txt not found.")
        sys.exit(1)

    normalized_file = normalize_domains(domains_file)
    findings = run_nuclei(normalized_file)
    save_findings(findings)

if __name__ == "__main__":
    main()