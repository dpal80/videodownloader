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
nel browser. Al primo avvio ci vuole circa un minuto (scarica Python e le
dipendenze), poi è immediato.

Preferisci il Terminale? Funziona anche:

```bash
cd /Users/danielepallotta/Projects/videodownloader
./avvia.sh
```

Grabby resta acceso in sottofondo fino al riavvio del Mac. Per spegnerlo prima:

```bash
lsof -ti tcp:8000 | xargs kill
```

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
- `static/`: la pagina web e il logo
- `icone/`: icone per Mac (PNG 1024px) e Windows (`.ico`)
- `avvia.sh`, `crea-app-mac.sh`: avvio e creazione dell'app su Mac
- `avvia.bat`, `crea-collegamento-windows.bat`: avvio e collegamento su Windows

Il server ascolta solo su `127.0.0.1`, quindi non è raggiungibile da altri
dispositivi della rete.
