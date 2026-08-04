# 🕷️ V E C N A

> Automated Subdomain Takeover Detection Framework  
> Fast. Clean. Tactical. ☠️

---

## 🔥 What is Vecna?

**Vecna** is an automation framework for detecting **Subdomain Takeovers** at scale.

It performs:

- 🧠 DNS Intelligence
- 🌐 HTTP Fingerprinting (async & optimized)
- 🔎 Internal Signature Matching
- 🛰 Third-Party Fingerprint Detection
- 💣 Nuclei Takeover Scanning
- 📸 Automated Evidence Collection (Screenshot + Raw HTTP + DNS)
- 📦 Organized PoC Packaging

Designed for bug bounty hunters, red teamers, and automation freaks.

---

# ⚙️ Installation

Clone the repository:

```bash
git clone https://github.com/indra-031/vecna.git
```

Go to install directory:

```bash
cd vecna/install
```

Run the installer:

```bash
python3 install.py
```

The installer will:

- Install required Python dependencies
- Install Go
- Install Subzy
- Install Playwright + Chromium
- Install Nuclei (if not already installed)
- Verify everything is ready

When done, Vecna is ready to hunt 😈

---

# 📢 Telegram Configuration (Optional but Recommended)

If you want real-time alerts when a takeover is detected, configure Telegram manually.

Go to:

```
configs/telegram-settings.json
```

Edit the file and replace the placeholder values:

```json
{
  "TELEGRAM_TOKEN": "YOUR_BOT_TOKEN",
  "TELEGRAM_CHAT_ID": "YOUR_CHAT_ID",
  "TELEGRAM_TOPIC_ID": "YOUR_TOPIC_ID",
  "TELEGRAM_ENABLED": true
}
```

## Required Steps:

1. Create a Telegram bot using `@BotFather`
2. Get your bot token
3. Get your chat ID (private chat or group)
4. Get topic ID if using Telegram forum groups
5. Set:

```json
"TELEGRAM_ENABLED": true
```

If you don't want Telegram alerts:

```json
"TELEGRAM_ENABLED": false
```

---

# 🚀 Usage

Vecna is a single-command pipeline that scans subdomains for takeover vulnerabilities.

Just point it at a target file (or a single domain) and it will handle the rest.

---

## 🔧 Prerequisites

Before running Vecna, make sure you have:

- **Go**  
  Required for `nuclei` and `subzy` if not already installed.  
  The included `install.py` can install it automatically.

- **Python 3.8+**  
  Required Python packages are installed automatically.

- **Nuclei + Takeover Templates**  
  Automatically installed if missing.

- **Subzy**  
  Automatically installed if missing.

---

# 🎯 Basic Usage

## 1. Scan a list of domains

```bash
bash vecna.sh domains.txt
```

Example:

```text
test1.example.com
test2.example.com
test3.example.com
admin.internal.lab
```

---

## 2. Scan a single domain

```bash
bash vecna.sh example.com
```

---

⚠️ **Important:**

The input must be bare domain names.

Do not include:

```
http://
https://
paths
parameters
```

Correct:

```
sub.example.com ✅
```

Wrong:

```
https://sub.example.com ❌
https://example.com/login ❌
```

---

# 📄 Domain File Format

`domains.txt`

Example:

```text
test1.example.com
test2.example.com
test3.example.com
admin.internal.lab
api.example.com
```

Simply provide:

```
one domain per line
```

---

# ⚙️ What Happens Behind the Scenes

Vecna automatically runs the following pipeline:

## 1. DNS Intelligence

Collects:

- A records
- AAAA records
- CNAME records
- MX records
- NS records
- DNS resolution status

---

## 2. HTTP Fingerprinting

The async HTTP engine:

- Detects live services
- Captures response headers
- Extracts fingerprints
- Checks HTTP behavior

---

## 3. Can-I-Take-Over-XYZ Detection

Matches discovered fingerprints against known vulnerable third-party services.

---

## 4. SubJack Detection

Runs additional takeover fingerprint checks.

---

## 5. SubOver Detection

Performs another takeover detection layer.

---

## 6. Tko-Subs Analysis

Checks for:

- Dangling DNS records
- Expired resources
- Unclaimed services

---

## 7. Subzy Scanner

Runs modern Go-based takeover detection.

---

## 8. Nuclei Takeover Templates

Executes dedicated takeover templates from Nuclei.

---

## 9. Correlation & Reporting

Vecna merges all findings:

- Removes duplicates
- Correlates results
- Calculates confidence
- Assigns severity

---

## 10. Evidence Collection

Automatically collects:

- Screenshots
- Raw HTTP responses
- DNS information

---

## 11. Telegram Alerting

If enabled, sends detailed vulnerability notifications.

---

## 12. Archiving & Cleanup

Stores complete results inside:

```
logs/<run_number>/
```

---

# 📦 Output Structure

Vecna generates:

```
output/
 ├── dns-output.json
 └── http-output.json
```

Detection engine results:

```
found/
 ├── nuclei.json
 ├── subzy.json
 ├── subjack.json
 ├── subover.json
 └── tko-subs.json
```

Final correlated report:

```
found/final.json
```

PoC evidence:

```
poc/
 └── target.domain/
      ├── dns.json
      ├── http.json
      ├── raw_http.txt
      ├── screenshot.png
      └── report.json
```

Complete execution logs:

```
logs/
 └── <run_number>/
```

---

# 🤖 Telegram Integration

Enable instant notifications by editing:

```
configs/telegram-settings.json
```

Vecna sends detailed alerts containing:

- Domain
- Detected service
- Severity
- Confidence score
- Detection engines
- Discussion links (if available)
- Screenshot evidence

---

# 📊 Confidence & Severity System

Vecna calculates confidence from:

```
0 - 100%
```

Severity levels:

```
0-9%     → Info
10-29%   → Low
30-49%   → Medium
50-79%   → High
80-100%  → Critical
```

---

# 🧠 What Makes Vecna Different?

- ⚡ Fully optimized async HTTP engine
- 🧹 NXDOMAIN-safe screenshot logic
- 🎯 Reduced false positives
- 📦 Clean PoC packaging
- 🔥 Minimal noise output
- 🧬 Modular architecture
- 🛰 Multi-engine correlation
- 📸 Automatic evidence generation

---

# 🛠️ First-Time Setup

Run:

```bash
cd install
python3 install.py
```

The installer automatically handles:

- Python dependencies
- Playwright browsers
- Chromium
- Go installation
- Nuclei installation
- Subzy installation

---

# 📌 Notes

For best results:

- Use only authorized targets.
- Provide only subdomains.
- CNAME-based subdomains usually provide the highest takeover detection accuracy.
- Third-party tools use conservative rate limits to avoid unnecessary traffic.
- Results should always be manually verified before reporting.

---

# ⚠️ Legal Disclaimer

This tool is for educational and authorized security testing purposes only.

You are responsible for your actions.

Only scan assets you own or have explicit permission to test.

---

# 👁️‍🗨️ Final Words

Vecna doesn't scan.

Vecna hunts. 🕷️

Stay sharp.  
Stay stealthy.  

Happy hacking. 🖤
