#!/usr/bin/env python3

import os
import json
from collections import defaultdict

# =========================================================
# Paths
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))

FOUND_DIR = os.path.join(ROOT_DIR, "found")
OUTPUT_FILE = os.path.join(FOUND_DIR, "final.json")

# =========================================================
# Engine Weights
# =========================================================

ENGINE_WEIGHTS = {
    "internal": 15,
    "can-i-take-over-xyz": 25,
    "subjack": 20,
    "subover": 20,
    "tkosubs": 15,
    "nuclei": 20
}

SEVERITY_ORDER = ["info", "low", "medium", "high", "critical"]

# =========================================================
# Severity
# =========================================================

def normalize_severity(sev):
    if not sev:
        return None

    sev = str(sev).lower().strip()

    if sev not in SEVERITY_ORDER:
        return "info"

    return sev

# =========================================================
# Utils
# =========================================================

def normalize_service(service):
    if not service:
        return None
    return service.lower().replace(" ", "").replace("-", "")

def load_all_findings():
    findings = []

    if not os.path.exists(FOUND_DIR):
        return findings

    for file in os.listdir(FOUND_DIR):

        if not file.endswith(".json"):
            continue

        if file == "final.json":
            continue

        path = os.path.join(FOUND_DIR, file)

        try:
            with open(path, "r") as f:
                data = json.load(f)

            if not isinstance(data, list):
                continue

            engine_name = file.replace(".json", "")

            for item in data:

                if not item.get("engine"):
                    item["engine"] = engine_name

                item["severity"] = normalize_severity(
                    item.get("severity")
                )

                findings.append(item)

        except Exception:
            continue

    return findings

def merge_severity(current, new):

    current = normalize_severity(current)
    new = normalize_severity(new)

    if not current:
        return new

    if not new:
        return current

    if SEVERITY_ORDER.index(new) > SEVERITY_ORDER.index(current):
        return new

    return current

# =========================================================
# Correlation Engine
# =========================================================

def correlate(findings):

    grouped = defaultdict(lambda: {
        "services": set(),
        "engines": set(),
        "severity": None,
        "discussions": set()
    })

    for item in findings:

        domain = item.get("domain")
        engine = item.get("engine")
        service = normalize_service(item.get("service"))
        severity = item.get("severity")
        discussion = item.get("discussion")

        if not domain:
            continue

        if engine:
            grouped[domain]["engines"].add(engine)

        if service:
            grouped[domain]["services"].add(service)

        else:
            if engine == "nuclei":
                nuclei_name = item.get("name")
                if nuclei_name:
                    grouped[domain]["services"].add(nuclei_name)

        if discussion:
            if isinstance(discussion, list):
                for d in discussion:
                    grouped[domain]["discussions"].add(d)
            else:
                grouped[domain]["discussions"].add(discussion)

        grouped[domain]["severity"] = merge_severity(
            grouped[domain]["severity"],
            severity
        )

    results = []

    for domain, data in grouped.items():

        engines = sorted(list(data["engines"]))
        services = sorted(list(data["services"]))
        discussions = sorted(list(data["discussions"]))

        score = sum(ENGINE_WEIGHTS.get(e, 0) for e in engines)

        severity = normalize_severity(data["severity"])

        if not severity:
            if score >= 90:
                severity = "critical"
            elif score >= 70:
                severity = "high"
            elif score >= 40:
                severity = "medium"
            elif score >= 20:
                severity = "low"
            else:
                severity = "info"

        results.append({
            "domain": domain,
            "services": services,
            "engines": engines,
            "confidence": score,
            "severity": severity,
            "discussion": discussions if discussions else None
        })

    results.sort(
        key=lambda x: SEVERITY_ORDER.index(x["severity"]),
        reverse=True
    )

    return results

# =========================================================
# Main
# =========================================================

def main():

    findings = load_all_findings()

    if not findings:
        print("[-] No findings to correlate.")
        return

    final_results = correlate(findings)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(final_results, f, indent=4)

    print(f"[+] {len(final_results)} unique vulnerable domain(s) found.")

# =========================================================

if __name__ == "__main__":
    main()