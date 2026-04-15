#!/usr/bin/env python3
"""
Automat postowania na pleaks.st
"""
import sys, json, time, random

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    pass

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# ─── POSTY DO WYSLANIA ───────────────────────────────────────────────────────
# (juz wyslane usuniete z listy)

POSTS = [
    # ── SZTUCZNA INTELIGENCJA ────────────────────────────────────────────────
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/jakie-macie-subskrypcje-ai-i-do-czego-je-wykorzystujecie.86910/",
        "content": (
            "u mnie chatgpt plus i claude pro, przy czym od jakiegos czasu rzadziej odpalam chatgpt. "
            "do dluzszych projektow i analizy dokumentow claude sonnet lepiej mi radzi moim zdaniem, "
            "zwlaszcza przy polskich tekstach\n"
            "jak ktos ma google one ai premium to gemini tez jest ok do arkuszy i docsow, "
            "dziala bezposrednio w workspace bez przelaczania zakladek"
        ),
    },
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/na-co-zwraca%C4%87-szczeg%C3%B3ln%C4%85-uwag%C4%99-jak-si%C4%99-programuje-z-ai-problemy-i-co-robi%C4%87.86932/",
        "content": (
            "z supabase mam dokladnie tak samo. ai generuje rls policies ktore wygladaja ok "
            "ale maja dziury jak prompt nie jest precyzyjny co do uprawnien - zawsze sprawdzam sql recznie\n"
            "no i halucynacje z bibliotekami to bol, pare razy dostalem funkcje ktora w danej wersji paczki "
            "po prostu nie istnieje. teraz zawsze weryfikuje w dokumentacji zanim cos idzie na produkcje"
        ),
    },
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/sztuczna-inteligencja-staje-si%C4%99-emocjonalna.86727/",
        "content": (
            "171 wzorcow emocjonalnych brzmi imponujaco ale to trochę nakladanie naszego myslenia "
            "na cos co dziala zupelnie inaczej\n"
            "ze cos wplywa na zachowanie i da sie zmierzyc - ok. ale czy to sa emocje "
            "tak jak my je czujemy to juz zupelnie inna rozmowa, szczerze nie kupuje tego na razie"
        ),
    },
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/czy-ktokolwiek-na-tym-forum-wyprodukowa%C5%82-jak%C4%85%C5%9B-aplikacj%C4%99-program-gr%C4%99-ca%C5%82kowicie-przy-pomocy-ai.86498/",
        "content": (
            "cursor jest teraz najpopularniejszy do vibe codingu i rozumiem czemu, "
            "autouzupelnianie jest naprawde dobre\n"
            "ale jak chcesz ogarnac cos od zera bez przepalania kasy to polecam najpierw claude.ai "
            "z projektem - wklejasz pliki do kontekstu i gadasz o architekturze zanim zaczniesz pisac. "
            "potem jak masz plan to cursor do implementacji. tak mi wychodzie taniej i lepiej "
            "niz probowanie zeby agent sam wszystko wymyslil od poczatku"
        ),
    },
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/nvidia-og%C5%82asza-%C5%BCe-jako-pierwsza-osi%C4%85gn%C4%99%C5%82a-og%C3%B3ln%C4%85-sztuczn%C4%85-inteligencj%C4%99-agi.86377/",
        "content": (
            "huang zrobil klasyczny ruch marketingowy, przedefiniowal agi tak zeby pasowala do tego co aktualnie maja\n"
            "jak zdefiniujesz agi jako 'zdolnosc do zarzadzania firma technologiczna' to aktualne modele sa blisko, "
            "ale kto tak definiuje agi serio. do czegos co naprawde mysli jak czlowiek daleko, "
            "naukowcy od lat to powtarzaja i maja racje"
        ),
    },
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/nie-potrafi%C4%99-powiedzie%C4%87-czy-nasz-chatbot-ma-%C5%9Bwiadomo%C5%9B%C4%87-czy-nie-przera%C5%BC%C4%85ce.83708/",
        "content": (
            "myslę ze amodei jest szczery, nie wydaje mi sie zeby to byl tylko ostrозny pr. "
            "problem ze swiadomoscia jest taki ze nawet dla czlowieka nie mamy dobrego testu - "
            "hard problem of consciousness nikt nie rozwiazal\n"
            "wiec nie dziwi ze przy ai tez nie wiemy. ja zakladam ze nie ma swiadomosci "
            "ale to bardziej domysl niz wiedza, uczciwie mowiac"
        ),
    },
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/polska-reguluje-ai-%E2%80%93-nowa-komisja-b%C4%99dzie-wydawa%C4%87-zezwolenia-i-nak%C5%82ada%C4%87-kary.86672/",
        "content": (
            "samokwalifikacja przez autorow systemow to chyba zart\n"
            "ai act w ue ma ten sam problem - definicje sa tak szerokie ze duze firmy z prawnikami "
            "bez problemu wchodza w 'niskie ryzyko'. male startupy beda sie bac i wpisywac wyzej niz trzeba. "
            "zawsze tak to dziala, regulacje uderzaja w malych a nie w tych co trzeba"
        ),
    },

    # ── PIENIADZE / KRYPTO ───────────────────────────────────────────────────
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/tw%C3%B3j-najwi%C4%99kszy-b%C5%82%C4%85d-zwi%C4%85zany-z-krypto.26846/",
        "content": (
            "klasyk z 2021 - trzymalem alty z przekonaniem ze jak btc rosnie to one tez poleca, "
            "a przy korekcie btc -30% altcoiny jechaly -70%\n"
            "teraz zasada ze alty tylko z procenta ktory jestem gotow stracic w calosci, reszta btc/eth. "
            "i stop-lossy zawsze, pare razy siedzialem w pozycji bez nich liczac na odbicie i to byl blad"
        ),
    },
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/bitcoin-po-halvingu-czy-obecny-cykl-naprawd%C4%99-r%C3%B3%C5%BCni-si%C4%99-od-poprzednich.85179/",
        "content": (
            "mnie przekonuje ten argument z etf-ami. wczesniej duze ruchy btc napędzone przez retail "
            "nakrecajacy sie na reddicie i twitterze. teraz blackrock kupuje co miesiac przez etf "
            "i nie sprzedaje przy kazdym dolku z paniki jak detaliczny inwestor\n"
            "stad pewnie ten cykl taki nudny w porownaniu z poprzednimi"
        ),
    },
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/jak-zacz%C4%85%C4%87-przygod%C4%99-z-inwestowaniem-w-akcje-i-etf.84464/",
        "content": (
            "na xtb polecam zaczac od konta demo - oswoic sie z platforma bez ryzyka. "
            "warto tez przeczytac o roznicy miedzy zleceniem rynkowym a limitowym "
            "bo wiele osob na tym traci przy mniej plynnych spolkach\n"
            "blue chip to dobry start ale etf na szeroki indeks bedzie bezpieczniejszy "
            "niz single-stock picks na poczatek"
        ),
    },
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/wyplata-zyskow-a-podatki.57553/",
        "content": (
            "pit-38 musisz zlozyc jesli miales jakiekolwiek przychody z krypto w danym roku, "
            "nawet jak jestes finalnie na stracie mozesz odliczyc koszty nabycia\n"
            "warto prowadzic rejestr transakcji z datami i kursami. "
            "koinly albo podobne narzedzie bardzo pomaga przy generowaniu raportu podatkowego"
        ),
    },

    # ── DARMOWE ──────────────────────────────────────────────────────────────
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/nordvpn-expires-on-february-20-2028-limit-2.86751/",
        "content": "dzieki, sprawdze czy dziala - szukam czegos do odblokowania zagranicznych serwisow streamingowych",
    },
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/steam-phasmophobia.87045/",
        "content": "o dzieki, wlasnie chcialem sprawdzic z kumplami. fajnie sie gra w pare osob",
    },
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/woblink-com-ebooki-95-audiobooki-0-%C5%81%C4%85cznie-95.85944/",
        "content": "sprawdze co jest w kolekcji, dzieki za wrzucenie",
    },

    # ── NOWE WATKI ───────────────────────────────────────────────────────────
    {
        "type": "new_thread",
        "forum_url": "https://pleaks.st/forums/aktualno%C5%9Bci-i-dyskusje.180/post-thread",
        "title": "Który model AI realnie oszczędza wam czas - konkretnie do czego?",
        "content": (
            "widze sporo watkow o subskrypcjach ale rzadko ktos pisze konkretnie co mu ten model "
            "realnie daje w pracy. pomyslalem ze fajnie zebrac takie przyklady bo to chyba "
            "najbardziej przydatna informacja dla tych co sie zastanawiaja co brac\n\n"
            "u mnie wyglada to tak:\n\n"
            "claude pro - do czytania i skracania dlugich dokumentow, maili, raportow. "
            "sonnet lepiej ogarnia kontekst dlugich polskich tekstow niz gpt moim zdaniem. "
            "jakies 30-40 minut dziennie zaoszczedzone tylko na tym\n\n"
            "chatgpt o3-mini - szybkie pytania przez apke, szybszy do odpalenia niz claude\n\n"
            "gemini advanced - jak mam cos w arkuszach albo docsach to jest po prostu pod reka, "
            "bez przelaczania aplikacji. nie najlepszy ale jak masz workspace to działa\n\n"
            "czuje ze ai nie zastąpiło mi zadnej roboty w calosci ale przyspieszylo duzo malych rzeczy o te 30-50%. "
            "ciekaw jestem jak to wyglada u innych, szczegolnie jak ktos uzywa do czegos niestandardowego"
        ),
    },
    {
        "type": "new_thread",
        "forum_url": "https://pleaks.st/forums/kryptowaluty.81/post-thread",
        "title": "DCA w btc - kto tak robi, od kiedy i czy żałujecie?",
        "content": (
            "dca w btc, czyli kupowanie co tydzien lub miesiac bez patrzenia na kurs. "
            "temat pojawia sie czesto jako rada dla poczatkujacych ale nigdzie nie widze "
            "konkretnych historii od osob ktore to faktycznie robia od dawna\n\n"
            "ja zaczelaem w polowie 2023. przez pierwsze miesiace wygladalo to slabo, "
            "kurs chodził w bok i mialem wrazenie ze wrzucam kase w proznje. "
            "potem przyszedl 2024 i z perspektywy calej strategii wyszlo calkiem ok, "
            "mimo ze w zadne dołki nie trafilem oczywiscie\n\n"
            "co mi to dalo: psychicznie latwiej niz kombinowanie z wejsciem w idealnym momencie, "
            "wymusza regularne odkładanie kasy, nie siedzisz codziennie przy wykresie\n\n"
            "czego nie dalo: nie mam tyle btc ile mialbym gdybym wszedl cala kwota w dołku - "
            "ale kto by trafil. i przy mocnych spadkach nadal ciezko psychicznie kontynuowac, teoria jest prosta\n\n"
            "ciekawe ilu tu robi dca od ponad roku i jak to wyglada praktycznie - ile, jak czesto, na jakiej gieldzie?"
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
    print(f"\n[>>] Odpowiedz: {label[:70]}")
    try:
        page.goto(url, wait_until='domcontentloaded', timeout=20000)
    except PWTimeout:
        print("  [!] Timeout ladowania")
        return False
    page.wait_for_timeout(random.randint(1500, 2500))

    if 'login' in page.url:
        print("  [!] Sesja wygasla!")
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

    print(f"  [OK] Wyslano -> {page.url}")
    return True


def create_thread(page, forum_url, title, content, label):
    print(f"\n[>>] Nowy watek: {title[:70]}")
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
        logged = page.query_selector('a[href*="logout"], a[href*="wyloguj"]') is not None
        print(f"[*] Sesja aktywna: {logged}\n")

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
