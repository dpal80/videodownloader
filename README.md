# Grabby Video Downloader

<img src="static/logo.svg" alt="Logo di Grabby Video Downloader" width="96">

**Grabby Video Downloader**: una piccola app locale per scaricare video da **YouTube** e **Facebook**.

Si usa da una pagina web che gira solo sul tuo Mac: incolli il link, scegli
formato e risoluzione e premi **Scarica**.

- Formati: **MP4**, **WebM** (video) oppure **MP3**, **M4A** (solo audio)
- Risoluzione: dalla migliore disponibile fino a 144p (4K, 2K, 1080p, 720p, …)
- Anteprima del video (titolo, miniatura, durata) con il pulsante **Analizza**
- Barra di avanzamento con velocità e tempo rimanente
- I file finiscono nella cartella **Download** del Mac

Sotto il cofano usa [yt-dlp](https://github.com/yt-dlp/yt-dlp) per il download
e [ffmpeg](https://ffmpeg.org/) per unire audio/video e convertire i formati.

> Scarica solo contenuti che hai il diritto di salvare (tuoi, con licenza
> libera o con il permesso dell'autore).

## Installazione su macOS

### 1. Strumenti necessari (una volta sola)

Se non hai ancora [Homebrew](https://brew.sh), aprilo dal Terminale con:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Poi installa Python, ffmpeg e git:

```bash
brew install python ffmpeg git
```

### 2. Scarica il progetto

```bash
mkdir -p /Users/danielepallotta/Projects
cd /Users/danielepallotta/Projects
git clone https://github.com/dpal80/videodownloader.git
cd videodownloader
```

### 3. Avvia l'app

```bash
./avvia.sh
```

Al primo avvio lo script crea un ambiente Python dedicato (cartella `.venv`) e
installa le dipendenze. Poi apre da solo il browser su
**http://127.0.0.1:8000**. Per fermare l'app premi `Ctrl + C` nel Terminale.

Le volte successive basta:

```bash
cd /Users/danielepallotta/Projects/videodownloader
./avvia.sh
```

Ad ogni avvio lo script aggiorna anche yt-dlp: YouTube e Facebook cambiano
spesso e una versione vecchia smette presto di funzionare.

## Impostazioni opzionali

Si passano come variabili d'ambiente prima del comando:

| Variabile      | Default       | A cosa serve                         |
| -------------- | ------------- | ------------------------------------ |
| `DOWNLOAD_DIR` | `~/Downloads` | Cartella dove salvare i file         |
| `PORT`         | `8000`        | Porta della pagina web               |

Esempio:

```bash
DOWNLOAD_DIR=~/Movies PORT=8080 ./avvia.sh
```

## Problemi comuni

- **"ffmpeg non trovato"**: esegui `brew install ffmpeg`.
- **Errore su un video che prima funzionava**: riavvia con `./avvia.sh`, che
  aggiorna yt-dlp all'ultima versione.
- **Video Facebook privati o di gruppi chiusi**: non sono scaricabili senza
  login; funzionano i video pubblici.
- **Porta occupata**: avvia con un'altra porta, ad esempio `PORT=8080 ./avvia.sh`.

## Per sviluppatori

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements-dev.txt
./.venv/bin/pytest
```

Struttura:

- `app.py`: server Flask (pagina e API `/api/info`, `/api/download`, `/api/progress/<id>`)
- `downloader.py`: logica di download con yt-dlp
- `static/index.html`: la pagina web
- `avvia.sh`: script di avvio per macOS

Il server ascolta solo su `127.0.0.1`, quindi non è raggiungibile da altri
dispositivi della rete.
