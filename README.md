# pleaks-bot

Automatyzacja aktywności na forum [pleaks.st](https://pleaks.st) (XenForo 2.x) — logowanie z TOTP 2FA, dynamiczne scrapowanie wątków, generowanie odpowiedzi przez Gemini AI, postowanie z randomizowanym timingiem. Działa przez WireGuard VPN. Przeglądarka dostępna przez VNC w przeglądarce.

---

## Jak to działa

1. Bot łączy się z ProtonVPN przez WireGuard
2. Loguje się na forum (z auto-TOTP jeśli podany seed)
3. Scrapuje świeże wątki z działów: Sztuczna Inteligencja, Pieniądze, Darmowe
4. Dla każdego wątku czyta treść i wysyła do Gemini API → generuje naturalną odpowiedź
5. Postuje odpowiedzi z losowymi przerwami (60–300s)
6. Kontener zostaje żywy — możesz przeglądać forum przez VNC (przez VPN)

---

## Uruchomienie przez Portainer

**Wymagania na serwerze:**
```bash
sudo modprobe wireguard
ls /dev/net/tun   # musi istnieć
```

**Portainer → Stacks → Add Stack → Web editor**, wklej zawartość `docker-compose.portainer.yml`, kliknij Deploy.

Portainer automatycznie sklonuje repo i zbuduje obraz.

**VNC** (po uruchomieniu kontenera):
```
http://IP_SERWERA:6080/vnc.html
hasło: pleaks123  (lub to co ustawiłeś w VNC_PASSWORD)
```

---

## Zmienne środowiskowe

| Zmienna | Opis |
|---|---|
| `BOT_MODE` | `auto` — postuje bez pytania · `preview` — podgląd bez postowania · `manual` — tylko VNC |
| `POSTS_TARGET` | Ile postów na run (domyślnie `7`, ustaw `2` na warmup nowego konta) |
| `VNC_PASSWORD` | Hasło do VNC (zostaw puste = brak hasła) |
| `PLEAKS_EMAIL` | Email konta forum |
| `PLEAKS_HASLO` | Hasło konta forum |
| `PLEAKS_TOTP_SECRET` | Seed 2FA z aplikacji authenticator (nie kod 6-cyfrowy!) |
| `GEMINI_API_KEY` | Klucz Gemini API (free tier, model: gemini-2.5-flash-lite) |
| `DISCORD_WEBHOOK_URL` | Webhook Discord do powiadomień (opcjonalnie) |
| `WG_PRIVATE_KEY` | WireGuard private key z pliku .conf ProtonVPN |
| `WG_PUBLIC_KEY` | WireGuard public key |
| `WG_ADDRESS` | Adres IP tunelu (np. `10.2.0.2/32`) |
| `WG_DNS` | DNS przez VPN (np. `10.2.0.1`) |
| `WG_ENDPOINT` | Serwer VPN `IP:port` (np. `79.127.186.163:51820`) |

---

## Skrypty

### `auto_generate_and_post.py` — główny bot (używaj tego)

Scrapuje wątki, generuje odpowiedzi przez Gemini, postuje.

```bash
python auto_generate_and_post.py           # pyta o zatwierdzenie
python auto_generate_and_post.py --auto    # postuje bez pytania
python auto_generate_and_post.py --preview # podgląd, nie postuje
```

### `login_and_scrape.py` — ręczne logowanie

Jeśli sesja wygasła i nie masz TOTP seed w .env:

```bash
python login_and_scrape.py 123456   # podaj aktualny kod z aplikacji
```

### `autopost.py` — stary bot z hardcoded postami

Przestarzały, używany tylko jeśli chcesz postować konkretne treści bez Gemini.

---

## Działania forum (gdzie bot postuje)

| Sekcja | Dział |
|---|---|
| Sztuczna Inteligencja | Aktualności i dyskusje, Automatyzacje |
| Pieniądze | Kryptowaluty, Dyskusje |
| Darmowe | Konta premium, Kursy |

---

## Pliki danych (gitignore)

| Plik | Opis |
|---|---|
| `.env` | Dane logowania i klucze API |
| `session_cookies.json` | Sesja forum (~30 dni ważności) |
| `posted_urls.json` | Historia odpisanych wątków (nie duplikuj) |
| `autopost_results.json` | Wyniki ostatniego runu |

---

## Nowe konto — procedura

1. Uruchom kontener z `BOT_MODE=manual`
2. Wejdź na `http://IP:6080/vnc.html`
3. Zarejestruj konto **przez Chromium w VNC** (jesteś przez VPN)
4. Przy rejestracji ustaw 2FA — **zapisz seed TOTP** do `PLEAKS_TOTP_SECRET`
5. Ustaw `POSTS_TARGET=2` na pierwsze kilka runów (warmup)
6. Po tygodniu bez bana zwiększ do `7`

---

## GitHub Actions

Cron wyłączony — bot odpala się tylko ręcznie przez Actions → Run workflow.  
Żeby włączyć automatyczny harmonogram, odkomentuj w `.github/workflows/autopost.yml`:

```yaml
# schedule:
#   - cron: '23 11 */12 * *'
```
