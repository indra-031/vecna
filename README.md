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
- 🛰 Third‑Party Fingerprint Detection
- 💣 Nuclei Takeover Scanning
- 📸 Automated Evidence Collection (Screenshot + Raw HTTP + DNS)
- 📦 Organized PoC Packaging

Designed for bug bounty hunters, red teamers, and automation freaks.

---

## ⚙️ Installation

Clone the repository:
```
git clone https://github.com/indra-031/vecna.git
```
Go to install directory:
```
cd vecna/install
```
Run the installer:
```
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

## 📢 Telegram Configuration (Optional but Recommended)

If you want real‑time alerts when a takeover is detected, you must configure Telegram manually.

Go to:

configs/telegram-settings.json

Edit the file and replace the placeholder values:
```
{
  "TELEGRAM_TOKEN": "YOUR_BOT_TOKEN",
  "TELEGRAM_CHAT_ID": "YOUR_CHAT_ID",
  "TELEGRAM_TOPIC_ID": "YOUR_TOPIC_ID",
  "TELEGRAM_ENABLED": true
}
```
### Required Steps:

1. Create a Telegram bot using @BotFather
2. Get your bot token
3. Get your chat ID (private chat or group)
4. (Optional) Get topic ID if using forum groups
5. Set "TELEGRAM_ENABLED": true

If you don’t want Telegram alerts, simply set:

"TELEGRAM_ENABLED": false

---

## 🚀 Usage

Run Vecna against a file of domains:
```
bash vecna.sh domains.txt
```
domains.txt example:
```
test1.example.com
test2.example.com
test3.example.com
test4.test.example.com
...
```
without https:// or http:// or path (just subdomain+doamin+tld)

Run Vecna against a single target:
```
bash vecna.sh test.target.com
```
---

## 📂 Output Structure

Vecna generates:
```
output/
 ├── dns-output.json
 ├── http-output.json
```
```
found/
 ├── nuclei.json
 ├── subzy.json
 ├── subjack.json
```
```
poc/
 ├── target.domain/
 │    ├── dns.json
 │    ├── http.json
 │    ├── raw_http.txt
 │    ├── screenshot.png
 │    └── report.json
```
Everything you need for a clean bug bounty report.

---

## 🧠 What Makes Vecna Different?

- ⚡ Fully optimized async HTTP engine
- 🧹 NXDOMAIN-safe screenshot logic
- 🎯 Reduced false positives
- 📦 Clean PoC packaging
- 🔥 Minimal noise output
- 🧬 Modular architecture

---

## ⚠️ Legal Disclaimer

This tool is for educational and authorized security testing purposes only.

You are responsible for your actions.

---

## 👁️‍🗨️ Final Words

Vecna doesn’t scan.

Vecna hunts. 🕷️

Stay sharp.
Stay stealthy.
Happy hacking. 🖤
