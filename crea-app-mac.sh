#!/usr/bin/env bash
# Crea "Grabby.app" in ~/Applications: un doppio clic avvia Grabby e apre la
# pagina nel browser, senza passare dal Terminale.
#
# È un'applet AppleScript "stay open": macOS chiude i processi lanciati da
# un'app quando l'app termina, quindi l'app resta aperta finché Grabby è acceso.
# Esci (Cmd+Q) spegne anche il server.
set -e
cd "$(dirname "$0")"
PROJECT_DIR="$(pwd)"
APP="$HOME/Applications/Grabby.app"
PLIST="$APP/Contents/Info.plist"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

echo "Creo $APP ..."
mkdir -p "$HOME/Applications"
rm -rf "$APP"

# Nota: dopo "cd" serve ";" e non "&&", altrimenti resta viva una subshell
# che tiene aperto l'output di "do shell script" e l'applet si blocca.
cat > "$WORK/grabby.applescript" <<APPLESCRIPT
property projectDir : "$PROJECT_DIR"

on run
	do shell script "cd " & quoted form of projectDir & "; nohup ./avvia.sh >> \"\$HOME/Library/Logs/Grabby.log\" 2>&1 < /dev/null &"
end run

on reopen
	do shell script "open http://127.0.0.1:8000"
end reopen

on quit
	try
		do shell script "lsof -ti tcp:8000 -sTCP:LISTEN | xargs kill"
	end try
	continue quit
end quit
APPLESCRIPT
osacompile -s -o "$APP" "$WORK/grabby.applescript"

# Icona: dal PNG 1024x1024 genera il file .icns con gli strumenti di macOS.
ICONSET="$WORK/Grabby.iconset"
mkdir -p "$ICONSET"
for size in 16 32 128 256 512; do
  sips -z $size $size icone/grabby-1024.png --out "$ICONSET/icon_${size}x${size}.png" >/dev/null
  sips -z $((size * 2)) $((size * 2)) icone/grabby-1024.png --out "$ICONSET/icon_${size}x${size}@2x.png" >/dev/null
done
iconutil -c icns "$ICONSET" -o "$APP/Contents/Resources/applet.icns"
# Senza questi due passaggi macOS mostra l'icona standard delle applet.
rm -f "$APP/Contents/Resources/Assets.car"
/usr/libexec/PlistBuddy -c "Delete :CFBundleIconName" "$PLIST" 2>/dev/null || true

/usr/libexec/PlistBuddy -c "Set :CFBundleName Grabby" "$PLIST"
/usr/libexec/PlistBuddy -c "Add :CFBundleDisplayName string Grabby Video Downloader" "$PLIST" 2>/dev/null \
  || /usr/libexec/PlistBuddy -c "Set :CFBundleDisplayName Grabby Video Downloader" "$PLIST"
/usr/libexec/PlistBuddy -c "Add :CFBundleIdentifier string com.dpal80.grabby" "$PLIST" 2>/dev/null \
  || /usr/libexec/PlistBuddy -c "Set :CFBundleIdentifier com.dpal80.grabby" "$PLIST"

# Ri-firma ad hoc dopo le modifiche al bundle.
codesign --force --deep -s - "$APP"
touch "$APP"

echo "Fatto! Trovi Grabby in Applicazioni (cartella Inizio > Applicazioni)."
echo "Trascinalo nel Dock per averlo sempre a portata di clic. Esci (Cmd+Q) spegne Grabby."
open -R "$APP"
