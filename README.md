<p align="center">
  <img src="static/logo.svg" alt="Logo di Grabby" width="112">
</p>

<h1 align="center">Grabby Video Downloader</h1>

<p align="center"><strong>Acchiappa i tuoi video con un clic.</strong><br>
Grabby · incolla, scegli, scarica.</p>

Grabby è una piccola app che gira **solo sul tuo computer** (Mac o PC Windows)
e scarica video da **YouTube** e **Facebook**. Si usa da una pagina web locale:
incolli il link, scegli formato e risoluzione e premi **Scarica**.

- Formati: **MP4**, **WebM** (video) oppure **MP3**, **M4A** (solo audio)
- Risoluzione: dalla migliore disponibile fino a 144p (4K, 2K, 1080p, 720p, …)
- Anteprima del video (titolo, miniatura, durata) con il pulsante **Analizza**
- Barra di avanzamento con velocità e tempo rimanente
- I file finiscono nella cartella **Download**
- Icona da cliccare nel Dock (Mac) o sul Desktop (Windows)
- Sfondo dinamico a tutto schermo, con la copertina del video che stai scaricando

Sotto il cofano usa [yt-dlp](https://github.com/yt-dlp/yt-dlp) per il download
e [ffmpeg](https://ffmpeg.org/) per unire audio/video e convertire i formati.
Python 3.12 viene installato in automatico da [uv](https://docs.astral.sh/uv/),
senza password di amministratore.

> Scarica solo contenuti che hai il diritto di salvare (tuoi, con licenza
> libera o con il permesso dell'autore).

---

## 🍎 Installazione su Mac

### 1. Strumenti necessari (una volta sola)

Apri il **Terminale** (Applicazioni › Utility › Terminale).

Se non hai ancora [Homebrew](https://brew.sh), installalo con:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Poi installa ffmpeg, git e uv:

```bash
brew install ffmpeg git
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Scarica Grabby

```bash
mkdir -p /Users/danielepallotta/Projects
cd /Users/danielepallotta/Projects
git clone https://github.com/dpal80/videodownloader.git
cd videodownloader
```

### 3. Crea l'app Grabby

```bash
./crea-app-mac.sh
```

Lo script crea **Grabby** nella cartella Applicazioni del tuo utente
(`~/Applications`) e la mostra nel Finder: trascinala nel **Dock**.
Da quel momento basta un clic sull'icona: Grabby si accende e apre la pagina
nel browser. Un secondo clic riapre solo la pagina. Al primo avvio ci vuole circa un minuto (scarica Python e le
dipendenze), poi è immediato.

Preferisci il Terminale? Funziona anche:

```bash
cd /Users/danielepallotta/Projects/videodownloader
./avvia.sh
```

Grabby resta acceso finché l'app è aperta: per spegnerlo **esci dall'app**
(Cmd+Q o clic destro sull'icona nel Dock › Esci). Se l'hai avviato da
Terminale, premi `Ctrl + C`.

---

## 🪟 Installazione su PC (Windows 10/11)

### 1. Strumenti necessari (una volta sola)

Apri **PowerShell** (tasto Start, scrivi "PowerShell", Invio) e incolla:

```powershell
winget install Git.Git
winget install Gyan.FFmpeg
winget install astral-sh.uv
```

Poi **chiudi e riapri PowerShell**, così Windows trova i programmi appena
installati.

### 2. Scarica Grabby

```powershell
mkdir $HOME\Projects -Force
cd $HOME\Projects
git clone https://github.com/dpal80/videodownloader.git
cd videodownloader
```

> Senza git: dalla pagina GitHub del progetto premi **Code › Download ZIP**,
> estrai la cartella in `Projects\videodownloader` dentro la tua cartella
> utente e prosegui.

### 3. Crea il collegamento Grabby

Nella cartella del progetto fai doppio clic su **`crea-collegamento-windows.bat`**
(oppure da PowerShell: `.\crea-collegamento-windows.bat`).

Trovi **Grabby** sul Desktop e nel menu Start, con la sua icona. Fai clic
destro › **Aggiungi alla barra delle applicazioni** per averla sempre a
portata di mano.

Con un doppio clic su Grabby si apre una finestra (ridotta a icona) e poi la
pagina nel browser. Al primo avvio ci vuole circa un minuto. **Per spegnere
Grabby chiudi quella finestra.**

Puoi anche avviarlo direttamente con un doppio clic su **`avvia.bat`**.

---

## Avviso legale

Grabby Video Downloader è uno strumento per uso personale e privato.
Usalo solo per scaricare video di cui possiedi i diritti, video con
licenza libera (es. Creative Commons, pubblico dominio) o video per
cui hai ottenuto il permesso dell'autore.

Scaricare contenuti da YouTube o Facebook può violare i loro Termini
di servizio. Non usare Grabby per scaricare, ridistribuire o
pubblicare opere protette da diritto d'autore senza autorizzazione.
Grabby non aggira sistemi DRM e non è affiliato a YouTube, Google,
Facebook o Meta.

L'utente è l'unico responsabile dell'uso che fa del software.
L'analisi completa, **Grabby e il diritto d'autore**, è in
[`static/note-legali.html`](static/note-legali.html) e nell'app alla pagina
http://127.0.0.1:8000/note-legali. Non è consulenza legale.

## Aggiornare Grabby

YouTube e Facebook cambiano spesso: ogni avvio aggiorna già yt-dlp da solo.
Per avere anche le novità di Grabby, dalla cartella del progetto:

```bash
git pull
```

## Impostazioni opzionali

| Variabile      | Default       | A cosa serve                         |
| -------------- | ------------- | ------------------------------------ |
| `DOWNLOAD_DIR` | `~/Downloads` | Cartella dove salvare i file         |
| `PORT`         | `8000`        | Porta della pagina web               |

Esempio su Mac: `DOWNLOAD_DIR=~/Movies PORT=8080 ./avvia.sh`

Esempio su Windows (PowerShell): `$env:PORT=8080; .\avvia.bat`

## Problemi comuni

- **"ffmpeg non trovato"** o **"uv non trovato"**: installali come indicato
  sopra. Su Windows ricordati di chiudere e riaprire la finestra dopo
  l'installazione.
- **Errore su un video che prima funzionava**: riavvia Grabby, che aggiorna
  yt-dlp all'ultima versione.
- **Video Facebook privati o di gruppi chiusi**: non sono scaricabili senza
  login; funzionano i video pubblici.
- **Porta occupata**: avvia con un'altra porta (vedi sopra).
- **Mac: l'app non si apre** ("sviluppatore non identificato"): clic destro
  sull'icona › **Apri** › **Apri**. Serve solo la prima volta.
- **Log**: su Mac l'app scrive in `~/Library/Logs/Grabby.log`.

## Per sviluppatori

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements-dev.txt
.venv/bin/pytest
```

Struttura:

- `app.py`: server Flask (pagina e API `/api/info`, `/api/download`, `/api/progress/<id>`)
- `downloader.py`: logica di download con yt-dlp
- `static/`: la pagina web, il logo, gli sfondi (`sfondi/`) e le note legali
- `icone/`: icone per Mac (PNG 1024px) e Windows (`.ico`)
- `avvia.sh`, `crea-app-mac.sh`: avvio e creazione dell'app su Mac
- `avvia.bat`, `crea-collegamento-windows.bat`: avvio e collegamento su Windows

Il server ascolta solo su `127.0.0.1`, quindi non è raggiungibile da altri
dispositivi della rete.

## 🐳 In alternativa: Grabby in un container Docker

Se hai [Docker Desktop](https://www.docker.com/products/docker-desktop/) non
servono né Python né ffmpeg sul computer: sono tutti dentro il container.

```bash
cd /Users/danielepallotta/Projects/videodownloader
docker compose up -d --build
```

Poi apri **http://127.0.0.1:8000**. Il container si riavvia da solo insieme a
Docker Desktop; per spegnerlo:

```bash
docker compose down
```

- I video finiscono nella cartella **Download** del Mac (per cambiarla:
  `DOWNLOAD_DIR=~/Movies docker compose up -d`).
- La pagina è raggiungibile solo da questo computer (`127.0.0.1`).
- Dal container non si può aprire il Finder, quindi il pulsante
  **Apri cartella** non compare: i file li trovi in Download.
- Per aggiornare yt-dlp ricostruisci l'immagine:
  `docker compose build --no-cache && docker compose up -d`.

Non usare insieme container e app Grabby: occupano la stessa porta 8000.

## Avviso prima di ogni download e registro

Quando premi **Scarica** si apre una finestra che ricorda i casi in cui l'uso
dei video è consentito (quelli in verde nelle [note legali](static/note-legali.html))
e chiede il tuo nome. Continuando, ti assumi la piena responsabilità legale
dell'uso del video.

Ogni download viene annotato in `registro-download.csv` (si apre con Excel),
nella cartella `Documenti/Grabby` (o in `GRABBY_REGISTRO_DIR`): data e ora,
evento, nome, utente del computer, IP, browser, lingua, versione dell'avviso
accettato, link, titolo, formato, esito e file.

## 🌐 Pubblicazione online (non ancora attiva)

Grabby ha una **modalità online** (`GRABBY_MODE=online`) pensata per un server:
il file viene consegnato al browser e poi cancellato, ci sono limiti di
download per IP e il registro tiene i dati per 30 giorni. Configurazione con
HTTPS in [`deploy/`](deploy/), informativa privacy in
[`static/privacy.html`](static/privacy.html).

> **Da non pubblicare prima del parere di un avvocato.** Un servizio online
> che scarica per conto di altri è lo scenario a rischio legale più alto.
> Il riepilogo da portargli è in [`docs/per-avvocato.md`](docs/per-avvocato.md).

| Variabile                     | Default (online) | A cosa serve                               |
| ----------------------------- | ---------------- | ------------------------------------------ |
| `GRABBY_MODE`                 | `local`          | `online` per la versione su server          |
| `GRABBY_PROXY_FIDATI`         | `0`              | Proxy davanti a Grabby (es. Caddy = `1`)    |
| `GRABBY_LIMITE_ORARIO`        | `10`             | Download all'ora per indirizzo IP           |
| `GRABBY_CONSERVAZIONE_GIORNI` | `30`             | Giorni dopo cui il registro si cancella     |
| `GRABBY_REGISTRO_DIR`         | `~/Documents/Grabby` | Cartella del registro                  |
