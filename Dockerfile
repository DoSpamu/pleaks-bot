FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    # WireGuard
    wireguard-tools \
    iproute2 \
    curl \
    procps \
    # VNC stack
    xvfb \
    x11vnc \
    openbox \
    obconf \
    # noVNC (web client + websockify proxy)
    novnc \
    websockify \
    # System Chromium do reczmej sesji w VNC
    chromium \
    fonts-liberation \
    # Misc
    xterm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir \
    patchright \
    pyotp \
    python-dotenv \
    google-genai

# Patchright chromium (dla bota — patched CDP)
RUN patchright install chromium && patchright install-deps chromium

COPY auto_generate_and_post.py .
COPY setup_vpn.py .
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 6080 = noVNC web, 5900 = raw VNC
EXPOSE 6080 5900

ENTRYPOINT ["/entrypoint.sh"]
