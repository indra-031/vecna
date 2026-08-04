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
    "internal": 1,                # کاهش وزن به ۱
    "can-i-take-over-xyz": 25,
    "subjack": 20,
    "subover": 20,
    "tkosubs": 15,
    "nuclei": 20,
    "subzy": 25
}

# حداکثر وزن ممکن (برای نرمال‌سازی درصد)
MAX_WEIGHT = sum(ENGINE_WEIGHTS.values())   # = 126

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
                item["severity"] = normalize_severity(item.get("severity"))
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

        # محاسبه امتیاز خام و تبدیل به درصد (0-100)
        raw_score = sum(ENGINE_WEIGHTS.get(e, 0) for e in engines)
        confidence = min(100, round((raw_score / MAX_WEIGHT) * 100)) if MAX_WEIGHT > 0 else 0

        # استفاده از شدت موتورها در صورت وجود، در غیر این صورت بر اساس درصد جدید
        severity = normalize_severity(data["severity"])
        if not severity:
            if confidence >= 80:
                severity = "critical"
            elif confidence >= 50:
                severity = "high"
            elif confidence >= 30:
                severity = "medium"
            elif confidence >= 10:
                severity = "low"
            else:
                severity = "info"

        results.append({
            "domain": domain,
            "services": services,
            "engines": engines,
            "confidence": confidence,
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