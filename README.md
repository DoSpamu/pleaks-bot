# pleaks-bot

Automatyzacja aktywnosci na forum [pleaks.st](https://pleaks.st) (XenForo) — logowanie z 2FA TOTP, scraping watkow, autopostowanie z randomizowanym timingiem.

## Wymagania

```bash
pip install playwright
playwright install chromium
```

## Skrypty

### `login_and_scrape.py` — pierwsze logowanie

Loguje sie na konto, obsluguje weryfikacje dwuetapowa (TOTP), zbiera watki ze wskazanych dzialow i zapisuje sesje do `session_cookies.json`.

```bash
python login_and_scrape.py <KOD_TOTP>
# np. python login_and_scrape.py 123456
```

Plik `session_cookies.json` jest tworzony automatycznie i pozwala na dalsze dzialanie bez 2FA przez ~30 dni.

### `autopost.py` — automat postowania

Wysyla 20 odpowiedzi i tworzy 2 nowe watki na forum w ~40 minut z losowymi przerwami (45-240s) zeby wygladalo naturalnie.

```bash
python autopost.py
```

Jesli sesja wygasla, skrypt poinformuje o tym i zakonczy dzialanie — wtedy uruchom ponownie `login_and_scrape.py`.

### `scrape_threads.py` — eksploracja (wersja robocza)

Wczesna wersja scrapera, uzywana do zbadania struktury forum. Nie wymaga logowania ale bez niego widzi tylko strone logowania.

## Dzialania

Posty sa rozkladane w nastepujacych dzialach, ktore przyznaja punkty aktywnosci:

- **Sztuczna Inteligencja** — odpowiedzi na dyskusje o modelach AI, regulacjach, toolach
- **Pieniadze** — kryptowaluty, ETF-y, inwestowanie
- **Darmowe** — reakcje na udostepnione konta premium, gry, kursy

## Bezpieczenstwo

- `session_cookies.json` jest w `.gitignore` — nie commituj
- Haslo i TOTP nie sa zapisywane w plikach, tylko podawane jako argument
- Headless Chromium — brak widocznego okna przegladarki

## Rozszerzanie

Zeby dodac nowe posty edytuj liste `POSTS` w `autopost.py`:

```python
POSTS = [
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/nazwa-watku.12345/",
        "content": "Tresc odpowiedzi...",
    },
    {
        "type": "new_thread",
        "forum_url": "https://pleaks.st/forums/nazwa-dzialu.99/create-thread",
        "title": "Tytul nowego watku",
        "content": "Tresc watku...",
    },
]
```
