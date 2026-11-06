# Calendar Copilot: plan projektu

## Cel

Zbudowac aplikacje do przegladania wydarzen z Google Calendar i tworzenia propozycji wydarzen na podstawie jezyka naturalnego. Projekt sluzy nauce pelnego przeplywu: UI, API, OAuth, walidacji, tool callingu i testow.

## MVP

Uzytkownik moze:

1. Zalogowac sie przez Google jako uzytkownik.
2. Przegladac wydarzenia z wybranego zakresu dat.
3. Zapytac asystenta o plan lub dostepnosc.
4. Poprosic o propozycje wydarzenia.
5. Zatwierdzic propozycje w UI, zanim backend zapisze ja w Google Calendar.

Jedynymi narzedziami modelu w MVP sa:

- `get_calendar_events` - odczyt wydarzen w zakresie dat.
- `propose_calendar_event` - utworzenie propozycji, bez zapisu wydarzenia do Google.

Zapis wydarzenia jest osobna, jawnie potwierdzana operacja backendu. Model nie otrzymuje tokenow Google i nie wykonuje samodzielnych zapytan HTTP.

## Poza zakresem MVP

- Edycja lub usuwanie wydarzen juz zapisanych w kalendarzu.
- Wiele kalendarzy, wydarzenia cykliczne i zapraszanie uczestnikow.
- Udostepnianie kalendarza, platnosci i funkcje produkcyjne, takie jak monitoring czy CDN.
- Automatyczne zapisywanie propozycji bez potwierdzenia uzytkownika.

Edycja lub anulowanie oczekujacej propozycji w UI nie oznacza edycji wydarzenia w Google Calendar.

## Zasady pracy

- Pracujemy etapami i zadaniami na okolo 30-60 minut.
- Nie rozpoczynamy kolejnego etapu, dopoki uzytkowniczka nie potwierdzi, ze poprzedni dziala i rozumie jego najwazniejsze decyzje.
- Przy bledzie najpierw diagnozujemy objaw i przyczyne; poprawke uzytkowniczka implementuje samodzielnie z naprowadzaniem.
- Po kazdym zadaniu omawiamy, co zostalo zrobione i co bylo zaskakujace.
- Asystent nie generuje za uzytkowniczke kompletnej aplikacji ani pelnych implementacji. Domyslnie podaje wskazowke lub pseudokod.
- Robimy male, tematyczne commity po dzialajacych fragmentach.

## Etapy i kryteria ukonczenia

### Etap 0: Plan i setup

**Status:** decyzje architektoniczne zatwierdzone; konfiguracja projektu bedzie realizowana wraz z Etapem 1.

**Zakres:** struktura monorepo, stos technologiczny, zmienne srodowiskowe, zasady Git i zakres MVP.

**Kryterium:** uzytkowniczka akceptuje kierunek. Uzgodnione wybory zapisane sa w [TECHNICAL_DECISIONS.md](TECHNICAL_DECISIONS.md).

### Etap 1: Szkielet Next.js

**Cel:** uruchomic frontend i poznac podstawowa strukture Next.js App Router.

**Zadania:** utworzyc `apps/web` z TypeScript, Tailwind CSS i ESLint; dodac prosty layout i strone z placeholderem czatu; skonfigurowac Prettier; uruchomic aplikacje lokalnie.

**Kryteria:** strona glowna dziala lokalnie, formatowanie i lint przechodza, nie ma sekretow w kodzie frontendu. Pierwszy commit projektu po zakonczeniu etapu.

### Etap 2: Szkielet FastAPI

**Cel:** uruchomic osobne API i zrozumiec granice miedzy routingiem a logika biznesowa.

**Zadania:** utworzyc `apps/api` i wirtualne srodowisko; dodac `GET /health`; skonfigurowac CORS dla lokalnego frontendu; przygotowac miejsca na routing, services, schemas i config.

**Kryteria:** API uruchamia sie lokalnie, health check zwraca sukces, frontend moze wykonac probne zapytanie, a zaleznosci sa odseparowane od frontendu.

### Etap 3: Google OAuth 2.0

**Cel:** uwierzytelnic uzytkownika Google i bezpiecznie obsluzyc jego tokeny.

**Zadania:** utworzyc projekt w Google Cloud, wlaczyc Calendar API, skonfigurowac ekran zgody i OAuth Client ID; przejsc flow frontend -> FastAPI -> Google -> callback; zdecydowac o sesji i ochronie refresh tokena; zapisac tokeny po stronie backendu.

**Kryteria:** uzytkowniczka moze zalogowac sie na wlasne konto; tokeny nie trafiaja do przegladarki, logow ani repozytorium; wyjasniona jest roznica miedzy access i refresh tokenem. Nie uzywac service account.

### Etap 4: Odczyt kalendarza bez AI

**Cel:** sprawdzic integracje z Google Calendar niezaleznie od LLM.

**Zadania:** dodac endpoint pobierajacy wydarzenia w zakresie; pokazac wybrany tydzien w UI; ustalic obsluge strefy czasowej; obsluzyc brak autoryzacji, wygasle tokeny i bledy Google.

**Kryteria:** reczny flow logowania i odczytu dziala dla zakresu dat, a bledy sa pokazane w zrozumialy sposob.

### Etap 5: Tool calling - odczyt

**Cel:** polaczyc wiadomosc uzytkownika z bezpiecznym odczytem kalendarza przez tool calling.

**Zadania:** zdefiniowac `get_calendar_events` z `timeMin`, `timeMax` i opcjonalnym `query`; dodac `/api/chat`; zaimplementowac petle model -> tool call -> walidacja i wykonanie w backendzie -> wynik -> odpowiedz modelu; logowac wywolania bez sekretow.

**Kryteria:** pytanie o plan uruchamia narzedzie, backend waliduje argumenty, a model formuluje odpowiedz na podstawie wyniku. Niepoprawne argumenty i bledy integracji sa obslugiwane.

### Etap 6: Tool calling - propozycja wydarzenia

**Cel:** przygotowac bezpieczny przeplyw od propozycji do jawnego potwierdzenia zapisu.

**Zadania:** zdefiniowac `propose_calendar_event` dla tytulu, startu, konca i opcjonalnego opisu/lokalizacji; walidowac dane i zapisac `pending_event`; pokazac karte propozycji z akcjami Dodaj, Zmien (tylko draft) i Anuluj; po potwierdzeniu wywolac Google `events.insert`; oznaczyc draft jako `created`.

**Kryteria:** samo wywolanie toola nie zapisuje wydarzenia; tylko potwierdzenie uprawnionego uzytkownika zapisuje oczekujacy draft; ponowione lub nieaktualne potwierdzenie nie tworzy duplikatu.

### Etap 7: Testy i jakosc

**Cel:** sprawdzic reguly biznesowe bez uzywania prawdziwych uslug zewnetrznych.

**Zadania:** dodac testy pytest dla walidacji dat, mapowania tool calli i bledow; test integracyjny `/api/chat` z mockami LLM i Google; testy Vitest dla odpowiednich zachowan UI; test E2E Playwright dla pytania o plan -> propozycji -> potwierdzenia -> widoku wydarzenia.

**Kryteria:** automatyczne testy nie lacza sie z prawdziwym Google Calendar ani platnym API LLM; istotne scenariusze MVP sa pokryte.

### Etap 8: Dokumentacja portfolio

**Cel:** przygotowac repozytorium do prezentacji i odtworzenia lokalnego uruchomienia.

**Zadania:** rozbudowac glowny README o opis, stack, diagram architektury i instrukcje uruchomienia; opisac "How tool calling works in this app", decyzje technologiczne i ograniczenia MVP; dodac zrzuty ekranu lub krotkie demo.

**Kryteria:** nowa osoba moze zrozumiec architekture i uruchomic projekt na podstawie dokumentacji bez dostepu do sekretow wlascicielki.

## Git i sekrety

- Glowna galaz to `main`; branch protection nie jest wymagany na start.
- Pierwszy commit po Etapie 1, pozniej male commity po dzialajacych zadaniach. Przyklady: `chore: initialize web app`, `feat(api): add health endpoint`.
- Pliki `.env`, `.env.*` (poza przykladowymi szablonami), pliki SQLite, tokeny i lokalne artefakty nie moga trafia do Git.
- Sekrety backendu nigdy nie moga miec prefiksu `NEXT_PUBLIC_`.
