FROM python:3.11-slim

# System deps dla Playwright + WireGuard
RUN apt-get update && apt-get install -y \
    wireguard-tools \
    iproute2 \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python deps
RUN pip install --no-cache-dir \
    playwright \
    pyotp \
    python-dotenv \
    google-genai

# Playwright chromium
RUN playwright install chromium && playwright install-deps chromium

# Kopiuj kod bota
COPY auto_generate_and_post.py .
COPY setup_vpn.py .

# Entrypoint
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
