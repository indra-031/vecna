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
# Engine Weights (total = 100 with internal=5, others sum=95)
# =========================================================

ENGINE_WEIGHTS = {
    "internal": 5,
    "can-i-take-over-xyz": 20,
    "subjack": 15,
    "subover": 15,
    "tkosubs": 10,
    "nuclei": 15,
    "subzy": 20
}

MAX_WEIGHT = 100   # حداکثر وزن ممکن = مجموع کل وزن‌ها

SEVERITY_ORDER = ["info", "low", "medium", "high", "critical"]

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
        if not file.endswith(".json") or file == "final.json":
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
                findings.append(item)
        except Exception:
            continue
    return findings

def confidence_to_severity(confidence):
    """تبدیل درصد اطمینان به severity"""
    if confidence >= 80:
        return "critical"
    elif confidence >= 50:
        return "high"
    elif confidence >= 30:
        return "medium"
    elif confidence >= 10:
        return "low"
    else:
        return "info"

# =========================================================
# Correlation Engine
# =========================================================

def correlate(findings):
    grouped = defaultdict(lambda: {
        "services": set(),
        "engines": set(),
        "discussions": set()
    })

    for item in findings:
        domain = item.get("domain")
        engine = item.get("engine")
        service = normalize_service(item.get("service"))
        discussion = item.get("discussion")

        if not domain:
            continue

        if engine:
            grouped[domain]["engines"].add(engine)

        if service:
            grouped[domain]["services"].add(service)
        else:
            # برای nuclei از name به‌عنوان سرویس استفاده کن (اگر service نبود)
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

    results = []
    for domain, data in grouped.items():
        engines = sorted(list(data["engines"]))
        services = sorted(list(data["services"]))
        discussions = sorted(list(data["discussions"]))

        # محاسبه confidence به صورت جمع وزن‌ها (حداکثر 100)
        score = sum(ENGINE_WEIGHTS.get(e, 0) for e in engines)
        confidence = min(100, score)   # چون مجموع وزن‌ها دقیقاً ۱۰۰ است

        # severity کاملاً بر اساس confidence
        severity = confidence_to_severity(confidence)

        results.append({
            "domain": domain,
            "services": services,
            "engines": engines,
            "confidence": confidence,
            "severity": severity,
            "discussion": discussions if discussions else None
        })

    results.sort(key=lambda x: SEVERITY_ORDER.index(x["severity"]), reverse=True)
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

if __name__ == "__main__":
    main()
