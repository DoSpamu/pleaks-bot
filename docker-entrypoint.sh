#!/bin/bash

MODE="${BOT_MODE:-auto}"
VNC_PASSWORD="${VNC_PASSWORD:-}"
DISPLAY_NUM=":1"
export DISPLAY=$DISPLAY_NUM

echo "============================================"
echo " pleaks-bot | mode=$MODE | VNC :6080"
echo "============================================"

# === 1. Virtual display ===
echo "[VNC] Uruchamiam Xvfb..."
Xvfb $DISPLAY_NUM -screen 0 1280x900x24 -ac +extension GLX +render -noreset &
sleep 2

# === 2. Window manager ===
openbox &
sleep 1

# === 3. VNC server ===
echo "[VNC] Uruchamiam x11vnc..."
if [ -n "$VNC_PASSWORD" ]; then
    x11vnc -storepasswd "$VNC_PASSWORD" /tmp/vncpass 2>/dev/null
    x11vnc -display $DISPLAY_NUM -forever -rfbauth /tmp/vncpass \
           -rfbport 5900 -quiet -noxdamage -shared &
else
    echo "[VNC] Brak VNC_PASSWORD — brak hasla (ustaw env VNC_PASSWORD)"
    x11vnc -display $DISPLAY_NUM -forever -nopw \
           -rfbport 5900 -quiet -noxdamage -shared &
fi
sleep 1

# === 4. noVNC (web) ===
echo "[VNC] Uruchamiam noVNC na porcie 6080..."
websockify --web /usr/share/novnc 6080 localhost:5900 &
sleep 1

# === 5. Chromium w VNC ===
echo "[VNC] Otwieram Chromium -> pleaks.st"
chromium \
    --no-sandbox \
    --disable-gpu \
    --display=$DISPLAY_NUM \
    --start-maximized \
    --disable-infobars \
    "https://pleaks.st/" &

sleep 2

echo ""
echo "[*] VNC dostepne: http://TWOJE_IP:6080/vnc.html"
echo "[*] Lub klient VNC: TWOJE_IP:5900"
echo ""

# === 6. VPN ===
echo "[*] Stawiam WireGuard..."
python setup_vpn.py up || echo "[!] VPN pominiety (brak kluczy lub nie-Linux)"

# === 7. Bot ===
if [ "$MODE" = "manual" ]; then
    echo "[*] Tryb manual — bot nie uruchomiony, VNC gotowe"
elif [ "$MODE" = "preview" ]; then
    echo "[*] Uruchamiam bota (preview)..."
    python auto_generate_and_post.py --preview
    echo "[*] Preview gotowy. VNC nadal dziala."
else
    echo "[*] Uruchamiam bota (auto)..."
    python auto_generate_and_post.py --auto
    echo "[*] Bot zakonczony. VNC nadal dziala."
fi

echo ""
echo "[*] Kontener aktywny — uzyj VNC zeby przegladac forum przez VPN"
echo "[*] http://TWOJE_IP:6080/vnc.html"
echo ""

# Trzymaj kontener przy zyciu
tail -f /dev/null
