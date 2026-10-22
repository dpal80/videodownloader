@echo off
rem Avvia Grabby Video Downloader su Windows: crea l'ambiente Python al primo
rem avvio, aggiorna yt-dlp e apre la pagina nel browser.
setlocal
cd /d "%~dp0"
title Grabby Video Downloader
if not defined PORT set "PORT=8000"

rem Se Grabby e' gia' acceso, apre solo la pagina.
curl -fs -o nul http://127.0.0.1:%PORT%/api/options >nul 2>nul
if not errorlevel 1 (
  start "" http://127.0.0.1:%PORT%
  exit /b 0
)

where ffmpeg >nul 2>nul
if errorlevel 1 (
  echo ffmpeg non trovato. Installalo con:  winget install Gyan.FFmpeg
  echo Poi chiudi e riapri questa finestra.
  pause
  exit /b 1
)

set "UV="
where uv >nul 2>nul
if not errorlevel 1 set "UV=uv"
if not defined UV if exist "%USERPROFILE%\.local\bin\uv.exe" set "UV=%USERPROFILE%\.local\bin\uv.exe"
if not defined UV (
  echo uv non trovato. Installalo con:  winget install astral-sh.uv
  echo Poi chiudi e riapri questa finestra.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Primo avvio: creo l'ambiente Python...
  "%UV%" venv --python 3.12 .venv
  if errorlevel 1 goto errore
)
rem yt-dlp va aggiornato spesso: YouTube e Facebook cambiano di frequente.
"%UV%" pip install -q --python .venv\Scripts\python.exe --upgrade -r requirements.txt
if errorlevel 1 goto errore

start "" /b cmd /c "timeout /t 3 /nobreak >nul & start http://127.0.0.1:%PORT%"
echo Per spegnere Grabby chiudi questa finestra.
.venv\Scripts\python.exe app.py
exit /b 0

:errore
echo Qualcosa e' andato storto: controlla i messaggi qui sopra.
pause
exit /b 1
