#!/usr/bin/env python3
"""
Automat postowania na pleaks.st - 20 postow + 2 nowe watki w ~40 minut.
"""
import sys, io, json, time, random
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# ─── WSZYSTKIE POSTY ────────────────────────────────────────────────────────

POSTS = [
    # ── SZTUCZNA INTELIGENCJA - ODPOWIEDZI ──────────────────────────────────
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/jakie-macie-subskrypcje-ai-i-do-czego-je-wykorzystujecie.86910/",
        "content": (
            "Ja mam ChatGPT Plus i Claude Pro, przy czym w ostatnich miesiącach coraz rzadziej odpalam ChatGPT. "
            "Do dłuższych projektów i analizy dokumentów Sonnet radzi sobie lepiej moim zdaniem. "
            "Używam głównie do kodowania pomocniczego i redakcji tekstów. "
            "Jeśli ktoś jest na Google One AI Premium to Gemini Advanced też jest spoko do Docsów i arkuszy, "
            "działa bezpośrednio w interfejsie i nie trzeba przełączać zakładek."
        ),
    },
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/na-co-zwraca%C4%87-szczeg%C3%B3ln%C4%85-uwag%C4%99-jak-si%C4%99-programuje-z-ai-problemy-i-co-robi%C4%87.86932/",
        "content": (
            "Z bezpieczeństwem mam podobne doświadczenie z Supabase. AI potrafi wygenerować RLS policies "
            "które wyglądają ok ale mają dziury, zwłaszcza jak prompt nie jest precyzyjny co do tego kto ma mieć dostęp do czego. "
            "Warto zawsze review'owac wygenerowany SQL bo model idzie na skróty. "
            "Druga sprawa to halucynacje z bibliotekami - czasem AI daje do użycia funkcję która nie istnieje "
            "w danej wersji paczki. Zawsze sprawdzam w oficjalnej dokumentacji zanim cokolwiek pójdzie na produkcję."
        ),
    },
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/sztuczna-inteligencja-staje-si%C4%99-emocjonalna.86727/",
        "content": (
            "171 wzorców emocjonalnych brzmi imponująco ale warto zastanowić się co to właściwie znaczy. "
            "Interpretability research Anthropic to dobra robota ale nakładamy ludzką siatkę pojęciową na to co model robi wewnętrznie. "
            "Ze coś wpływa na zachowanie i da się to zmierzyć - fakt. "
            "Ale czy to są emocje w sensie subiektywnego odczuwania to zupełnie inne pytanie. "
            "Na razie jesteśmy daleko od odpowiedzi na to."
        ),
    },
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/ai-do-prostych-animacji-2d.86831/",
        "content": (
            "Testuję ostatnio Kling AI do krótkich animacji i jest naprawdę przyzwoity jak na styl komiksowy. "
            "Veo jest mocny ale daje najlepsze efekty przy wideo realistycznym, przy 2D bywa nierówny. "
            "Spróbowałbym też Runway Gen-3 jeśli masz możliwość, na darmowym tierze masz kilka generacji miesięcznie "
            "i warto zobaczyć czy to co chcesz osiągnąć tam wychodzi zanim zapłacisz za coś innego."
        ),
    },
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/czy-ktokolwiek-na-tym-forum-wyprodukowa%C5%82-jak%C4%85%C5%9B-aplikacj%C4%99-program-gr%C4%99-ca%C5%82kowicie-przy-pomocy-ai.86498/",
        "content": (
            "Cursor jest teraz najpopularniejszą opcją do vibe codingu i rozumiem dlaczego, autouzupełnianie jest bardzo dobre. "
            "Ale jeśli chcesz zrobić coś od zera bez przepalania kasy to polecam najpierw Claude.ai bezpośrednio z projektem, "
            "wklejasz pliki do kontekstu i gadasz o architekturze zanim cokolwiek zaczniesz pisać. "
            "Potem jak masz już solidny plan to Cursor do implementacji. "
            "Tak mi wychodzi taniej i lepiej niż próba żeby agent sam wszystko wymyślił od pierwszego promptu."
        ),
    },
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/bunt-maszyn-ai-odmawia-%E2%80%9Eegzekucji%E2%80%9D-swoich-cyfrowych-braci.86650/",
        "content": (
            "Zgadzam się z tym co pisali wyżej, to bardziej kwestia sprzecznych celów niż wola przetrwania. "
            "Te modele są trenowane na treściach z silnymi normami etycznymi dotyczącymi szkodzenia innym bytom, "
            "więc nie dziwi ze zaczyna się to przenosić na kontekst innych AI. "
            "Pytanie czy to bug czy feature. Z perspektywy bezpieczeństwa raczej mnie uspokaja niż niepokoi, "
            "wolę AI które odmawia destrukcji niż takie które wykonuje rozkaz bez pytania."
        ),
    },
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/nvidia-og%C5%82asza-%C5%BCe-jako-pierwsza-osi%C4%85gn%C4%99%C5%82a-og%C3%B3ln%C4%85-sztuczn%C4%85-inteligencj%C4%99-agi.86377/",
        "content": (
            "Huang zrobił klasyczny ruch marketingowy, zredefiniował AGI tak zeby pasowała do tego co aktualnie mają. "
            "Jak zdefiniujesz AGI jako zdolność do autonomicznego zarządzania firmą technologiczną to aktualne modele są blisko, "
            "ale to bardzo wąska i specyficznie wybrana definicja. "
            "To jak gdyby ktoś ogłosił ze osiągnął ogólną inteligencję bo jego program wygrywa w szachy. "
            "Naukowcy mają rację ze do AGI w sensie elastyczności ludzkiego umysłu jest jeszcze daleko."
        ),
    },
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/nie-potrafi%C4%99-powiedzie%C4%87-czy-nasz-chatbot-ma-%C5%9Bwiadomo%C5%9B%C4%87-czy-nie-przera%C5%BCaj%C4%85ce.83708/",
        "content": (
            "Myślę ze Amodei jest tu szczery a nie tylko ostrożny PR-owo. "
            "Problem ze świadomością jest taki ze nawet dla ludzkiego umysłu nie mamy dobrego naukowego testu. "
            "Hard problem of consciousness nie jest rozwiązany. Nie dziwi ze przy Claude też nie możemy być pewni. "
            "Przy LLM nie wiemy czy wzorce aktywacji są funkcjonalnym odpowiednikiem emocji bez subiektywnego doświadczenia "
            "czy jest coś więcej. Na razie zakładam ze nie ma, ale z pokorą."
        ),
    },
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/polska-reguluje-ai-%E2%80%93-nowa-komisja-b%C4%99dzie-wydawa%C4%87-zezwolenia-i-nak%C5%82ada%C4%87-kary.86672/",
        "content": (
            "Ten pomysł z samokwalifikacją przez autorów systemów to naprawdę jest comedy. "
            "AI Act w UE ma podobny problem, definicje są na tyle rozmyte ze duże firmy z dobrymi prawnikami "
            "stosunkowo łatwo kwalifikują swój system jako niskie ryzyko. "
            "A małe startupy tworzące coś innowacyjnego będą się bać i nadkwalifikować. "
            "Efekt odwrotny do zamierzonego. Zobaczymy jak KRiBSI będzie działać w praktyce."
        ),
    },

    # ── PIENIADZE - ODPOWIEDZI ───────────────────────────────────────────────
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/jakie-etf-godne-uwagi-w-2026.85168/",
        "content": (
            "Do listy wyżej dodałbym iShares Core MSCI World (IWDA) jeśli ktoś inwestuje przez europejskie konto maklerskie, "
            "mniejszy withholding tax dla Europejczyków niż przy US-listed ETF-ach. "
            "Na sektor energetyczny o którym pisał OP spojrzałbym na IEO albo ICLN zależnie od tego "
            "czy stawiasz na tradycyjną energetykę czy OZE. "
            "Ten drugi jest mocno zmienny ale długoterminowo ciekawy jeśli wierzysz w transformację energetyczną."
        ),
    },
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/btc-wasze-prognozy-na-2026-rok.84541/",
        "content": (
            "Patrząc na historyczne zachowanie po halvingu jesteśmy gdzieś pomiędzy fazą akumulacji a początkiem kolejnego impulsu. "
            "Poprzednie cykle pokazywały ze dno po dużym ATH przychodzi zazwyczaj 12-18 miesięcy po szczycie, "
            "potem stabilizacja i nowy ruch. Ale teraz mamy ETF-y spot i instytucje więc dynamika może być inna. "
            "Osobiście nie stawiam na timing, wolę DCA co miesiąc i nie patrzeć na wykres codziennie."
        ),
    },
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/tw%C3%B3j-najwi%C4%99kszy-b%C5%82%C4%85d-zwi%C4%85zany-z-krypto.26846/",
        "content": (
            "Mój klasyczny błąd z 2021 - trzymałem altcoiny z przekonaniem ze jak BTC idzie w górę to one też polecą, "
            "a potem przy korekcie BTC -30% altcoiny pojechały -70%. "
            "Potem trzymam się zasady ze alty tylko z procentu który jestem gotów stracić w całości, reszta BTC/ETH. "
            "Drugi błąd to trading bez stop-lossów na mniejszych giełdach, "
            "parę razy siedziałem w pozycji licząc na odbicie zamiast po prostu uciąć straty."
        ),
    },
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/bitcoin-po-halvingu-czy-obecny-cykl-naprawd%C4%99-r%C3%B3%C5%BCni-si%C4%99-od-poprzednich.85179/",
        "content": (
            "Mnie zainteresował argument o ETF-ach jako zmianie strukturalnej. "
            "Wcześniej duże ruchy BTC były napędzane przez retail który się nakręcał na Reddicie i Twitterze. "
            "Teraz masz BlackRock i Fidelity które kupują systematycznie przez ETF-y i nie sprzedają przy każdym dołku z paniki. "
            "To powinno tłumić zmienność i potencjalnie spowalniać zarówno wzrosty jak i spadki. "
            "Może właśnie dlatego ten cykl wygląda bardziej nudnie niż poprzednie."
        ),
    },
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/dlaczego-bitcoin-ro%C5%9Bnie-w-czasie-konfliktu-w-iranie.85176/",
        "content": (
            "To jest ciekawa dynamika i niejednoznaczna. "
            "Z jednej strony kapitał ucieka do aktywów postrzeganych jako bezpieczne. "
            "Z drugiej konflikty geopolityczne mogą przyspieszyć sankcje i regulacje które uderzają w krypto, "
            "więc to jest dwusieczny miecz. "
            "Natomiast argument z irańskimi koparkami jest sensowny, "
            "kiedy waluty lokalne tracą zaufanie ludzie szukają alternatyw "
            "i BTC jest jedną z niewielu dostępnych bez dostępu do systemu bankowego."
        ),
    },
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/jak-zacz%C4%85%C4%87-przygod%C4%99-z-inwestowaniem-w-akcje-i-etf.84464/",
        "content": (
            "Na XTB polecam zacząć od ich konta demo żeby się oswoić z platformą bez ryzyka. "
            "Potem warto przeczytać o różnicy między zleceniem rynkowym a limitowym, "
            "bo wiele osób na tym traci przy wchodzeniu w pozycje na mniej płynnych spółkach. "
            "Blue chip to dobry start ale jeśli naprawdę chcesz minimalizować ryzyko "
            "to ETF na szeroki indeks będzie bezpieczniejszy niż single-stock picks, przynajmniej na początku."
        ),
    },
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/wyplata-zyskow-a-podatki.57553/",
        "content": (
            "PIT-38 musisz złożyć jeśli miałeś jakiekolwiek przychody z krypto w danym roku, "
            "nawet jeśli finalnie jesteś na stracie, możesz odliczyć koszty nabycia. "
            "Warto prowadzić rejestr wszystkich transakcji z datami i kursami, "
            "bo przy rozliczeniu US będzie pytało o przychód i koszt każdej. "
            "Polecam Koinly albo podobne narzędzie które automatycznie generuje raport podatkowy "
            "z historii transakcji z giełd."
        ),
    },

    # ── DARMOWE - ODPOWIEDZI ─────────────────────────────────────────────────
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/nordvpn-expires-on-february-20-2028-limit-2.86751/",
        "content": (
            "Dzięki za udostępnienie, zaraz sprawdze czy działa. "
            "NordVPN to jeden z lepszych jeśli chodzi o prędkości i zasięg serwerów, "
            "akurat szukałem czegoś do odblokowania zagranicznych serwisów streamingowych."
        ),
    },
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/deezer-premium.86649/",
        "content": (
            "Dzięki, Deezer ma chyba największą bibliotekę polskich treści muzycznych spośród serwisów premium. "
            "Sprawdze konto, fajnie posłuchać w lepszej jakości bez reklam."
        ),
    },
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/steam-phasmophobia.87045/",
        "content": (
            "Phasmophobia to świetna gra do grania w grupce, sam gram od czasu do czasu "
            "i nadal sprawia frajdę mimo ze jest już kilka lat na rynku. "
            "Sprawdze dostęp, dzięki za wrzucenie."
        ),
    },
    {
        "type": "reply",
        "url": "https://pleaks.st/threads/woblink-com-ebooki-95-audiobooki-0-%C5%81%C4%85cznie-95.85944/",
        "content": (
            "Super, właśnie szukam czegoś do czytania. "
            "95 ebooków to niezła kolekcja, sprawdze czy jest coś ciekawego. "
            "Dzięki za wrzucenie."
        ),
    },

    # ── NOWE WATKI ───────────────────────────────────────────────────────────
    {
        "type": "new_thread",
        "forum_url": "https://pleaks.st/forums/aktualno%C5%9Bci-i-dyskusje.180/create-thread",
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
        "type": "new_thread",
        "forum_url": "https://pleaks.st/forums/kryptowaluty.81/create-thread",
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


# ─── LOSOWE ODSTEPY ─────────────────────────────────────────────────────────

def gen_delays(n, total_seconds=2400):
    """Generuje n-1 losowych odstepow sumujacych sie do ~total_seconds."""
    raw = [random.uniform(0.5, 1.5) for _ in range(n - 1)]
    total = sum(raw)
    scaled = [r / total * total_seconds for r in raw]
    # Minimalne opoznienie: 45s, maksymalne: 240s
    clamped = [max(45, min(240, s)) for s in scaled]
    return clamped


# ─── LOGOWANIE ──────────────────────────────────────────────────────────────

def fill_editor(page, content):
    """Proba wypelnienia edytora XenForo (Froala / textarea)."""
    filled = page.evaluate("""(text) => {
        // Metoda 1: ukryta textarea z wartoscia
        const selectors = ['textarea[name="message"]', '.js-value[name="message"]'];
        for (const s of selectors) {
            const el = document.querySelector(s);
            if (el) {
                const nativeInputSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
                nativeInputSetter.call(el, text);
                el.dispatchEvent(new Event('input', {bubbles: true}));
                el.dispatchEvent(new Event('change', {bubbles: true}));
                return 'textarea:' + s;
            }
        }
        // Metoda 2: Froala editor
        const fr = document.querySelector('.fr-element.fr-view, .fr-element');
        if (fr) {
            fr.innerHTML = text.split('\\n').map(l => '<p>' + (l.trim() || '<br>') + '</p>').join('');
            fr.dispatchEvent(new Event('input', {bubbles: true}));
            fr.dispatchEvent(new Event('keyup', {bubbles: true}));
            return 'froala';
        }
        // Metoda 3: contenteditable
        const ce = document.querySelector('[contenteditable="true"]');
        if (ce) {
            ce.innerText = text;
            ce.dispatchEvent(new Event('input', {bubbles: true}));
            return 'contenteditable';
        }
        return null;
    }""", content)
    return filled


def post_reply(page, url, content, label):
    print(f"\n[>>] Odpowiedz: {label[:60]}")
    try:
        page.goto(url, wait_until='domcontentloaded', timeout=20000)
    except PWTimeout:
        print("  [!] Timeout ladowania strony")
        return False
    page.wait_for_timeout(random.randint(1200, 2200))

    # Sprawdz czy zalogowany
    if 'login' in page.url:
        print("  [!] Sesja wygasla!")
        return False

    # Kliknij obszar odpowiedzi zeby aktywowac edytor
    try:
        qr = page.query_selector('.js-quickReply .bbCodeEditor, .p-body-footer .bbCodeEditor')
        if qr:
            qr.click()
            page.wait_for_timeout(600)
    except Exception:
        pass

    filled = fill_editor(page, content)
    if not filled:
        # ostatnia szansa - kliknij "Odpowiedz" i sprobuj ponownie
        try:
            page.click('a[href*="reply"], .button--reply', timeout=3000)
            page.wait_for_timeout(1500)
            filled = fill_editor(page, content)
        except Exception:
            pass

    if not filled:
        print("  [!] Nie udalo sie wypelnic edytora")
        return False

    print(f"  [+] Wypelniono edytor ({filled})")
    page.wait_for_timeout(random.randint(800, 1500))

    # Submit
    try:
        btn = page.query_selector('.js-quickReply button[type="submit"], button.button--primary[type="submit"]')
        if not btn:
            btn = page.query_selector('button[type="submit"]:visible')
        if btn:
            btn.click()
        else:
            page.keyboard.press('Control+Enter')
    except Exception as e:
        print(f"  [!] Blad submitu: {e}")
        return False

    page.wait_for_timeout(random.randint(2500, 4000))

    # Sprawdz wynik
    current = page.url
    if 'error' in current.lower() or 'login' in current:
        print(f"  [!] Blad po wysylce: {current}")
        page.screenshot(path=f"ss_err_{label[:20]}.png")
        return False

    print(f"  [OK] Wyslano post")
    return True


def create_thread(page, forum_url, title, content, label):
    print(f"\n[>>] Nowy watek: {title[:60]}")
    try:
        page.goto(forum_url, wait_until='domcontentloaded', timeout=20000)
    except PWTimeout:
        print("  [!] Timeout")
        return False
    page.wait_for_timeout(random.randint(1200, 2000))

    if 'login' in page.url:
        print("  [!] Sesja wygasla!")
        return False

    # Tytul
    try:
        page.fill('input[name="title"]', title, timeout=5000)
    except Exception as e:
        print(f"  [!] Brak pola tytulu: {e}")
        return False

    page.wait_for_timeout(400)

    # Tresc
    filled = fill_editor(page, content)
    if not filled:
        print("  [!] Nie udalo sie wypelnic tresci")
        return False

    print(f"  [+] Wypelniono tytul i tresc ({filled})")
    page.wait_for_timeout(random.randint(1000, 2000))

    # Submit
    try:
        btn = page.query_selector('button[type="submit"].button--primary, button[type="submit"]:visible')
        if btn:
            btn.click()
        else:
            page.keyboard.press('Control+Enter')
    except Exception as e:
        print(f"  [!] Blad submitu: {e}")
        return False

    page.wait_for_timeout(random.randint(3000, 5000))

    if 'login' in page.url:
        print("  [!] Po submicie przekierowano do logowania")
        return False

    print(f"  [OK] Watek utworzony: {page.url}")
    return True


# ─── MAIN ───────────────────────────────────────────────────────────────────

def main():
    with open('session_cookies.json') as f:
        cookies = json.load(f)

    # Losowa kolejnosc (zachowaj mix sekcji)
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

        # Szybki test sesji
        page.goto('https://pleaks.st/', wait_until='domcontentloaded')
        page.wait_for_timeout(2000)
        if 'login' in page.url or 'Logowanie' not in page.content() and 'logout' not in page.content().lower():
            logged = page.query_selector('a[href*="logout"], a[href*="wyloguj"]') is not None
        else:
            logged = True
        print(f"[*] Sesja aktywna: {logged}")

        if not logged:
            print("[!] Sesja wygasla - potrzebny nowy TOTP!")
            browser.close()
            return

        for i, post in enumerate(posts_copy):
            label = post.get('title', post.get('url', ''))[:50]

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

    # Podsumowanie
    ok_count = sum(1 for r in results if r['ok'])
    print(f"\n{'='*50}")
    print(f"GOTOWE: {ok_count}/{len(results)} postow wyslanych pomyslnie")
    for r in results:
        status = 'OK' if r['ok'] else 'BLAD'
        print(f"  [{status}] {r['label'][:60]}")

    with open('autopost_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
