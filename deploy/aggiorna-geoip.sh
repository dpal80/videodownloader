#!/usr/bin/env bash
# Scarica (o aggiorna) i database gratuiti di DB-IP usati dal registro per
# ricavare paese, città e provider dall'indirizzo IP. Escono ogni mese:
# conviene rilanciarlo una volta al mese, per esempio con cron.
#   IP Geolocation by DB-IP (https://db-ip.com), licenza CC BY 4.0.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p geoip

month_ago() {  # GNU date (Linux) oppure BSD date (Mac)
  date -d "-$1 month" +%Y-%m 2>/dev/null || date -v-"$1"m +%Y-%m
}

for db in city asn; do
  ok=""
  # Il file del mese esce nei primi giorni: se non c'è ancora, prende quello precedente.
  for month in "$(month_ago 0)" "$(month_ago 1)"; do
    url="https://download.db-ip.com/free/dbip-$db-lite-$month.mmdb.gz"
    if curl -fsSL "$url" -o "geoip/dbip-$db-lite.mmdb.gz.tmp"; then
      gunzip -c "geoip/dbip-$db-lite.mmdb.gz.tmp" > "geoip/dbip-$db-lite.mmdb.tmp"
      mv "geoip/dbip-$db-lite.mmdb.tmp" "geoip/dbip-$db-lite.mmdb"
      rm -f "geoip/dbip-$db-lite.mmdb.gz.tmp"
      echo "Aggiornato geoip/dbip-$db-lite.mmdb ($month)"
      ok=1
      break
    fi
  done
  rm -f "geoip/dbip-$db-lite.mmdb.gz.tmp"
  [ -n "$ok" ] || { echo "Non riesco a scaricare il database $db di DB-IP" >&2; exit 1; }
done
echo "Fatto. Riavvia Grabby per usare i nuovi file: docker compose -f compose.online.yaml restart grabby"
