"""
Fonctions partagées : appel de l'API OpenWeatherMap Air Pollution,
et sauvegarde des fichiers bruts dans raw/.
"""
import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env")

BASE_URL = "http://api.openweathermap.org/data/2.5/air_pollution"

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "raw"
CLEAN_DIR = ROOT / "clean"
RAW_DIR.mkdir(exist_ok=True)
CLEAN_DIR.mkdir(exist_ok=True)


def get_api_key() -> str:
    key = os.environ.get("OWM_API_KEY")
    if not key:
        raise RuntimeError(
            "OWM_API_KEY manquante. Définissez-la en variable d'environnement "
            "(ou dans un fichier .env local, ou en GitHub Secret en CI)."
        )
    return key


def call_current(lat: float, lon: float, api_key: str) -> dict:
    """Appelle l'endpoint 'current' (données en direct)."""
    params = {"lat": lat, "lon": lon, "appid": api_key}
    r = requests.get(BASE_URL, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def call_history(lat: float, lon: float, start_ts: int, end_ts: int, api_key: str) -> dict:
    """Appelle l'endpoint 'history' pour un intervalle [start_ts, end_ts] en UNIX time."""
    params = {
        "lat": lat, "lon": lon,
        "start": start_ts, "end": end_ts,
        "appid": api_key,
    }
    r = requests.get(f"{BASE_URL}/history", params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def save_raw(ville: dict, api_response: dict, suffix: str) -> Path:
    """
    Sauvegarde une réponse API brute dans raw/, jamais modifiée ensuite.
    On enveloppe la réponse avec les métadonnées de la ville pour que
    build_clean.py n'ait jamais à deviner quoi que ce soit depuis le nom
    de fichier : le fichier raw se suffit à lui-même.
    """
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    nom_fichier = f"{ville['nom'].replace(' ', '_')}_{suffix}_{now}.json"
    path = RAW_DIR / nom_fichier

    payload = {
        "ville": ville["nom"],
        "pays": ville["pays"],
        "lat": ville["lat"],
        "lon": ville["lon"],
        "collected_at_utc": now,
        "source": "openweathermap_air_pollution",
        "api_response": api_response,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path


def polite_sleep(seconds: float = 1.0):
    """Respecte le rate limit du plan gratuit (60 appels/minute)."""
    time.sleep(seconds)
