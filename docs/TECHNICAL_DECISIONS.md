# Calendar Copilot: decyzje techniczne

Ten dokument przechowuje zatwierdzone wybory oraz kwestie, ktore trzeba rozstrzygnac przed implementacja. Nowa decyzja nie powinna po cichu przeczyc zakresowi MVP z [PROJECT_PLAN.md](PROJECT_PLAN.md).

## Zatwierdzone decyzje

| Obszar | Decyzja | Powod / konsekwencja |
| --- | --- | --- |
| Repozytorium | Monorepo: `apps/web` i `apps/api` | Wspolna historia zmian i prostsze testowanie pelnego flow, przy zachowaniu osobnych zaleznosci aplikacji. |
| Frontend | Next.js App Router, TypeScript, Tailwind CSS | UI, czat i karta potwierdzenia wydarzenia. |
| Backend | Python + FastAPI | Jedno miejsce na logike, walidacje oraz komunikacje z Google i LLM. |
| Baza na start | Lokalny SQLite + SQLAlchemy | Brak osobnego serwera bazy podczas nauki; SQLAlchemy utrzymuje warstwe dostepu do danych odseparowana od routingu. |
| Baza pozniej | PostgreSQL jako mozliwy kolejny krok | Przed migracja trzeba sprawdzic roznice dialektow, migracje i testy na docelowej bazie. |
| Uwierzytelnianie | Google OAuth zalogowanego uzytkownika; bez service account | Uzytkownik udziela dostepu do swojego kalendarza. |
| Wlasciciel integracji | FastAPI komunikuje sie z Google Calendar i OpenAI | Frontend nie otrzymuje sekretow dostawcow ani tokenow Google. |
| Tool calling | Model zwraca ustrukturyzowane wywolania narzedzi; backend waliduje argumenty i sam wykonuje operacje | Model nie dostaje tokenow i nie wykonuje wlasnych HTTP requestow. |
| Zmiana danych | Propozycja zapisana jako `pending_event`; zapis dopiero po osobnym potwierdzeniu w UI | Wywolanie `propose_calendar_event` samo w sobie nie moze zapisac wydarzenia. |
| Dostawca LLM | OpenAI na start, za interfejsem/warstwa dostawcy | Pozwala pozniej podmienic model bez przenoszenia logiki domenowej do kodu konkretnego API. |
| Testy | Vitest, pytest i Playwright; Google/LLM mockowane w testach | Testy automatyczne nie zmieniaja prawdziwego kalendarza i nie wymagaja platnych wywolan. |

## Granice odpowiedzialnosci

- **Next.js:** widoki, stan UI, czat, przegladanie wynikow i jawne potwierdzenie draftu.
- **FastAPI:** endpointy, sesja, walidacja schematow, logika biznesowa, przechowywanie tokenow i draftow, integracje z Google oraz LLM.
- **LLM:** interpretacja wiadomosci i zwracanie odpowiedzi albo jednego z dozwolonych structured tool calli. Nie jest zrodlem autoryzacji ani bezposrednim klientem Google.
- **Google Calendar API:** zewnetrzny system zrodlowy wydarzen; zapis MVP odbywa sie przez `events.insert` dopiero po potwierdzeniu.

Przeplyw zapisu:

1. Uzytkownik prosi o wydarzenie.
2. LLM zwraca `propose_calendar_event` z argumentami.
3. Backend waliduje argumenty i zapisuje propozycje jako oczekujacy draft.
4. UI pokazuje draft uzytkownikowi.
5. Uzytkownik potwierdza; backend sprawdza uprawnienie i status draftu.
6. Backend zapisuje wydarzenie w Google Calendar i oznacza draft jako `created`.

## Zmienne srodowiskowe

Nazwy sa propozycja do potwierdzenia podczas konfiguracji. Dokladny zestaw zalezy od wybranego mechanizmu sesji i szyfrowania tokenow.

**Frontend (`apps/web`, lokalny plik `.env.local`):**

- `NEXT_PUBLIC_API_URL` - publiczny adres lokalnego API, bez sekretow.

**Backend (`apps/api`, lokalny plik `.env`):**

- `GOOGLE_CLIENT_ID` i `GOOGLE_CLIENT_SECRET` - OAuth client.
- `GOOGLE_REDIRECT_URI` - callback FastAPI zarejestrowany w Google Cloud.
- `OPENAI_API_KEY` - klucz do API modelu.
- `OPENAI_MODEL` - identyfikator modelu, jesli konfiguracja dostawcy tego wymaga.
- `DATABASE_URL` - lokalny URL SQLite.
- `FRONTEND_ORIGIN` - dozwolone lokalne pochodzenie frontendu dla CORS.
- Sekret sesji i ewentualny klucz szyfrowania tokenow - dopiero po wyborze konkretnego rozwiazania.

## Bezpieczenstwo i dane

- Nie commitowac `.env`, `.env.local`, pliku SQLite, tokenow, kodow OAuth ani kluczy API.
- Przygotowac przykladowy plik srodowiskowy z pustymi wartosciami dopiero, gdy nazwy konfiguracji beda ustalone.
- Nigdy nie umieszczac sekretow backendu w `NEXT_PUBLIC_*`.
- Refresh token jest dlugotrwalym sekretem: przed Etapem 3 trzeba zdecydowac, jak jest chroniony w bazie oraz jak ograniczyc dostep do sesji.
- Nie logowac access/refresh tokenow, kluczy API ani pelnych danych wrazliwych.
- Walidowac kazdy argument narzedzia po stronie backendu; nie ufac samemu schematowi zwroconemu przez model.
- Potwierdzenie musi dotyczyc konkretnego draftu, uzytkownika i oczekujacego statusu. Ponowne potwierdzenie nie moze tworzyc duplikatu.
- Uzyc najmniejszego zakresu OAuth wystarczajacego do listowania i dodawania wydarzen; zakres potwierdzic z dokumentacja Google podczas Etapu 3.

## Otwarte decyzje

Przed Etapem 3 omowic i zapisac:

1. Mechanizm sesji frontend-backend, a w szczegolnosci cookie `HttpOnly`, `Secure`, `SameSite`, ochrone CSRF oraz lokalne ustawienia dla roznych portow.
2. Szyfrowanie refresh tokenow w spoczynku i miejsce przechowywania klucza. Plik SQLite jest lokalny, ale sam w sobie nie szyfruje danych.
3. Model danych uzytkownika i draftu oraz sposob przypisania tokenow i propozycji do zalogowanego uzytkownika.
4. Dokladne zakresy Google OAuth i wymagane ustawienia ekranu zgody.
5. Czy i kiedy dodac Alembic do migracji schematu SQLite/PostgreSQL.

## Uzgodnione ograniczenia MVP

Brak wielu kalendarzy, wydarzen cyklicznych, uczestnikow, edycji/usuwania juz utworzonych wydarzen, udostepniania, platnosci i infrastruktury produkcyjnej. Zmiana lub anulowanie pending draftu w UI nie jest edycja wydarzenia zapisanego w Google.
