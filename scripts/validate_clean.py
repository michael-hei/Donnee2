"""
Valide clean/aqi_clean.csv par rapport au contrat de données :
- colonnes attendues présentes
- pas de doublons (ville, timestamp)
- trié chronologiquement par ville
- valeurs clés non nulles (ville, timestamp, aqi)
- aqi dans l'échelle attendue (1-5, échelle OpenWeather)

Usage :
    python scripts/validate_clean.py
Sort avec un code non-zéro si une règle est violée (utile en CI).
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
import pandas as pd
from scripts.common import CLEAN_DIR

COLONNES_ATTENDUES = [
    "ville", "pays", "lat", "lon", "timestamp",
    "aqi", "co", "no", "no2", "o3", "so2", "pm2_5", "pm10", "nh3",
]


def main():
    path = CLEAN_DIR / "aqi_clean.csv"
    if not path.exists():
        print(f"[ECHEC] {path} n'existe pas. Lancez build_clean.py d'abord.")
        sys.exit(1)

    df = pd.read_csv(path)
    erreurs = []

    # 1. colonnes
    manquantes = set(COLONNES_ATTENDUES) - set(df.columns)
    if manquantes:
        erreurs.append(f"Colonnes manquantes : {manquantes}")

    # 2. doublons
    doublons = df.duplicated(subset=["ville", "timestamp"]).sum()
    if doublons > 0:
        erreurs.append(f"{doublons} doublons (ville, timestamp) détectés")

    # 3. tri chronologique par ville
    for ville, sous_df in df.groupby("ville"):
        ts = pd.to_datetime(sous_df["timestamp"])
        if not ts.is_monotonic_increasing:
            erreurs.append(f"{ville} : timestamps non triés")

    # 4. valeurs clés non nulles
    for col in ["ville", "timestamp", "aqi"]:
        nb_nuls = df[col].isna().sum()
        if nb_nuls > 0:
            erreurs.append(f"{nb_nuls} valeurs nulles dans la colonne '{col}'")

    # 5. échelle AQI OpenWeather (1 à 5)
    hors_echelle = df[~df["aqi"].between(1, 5)]
    if len(hors_echelle) > 0:
        erreurs.append(f"{len(hors_echelle)} valeurs d'AQI hors de l'échelle 1-5")

    print(f"Lignes totales : {len(df)}")
    print(f"Villes : {sorted(df['ville'].unique().tolist())}")
    print(f"Période couverte : {df['timestamp'].min()} -> {df['timestamp'].max()}")

    if erreurs:
        print("\n[ECHEC] Validation échouée :")
        for e in erreurs:
            print(f"  - {e}")
        sys.exit(1)

    print("\n[OK] clean/aqi_clean.csv est conforme au contrat de données.")


if __name__ == "__main__":
    main()
