#!/usr/bin/env python3
"""
Dynamiczny bot pleaks.st:
1. Scrapuje swieże watki z forum
2. Generuje odpowiedzi przez Gemini API (styl forum)
3. Opcjonalnie pyta przez Discord webhook przed postowaniem
4. Postuje z losowymi odstepami

Uzycie:
  python auto_generate_and_post.py            # generuje i pyta o zatwierdzenie
  python auto_generate_and_post.py --auto     # postuje bez pytania
  python auto_generate_and_post.py --preview  # tylko podglad, nie postuje
"""
import sys, json, time, random, os, re, datetime

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv()

import pyotp
from google import genai
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# ─── CONFIG ─────────────────────────────────────────────────────────────────

EMAIL        = os.getenv("PLEAKS_EMAIL", "")
HASLO        = os.getenv("PLEAKS_HASLO", "")
TOTP_SECRET  = os.getenv("PLEAKS_TOTP_SECRET", "")
GEMINI_KEY   = os.getenv("GEMINI_API_KEY", "")
DISCORD_URL  = os.getenv("DISCORD_WEBHOOK_URL", "")

POSTS_NEEDED = 5          # ile postow na cykl antypijawki
POSTS_TARGET = 7          # robimy z nadwyzka
MAX_THREADS  = 20         # ile watkow scrapujemy do wyboru
POSTED_LOG   = "posted_urls.json"  # historia - jakie URL juz odpisalismy

MODE_AUTO    = "--auto" in sys.argv
MODE_PREVIEW = "--preview" in sys.argv

DZIALY = [
    ("Sztuczna Inteligencja", "https://pleaks.st/forums/aktualnoci-i-dyskusje.180/"),
    ("Sztuczna Inteligencja", "https://pleaks.st/forums/automatyzacje.184/"),
    ("Pieniadze",             "https://pleaks.st/forums/kryptowaluty.81/"),
    ("Pieniadze",             "https://pleaks.st/forums/dyskusje.83/"),
    ("Darmowe",               "https://pleaks.st/forums/konta-premium.7/"),
    ("Darmowe",               "https://pleaks.st/forums/kursy.168/"),
]

# ─── STYL PISANIA — PROMPT ──────────────────────────────────────────────────

STYLE_PROMPT = """Jesteś użytkownikiem polskiego forum pleaks.st. Piszesz krótkie, naturalne odpowiedzi.

ZASADY ABSOLUTNE:
- Bez kropki na końcu postu
- Małe litery na początku zdania (styl forum)
- Krótko: 2-4 zdania dla SI/Pieniadze, 1-2 zdania dla Darmowe
- Bez formalnego języka: nie "należy", "warto", "istotny", "kluczowy"
- Pisz jakbyś to pisał na telefonie, szybko
- Occasionalnie "xd" lub ":)" ale nie w każdym poście - max 1 na 4-5 postów
- Bez emoji w treści postów
- Mieszaj polskie i angielskie słowa techniczne naturalnie (btc, etf, ai, vibe coding)
- Osobiste doświadczenia, nie wykłady
- Czasem krótkie zdanie urwane myślą
- Nie zaczynaj od "ja" - zacznij od tematu lub obserwacji

PRZYKŁADY DOBRYCH POSTÓW:
"mam google one więc gemini wychodzi przy okazji, do roboty na co dzień starcza"
"klasyk z 2021 - kupno altów w szczycie i potem patrzyłem jak topnieją"
"dzieki, akurat szukam czegoś do streamingu z uk"

Odpowiedz TYLKO treścią posta, bez cudzysłowów, bez wyjaśnień."""

# ─── HISTORIA POSTOW ────────────────────────────────────────────────────────

def load_posted() -> set:
    if os.path.exists(POSTED_LOG):
        try:
            return set(json.load(open(POSTED_LOG, encoding="utf-8")))
        except Exception:
            pass
    return set()

def save_posted(urls: set):
    with open(POSTED_LOG, "w", encoding="utf-8") as f:
        json.dump(list(urls), f, ensure_ascii=False, indent=2)

# ─── GEMINI ─────────────────────────────────────────────────────────────────

def generate_reply(thread_title: str, thread_posts: list[str], section: str) -> str:
    """Generuje odpowiedz przez Gemini Flash (darmowy)."""
    if not GEMINI_KEY:
        print("  [!] Brak GEMINI_API_KEY w .env")
        return ""

    client = genai.Client(api_key=GEMINI_KEY)

    context = "\n---\n".join(thread_posts[:4]) if thread_posts else "(brak tresci)"
    section_hint = {
        "Darmowe": "To jest post z podziekowaniem za darmowy dostep/konto. Bardzo krotko, 1-2 zdania.",
        "Pieniadze": "To jest dyskusja o finansach/kryptowalutach. 2-3 zdania, osobiste doswiadczenie.",
        "Sztuczna Inteligencja": "To jest dyskusja o AI/technologii. 2-4 zdania, konkretne obserwacje.",
    }.get(section, "")

    prompt = f"""{STYLE_PROMPT}

Sekcja forum: {section}
{section_hint}

Tytul watku: {thread_title}

Tresc watku (posty innych):
{context}

Napisz naturalna odpowiedz w tym watku:"""

    try:
        resp = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
        )
        text = resp.text.strip().strip('"').strip("'")
        if text.endswith("."):
            text = text[:-1]
        return text
    except Exception as e:
        print(f"  [!] Gemini blad: {e}")
        return ""

# ─── DISCORD WEBHOOK ────────────────────────────────────────────────────────

def send_discord(message: str):
    if not DISCORD_URL:
        return
    try:
        import urllib.request
        data = json.dumps({"content": message}).encode("utf-8")
        req = urllib.request.Request(DISCORD_URL, data=data,
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"  [!] Discord blad: {e}")

# ─── PLAYWRIGHT — LOGOWANIE ─────────────────────────────────────────────────

def login(ctx, page):
    print("[*] Logowanie...")
    page.goto("https://pleaks.st/login/", wait_until="domcontentloaded")
    page.wait_for_timeout(1500)

    page.fill("input[name='login']", EMAIL)
    page.fill("input[name='password']", HASLO)
    page.click("button[type='submit']")
    page.wait_for_timeout(3000)

    if "two-step" in page.url:
        if not TOTP_SECRET:
            print("[!] Brak PLEAKS_TOTP_SECRET w .env - nie mozna zalogowac sie automatycznie")
            return False
        totp_code = pyotp.TOTP(TOTP_SECRET).now()
        print(f"[*] Kod TOTP: {totp_code}")
        page.fill("input[name='code']", totp_code)
        page.click("button[type='submit']")
        page.wait_for_timeout(3000)

    content = page.content().lower()
    if "zbanowany" in content or "banned" in content:
        print("[!] KONTO ZBANOWANE")
        return False

    logged = page.query_selector("a[href*='logout']") is not None
    print(f"[*] Zalogowany: {logged}")
    return logged

# ─── PLAYWRIGHT — SCRAPOWANIE WATKOW ────────────────────────────────────────

NAVIGATION_SKIP = {
    "dołącz do ekipy", "jak kupić kredyty", "szukaj wątków",
    "wątki z moimi postami", "wątki bez odpowiedzi", "kanał forum",
    "telegram", "dotacje", "vip", "rekrutacja",
}

def scrape_threads(page, posted_urls: set) -> list[dict]:
    """Zbiera swieże watki z forum, pomijając już odpisane."""
    candidates = []

    for section_name, section_url in DZIALY:
        print(f"\n[*] Scrapuje: {section_name}")
        page.goto(section_url, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        # Szukaj tylko w strukturze listy watkow, nie w nawigacji
        thread_items = page.query_selector_all(
            ".structItem-title a[href*='threads/'], "
            ".discussionListItem a[href*='threads/'], "
            "h3.structItem-title a"
        )
        # Fallback: wszystkie linki do threads ale z filtrowaniem
        if not thread_items:
            thread_items = page.query_selector_all("a[href*='threads/']")

        seen = set()
        before = len(candidates)
        for lnk in thread_items:
            href = lnk.get_attribute("href") or ""
            title = (lnk.inner_text() or "").strip()

            if not title or len(title) < 8:
                continue
            # Odfiltruj linki nawigacyjne
            if title.lower() in NAVIGATION_SKIP:
                continue
            if any(skip in title.lower() for skip in ["dołącz", "kupić kredyty", "szukaj"]):
                continue

            full = href if href.startswith("http") else f"https://pleaks.st{href}"
            if "/page-" in full or "#" in full or "/find-threads" in full:
                continue

            normalized = re.sub(r'/page-\d+', '', full).rstrip('/')
            if normalized in posted_urls or full in seen:
                continue

            seen.add(full)
            candidates.append({"url": full, "title": title, "section": section_name})

        added = len(candidates) - before
        print(f"  Nowych watkow: {added}")

    random.shuffle(candidates)
    return candidates[:MAX_THREADS]

def read_thread_posts(page, url: str) -> list[str]:
    """Czyta posty z watku."""
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(1500)
    except PWTimeout:
        return []

    posts = []
    for sel in [".bbWrapper", ".message-body .bbWrapper", ".message-body"]:
        els = page.query_selector_all(sel)
        if els:
            for el in els[:6]:
                txt = (el.inner_text() or "").strip()
                if txt and len(txt) > 15:
                    posts.append(txt[:600])
            if posts:
                break
    return posts

# ─── PLAYWRIGHT — POSTOWANIE ─────────────────────────────────────────────────

def type_into_editor(page, content: str) -> bool:
    editor = page.query_selector(".fr-element.fr-view, .fr-element")
    if not editor:
        page.keyboard.press("End")
        page.wait_for_timeout(800)
        for sel in ['a.button--link[href*="reply"]', '.js-quickReply', 'a[data-xf-click="quick-reply"]']:
            btn = page.query_selector(sel)
            if btn:
                btn.click()
                page.wait_for_timeout(1000)
                break
        editor = page.query_selector(".fr-element.fr-view, .fr-element")

    if not editor:
        print("  [!] Brak edytora Froala")
        return False

    editor.click()
    page.wait_for_timeout(400)
    page.keyboard.press("Control+a")
    page.keyboard.press("Delete")
    page.keyboard.type(content, delay=18)
    page.wait_for_timeout(300)
    return True

def click_submit(page) -> bool:
    for locator_args in [{"has_text": "Odpowiedz"}, {"has_text": "Opublikuj"}, {"has_text": "Wyslij"}]:
        try:
            page.locator("button", **locator_args).last.click(timeout=4000)
            return True
        except Exception:
            pass
    try:
        page.locator("button[type='submit']").last.click(timeout=3000)
        return True
    except Exception:
        pass
    return False

def post_reply(page, url: str, content: str, label: str) -> bool:
    print(f"\n[>>] {label[:70]}")
    try:
        page.goto(url, wait_until='domcontentloaded', timeout=20000)
    except PWTimeout:
        print("  [!] Timeout ladowania")
        return False
    page.wait_for_timeout(random.randint(1500, 2500))

    if 'login' in page.url:
        print("  [!] Sesja wygasla")
        return False

    content_lower = page.content().lower()
    if "zbanowany" in content_lower:
        print("  [!] Konto zbanowane!")
        return False

    if not type_into_editor(page, content):
        return False

    print("  [+] Wpisano tresc")
    page.wait_for_timeout(random.randint(600, 1200))

    if not click_submit(page):
        print("  [!] Blad submitu")
        return False

    page.wait_for_timeout(random.randint(2500, 4000))

    if 'login' in page.url:
        print("  [!] Przekierowano do logowania")
        return False

    print(f"  [OK] -> {page.url}")
    return True

# ─── MAIN ───────────────────────────────────────────────────────────────────

def gen_delays(n: int, total_seconds: int = 2400) -> list[float]:
    if n <= 1:
        return []
    raw = [random.uniform(0.5, 1.5) for _ in range(n - 1)]
    total = sum(raw)
    scaled = [r / total * total_seconds for r in raw]
    return [max(60, min(300, s)) for s in scaled]

def main():
    print(f"[*] Tryb: {'AUTO' if MODE_AUTO else 'PREVIEW' if MODE_PREVIEW else 'ZATWIERDZENIE'}")
    print(f"[*] Cel: {POSTS_TARGET} postow\n")

    posted_urls = load_posted()
    print(f"[*] Juz odpisane URL: {len(posted_urls)}")

    # ── Faza 1: scraping + generowanie ────────────────────────────────
    generated = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="pl-PL",
            viewport={"width": 1280, "height": 900},
        )

        # Zaladuj cookies jesli sa, albo zaloguj sie
        if os.path.exists("session_cookies.json"):
            try:
                cookies = json.load(open("session_cookies.json", encoding="utf-8"))
                ctx.add_cookies(cookies)
            except Exception:
                pass

        page = ctx.new_page()
        page.goto("https://pleaks.st/", wait_until="domcontentloaded")
        page.wait_for_timeout(1500)

        logged = page.query_selector("a[href*='logout']") is not None
        if not logged:
            ok = login(ctx, page)
            if not ok:
                browser.close()
                return
            # Zapisz nowe cookies
            cookies = ctx.cookies()
            with open("session_cookies.json", "w", encoding="utf-8") as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)

        print("[*] Sesja aktywna\n")

        # Scraping watkow
        threads = scrape_threads(page, posted_urls)
        print(f"\n[*] Kandydatow do odpisania: {len(threads)}")

        # Generowanie odpowiedzi
        for t in threads:
            if len(generated) >= POSTS_TARGET:
                break

            print(f"\n[G] {t['title'][:60]}")
            posts = read_thread_posts(page, t["url"])
            reply = generate_reply(t["title"], posts, t["section"])

            if not reply:
                print("  [!] Pusta odpowiedz, pomijam")
                continue

            print(f"  -> {reply[:100]}")
            generated.append({
                "url": t["url"],
                "title": t["title"],
                "section": t["section"],
                "content": reply,
            })

        browser.close()

    if not generated:
        print("\n[!] Brak wygenerowanych postow - koniec")
        return

    # ── Faza 2: podglad / zatwierdzenie ───────────────────────────────
    print(f"\n{'='*55}")
    print(f"WYGENEROWANO {len(generated)} POSTOW:")
    print('='*55)
    for i, g in enumerate(generated, 1):
        print(f"\n[{i}] {g['section']} | {g['title'][:55]}")
        print(f"    {g['content']}")

    if MODE_PREVIEW:
        print("\n[PREVIEW] Tryb podgladu - nie postuje")
        return

    if not MODE_AUTO:
        if DISCORD_URL:
            msg = f"**pleaks.st — {len(generated)} postow do zatwierdzenia:**\n"
            for i, g in enumerate(generated, 1):
                msg += f"\n**[{i}] {g['section']}** — {g['title'][:50]}\n> {g['content']}\n"
            msg += "\nOdpisz **ok** zeby poslac, albo zignoruj."
            send_discord(msg)
            print("\n[*] Wyslano na Discord. Czekam 5 minut na 'ok'...")
            print("[*] Jesli chcesz postowac teraz, wpisz 'ok' tutaj:")
        else:
            print("\nWpisz 'ok' zeby postowac, cokolwiek innego zeby przerwac:")

        try:
            ans = input("> ").strip().lower()
        except EOFError:
            ans = "ok"  # w trybie nieinteraktywnym (GitHub Actions) domyslnie ok

        if ans != "ok":
            print("[*] Anulowano")
            return

    # ── Faza 3: postowanie ─────────────────────────────────────────────
    random.shuffle(generated)
    delays = gen_delays(len(generated))

    print(f"\n[*] Postuje {len(generated)} postow...")
    print(f"[*] Szacowany czas: {int(sum(delays)/60)} minut\n")

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="pl-PL",
            viewport={"width": 1280, "height": 900},
        )
        cookies = json.load(open("session_cookies.json", encoding="utf-8"))
        ctx.add_cookies(cookies)
        page = ctx.new_page()

        for i, post in enumerate(generated):
            ok = post_reply(page, post["url"], post["content"], post["title"])
            results.append({"title": post["title"], "url": post["url"], "ok": ok})

            if ok:
                posted_urls.add(post["url"])
                save_posted(posted_urls)

            if i < len(generated) - 1:
                delay = delays[i]
                print(f"  [~] Czekam {int(delay//60)}m {int(delay%60)}s...", flush=True)
                time.sleep(delay)

        browser.close()

    # ── Podsumowanie ───────────────────────────────────────────────────
    ok_count = sum(1 for r in results if r["ok"])
    print(f"\n{'='*55}")
    print(f"GOTOWE: {ok_count}/{len(results)}")
    for r in results:
        status = "OK" if r["ok"] else "BLAD"
        print(f"  [{status}] {r['title'][:60]}")

    with open("autopost_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    if DISCORD_URL and not MODE_PREVIEW:
        send_discord(f"pleaks.st — gotowe: {ok_count}/{len(results)} postow wyslanych")


if __name__ == "__main__":
    main()
