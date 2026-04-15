#!/usr/bin/env python3
"""
Scraper pleaks.st - logowanie + zbieranie wątków.
Użycie: python login_and_scrape.py <KOD_TOTP>
"""
import sys
import json
import random
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

EMAIL = "dospamu.pl@gmail.com"
HASLO = "Zalas539!"
TOTP = sys.argv[1] if len(sys.argv) > 1 else ""

DZIALY = [
    ("Darmowe",              "https://pleaks.st/forums/darmowe.93/"),
    ("Sztuczna Inteligencja","https://pleaks.st/forums/sztuczna-inteligencja.179/"),
    ("Pieniadze",            "https://pleaks.st/forums/pieniadze.80/"),
]


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="pl-PL",
            viewport={"width": 1280, "height": 900},
        )
        page = ctx.new_page()

        # ── 1. Logowanie ───────────────────────────────────────────────
        print("[*] Przechodzę do strony logowania...")
        page.goto("https://pleaks.st/login/", wait_until="domcontentloaded")
        page.wait_for_timeout(1500)

        page.fill("input[name='login']", EMAIL)
        page.fill("input[name='password']", HASLO)
        page.click("button[type='submit']")
        page.wait_for_timeout(3000)
        print(f"[*] URL po haśle: {page.url}")

        if "two-step" in page.url:
            if not TOTP:
                print("[!] Wymagany kod 2FA! Uruchom: python login_and_scrape.py <KOD>")
                browser.close()
                return
            print(f"[*] Wpisuję kod 2FA: {TOTP}")
            page.fill("input[name='code']", TOTP)
            page.click("button[type='submit']")
            page.wait_for_timeout(3000)
            print(f"[*] URL po 2FA: {page.url}")

        page.screenshot(path="ss_logged.png")
        logged = (
            "logout" in page.content().lower() or
            "wyloguj" in page.content().lower() or
            page.query_selector("a[href*='logout']") is not None
        )
        print(f"[*] Zalogowany: {logged}")
        if not logged:
            print("[!] Logowanie nieudane")
            browser.close()
            return

        # ── 2. Zbierz wątki z działów ──────────────────────────────────
        all_threads = []
        for name, url in DZIALY:
            print(f"\n[*] Dział: {name}")
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(2500)
            page.screenshot(path=f"ss_{name.split()[0]}.png")

            links = page.query_selector_all("a[href*='threads/']")
            for lnk in links:
                href = lnk.get_attribute("href") or ""
                text = (lnk.inner_text() or "").strip()
                if text and len(text) > 5:
                    full = href if href.startswith("http") else f"https://pleaks.st{href}"
                    # Pomiń podstrony wątku (/page-N, #post-N itp.)
                    if "/page-" not in full and "#" not in full:
                        all_threads.append({"url": full, "title": text, "section": name})

            # Deduplikuj
            seen = set()
            deduped = []
            for t in all_threads:
                if t["url"] not in seen:
                    seen.add(t["url"])
                    deduped.append(t)
            all_threads = deduped

            section_count = sum(1 for t in all_threads if t["section"] == name)
            print(f"  Wątki w dziale: {section_count}")

        print(f"\n[*] Łącznie: {len(all_threads)} wątków")
        with open("all_threads.json", "w", encoding="utf-8") as f:
            json.dump(all_threads, f, ensure_ascii=False, indent=2)

        # ── 3. Czytaj 5 losowych wątków ────────────────────────────────
        chosen = random.sample(all_threads, min(5, len(all_threads)))
        results = []

        for t in chosen:
            print(f"\n[*] Otwieram: {t['title'][:70]}")
            try:
                page.goto(t["url"], wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(2000)
            except PWTimeout:
                print("  [!] Timeout")
                continue

            posts = []
            for sel in [".message-body .bbWrapper", ".bbWrapper", ".message-body", "[itemprop='text']"]:
                els = page.query_selector_all(sel)
                if els:
                    for el in els[:6]:
                        txt = (el.inner_text() or "").strip()
                        if txt and len(txt) > 20:
                            posts.append(txt[:600])
                    if posts:
                        break

            if not posts:
                body = page.inner_text("body")
                lines = [l.strip() for l in body.split("\n") if l.strip() and len(l.strip()) > 30]
                posts = ["\n".join(lines[3:15])]

            results.append({
                "url": t["url"],
                "title": t["title"],
                "section": t["section"],
                "posts": posts[:4],
            })
            print(f"  Postów zebranych: {len(posts)}")

        with open("threads_data.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n[✓] Zapisano {len(results)} wątków → threads_data.json")
        browser.close()


if __name__ == "__main__":
    main()
