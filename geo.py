"""Paese, città e provider ricavati dall'indirizzo IP, per il registro.

Usa i database gratuiti di DB-IP (formato .mmdb) salvati sul server: nessun
dato viene inviato a servizi esterni. Se i file non ci sono, i campi restano
vuoti. Per scaricarli: deploy/aggiorna-geoip.sh.
IP Geolocation by DB-IP (https://db-ip.com), licenza CC BY 4.0.
"""
import ipaddress
import os
from functools import lru_cache
from pathlib import Path

GEOIP_DIR = Path(os.environ.get("GRABBY_GEOIP_DIR", Path(__file__).resolve().parent / "geoip"))
CITY_DB = "dbip-city-lite.mmdb"
ASN_DB = "dbip-asn-lite.mmdb"


@lru_cache(maxsize=None)
def _reader(name: str):
    path = GEOIP_DIR / name
    if not path.exists():
        return None
    try:
        import maxminddb
    except ImportError:
        return None
    return maxminddb.open_database(str(path))


def _name(record: dict, key: str) -> str:
    names = (record.get(key) or {}).get("names") or {}
    return names.get("it") or names.get("en") or ""


def lookup(ip: str) -> dict:
    """{"paese", "citta", "provider"}; vuoti per IP privati o senza database."""
    result = {"paese": "", "citta": "", "provider": ""}
    try:
        if not ipaddress.ip_address(ip).is_global:
            return result
    except ValueError:
        return result
    try:
        if city := _reader(CITY_DB):
            record = city.get(ip) or {}
            code = (record.get("country") or {}).get("iso_code", "")
            country = _name(record, "country")
            result["paese"] = f"{country} ({code})" if country and code else country or code
            result["citta"] = _name(record, "city")
        if asn := _reader(ASN_DB):
            record = asn.get(ip) or {}
            org = record.get("autonomous_system_organization", "")
            number = record.get("autonomous_system_number")
            result["provider"] = f"{org} (AS{number})" if org and number else org
    except Exception:  # noqa: BLE001 - un database rovinato non deve fermare i download
        pass
    return result
