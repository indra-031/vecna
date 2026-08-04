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
    """Remove protocol from domains for Nuclei."""
    normalized_file = ROOT_DIR / "output" / "normalized-nuclei.txt"
    normalized_file.parent.mkdir(exist_ok=True)

    with open(domains_file, "r") as infile, open(normalized_file, "w") as outfile:
        for line in infile:
            domain = line.strip()
            if not domain:
                continue
            # remove protocol if present
            if domain.startswith("http://"):
                domain = domain[len("http://"):]
            elif domain.startswith("https://"):
                domain = domain[len("https://"):]
            outfile.write(domain + "\n")

    return normalized_file

def run_nuclei(target_file):
    print("[+] Running Nuclei (takeover templates only - please wait)...")

    cmd = [
        "nuclei",
        "-silent",
        "-j",
        "-t", str(TEMPLATES_DIR),
        "-l", str(target_file),
    ]

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
    except FileNotFoundError:
        print("[-] nuclei binary not found.")
        sys.exit(1)

    # Read all output safely
    stdout_data, stderr_data = process.communicate()

    if stderr_data:
        print("[!] Nuclei stderr:")
        print(stderr_data)

    findings = []
    for line in stdout_data.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue

        domain = data.get("host")
        if not domain:
            matched = data.get("matched-at")
            if matched and "://" in matched:
                domain = matched.split("://")[1].split("/")[0]
            else:
                domain = matched

        findings.append({
            "engine": "nuclei",
            "domain": domain,
            "template": data.get("template-id"),
            "severity": data.get("info", {}).get("severity"),
            "name": data.get("info", {}).get("name"),
            "matched_at": data.get("matched-at"),
            "type": "takeover"
        })

    # Debug line (uncomment if needed)
    # print(f"[DEBUG] Nuclei raw findings count: {len(findings)}")

    return findings

def save_findings(findings):
    if not findings:
        print("[-] No takeover findings from nuclei.")
        return

    FOUND_DIR.mkdir(exist_ok=True)
    output_file = FOUND_DIR / "nuclei.json"
    with open(output_file, "w") as f:
        json.dump(findings, f, indent=4)
    print(f"[+] Found {len(findings)} vulnerable target(s) via Nuclei.")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 nuclei.py domains.txt")
        sys.exit(1)

    domains_file = sys.argv[1]
    normalized_file = normalize_domains(domains_file)
    findings = run_nuclei(normalized_file)
    save_findings(findings)

if __name__ == "__main__":
    main()
