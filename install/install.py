#!/usr/bin/env python3

import subprocess
import sys
import shutil
import os
import platform
import urllib.request
import tempfile

# ---------------------------------------
# Versions
# ---------------------------------------

GO_VERSION = "1.22.5"          # stable Go version (change if needed)
NUCLEI_MODULE = "github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest"
SUBZY_MODULE  = "github.com/PentestPad/subzy@latest"

# ---------------------------------------
# Utils
# ---------------------------------------

def run(cmd, check=True, env=None, capture_output=False):
    print(f"[+] Running: {' '.join(cmd)}")
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    if capture_output:
        return subprocess.run(cmd, check=check, env=merged_env,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return subprocess.run(cmd, check=check, env=merged_env)


def command_exists(cmd):
    return shutil.which(cmd) is not None


# ---------------------------------------
# Install Go if missing (Linux amd64)
# ---------------------------------------

def install_go():
    print("\n[3/6] Checking Go installation...")

    # 1. go already in PATH
    if command_exists("go"):
        print("[✓] Go is already installed and in PATH.")
        return

    # 2. check typical location /usr/local/go/bin/go
    go_default_bin = "/usr/local/go/bin/go"
    if os.path.isfile(go_default_bin):
        print("[✓] Go found at /usr/local/go, adding to PATH for this session.")
        os.environ["PATH"] = f"/usr/local/go/bin:{os.environ.get('PATH', '')}"
        # Also ensure GOPATH
        gopath = os.path.expanduser("~/go")
        os.environ["GOPATH"] = gopath
        os.makedirs(os.path.join(gopath, "bin"), exist_ok=True)
        os.environ["PATH"] = f"{os.path.join(gopath, 'bin')}:{os.environ['PATH']}"
        return

    # 3. Not found -> install
    print("[!] Go not found. Installing Go automatically...")
    system = platform.system().lower()
    arch = platform.machine().lower()

    if system != "linux" or arch not in ("x86_64", "amd64"):
        print("[-] Auto Go install only supports Linux x86_64.")
        print("    Please install Go manually from https://go.dev/dl/")
        sys.exit(1)

    url = f"https://go.dev/dl/go{GO_VERSION}.linux-amd64.tar.gz"
    tmpdir = tempfile.mkdtemp()
    archive_path = os.path.join(tmpdir, "go.tar.gz")

    print(f"[+] Downloading Go {GO_VERSION}...")
    urllib.request.urlretrieve(url, archive_path)

    # Extract directly to /usr/local (no deletion of existing)
    run(["sudo", "tar", "-C", "/usr/local", "-xzf", archive_path])

    # Add go binary to PATH for this session
    go_bin_path = "/usr/local/go/bin"
    os.environ["PATH"] = f"{go_bin_path}:{os.environ.get('PATH', '')}"

    # Set GOPATH
    gopath = os.path.expanduser("~/go")
    os.environ["GOPATH"] = gopath
    os.makedirs(os.path.join(gopath, "bin"), exist_ok=True)
    os.environ["PATH"] = f"{os.path.join(gopath, 'bin')}:{os.environ['PATH']}"

    # Clean up
    shutil.rmtree(tmpdir)
    print("[✓] Go installation complete.")


# ---------------------------------------
# Step 1 – Install Python Requirements
# ---------------------------------------

def install_requirements():
    print("\n[1/6] Installing Python dependencies...")

    if not os.path.exists("requirements.txt"):
        print("[-] requirements.txt not found.")
        sys.exit(1)

    run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])


# ---------------------------------------
# Step 2 – Install Playwright Browsers
# ---------------------------------------

def install_playwright():
    print("\n[2/6] Installing Playwright Chromium...")

    run([sys.executable, "-m", "playwright", "install", "chromium"])


# ---------------------------------------
# Step 3 – Install Go (if missing)
# (already defined above, will be called in main)
# ---------------------------------------


# ---------------------------------------
# Step 4 – Install Nuclei via go install
# ---------------------------------------

def install_nuclei():
    print("\n[4/6] Installing Nuclei (go install)...")

    run(["go", "install", "-v", NUCLEI_MODULE])

    # Ensure binary is accessible
    gopath = os.environ.get("GOPATH", os.path.expanduser("~/go"))
    bin_path = os.path.join(gopath, "bin", "nuclei")

    if not command_exists("nuclei"):
        if os.path.isfile(bin_path):
            print("[+] Moving nuclei to /usr/local/bin")
            run(["sudo", "mv", bin_path, "/usr/local/bin/nuclei"])
        else:
            print("[-] nuclei not found after go install.")
            sys.exit(1)
    else:
        print("[✓] Nuclei installed successfully.")


# ---------------------------------------
# Step 5 – Install Subzy via go install
# ---------------------------------------

def install_subzy():
    print("\n[5/6] Installing Subzy (go install)...")

    run(["go", "install", "-v", SUBZY_MODULE])

    gopath = os.environ.get("GOPATH", os.path.expanduser("~/go"))
    bin_path = os.path.join(gopath, "bin", "subzy")

    if not command_exists("subzy"):
        if os.path.isfile(bin_path):
            print("[+] Moving subzy to /usr/local/bin")
            run(["sudo", "mv", bin_path, "/usr/local/bin/subzy"])
        else:
            print("[-] subzy not found after go install.")
            sys.exit(1)
    else:
        print("[✓] Subzy installed successfully.")


# ---------------------------------------
# Step 6 – Verify Installation
# ---------------------------------------

def verify():
    print("\n[6/6] Verifying installation...")

    if not command_exists("nuclei"):
        print("[-] Nuclei installation failed.")
        sys.exit(1)

    if not command_exists("subzy"):
        print("[-] Subzy installation failed.")
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

    # Sequence
    install_requirements()      # 1
    install_playwright()        # 2
    install_go()                # 3  <-- safe Go handling
    install_nuclei()            # 4
    install_subzy()             # 5
    verify()                    # 6


if __name__ == "__main__":
    main()