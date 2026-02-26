#!/usr/bin/env python3

import subprocess
import sys
import shutil
import platform
import os
import urllib.request
import tarfile

NUCLEI_VERSION = "v3.2.4"  


# ---------------------------------------
# Utils
# ---------------------------------------

def run(cmd, check=True):
    print(f"[+] Running: {' '.join(cmd)}")
    return subprocess.run(cmd, check=check)


def command_exists(cmd):
    return shutil.which(cmd) is not None


# ---------------------------------------
# Step 1 – Install Python Requirements
# ---------------------------------------

def install_requirements():
    print("\n[1/4] Installing Python dependencies...")

    if not os.path.exists("requirements.txt"):
        print("[-] requirements.txt not found.")
        sys.exit(1)

    run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])


# ---------------------------------------
# Step 2 – Install Playwright Browsers
# ---------------------------------------

def install_playwright():
    print("\n[2/4] Installing Playwright Chromium...")

    run([sys.executable, "-m", "playwright", "install", "chromium"])


# ---------------------------------------
# Step 3 – Install Nuclei (Linux x64)
# ---------------------------------------

def install_nuclei():
    print("\n[3/4] Checking Nuclei...")

    if command_exists("nuclei"):
        print("[✓] Nuclei already installed.")
        return

    print("[!] Nuclei not found. Installing...")

    system = platform.system().lower()
    arch = platform.machine().lower()

    if system != "linux" or "x86_64" not in arch:
        print("[-] Auto-install currently supports Linux x64 only.")
        print("Install manually from: https://github.com/projectdiscovery/nuclei/releases")
        sys.exit(1)

    url = f"https://github.com/projectdiscovery/nuclei/releases/download/{NUCLEI_VERSION}/nuclei_{NUCLEI_VERSION[1:]}_linux_amd64.zip"
    zip_path = "nuclei.zip"

    print(f"[+] Downloading Nuclei {NUCLEI_VERSION}...")
    urllib.request.urlretrieve(url, zip_path)

    # unzip
    run(["unzip", "-o", zip_path])
    run(["chmod", "+x", "nuclei"])
    run(["sudo", "mv", "nuclei", "/usr/local/bin/"])

    os.remove(zip_path)

    print("[✓] Nuclei installed successfully.")


# ---------------------------------------
# Step 4 – Verify Installation
# ---------------------------------------

def verify():
    print("\n[4/4] Verifying installation...")

    if not command_exists("nuclei"):
        print("[-] Nuclei installation failed.")
        sys.exit(1)

    print("[✓] All dependencies installed successfully.")
    print("\nVecna is ready to hunt 😈")


# ---------------------------------------
# Main
# ---------------------------------------

def main():
    print("=====================================")
    print("        V E C N A  Installer")
    print("=====================================")

    install_requirements()
    install_playwright()
    install_nuclei()
    verify()


if __name__ == "__main__":
    main()