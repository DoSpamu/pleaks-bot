#!/bin/bash
set -e

MODE="${BOT_MODE:-auto}"

echo "[*] Stawiam WireGuard..."
python setup_vpn.py up || echo "[!] VPN skip (brak kluczy lub nie-Linux)"

echo "[*] Startuje bota (mode: $MODE)..."
if [ "$MODE" = "preview" ]; then
    python auto_generate_and_post.py --preview
else
    python auto_generate_and_post.py --auto
fi

echo "[*] Zamykam VPN..."
python setup_vpn.py down || true
