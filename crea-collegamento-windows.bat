@echo off
rem Crea il collegamento "Grabby" sul Desktop e nel menu Start, con l'icona.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$sh = New-Object -ComObject WScript.Shell;" ^
  "foreach ($dir in @([Environment]::GetFolderPath('Desktop'), [Environment]::GetFolderPath('Programs'))) {" ^
  "  $lnk = $sh.CreateShortcut((Join-Path $dir 'Grabby.lnk'));" ^
  "  $lnk.TargetPath = Join-Path '%~dp0' 'avvia.bat';" ^
  "  $lnk.WorkingDirectory = '%~dp0';" ^
  "  $lnk.IconLocation = Join-Path '%~dp0' 'icone\grabby.ico';" ^
  "  $lnk.WindowStyle = 7;" ^
  "  $lnk.Description = 'Grabby Video Downloader';" ^
  "  $lnk.Save() }"
if errorlevel 1 (
  echo Non sono riuscito a creare il collegamento.
) else (
  echo Fatto! Trovi Grabby sul Desktop e nel menu Start.
)
pause
