#!/usr/bin/env python3
"""
Stawia tunel WireGuard przed uruchomieniem bota (tylko Linux / GitHub Actions).
Uzycie: python setup_vpn.py up | down
"""
import sys, os, subprocess, textwrap

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv()

WG_PRIVATE_KEY = os.getenv("WG_PRIVATE_KEY", "")
WG_PUBLIC_KEY  = os.getenv("WG_PUBLIC_KEY", "")
WG_ADDRESS     = os.getenv("WG_ADDRESS", "10.2.0.2/32")
WG_DNS         = os.getenv("WG_DNS", "10.2.0.1")
WG_ENDPOINT    = os.getenv("WG_ENDPOINT", "")

CONFIG = textwrap.dedent(f"""\
    [Interface]
    PrivateKey = {WG_PRIVATE_KEY}
    Address = {WG_ADDRESS}
    DNS = {WG_DNS}

    [Peer]
    PublicKey = {WG_PUBLIC_KEY}
    Endpoint = {WG_ENDPOINT}
    AllowedIPs = 0.0.0.0/0
    PersistentKeepalive = 25
""")

CONFIG_PATH = "/etc/wireguard/wg0.conf"


def run(cmd: str):
    print(f"  $ {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout.strip():
        print(f"    {result.stdout.strip()}")
    if result.returncode != 0:
        print(f"  [!] ERR: {result.stderr.strip()}")
        sys.exit(1)


def vpn_up():
    if not WG_PRIVATE_KEY or not WG_ENDPOINT or "UZUPELNIJ" in WG_ENDPOINT:
        print("[!] Brak WG_PRIVATE_KEY lub WG_ENDPOINT w .env - pomijam VPN")
        return

    print("[*] Stawiam tunel WireGuard...")
    run("apt-get install -y wireguard-tools iproute2 > /dev/null 2>&1 || true")

    with open(CONFIG_PATH, "w") as f:
        f.write(CONFIG)
    run(f"chmod 600 {CONFIG_PATH}")
    run("wg-quick up wg0")

    # Weryfikacja IP
    result = subprocess.run("curl -s https://api.ipify.org", shell=True, capture_output=True, text=True)
    print(f"[*] Publiczne IP po VPN: {result.stdout.strip()}")


def vpn_down():
    print("[*] Zamykam tunel WireGuard...")
    run("wg-quick down wg0")


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "up"
    if action == "up":
        vpn_up()
    elif action == "down":
        vpn_down()
    else:
        print(f"Uzycie: python setup_vpn.py up | down")
