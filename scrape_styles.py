#!/usr/bin/env python3
"""
Scrapuje posty z konkretnych wątków z autopost.py żeby przeczytać jak tam piszą.
Użycie: python scrape_styles.py
(wymaga aktywnej sesji w session_cookies.json)
"""
import json
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

TARGET_THREADS = [
    "https://pleaks.st/threads/jakie-macie-subskrypcje-ai-i-do-czego-je-wykorzystujecie.86910/",
    "https://pleaks.st/threads/na-co-zwracac-szczegolna-uwage-jak-sie-programuje-z-ai-problemy-i-co-robic.86932/",
    "https://pleaks.st/threads/sztuczna-inteligencja-staje-sie-emocjonalna.86727/",
    "https://pleaks.st/threads/czy-ktokolwiek-na-tym-forum-wyprodukowa%C5%82-jak%C4%85%C5%9B-aplikacj%C4%99-program-gr%C4%99-ca%C5%82kowicie-przy-pomocy-ai.86498/",
    "https://pleaks.st/threads/nvidia-og%C5%82asza-%C5%BCe-jako-pierwsza-osi%C4%85gn%C4%99%C5%82a-og%C3%B3ln%C4%85-sztuczn%C4%85-inteligencj%C4%99-agi.86377/",
    "https://pleaks.st/threads/nie-potrafi%C4%99-powiedzie%C4%87-czy-nasz-chatbot-ma-%C5%9Bwiadomo%C5%9B%C4%87-czy-nie-przera%C5%BC%C4%85ce.83708/",
    "https://pleaks.st/threads/polska-reguluje-ai-%E2%80%93-nowa-komisja-b%C4%99dzie-wydawa%C4%87-zezwolenia-i-nak%C5%82ada%C4%87-kary.86672/",
    "https://pleaks.st/threads/tw%C3%B3j-najwi%C4%99kszy-b%C5%82%C4%85d-zwi%C4%85zany-z-krypto.26846/",
    "https://pleaks.st/threads/bitcoin-po-halvingu-czy-obecny-cykl-naprawd%C4%99-r%C3%B3%C5%BCni-si%C4%99-od-poprzednich.85179/",
    "https://pleaks.st/threads/jak-zacz%C4%85%C4%87-przygod%C4%99-z-inwestowaniem-w-akcje-i-etf.84464/",
    "https://pleaks.st/threads/wyplata-zyskow-a-podatki.57553/",
    "https://pleaks.st/threads/nordvpn-expires-on-february-20-2028-limit-2.86751/",
    "https://pleaks.st/threads/steam-phasmophobia.87045/",
    "https://pleaks.st/threads/woblink-com-ebooki-95-audiobooki-0-%C5%81%C4%85cznie-95.85944/",
]


def scrape_thread(page, url):
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(1500)
    except PWTimeout:
        print(f"  [!] Timeout: {url}")
        return []

    if "login" in page.url:
        print("  [!] Sesja wygasla!")
        return []

    posts = []
    for sel in [".message-body .bbWrapper", ".bbWrapper", ".message-body"]:
        els = page.query_selector_all(sel)
        if els:
            for el in els[:10]:
                txt = (el.inner_text() or "").strip()
                if txt and len(txt) > 15:
                    posts.append(txt[:800])
            if posts:
                break

    return posts


def main():
    with open("session_cookies.json") as f:
        cookies = json.load(f)

    results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="pl-PL",
            viewport={"width": 1280, "height": 900},
        )
        ctx.add_cookies(cookies)
        page = ctx.new_page()

        page.goto("https://pleaks.st/", wait_until="domcontentloaded")
        page.wait_for_timeout(1500)
        logged = page.query_selector('a[href*="logout"], a[href*="wyloguj"]') is not None
        print(f"[*] Sesja aktywna: {logged}")
        if not logged:
            print("[!] Sesja wygasla - uruchom login_and_scrape.py z kodem TOTP")
            browser.close()
            return

        for url in TARGET_THREADS:
            short = url.split("/threads/")[1][:50] if "/threads/" in url else url[-40:]
            print(f"\n[>>] {short}")
            posts = scrape_thread(page, url)
            results[url] = posts
            print(f"  Zebrano postow: {len(posts)}")

        browser.close()

    with open("thread_styles.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Zapisano -> thread_styles.json")


if __name__ == "__main__":
    main()
