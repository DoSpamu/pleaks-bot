#!/usr/bin/env python3
"""
Skrypt do przeglądania forum pleaks.st, zbierania i czytania wątków.
"""
import json
import random
import time
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

EMAIL = "dospamu.pl@gmail.com"
HASLO = "Zalas539!"

DZIALY = [
    ("Darmowe", "https://pleaks.st/#darmowe.93"),
    ("Sztuczna Inteligencja", "https://pleaks.st/#sztuczna-inteligencja.179"),
    ("Pieniądze", "https://pleaks.st/#pieniadze.80"),
]


def screenshot(page, name):
    page.screenshot(path=f"ss_{name}.png", full_page=False)


def login(page):
    print("[*] Otwieram stronę główną...")
    page.goto("https://pleaks.st/", wait_until="domcontentloaded")
    page.wait_for_timeout(2000)
    screenshot(page, "01_home")

    # Kliknij przycisk "Logowanie" w nawigacji
    print("[*] Klikam 'Logowanie' w navbarze...")
    try:
        # Szukaj linka Logowanie w nav (nie modala)
        page.click("a[href*='login']:visible, a:text('Logowanie'):visible", timeout=5000)
    except Exception:
        try:
            page.click("text=Logowanie", timeout=3000)
        except Exception:
            print("[!] Nie znaleziono przycisku - może już jest modal lub przekierowanie")

    page.wait_for_timeout(1500)
    screenshot(page, "02_after_login_click")

    # Sprawdź czy jest modal
    modal_visible = page.query_selector(".modal:visible, dialog:visible, [role='dialog']:visible")

    if modal_visible:
        print("[*] Modal logowania widoczny, wypełniam...")
        # Wypełnij pola w modalu
        page.fill(".modal input[name='login'], dialog input[name='login'], [role='dialog'] input[name='login']", EMAIL)
        page.wait_for_timeout(300)
        page.fill(".modal input[type='password'], dialog input[type='password'], [role='dialog'] input[type='password']", HASLO)
        page.wait_for_timeout(300)
        screenshot(page, "03_modal_filled")
        page.click(".modal button[type='submit'], dialog button[type='submit'], [role='dialog'] button[type='submit']")
    else:
        # Może strona logowania bez modala
        print("[*] Brak modala, szukam formularza na stronie...")
        try:
            page.fill("input[name='login']", EMAIL, timeout=3000)
            page.fill("input[type='password']", HASLO, timeout=3000)
            screenshot(page, "03_form_filled")
            page.click("button[type='submit']")
        except Exception as e:
            print(f"[!] Błąd wypełniania formularza: {e}")

    page.wait_for_timeout(3000)
    screenshot(page, "04_after_submit")

    # Sprawdź wynik
    url = page.url
    content = page.content().lower()
    logged_in = (
        "logout" in content or
        "wyloguj" in content or
        "avatar" in content and "login" not in url or
        page.query_selector("a[href*='logout'], a[href*='wyloguj']") is not None
    )
    print(f"[*] URL po logowaniu: {url}")
    print(f"[*] Zalogowany: {logged_in}")
    return logged_in


def navigate_to_section(page, hash_url):
    """Nawiguje do działu forum (hash-based routing)."""
    # Najpierw wejdź na base URL
    base = "https://pleaks.st/"
    if page.url != base and not page.url.startswith(base):
        page.goto(base, wait_until="domcontentloaded")
        page.wait_for_timeout(1000)

    # Teraz nawiguj do hash URL
    print(f"[*] Przechodzę do: {hash_url}")
    page.goto(hash_url, wait_until="domcontentloaded")
    page.wait_for_timeout(3000)  # Czekaj na załadowanie JS

    # Spróbuj też evaluate hash change
    fragment = hash_url.split("#")[1] if "#" in hash_url else ""
    if fragment:
        try:
            page.evaluate(f"window.location.hash = '#{fragment}'")
            page.wait_for_timeout(2000)
        except Exception:
            pass


def get_threads(page, hash_url, section_name):
    """Zbiera linki do wątków z danego działu."""
    navigate_to_section(page, hash_url)
    screenshot(page, f"section_{section_name.replace(' ', '_')}")

    # Zbierz wszystkie linki
    all_links = page.query_selector_all("a[href]")
    threads = []
    seen = set()

    for link in all_links:
        try:
            href = link.get_attribute("href") or ""
            text = link.inner_text().strip()

            # Pomiń puste, nawigacyjne, hash-only
            if not href or not text or len(text) < 5:
                continue
            if href in ("#", "/", "javascript:void(0)"):
                continue
            if href.startswith("mailto:") or href.startswith("javascript:"):
                continue

            # Zbuduj pełny URL
            if href.startswith("http"):
                full_url = href
            elif href.startswith("/"):
                full_url = f"https://pleaks.st{href}"
            else:
                full_url = f"https://pleaks.st/{href}"

            # Filtruj tylko linki do wątków (thread, temat, t/, topic)
            is_thread = any(x in full_url for x in [
                "/thread", "/temat", "/topic", "/t/",
                "threads/", "showthread", "viewtopic",
                ".html", "/post"
            ])

            # Pomiń strony systemowe
            is_system = any(x in full_url for x in [
                "login", "register", "lost-password", "logout",
                "whats-new", "misc/language", "online", "/register",
                "account", "settings", "contact", "privacy"
            ])

            if is_thread and not is_system and full_url not in seen:
                seen.add(full_url)
                threads.append({
                    "url": full_url,
                    "title": text[:120],
                    "section": section_name
                })
            elif not is_system and full_url not in seen and "pleaks.st" in full_url:
                # Może być wątek bez wyraźnego wzorca - dodaj z niższym priorytetem
                seen.add(full_url)
                # sprawdź czy to wygląda jak wątek (długi tekst tytułu)
                if len(text) > 15 and not any(x in text.lower() for x in [
                    "logowanie", "rejestracja", "aktualności", "kontakt",
                    "strona główna", "home", "forum", "kategoria"
                ]):
                    threads.append({
                        "url": full_url,
                        "title": text[:120],
                        "section": section_name,
                        "priority": "low"
                    })
        except Exception:
            continue

    print(f"[*] Dział '{section_name}': znaleziono {len(threads)} potencjalnych wątków")
    return threads


def read_thread_content(page, thread):
    """Otwiera wątek i zbiera treść postów."""
    url = thread["url"]
    print(f"\n[*] Otwieram: {thread['title'][:60]}")
    print(f"    URL: {url}")

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(2000)
    except PWTimeout:
        print("[!] Timeout ładowania strony")
        return None
    except Exception as e:
        print(f"[!] Błąd: {e}")
        return None

    # Sprawdź czy jesteśmy nadal zalogowani / czy to wątek
    current_url = page.url
    page_title = page.title()

    # Zbierz treść postów
    post_selectors = [
        ".message-body", ".post-body", ".bbWrapper",
        ".message-text", "article .content", ".postContent",
        "[itemprop='text']", ".post_body"
    ]

    posts = []
    for sel in post_selectors:
        els = page.query_selector_all(sel)
        if els:
            for el in els[:5]:  # Max 5 postów
                try:
                    text = el.inner_text().strip()
                    if text and len(text) > 20:
                        posts.append(text[:500])
                except Exception:
                    pass
            if posts:
                break

    # Jeśli nie znaleziono postów, weź cały tekst strony
    if not posts:
        try:
            body_text = page.inner_text("body")
            # Wyczyść nawigację
            lines = [l.strip() for l in body_text.split("\n") if l.strip() and len(l.strip()) > 20]
            # Pomiń pierwsze linie (nawigacja) i ostatnie (footer)
            relevant = lines[5:-5] if len(lines) > 10 else lines
            posts = ["\n".join(relevant[:10])]
        except Exception:
            posts = ["[Nie udało się pobrać treści]"]

    screenshot(page, f"thread_{thread['title'][:20].replace(' ', '_').replace('/', '_')}")

    return {
        "url": url,
        "title": thread["title"],
        "section": thread["section"],
        "page_title": page_title,
        "posts": posts[:3]  # Max 3 posty
    }


def main():
    print("=" * 60)
    print("PLEAKS FORUM SCRAPER")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--lang=pl-PL"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="pl-PL",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()

        # 1. Zaloguj się
        logged_in = login(page)
        if not logged_in:
            print("\n[!] Logowanie nieudane — próbuję mimo to przeglądać forum...")

        # 2. Zbierz wątki ze wszystkich działów
        all_threads = []
        for section_name, hash_url in DZIALY:
            threads = get_threads(page, hash_url, section_name)
            all_threads.extend(threads)

        # Preferuj wątki z wyraźnym wzorcem URL
        priority_threads = [t for t in all_threads if t.get("priority") != "low"]
        low_threads = [t for t in all_threads if t.get("priority") == "low"]

        print(f"\n[*] Łącznie: {len(priority_threads)} wątków (pewne) + {len(low_threads)} (możliwe)")

        # Wybierz 5 losowych (priorytet → pewne, potem reszta)
        pool = priority_threads if len(priority_threads) >= 5 else all_threads
        chosen = random.sample(pool, min(5, len(pool)))

        if len(chosen) == 0:
            print("[!] Nie znaleziono żadnych wątków!")
            browser.close()
            return

        # 3. Przeczytaj treść każdego wątku
        results = []
        for thread in chosen:
            data = read_thread_content(page, thread)
            if data:
                results.append(data)

        browser.close()

    # 4. Zapisz wyniki
    with open("threads_data.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 5. Wyświetl
    print(f"\n\n{'='*60}")
    print(f"ZNALEZIONE WĄTKI ({len(results)})")
    print("="*60)

    for i, r in enumerate(results, 1):
        print(f"\n{'='*60}")
        print(f"WĄTEK {i}: {r['title'][:80]}")
        print(f"URL: {r['url']}")
        print(f"Dział: {r['section']}")
        print(f"Posty:")
        for j, post in enumerate(r['posts'], 1):
            print(f"  Post {j}: {post[:300]}")


if __name__ == "__main__":
    main()
