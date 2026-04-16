#!/usr/bin/env python3
"""
Scraper pleaks.st - logowanie + zbieranie watkow.
Uzycie:
  python login_and_scrape.py          # TOTP z .env (PLEAKS_TOTP_SECRET)
  python login_and_scrape.py 123456   # reczny kod TOTP
"""
import sys
import json
import random
import os

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv()

from patchright.sync_api import sync_playwright, TimeoutError as PWTimeout

EMAIL       = os.getenv("PLEAKS_EMAIL", "chmurkowychmurkas@gmail.com")
HASLO       = os.getenv("PLEAKS_HASLO", "Biolanic2026!")
TOTP_SECRET = os.getenv("PLEAKS_TOTP_SECRET", "")

# Jesli podano kod recznie — uzyj go; jesli jest secret — generuj automatycznie
if len(sys.argv) > 1:
    TOTP = sys.argv[1]
elif TOTP_SECRET:
    import pyotp
    TOTP = pyotp.TOTP(TOTP_SECRET).now()
    print(f"[*] TOTP wygenerowany automatycznie: {TOTP}")
else:
    TOTP = ""

DZIALY = [
    ("Darmowe",               "https://pleaks.st/forums/darmowe.93/"),
    ("Sztuczna Inteligencja", "https://pleaks.st/forums/sztuczna-inteligencja.179/"),
    ("Pieniadze",             "https://pleaks.st/forums/pieniadze.80/"),
]


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            locale="pl-PL",
            viewport={"width": 1280, "height": 900},
        )
        page = ctx.new_page()

        # ── 1. Logowanie ───────────────────────────────────────────────
        print("[*] Logowanie...")
        page.goto("https://pleaks.st/login/", wait_until="domcontentloaded")
        page.wait_for_timeout(1500)

        page.fill("input[name='login']", EMAIL)
        page.fill("input[name='password']", HASLO)
        page.click("button[type='submit']")
        page.wait_for_timeout(3000)

        if "two-step" in page.url:
            if not TOTP:
                print("[!] Wymagany kod 2FA! Uruchom: python login_and_scrape.py <KOD>")
                browser.close()
                return
            print(f"[*] Wpisuje kod 2FA: {TOTP}")
            page.fill("input[name='code']", TOTP)
            page.click("button[type='submit']")
            page.wait_for_timeout(3000)

        # Sprawdz ban
        content = page.content().lower()
        if "zbanowany" in content or "banned" in content:
            print("[!] KONTO ZBANOWANE - przerywam")
            browser.close()
            return

        logged = (
            "logout" in content or
            "wyloguj" in content or
            page.query_selector("a[href*='logout']") is not None
        )
        print(f"[*] Zalogowany: {logged}")
        if not logged:
            print("[!] Logowanie nieudane")
            browser.close()
            return

        # ── 2. Zapisz cookies ─────────────────────────────────────────
        cookies = ctx.cookies()
        with open("session_cookies.json", "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        print(f"[*] Cookies zapisane: {len(cookies)} sztuk")

        # ── 3. Zbierz watki z dzialow ─────────────────────────────────
        all_threads = []
        for name, url in DZIALY:
            print(f"\n[*] Dzial: {name}")
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

            links = page.query_selector_all("a[href*='threads/']")
            for lnk in links:
                href = lnk.get_attribute("href") or ""
                text = (lnk.inner_text() or "").strip()
                if text and len(text) > 5:
                    full = href if href.startswith("http") else f"https://pleaks.st{href}"
                    if "/page-" not in full and "#" not in full:
                        all_threads.append({"url": full, "title": text, "section": name})

            seen = set()
            deduped = []
            for t in all_threads:
                if t["url"] not in seen:
                    seen.add(t["url"])
                    deduped.append(t)
            all_threads = deduped
            section_count = sum(1 for t in all_threads if t["section"] == name)
            print(f"  Watkow: {section_count}")

        print(f"\n[*] Lacznie: {len(all_threads)} watkow")
        with open("all_threads.json", "w", encoding="utf-8") as f:
            json.dump(all_threads, f, ensure_ascii=False, indent=2)
        print("[OK] Gotowe")
        browser.close()


if __name__ == "__main__":
    main()
