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
| Uwierzytelnianie | Google OAuth zalogowanego uzytkownika; bez service account | Frontend rozpoczyna logowanie nawigacja do FastAPI; callback weryfikuje `state` i wymienia kod po stronie backendu. |
| Tokeny Google | Access token pozostaje po stronie backendu; refresh token jest przechowywany w SQLite w postaci zaszyfrowanej | Przegladarka otrzymuje opaque token sesji w cookie `HttpOnly`; baza przechowuje hash sesji. Lokalna sesja wygasa po 7 dniach, a logout usuwa jej rekord i cookie. Produkcyjne ustawienia `Secure`, CSRF i zarzadzanie kluczem szyfrujacym pozostaja do ustalenia. |
| Wlasciciel integracji | FastAPI komunikuje sie z Google Calendar i lokalnym Ollama | Frontend nie otrzymuje sekretow dostawcow ani tokenow Google; Ollama jest wywolywane z backendu przez lokalny endpoint. |
| Tool calling | Model zwraca ustrukturyzowane wywolania narzedzi; backend waliduje argumenty i sam wykonuje operacje | Model nie dostaje tokenow i nie wykonuje wlasnych HTTP requestow. |
| Zmiana danych | Propozycja zapisana jako `pending_event`; zapis dopiero po osobnym potwierdzeniu w UI | Wywolanie `propose_calendar_event` samo w sobie nie moze zapisac wydarzenia. |
| Dostawca LLM | Lokalny Ollama za interfejsem dostawcy; poczatkowy model `qwen3:latest`, wywolywany przez endpoint zgodny z OpenAI | Brak platnych wywolan OpenAI API; model dziala lokalnie. Jego obsluge tool calling trzeba potwierdzic w implementacji. |
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

Nazwy sa aktualnym lokalnym kontraktem konfiguracji; wartosci sekretow pozostaja w pliku `.env` i nie trafiaja do repozytorium.

**Frontend (`apps/web`, lokalny plik `.env.local`):**

- `NEXT_PUBLIC_API_URL` - publiczny adres lokalnego API, bez sekretow.

**Backend (`apps/api`, lokalny plik `.env`):**

- `GOOGLE_CLIENT_ID` i `GOOGLE_CLIENT_SECRET` - OAuth client.
- `GOOGLE_REDIRECT_URI` - callback FastAPI zarejestrowany w Google Cloud.
- `OLLAMA_BASE_URL` - lokalny endpoint zgodny z OpenAI, domyslnie `http://localhost:11434/v1`.
- `OLLAMA_MODEL` - lokalny model, obecnie `qwen3:latest`.
- `DATABASE_URL` - lokalny URL SQLite.
- `FRONTEND_ORIGIN` - dozwolone lokalne pochodzenie frontendu dla CORS.
- Klucz sesji nie jest przechowywany w `.env`; przegladarka dostaje losowy token, a baza tylko jego hash. Klucz szyfrowania refresh tokenow jest w `.env`.
- Klient OpenAI-compatible moze wymagac pola `api_key`; dla lokalnego Ollama jest to umowna wartosc `ollama`, nie klucz OpenAI ani sekret.

## Bezpieczenstwo i dane

- Nie commitowac `.env`, `.env.local`, pliku SQLite, tokenow, kodow OAuth ani kluczy API.
- Przygotowac przykladowy plik srodowiskowy z pustymi wartosciami dopiero, gdy nazwy konfiguracji beda ustalone.
- Nigdy nie umieszczac sekretow backendu w `NEXT_PUBLIC_*`.
- Refresh token jest dlugotrwalym sekretem i bedzie przechowywany w SQLite w postaci zaszyfrowanej; sposob przechowywania klucza szyfrujacego i ograniczania sesji nadal wymaga ustalenia.
- Nie logowac access/refresh tokenow, kluczy API ani pelnych danych wrazliwych.
- Walidowac kazdy argument narzedzia po stronie backendu; nie ufac samemu schematowi zwroconemu przez model.
- Potwierdzenie musi dotyczyc konkretnego draftu, uzytkownika i oczekujacego statusu. Ponowne potwierdzenie nie moze tworzyc duplikatu.
- Aktualny zakres OAuth pozwala na odczyt wydarzen; przed Etapem 6 trzeba wybrac i skonfigurowac najmniejszy zakres potrzebny do zapisu.

## Otwarte decyzje

Przed implementacja callbacku i zapisem tokenow omowic i zapisac:

1. Produkcyjne ustawienia sesji: `Secure`, ochrona CSRF i konfiguracja domen/originow. Lokalnie cookie jest `HttpOnly`, `SameSite=Lax`, ma 7-dniowy czas zycia, a logout usuwa sesje z bazy.
2. Sposob przechowywania i rotacji klucza szyfrujacego refresh tokeny. SQLite sam w sobie nie szyfruje danych.
3. Model konta Google i sesji jest zaimplementowany; do zaprojektowania pozostaje model draftu i jego przypisanie do uzytkownika.
4. Obecny zakres Google pozwala czytac wydarzenia z posiadanych kalendarzy; zakres do zapisu wydarzen trzeba ustalic przed Etapem 6.
5. Czy i kiedy dodac Alembic do migracji schematu SQLite/PostgreSQL.

## Uzgodnione ograniczenia MVP

Brak wielu kalendarzy, wydarzen cyklicznych, uczestnikow, edycji/usuwania juz utworzonych wydarzen, udostepniania, platnosci i infrastruktury produkcyjnej. Zmiana lub anulowanie pending draftu w UI nie jest edycja wydarzenia zapisanego w Google.
