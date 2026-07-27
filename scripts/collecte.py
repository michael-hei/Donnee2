"""
Collecte horaire : appelle l'endpoint 'current' pour chaque ville et
sauvegarde un fichier brut par ville dans raw/.

Usage :
    python scripts/collecte.py

Ce script est fait pour être lancé toutes les heures par l'orchestrateur
(voir .github/workflows/collecte.yml). Il n'écrit jamais dans clean/ ;
c'est le rôle de build_clean.py.
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.villes import VILLES
from scripts.common import get_api_key, call_current, save_raw, polite_sleep


def main():
    api_key = get_api_key()
    erreurs = []

    for ville in VILLES:
        try:
            data = call_current(ville["lat"], ville["lon"], api_key)
            path = save_raw(ville, data, suffix="current")
            print(f"[OK] {ville['nom']} -> {path.name}")
        except Exception as e:
            print(f"[ERREUR] {ville['nom']}: {e}")
            erreurs.append(ville["nom"])
        polite_sleep(1.0)

    if erreurs:
        print(f"\nVilles en échec : {erreurs}")
        # on ne bloque pas le pipeline pour une ville en échec ponctuel,
        # mais on sort en code non-zéro pour que la CI le signale
        sys.exit(1)


if __name__ == "__main__":
    main()
