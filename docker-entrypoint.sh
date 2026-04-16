#!/bin/bash

MODE="${BOT_MODE:-auto}"
VNC_PASSWORD="${VNC_PASSWORD:-}"
VNC_WEB_PORT="${VNC_WEB_PORT:-6080}"    # zmien przez env jesli 6080 zajete
VNC_RAW_PORT="${VNC_RAW_PORT:-5900}"    # raw VNC port
DISPLAY_NUM=":1"
export DISPLAY=$DISPLAY_NUM

echo "============================================"
echo " pleaks-bot | mode=$MODE | VNC :$VNC_WEB_PORT"
echo "============================================"

# === 1. Virtual display ===
echo "[VNC] Uruchamiam Xvfb..."
Xvfb $DISPLAY_NUM -screen 0 1280x900x24 -ac +extension GLX +render -noreset &
sleep 2

# === 2. Window manager ===
openbox &
sleep 1

# === 3. VNC server ===
echo "[VNC] Uruchamiam x11vnc na porcie $VNC_RAW_PORT..."
if [ -n "$VNC_PASSWORD" ]; then
    x11vnc -storepasswd "$VNC_PASSWORD" /tmp/vncpass 2>/dev/null
    x11vnc -display $DISPLAY_NUM -forever -rfbauth /tmp/vncpass \
           -rfbport $VNC_RAW_PORT -quiet -noxdamage -shared &
else
    x11vnc -display $DISPLAY_NUM -forever -nopw \
           -rfbport $VNC_RAW_PORT -quiet -noxdamage -shared &
fi
sleep 1

# === 4. noVNC (web) ===
echo "[VNC] Uruchamiam noVNC na porcie $VNC_WEB_PORT..."
websockify --web /usr/share/novnc $VNC_WEB_PORT localhost:$VNC_RAW_PORT &
sleep 1

# === 5. Chromium w VNC ===
echo "[VNC] Otwieram Chromium -> pleaks.st"
chromium \
    --no-sandbox \
    --disable-gpu \
    --disable-features=MediaRouter \
    --display=$DISPLAY_NUM \
    --start-maximized \
    --disable-infobars \
    "https://pleaks.st/" &

sleep 2

echo ""
echo "[*] VNC web:  http://TWOJE_IP:$VNC_WEB_PORT/vnc.html"
echo "[*] VNC raw:  TWOJE_IP:$VNC_RAW_PORT"
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
echo "[*] Kontener aktywny — VNC: http://TWOJE_IP:$VNC_WEB_PORT/vnc.html"
echo ""

tail -f /dev/null
