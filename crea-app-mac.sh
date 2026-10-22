#!/usr/bin/env bash
# Crea "Grabby.app" in ~/Applications: un doppio clic avvia Grabby e apre la
# pagina nel browser, senza passare dal Terminale.
set -e
cd "$(dirname "$0")"
PROJECT_DIR="$(pwd)"
APP="$HOME/Applications/Grabby.app"

echo "Creo $APP ..."
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"

cat > "$APP/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key><string>Grabby</string>
  <key>CFBundleDisplayName</key><string>Grabby Video Downloader</string>
  <key>CFBundleIdentifier</key><string>com.dpal80.grabby</string>
  <key>CFBundleExecutable</key><string>Grabby</string>
  <key>CFBundleIconFile</key><string>Grabby</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleShortVersionString</key><string>1.0</string>
</dict>
</plist>
PLIST

cat > "$APP/Contents/MacOS/Grabby" <<LAUNCHER
#!/usr/bin/env bash
mkdir -p "\$HOME/Library/Logs"
cd "$PROJECT_DIR" && nohup ./avvia.sh >> "\$HOME/Library/Logs/Grabby.log" 2>&1 &
LAUNCHER
chmod +x "$APP/Contents/MacOS/Grabby"

# Icona: dal PNG 1024x1024 genera il file .icns con gli strumenti di macOS.
ICONSET="$(mktemp -d)/Grabby.iconset"
mkdir -p "$ICONSET"
for size in 16 32 128 256 512; do
  sips -z $size $size icone/grabby-1024.png --out "$ICONSET/icon_${size}x${size}.png" >/dev/null
  sips -z $((size * 2)) $((size * 2)) icone/grabby-1024.png --out "$ICONSET/icon_${size}x${size}@2x.png" >/dev/null
done
iconutil -c icns "$ICONSET" -o "$APP/Contents/Resources/Grabby.icns"
rm -rf "$(dirname "$ICONSET")"
touch "$APP"

echo "Fatto! Trovi Grabby in Applicazioni (cartella Inizio > Applicazioni)."
echo "Trascinalo nel Dock per averlo sempre a portata di clic."
open -R "$APP"
