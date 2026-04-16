#!/usr/bin/env python3
"""Posty nowych watkow - uruchamiac po autopost.py."""
import sys, json, random, time

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    pass

from patchright.sync_api import sync_playwright, TimeoutError as PWTimeout

THREADS = [
    {
        "forum_url": "https://pleaks.st/forums/aktualno%C5%9Bci-i-dyskusje.180/post-thread",
        "title": "Który model AI najbardziej skraca Wam czas pracy i do czego konkretnie?",
        "content": (
            "Widzę na forum sporo wątków o tym jakie subskrypcje kto ma, "
            "ale rzadko kiedy ktoś pisze konkretnie co mu ten model AI realnie daje w codziennej robocie. "
            "Pomyślałem ze fajnie byłoby zebrać takie case'y w jednym miejscu, "
            "bo to jest chyba najbardziej przydatna informacja dla osób które zastanawiają się co warto mieć.\n\n"
            "U mnie wygląda to tak:\n\n"
            "Claude Pro - do przeczytania i podsumowania długich dokumentów, maili, raportów. "
            "Mam wrażenie ze Sonnet lepiej ogarnia kontekst przy długich tekstach niż GPT, "
            "przynajmniej przy polskich dokumentach. "
            "Oszczędza mi pewnie z 30-40 minut dziennie na samym czytaniu i streszczaniu rzeczy które muszę ogarniać w pracy.\n\n"
            "ChatGPT o3-mini - do szybkich pytań gdzie nie potrzebuję kontekstu z poprzednich rozmów. "
            "Szybszy do odpalenia przez aplikację mobilną niż Claude.\n\n"
            "Gemini Advanced (Google One) - głównie do spraw związanych z arkuszami kalkulacyjnymi i Docsami, "
            "bo działa bezpośrednio w ekosystemie Google. Nie jest najlepszy ale jak masz już Workspace to po prostu jest pod ręką.\n\n"
            "Ogólnie mam poczucie ze AI nie zastąpiło mi żadnej konkretnej pracy w całości, "
            "ale skróciło czas wykonywania mnóstwa małych rzeczy o 30-50%. "
            "Ciekaw jestem jak to wygląda u innych, zwłaszcza tych którzy używają AI "
            "do czegoś bardziej niestandardowego niż kodowanie i pisanie tekstów."
        ),
    },
    {
        "forum_url": "https://pleaks.st/forums/kryptowaluty.81/post-thread",
        "title": "DCA w BTC - od kiedy stosujecie i czy zalujecie?",
        "content": (
            "Dollar Cost Averaging czyli kupowanie BTC regularnie, np. co tydzień lub co miesiąc, "
            "niezależnie od kursu. Temat pojawia się w wielu wątkach jako rada dla początkujących, "
            "ale nigdzie nie widzę zebranych konkretnych doświadczeń od osób które faktycznie to robią od dłuższego czasu.\n\n"
            "Ja zacząłem DCA w BTC w połowie 2023 roku. Przez pierwsze miesiące wyglądało to dość słabo "
            "bo kurs chodził w bok i miałem wrażenie ze wrzucam kasę w próżnię. "
            "Potem przyszedł 2024 i z perspektywy całej strategii wyszło całkiem nieźle, "
            "mimo ze oczywiście nie trafiłem w żadne lokalne dołki.\n\n"
            "Co mi dało DCA:\n"
            "- psychicznie jest dużo łatwiej niż próba trafienia w idealny moment wejścia\n"
            "- zmusza do regularnego odkładania konkretnej kwoty, co jest dobrą dyscypliną finansową "
            "niezależnie od wyników\n"
            "- nie musisz śledzić wykresu codziennie żeby czuć ze coś robisz\n\n"
            "Czego nie dało:\n"
            "- nie kupiłem tyle ile mógłbym gdybym wszedł całą kwotą w odpowiednim momencie, "
            "ale kto by trafił ten moment z góry\n"
            "- przy mocnych spadkach nadal jest psychicznie ciężko kontynuować, "
            "teoria jest prosta a praktyka inna\n\n"
            "Ciekaw jestem ile osób tutaj faktycznie stosuje DCA systematycznie od ponad roku "
            "i jak to u Was wygląda. Jaka kwota co jaki czas, na jakiej giełdzie, "
            "czy robicie to ręcznie czy macie jakiś automat?"
        ),
    },
]


def type_into_editor(page, content):
    editor = page.query_selector(".fr-element.fr-view, .fr-element")
    if not editor:
        print("  [!] Brak edytora Froala")
        return False
    editor.click()
    page.wait_for_timeout(400)
    page.keyboard.press("Control+a")
    page.keyboard.press("Delete")
    page.keyboard.type(content, delay=20)
    page.wait_for_timeout(300)
    return True


def click_submit(page):
    try:
        page.locator("button", has_text="Opublikuj watek").last.click(timeout=5000)
        return True
    except Exception:
        pass
    try:
        page.locator("button", has_text="Odpowiedz").last.click(timeout=3000)
        return True
    except Exception:
        pass
    try:
        page.locator("button[type='submit']").last.click(timeout=3000)
        return True
    except Exception:
        pass
    return False


def create_thread(page, forum_url, title, content):
    print(f"\n[>>] Nowy watek: {title[:60]}")
    try:
        page.goto(forum_url, wait_until='networkidle', timeout=25000)
    except PWTimeout:
        print("  [!] Timeout")
        return False
    page.wait_for_timeout(2000)

    if 'login' in page.url:
        print("  [!] Sesja wygasla!")
        return False

    print(f"  URL po redirect: {page.url}")

    # Tytul to textarea, nie input
    try:
        page.fill('textarea[name="title"]', title, timeout=8000)
        print(f"  [+] Wpisano tytul")
    except Exception as e:
        print(f"  [!] Brak pola tytulu: {e}")
        # Pokaz co jest na stronie
        inputs = page.query_selector_all('input, textarea')
        for el in inputs:
            n = el.get_attribute('name') or ''
            t = el.tag_name
            if n:
                print(f"      {t}[name={n}]")
        return False

    page.wait_for_timeout(500)

    if not type_into_editor(page, content):
        return False

    print(f"  [+] Wpisano tresc")
    page.wait_for_timeout(random.randint(800, 1500))

    if not click_submit(page):
        print("  [!] Blad submitu")
        return False

    page.wait_for_timeout(random.randint(3000, 5000))

    if 'login' in page.url:
        print("  [!] Po submicie -> logowanie")
        return False

    print(f"  [OK] Watek utworzony: {page.url}")
    return True


def main():
    with open('session_cookies.json') as f:
        cookies = json.load(f)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            locale='pl-PL',
            viewport={'width': 1280, 'height': 900},
        )
        ctx.add_cookies(cookies)
        page = ctx.new_page()

        for i, t in enumerate(THREADS):
            ok = create_thread(page, t['forum_url'], t['title'], t['content'])
            if not ok:
                print(f"  [!!] NIEUDANY: {t['title'][:50]}")
            if i < len(THREADS) - 1:
                delay = random.randint(60, 120)
                print(f"  [~] Czekam {delay}s...")
                time.sleep(delay)

        browser.close()

    print("\nGotowe.")


if __name__ == '__main__':
    main()
