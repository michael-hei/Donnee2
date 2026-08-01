"""
Usage :
    python scripts/backfill.py --months 12
    python scripts/backfill.py --start 2025-07-01 --end 2026-07-01
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta, timezone

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.villes import VILLES
from scripts.common import get_api_key, call_history, save_raw, polite_sleep

CHUNK_DAYS = 30
DATE_DISPONIBLE_DEPUIS = datetime(2020, 11, 27, tzinfo=timezone.utc)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--months", type=int, default=12,
                    help="Nombre de mois à remonter depuis aujourd'hui (défaut : 12)")
    p.add_argument("--start", type=str, default=None,
                    help="Date de début AAAA-MM-JJ (remplace --months si fourni)")
    p.add_argument("--end", type=str, default=None,
                    help="Date de fin AAAA-MM-JJ (défaut : aujourd'hui)")
    return p.parse_args()


def daterange_chunks(start: datetime, end: datetime, days: int):
    cur = start
    while cur < end:
        nxt = min(cur + timedelta(days=days), end)
        yield cur, nxt
        cur = nxt


def main():
    args = parse_args()
    api_key = get_api_key()

    end = datetime.now(timezone.utc)
    if args.end:
        end = datetime.strptime(args.end, "%Y-%m-%d").replace(tzinfo=timezone.utc)

    if args.start:
        start = datetime.strptime(args.start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        start = end - timedelta(days=30 * args.months)

    start = max(start, DATE_DISPONIBLE_DEPUIS)

    print(f"Backfill de {start.date()} à {end.date()} pour {len(VILLES)} villes")

    total_appels = 0
    erreurs = []

    for ville in VILLES:
        for chunk_start, chunk_end in daterange_chunks(start, end, CHUNK_DAYS):
            try:
                data = call_history(
                    ville["lat"], ville["lon"],
                    int(chunk_start.timestamp()), int(chunk_end.timestamp()),
                    api_key,
                )
                suffix = f"history_{chunk_start.strftime('%Y%m%d')}_{chunk_end.strftime('%Y%m%d')}"
                path = save_raw(ville, data, suffix=suffix)
                n = len(data.get("list", []))
                print(f"[OK] {ville['nom']} {chunk_start.date()}->{chunk_end.date()} "
                      f"({n} points) -> {path.name}")
                total_appels += 1
            except Exception as e:
                print(f"[ERREUR] {ville['nom']} {chunk_start.date()}->{chunk_end.date()}: {e}")
                erreurs.append((ville["nom"], str(chunk_start.date())))
            polite_sleep(1.0)

    print(f"\nTerminé : {total_appels} appels effectués.")
    if erreurs:
        print(f"Échecs ({len(erreurs)}): {erreurs}")
        sys.exit(1)


if __name__ == "__main__":
    main()
