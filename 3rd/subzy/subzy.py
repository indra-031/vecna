#!/usr/bin/env python3
"""
Vecna - Subzy integration module.
Runs subzy against a list of subdomains and stores vulnerable results as JSON.
"""

import subprocess
import json
import sys
import re
import os
from pathlib import Path

# ------------------------------------------------------------
# Paths – adjust if needed
# ------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parents[2]         # vecna/
FOUND_DIR = ROOT_DIR / "found"
SUBBY_BIN = ROOT_DIR / "3rd" / "subzy" / "subzy"      # local binary first

if not SUBBY_BIN.is_file():
    SUBBY_BIN = "subzy"

SUBBY_CONCURRENCY = 50

ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def strip_ansi(text):
    return ANSI_ESCAPE.sub('', text)

# ------------------------------------------------------------
def run_subzy(target_file: Path) -> list[dict]:
    """
    Execute subzy and parse its stdout for vulnerable/potential subdomains.
    """
    # print(f"[+] Running subzy on {target_file} ...")

    env = os.environ.copy()
    env["NO_COLOR"] = "1"

    cmd = [
        str(SUBBY_BIN), "run",
        "--targets", str(target_file),
        "--concurrency", str(SUBBY_CONCURRENCY),
        "--hide_fails",
    ]

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=env
        )
    except FileNotFoundError:
        print("[-] subzy binary not found. Install it or adjust SUBBY_BIN path.")
        sys.exit(1)

    findings = []
    current = None

    main_pattern = re.compile(
        r"^\[ (?P<flag>VULNERABLE|POTENTIALLY\ VULNERABLE) \]\s+-\s+(?P<domain>\S+)\s+\[\s?(?P<service>[^\]]*?)\s?\]"
    )
    discussion_pattern = re.compile(r"^\[ DISCUSSION \]\s+-\s+(?P<discussion>.+)$")
    documentation_pattern = re.compile(r"^\[ DOCUMENTATION \]\s+-\s+(?P<documentation>.*)$")
    separator_pattern = re.compile(r"^\-{5,}$")

    for line in proc.stdout:
        line = strip_ansi(line.strip())
        if not line:
            continue

        if separator_pattern.match(line):
            if current:
                findings.append(current)
                current = None
            continue

        main_match = main_pattern.match(line)
        if main_match:
            if current:
                findings.append(current)

            flag = main_match.group("flag")
            domain = main_match.group("domain")
            service = main_match.group("service").strip()
            status = "vulnerable" if flag == "VULNERABLE" else "potential"

            current = {
                "engine": "subzy",
                "domain": domain,
                "service": service if service else "unknown",
                "status": status,
                "description": f"{flag} to takeover ({service})" if service else f"{flag} to takeover",
                "discussion": None,
                "documentation": None,
                "type": "takeover"
            }
            continue

        if current:
            disc_match = discussion_pattern.match(line)
            if disc_match:
                current["discussion"] = disc_match.group("discussion").strip()
                continue

            doc_match = documentation_pattern.match(line)
            if doc_match:
                doc = doc_match.group("documentation").strip()
                current["documentation"] = doc if doc else None
                continue

    if current:
        findings.append(current)

    stderr_output = proc.stderr.read()
    proc.wait()
    if stderr_output:
        print(f"[!] subzy stderr:\n{stderr_output}")

    return findings

# ------------------------------------------------------------
def save_findings(findings: list[dict]) -> None:
    """Store findings silently and print Vecna-compatible summary."""
    FOUND_DIR.mkdir(parents=True, exist_ok=True)
    output_file = FOUND_DIR / "subzy.json"

    if not findings:
        print("[-] No takeover findings from subzy.")
        return

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(findings, f, indent=4, ensure_ascii=False)

    print(f"[+] Found {len(findings)} vulnerable target(s) via Subzy.")

# ------------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print("Usage: python3 subzy.py domains.txt")
        sys.exit(1)

    target_file = Path(sys.argv[1])
    if not target_file.is_file():
        print(f"[-] File not found: {target_file}")
        sys.exit(1)

    findings = run_subzy(target_file)
    save_findings(findings)

if __name__ == "__main__":
    main()