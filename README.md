# pleaks-bot

Automatyzacja aktywności na forum [pleaks.st](https://pleaks.st) (XenForo 2.x).

Bot scrapuje świeże wątki, generuje naturalne odpowiedzi przez Gemini AI i postuje z losowymi przerwami — wszystko przez WireGuard VPN. Po robocie kontener zostaje żywy z przeglądarką dostępną przez VNC, żeby można było korzystać z forum ręcznie przez ten sam VPN.

---

## Jak to działa

1. Łączy się z ProtonVPN przez WireGuard
2. Loguje się na konto forum (auto-TOTP jeśli podany seed)
3. Scrapuje świeże wątki z 6 działów (SI, Pieniądze, Darmowe)
4. Dla każdego wątku czyta posty innych → wysyła do Gemini → generuje naturalną odpowiedź
5. Postuje z losowymi przerwami 60–300s między postami
6. Po każdym poście wysyła powiadomienie na Discord
7. Kontener zostaje żywy — możesz przeglądać forum przez VNC (przez VPN)

---

## Uruchomienie przez Portainer

**Wymagania na serwerze (sprawdź raz przed pierwszym uruchomieniem):**
```bash
sudo modprobe wireguard
ls /dev/net/tun   # musi istnieć
```

**Portainer → Stacks → Add Stack → Web editor**, wklej poniższy compose, podmień dane i kliknij Deploy.  
Portainer sam sklonuje repo z GitHub i zbuduje obraz — nie trzeba nic instalować ręcznie.

```yaml
services:
  pleaks-bot:
    build:
      context: https://github.com/DoSpamu/pleaks-bot.git
    container_name: pleaks-bot
    restart: "no"   # nie restartuj automatycznie po zakończeniu bota

    # WireGuard wymaga uprawnień sieciowych
    cap_add:
      - NET_ADMIN
      - SYS_MODULE
    devices:
      - /dev/net/tun:/dev/net/tun

    ports:
      - "6080:6080"   # noVNC — otwórz http://IP_SERWERA:6080/vnc.html
      - "5900:5900"   # raw VNC (opcjonalnie, do klienta VNC typu RealVNC)

    environment:
      # --- tryb pracy ---
      BOT_MODE: auto        # auto | preview (podgląd bez postowania) | manual (tylko VNC)
      POSTS_TARGET: "2"     # ile postów na run — 2 na warmup nowego konta, potem 7

      # --- VNC ---
      VNC_PASSWORD: "zmien_na_swoje"   # hasło do przeglądarki VNC

      # --- konto forum ---
      PLEAKS_EMAIL: twoj@email.com
      PLEAKS_HASLO: TwojeHaslo123!
      PLEAKS_TOTP_SECRET: ""   # seed z aplikacji 2FA (nie kod 6-cyfrowy — seed to długi ciąg znaków)

      # --- Gemini API (free tier) ---
      GEMINI_API_KEY: twoj_klucz_z_aistudio.google.com

      # --- Discord webhook (opcjonalnie — powiadomienia po każdym poście) ---
      DISCORD_WEBHOOK_URL: https://discord.com/api/webhooks/...

      # --- WireGuard / ProtonVPN (skopiuj z pliku .conf pobranego z ProtonVPN) ---
      WG_PRIVATE_KEY: "klucz_z_pliku_conf"
      WG_PUBLIC_KEY:  "klucz_z_pliku_conf"
      WG_ADDRESS:     "10.2.0.2/32"
      WG_DNS:         "10.2.0.1"
      WG_ENDPOINT:    "IP_SERWERA:51820"

    volumes:
      - pleaks-data:/app   # cookies, historia postów — persystuje między uruchomieniami

volumes:
  pleaks-data:
```

**Po uruchomieniu kontener:**
- stawia VPN
- odpala bota (jeśli `BOT_MODE != manual`)
- otwiera Chromium w VNC z pleaks.st
- zostaje żywy — VNC dostępne pod `http://IP_SERWERA:6080/vnc.html`

---

## Tryby pracy

| `BOT_MODE` | Co robi |
|---|---|
| `auto` | Postuje bez pytania, powiadamia Discord |
| `preview` | Scrapuje i generuje posty, ale nie wysyła — do testów |
| `manual` | Tylko VNC, bot nie startuje — do ręcznego przeglądania forum przez VPN |

---

## Zmienne środowiskowe

| Zmienna | Opis |
|---|---|
| `POSTS_TARGET` | Ile postów na run (domyślnie `7`, ustaw `2` na warmup nowego konta) |
| `VNC_PASSWORD` | Hasło do VNC — zostaw puste jeśli nie chcesz hasła |
| `PLEAKS_EMAIL` | Email konta forum |
| `PLEAKS_HASLO` | Hasło konta forum |
| `PLEAKS_TOTP_SECRET` | Seed 2FA z aplikacji authenticator (nie kod 6-cyfrowy!) |
| `GEMINI_API_KEY` | Klucz Gemini API — free tier, model: `gemini-2.5-flash-lite` |
| `DISCORD_WEBHOOK_URL` | Webhook do powiadomień po każdym poście (opcjonalnie) |
| `WG_PRIVATE_KEY` | Z sekcji `[Interface]` pliku .conf ProtonVPN |
| `WG_PUBLIC_KEY` | Z sekcji `[Peer]` pliku .conf ProtonVPN |
| `WG_ADDRESS` | Adres IP tunelu, np. `10.2.0.2/32` |
| `WG_DNS` | DNS przez VPN, np. `10.2.0.1` |
| `WG_ENDPOINT` | Serwer VPN `IP:port`, np. `79.127.186.163:51820` |

---

## Procedura nowego konta (żeby uniknąć bana)

1. Uruchom kontener z `BOT_MODE=manual`
2. Wejdź na `http://IP:6080/vnc.html`
3. W Chromium w VNC zarejestruj nowe konto na pleaks.st — **jesteś przez VPN, IP jest czyste**
4. Przy rejestracji ustaw 2FA w aplikacji authenticator, **zapisz seed** (długi ciąg znaków) do `PLEAKS_TOTP_SECRET`
5. Ustaw `POSTS_TARGET=2` na pierwsze kilka runów (warmup — nowe konto nie może od razu pisać 7 postów)
6. Po tygodniu bez bana zwiększ `POSTS_TARGET` do `7`

---

## Skrypty

### `auto_generate_and_post.py` — główny bot

```bash
python auto_generate_and_post.py --auto     # postuje bez pytania
python auto_generate_and_post.py --preview  # podgląd, nie postuje
```

### `login_and_scrape.py` — ręczne odświeżenie sesji

Gdy sesja wygasła (po ~30 dniach) i nie masz TOTP seed:
```bash
python login_and_scrape.py 123456   # podaj aktualny kod z aplikacji
```

---

## Gdzie bot postuje

| Sekcja | Dział |
|---|---|
| Sztuczna Inteligencja | Aktualności i dyskusje, Automatyzacje |
| Pieniądze | Kryptowaluty, Dyskusje |
| Darmowe | Konta premium, Kursy |

---

## Pliki danych (w .gitignore — nie idą do repo)

| Plik | Opis |
|---|---|
| `.env` | Dane logowania i klucze API |
| `session_cookies.json` | Sesja forum (~30 dni ważności) |
| `posted_urls.json` | Historia odpisanych wątków — bot nie odpisuje dwa razy |
| `autopost_results.json` | Wyniki ostatniego runu |

---

## GitHub Actions

Cron wyłączony — bot odpala się tylko ręcznie przez Actions → Run workflow.  
Żeby włączyć harmonogram, odkomentuj w `.github/workflows/autopost.yml`:

```yaml
# schedule:
#   - cron: '23 11 */12 * *'
```
