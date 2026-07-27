"""
Reconstruit intégralement clean/aqi_clean.csv à partir de tous les
fichiers présents dans raw/. Ne modifie jamais raw/.

Usage :
    python scripts/build_clean.py
"""
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

sys.path.append(str(Path(__file__).resolve().parent.parent))
import pandas as pd
from scripts.common import RAW_DIR, CLEAN_DIR

COLONNES = [
    "ville", "pays", "lat", "lon", "timestamp",
    "aqi", "co", "no", "no2", "o3", "so2", "pm2_5", "pm10", "nh3",
]


def parse_raw_file(path: Path) -> list[dict]:
    """Un fichier raw peut contenir un seul point (current) ou plusieurs
    (history) : dans les deux cas c'est une liste dans api_response.list"""
    with open(path, encoding="utf-8") as f:
        payload = json.load(f)

    rows = []
    api_resp = payload.get("api_response", {})
    for point in api_resp.get("list", []):
        components = point.get("components", {})
        rows.append({
            "ville": payload["ville"],
            "pays": payload["pays"],
            "lat": payload["lat"],
            "lon": payload["lon"],
            "timestamp": datetime.fromtimestamp(point["dt"], tz=timezone.utc).isoformat(),
            "aqi": point.get("main", {}).get("aqi"),
            "co": components.get("co"),
            "no": components.get("no"),
            "no2": components.get("no2"),
            "o3": components.get("o3"),
            "so2": components.get("so2"),
            "pm2_5": components.get("pm2_5"),
            "pm10": components.get("pm10"),
            "nh3": components.get("nh3"),
        })
    return rows


def main():
    fichiers = sorted(RAW_DIR.glob("*.json"))
    if not fichiers:
        print("Aucun fichier dans raw/. Lancez d'abord collecte.py ou backfill.py.")
        sys.exit(1)

    toutes_les_lignes = []
    fichiers_en_erreur = []

    for path in fichiers:
        try:
            toutes_les_lignes.extend(parse_raw_file(path))
        except Exception as e:
            fichiers_en_erreur.append((path.name, str(e)))

    if fichiers_en_erreur:
        print(f"Fichiers raw illisibles ignorés : {fichiers_en_erreur}")

    df = pd.DataFrame(toutes_les_lignes, columns=COLONNES)

    avant = len(df)
    # Déduplication stricte : même ville + même heure = une seule ligne.
    # On garde la dernière occurrence (utile si une ville a été recollectée
    # deux fois pour la même heure, ex : current + history qui se recoupent).
    df = df.drop_duplicates(subset=["ville", "timestamp"], keep="last")
    apres = len(df)

    df = df.sort_values(["ville", "timestamp"]).reset_index(drop=True)

    out_path = CLEAN_DIR / "aqi_clean.csv"
    df.to_csv(out_path, index=False)

    print(f"clean/aqi_clean.csv reconstruit : {apres} lignes "
          f"({avant - apres} doublons supprimés).")
    print(df.groupby("ville")["timestamp"].agg(["min", "max", "count"]))


if __name__ == "__main__":
    main()
