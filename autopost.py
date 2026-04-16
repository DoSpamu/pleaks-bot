#!/usr/bin/env python3
"""
Automat postowania na pleaks.st (hardcoded posty).
Do dynamicznego trybu uzyj: auto_generate_and_post.py
"""
import sys, json, time, random, os

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv()

# ─── BLOKADA — tylko jedna instancja naraz ───────────────────────────────────
LOCK_FILE = "autopost.lock"
if os.path.exists(LOCK_FILE):
    print(f"[!] Bot juz dziala (znaleziono {LOCK_FILE}). Przerywam.")
    sys.exit(1)
with open(LOCK_FILE, "w") as f:
    f.write(str(os.getpid()))

import atexit
atexit.register(lambda: os.remove(LOCK_FILE) if os.path.exists(LOCK_FILE) else None)
# ─────────────────────────────────────────────────────────────────────────────

from patchright.sync_api import sync_playwright, TimeoutError as PWTimeout


# ─── HUMANIZER ──────────────────────────────────────────────────────────────

def humanize_text(page, text):
    """Przepuszcza tekst przez ai-text-humanizer.com (darmowy, bez logowania).
    Wymaga min. 300 znakow. Zwraca przetworzony tekst lub oryginalny jesli blad."""
    if len(text) < 300:
        return text  # za krotki - pomijamy humanizacje

    try:
        page.goto("https://ai-text-humanizer.com/", wait_until='networkidle', timeout=20000)
        page.wait_for_timeout(1500)

        escaped = text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        page.evaluate(f"""(function() {{
            var ta = document.querySelectorAll('textarea')[0];
            var setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
            setter.call(ta, "{escaped}");
            ta.dispatchEvent(new Event('input', {{bubbles: true}}));
        }})()""")
        page.wait_for_timeout(500)

        btn = page.query_selector("button:has-text('Humanize Text')")
        if not btn:
            print("  [!] Brak przycisku humanizera")
            return text
        btn.scroll_into_view_if_needed()
        btn.click(force=True)

        for _ in range(20):
            page.wait_for_timeout(2000)
            output = page.evaluate("(function(){ return document.querySelectorAll('textarea')[1].value; })()")
            if output and len(output) > 30:
                print(f"  [H] Humanizacja OK ({len(text)} -> {len(output)} zn)")
                return output

        print("  [!] Humanizacja timeout - uzyto oryginalny tekst")
        return text
    except Exception as e:
        print(f"  [!] Humanizacja blad: {e}")
        return text

# ─── POSTY DO WYSLANIA ───────────────────────────────────────────────────────
# (juz wyslane usuniete z listy)

POSTS = [
    # ── SZTUCZNA INTELIGENCJA ────────────────────────────────────────────────
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/jakie-macie-subskrypcje-ai-i-do-czego-je-wykorzystujecie.86910/",
        "content": (
            "na razie tylko gemini advanced bo mam google one i wychodzi przy okazji, nie musiałem płacić osobno\n"
            "do roboty na co dzień starcza, jakiś czas temu bym powiedział że gpt bije gemini ale 2.5 mocno nadgonił\n"
            "jedyne co - integracja z androidem kuleje, notebooki super ale apka mobilna to dramat jak dla mnie"
        ),
    },
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/na-co-zwraca%C4%87-szczeg%C3%B3ln%C4%85-uwag%C4%99-jak-si%C4%99-programuje-z-ai-problemy-i-co-robi%C4%87.86932/",
        "content": (
            "mnie ai parę razy zaskoczyło tym że generuje kod który wygląda ok ale ma edge case'y których nie testuje\n"
            "szczególnie obsługa błędów - działa na happy path i tyle, jak przychodzi wyjątek to crash\n"
            "od jakiegoś czasu wymuszam żeby pisało unit testy razem z kodem, przynajmniej trochę pomaga"
        ),
    },
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/sztuczna-inteligencja-staje-si%C4%99-emocjonalna.86727/",
        "content": (
            "no ale czy \"wpływa na zachowanie\" to już \"odczuwa\" to chyba duże uproszczenie nie? xd\n"
            "rozumiem że ciekawe badanie ale od \"mamy wektory emocjonalne\" do \"ai ma emocje\" to długa droga"
        ),
    },
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/czy-ktokolwiek-na-tym-forum-wyprodukowa%C5%82-jak%C4%85%C5%9B-aplikacj%C4%99-program-gr%C4%99-ca%C5%82kowicie-przy-pomocy-ai.86498/",
        "content": (
            "zrobiłem prosty bot do scrapowania danych, nie żadna duża apka ale działa na co dzień i mi starcza\n"
            "cursor bardzo pomógł, wcześniej pisałem wszystko ręcznie i zajmowało 3x tyle\n"
            "chyba nie wyjdzie z tego biznes ale przynajmniej wiem że da się coś skończyć z pomocą ai xd"
        ),
    },
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/nvidia-og%C5%82asza-%C5%BCe-jako-pierwsza-osi%C4%85gn%C4%99%C5%82a-og%C3%B3ln%C4%85-sztuczn%C4%85-inteligencj%C4%99-agi.86377/",
        "content": (
            "to trochę jakby powiedzieć że samochód osiągnął pełną autonomię bo raz przejechał parking bez wpadnięcia w słupek\n"
            "definiujesz cel pod to co już masz i bingo, agi osiągnięte\n"
            "naukowcy słusznie to olewają, huang robi swoje a rynek i tak kupuje nvidię więc po co się starać"
        ),
    },
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/nie-potrafi%C4%99-powiedzie%C4%87-czy-nasz-chatbot-ma-%C5%9Bwiadomo%C5%9B%C4%87-czy-nie-przera%C5%BC%C4%85ce.83708/",
        "content": (
            "bardziej bym się niepokoił tym że my nie wiemy czym jest świadomość u człowieka a już chcemy oceniać czy ai to ma :)\n"
            "sam fakt że amodei mówi \"nie wiem\" to chyba dobry znak, gorzej jak ktoś twierdzi że na pewno nie albo na pewno tak"
        ),
    },
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/polska-reguluje-ai-%E2%80%93-nowa-komisja-b%C4%99dzie-wydawa%C4%87-zezwolenia-i-nak%C5%82ada%C4%87-kary.86672/",
        "content": (
            "samokwalifikacja przez twórców systemów to szczyt xd - ci co zarabiają na systemie mają oceniać czy jest ryzykowny\n"
            "no i te przepisy i tak będą z 2-letnim opóźnieniem wobec technologii, takie tempo legislacji vs tempo ai"
        ),
    },

    # ── PIENIADZE / KRYPTO ───────────────────────────────────────────────────
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/tw%C3%B3j-najwi%C4%99kszy-b%C5%82%C4%85d-zwi%C4%85zany-z-krypto.26846/",
        "content": (
            "mój klasyk to kupno paru altcoinów \"z potencjałem\" w szczycie 2021, jeden projekt po roku po prostu zniknął z coingecko\n"
            "nauczka: jak projektu nie ma na binance to likwidacja bardziej prawdopodobna niż x10\n"
            "teraz trzymam się btc i eth, alty co najwyżej małe kwoty żeby nie było nudno"
        ),
    },
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/bitcoin-po-halvingu-czy-obecny-cykl-naprawd%C4%99-r%C3%B3%C5%BCni-si%C4%99-od-poprzednich.85179/",
        "content": (
            "ciekawe jak długo btc będzie w ogóle reagował na halving skoro nagroda za blok jest coraz mniejsza procentowo\n"
            "kiedyś to był mega event bo zdejmował duży % podaży, teraz robi się coraz mniej istotny\n"
            "z etf-ami zgadzam się - to chyba teraz większy driver niż sam halving"
        ),
    },
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/jak-zacz%C4%85%C4%87-przygod%C4%99-z-inwestowaniem-w-akcje-i-etf.84464/",
        "content": (
            "jak zaczynałem to też szukałem jakichś \"ciekawych spółek\" zamiast wziąć szeroki etf xd\n"
            "przez pół roku tradeowałem single stocki i byłem 15% w dół, potem przeniosłem większość w s&p500 i działa normalnie\n"
            "konto demo na xtb serio warto, nie pomijaj tego nawet jak ci się wydaje że już rozumiesz"
        ),
    },
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/wyplata-zyskow-a-podatki.57553/",
        "content": (
            "pit-38, w tym roku po raz pierwszy składałem przez e-pit i jakoś poszło\n"
            "dla małej liczby transakcji excel z ręcznym wpisywaniem wystarczył szczerze, koinly trochę overkill"
        ),
    },

    # ── DARMOWE ──────────────────────────────────────────────────────────────
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/nordvpn-expires-on-february-20-2028-limit-2.86751/",
        "content": "dzieki, akurat szukam czegoś do treści z uk",
    },
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/steam-phasmophobia.87045/",
        "content": "dzięki, gram z ekipą w horrorki co jakiś czas, w sam raz na weekend",
    },
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/woblink-com-ebooki-95-audiobooki-0-%C5%81%C4%85cznie-95.85944/",
        "content": "o, mam już konto na woblink ale z takim dostępem to niezły deal, dziękuję",
    },

    # ── NOWE WATKI ───────────────────────────────────────────────────────────
    {
        "type": "new_thread",
        "forum_url": "https://pleaks.st/forums/aktualno%C5%9Bci-i-dyskusje.180/post-thread",
        "title": "jak ogarniacie kontekst przy dłuższych projektach w ai?",
        "content": (
            "piszę coraz więcej z pomocą ai ale przy większych projektach zaczyna gubić kontekst po kilkunastu wiadomościach\n\n"
            "próbowałem wklejać summary poprzednich rozmów na początku nowej sesji, działa jakoś ale ręczna robota\n"
            "w cursor jest rules for ai ale to bardziej pod styl kodu niż pod logikę projektu\n\n"
            "ciekawy jestem jak inni to ogarniają - memory w chatgpt, projekty w claude, może coś innego? "
            "bo czuję że tu jest jakiś patent którego mi brakuje"
        ),
    },
    {
        "type": "new_thread",
        "forum_url": "https://pleaks.st/forums/kryptowaluty.81/post-thread",
        "title": "altcoiny w tym cyklu - wchodzić czy lepiej odpuścić?",
        "content": (
            "w poprzednich cyklach schemat był prosty: btc rośnie, potem alt season i alty robią x5-x20\n"
            "tym razem btc już był wysoko a altcoiny generalnie w dół albo w miejscu, przynajmniej te które trzymam xd\n\n"
            "zastanawiam się czy ten cykl po prostu jest inny i alt season się nie pojawi, czy może po prostu jeszcze nie czas\n\n"
            "ktoś aktywnie gra na altach w tym roku? które sektory waszym zdaniem mają jeszcze sens - defi, ai tokeny, coś innego?"
        ),
    },
]


# ─── LOSOWE ODSTEPY ─────────────────────────────────────────────────────────

def gen_delays(n, total_seconds=2200):
    raw = [random.uniform(0.5, 1.5) for _ in range(n - 1)]
    total = sum(raw)
    scaled = [r / total * total_seconds for r in raw]
    clamped = [max(45, min(240, s)) for s in scaled]
    return clamped


# ─── LOGIKA POSTOWANIA ──────────────────────────────────────────────────────

def type_into_editor(page, content):
    # Probuj tez kliknac przycisk odpowiedzi jesli edytor nie jest widoczny
    editor = page.query_selector(".fr-element.fr-view, .fr-element")
    if not editor:
        # Scroll na dol i szukaj przycisku odpowiedzi
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


def click_submit(page):
    for locator_args in [
        {"has_text": "Odpowiedz"},
        {"has_text": "Opublikuj"},
        {"has_text": "Wyslij"},
    ]:
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


def post_reply(page, url, content, label):
    print(f"\n[>>] Odpowiedz: {label[:70]}", flush=True)
    # content = humanize_text(page, content)  # wlacz na prosbe uzytkownika
    try:
        page.goto(url, wait_until='domcontentloaded', timeout=20000)
    except PWTimeout:
        print("  [!] Timeout ladowania", flush=True)
        return False
    page.wait_for_timeout(random.randint(1500, 2500))

    if 'login' in page.url:
        print("  [!] Sesja wygasla!", flush=True)
        return False

    if "zbanowany" in page.content().lower():
        print("  [!] KONTO ZBANOWANE", flush=True)
        return False

    if not type_into_editor(page, content):
        return False

    print("  [+] Wpisano tresc", flush=True)
    page.wait_for_timeout(random.randint(600, 1200))

    if not click_submit(page):
        print("  [!] Blad submitu", flush=True)
        return False

    page.wait_for_timeout(random.randint(2500, 4000))

    if 'login' in page.url:
        print("  [!] Przekierowano do logowania", flush=True)
        return False

    print(f"  [OK] Wyslano -> {page.url}", flush=True)
    return True


def create_thread(page, forum_url, title, content, label):
    print(f"\n[>>] Nowy watek: {title[:70]}", flush=True)
    # content = humanize_text(page, content)  # wlacz na prosbe uzytkownika
    try:
        page.goto(forum_url, wait_until='networkidle', timeout=25000)
    except PWTimeout:
        print("  [!] Timeout")
        return False
    page.wait_for_timeout(2000)

    if 'login' in page.url:
        print("  [!] Sesja wygasla!")
        return False

    # XenForo uzywa textarea[name="title"], nie input
    try:
        page.fill('textarea[name="title"]', title, timeout=8000)
        print("  [+] Wpisano tytul")
    except Exception as e:
        print(f"  [!] Brak pola tytulu: {e}")
        return False

    page.wait_for_timeout(500)

    if not type_into_editor(page, content):
        return False

    print("  [+] Wpisano tresc")
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


# ─── MAIN ───────────────────────────────────────────────────────────────────

def main():
    with open('session_cookies.json') as f:
        cookies = json.load(f)

    posts_copy = POSTS.copy()
    random.shuffle(posts_copy)

    delays = gen_delays(len(posts_copy))

    print(f"[*] Lacznie postow: {len(posts_copy)}")
    print(f"[*] Szacowany czas: {int(sum(delays)/60)} minut")
    print(f"[*] Opoznienia (s): {[int(d) for d in delays]}\n")

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            locale='pl-PL',
            viewport={'width': 1280, 'height': 900},
        )
        ctx.add_cookies(cookies)
        page = ctx.new_page()

        page.goto('https://pleaks.st/', wait_until='domcontentloaded')
        page.wait_for_timeout(2000)

        content_lower = page.content().lower()
        if "zbanowany" in content_lower:
            print("[!] KONTO ZBANOWANE - przerywam")
            browser.close()
            return

        logged = page.query_selector('a[href*="logout"], a[href*="wyloguj"]') is not None
        print(f"[*] Sesja aktywna: {logged}\n", flush=True)

        if not logged:
            print("[!] Sesja wygasla - potrzebny nowy TOTP!")
            browser.close()
            return

        for i, post in enumerate(posts_copy):
            label = post.get('title', post.get('url', ''))[:60]

            if post['type'] == 'reply':
                ok = post_reply(page, post['url'], post['content'], label)
            else:
                ok = create_thread(page, post['forum_url'], post['title'], post['content'], label)

            results.append({'label': label, 'ok': ok})

            if i < len(posts_copy) - 1:
                delay = delays[i]
                mins = int(delay // 60)
                secs = int(delay % 60)
                print(f"  [~] Czekam {mins}m {secs}s przed kolejnym postem...")
                time.sleep(delay)

        browser.close()

    ok_count = sum(1 for r in results if r['ok'])
    print(f"\n{'='*50}")
    print(f"GOTOWE: {ok_count}/{len(results)} postow wyslanych")
    for r in results:
        status = 'OK' if r['ok'] else 'BLAD'
        print(f"  [{status}] {r['label'][:60]}")

    with open('autopost_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
