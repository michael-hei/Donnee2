"""
Charge clean/aqi_clean.csv dans le data warehouse PostgreSQL, en
respectant le schéma en étoile (dim_ville, dim_temps, fait_qualite_air).

Rejouable / idempotent : chaque insertion utilise ON CONFLICT DO NOTHING
ou DO UPDATE, donc relancer ce script après une nouvelle collecte ne
duplique jamais rien.

Variable d'environnement requise :
    DATABASE_URL = postgresql://user:password@host:port/dbname

Usage :
    python scripts/load_warehouse.py
"""
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from scripts.common import CLEAN_DIR

SQL_INIT_PATH = Path(__file__).resolve().parent / "init_warehouse.sql"


def get_connection():
    """Lecture forcée du .env pour éviter les conflits de variables d'environnement"""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    dsn = None

    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("DATABASE_URL="):
                    dsn = line.split("=", 1)[1].strip()
                    break

    if not dsn:
        # fallback : variable d'environnement classique (pour GitHub Actions)
        dsn = os.environ.get("DATABASE_URL")

    if not dsn:
        raise RuntimeError("DATABASE_URL manquante (postgresql://user:pass@host:port/db)")

    return psycopg2.connect(dsn)


def init_schema(conn):
    with open(SQL_INIT_PATH, encoding="utf-8") as f:
        sql = f.read()
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def load_dim_ville(conn, df: pd.DataFrame) -> dict:
    villes = df[["ville", "pays", "lat", "lon"]].drop_duplicates()
    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO dim_ville (nom, pays, latitude, longitude)
            VALUES %s
            ON CONFLICT (nom, pays) DO UPDATE
              SET latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude
            """,
            villes[["ville", "pays", "lat", "lon"]].values.tolist(),
        )
    conn.commit()

    with conn.cursor() as cur:
        cur.execute("SELECT id_ville, nom, pays FROM dim_ville")
        rows = cur.fetchall()
    return {(nom, pays): id_ville for id_ville, nom, pays in rows}


def load_dim_temps(conn, df: pd.DataFrame) -> dict:
    ts = pd.to_datetime(df["timestamp"], utc=True).drop_duplicates()
    lignes = []
    for t in ts:
        lignes.append((
            t.date(),
            t.hour,
            t.weekday(),          # 0 = lundi
            t.weekday() >= 5,     # samedi/dimanche
            t.month,
            t.year,
        ))

    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO dim_temps (date, heure, jour_semaine, est_weekend, mois, annee)
            VALUES %s
            ON CONFLICT (date, heure) DO NOTHING
            """,
            lignes,
        )
    conn.commit()

    with conn.cursor() as cur:
        cur.execute("SELECT id_temps, date, heure FROM dim_temps")
        rows = cur.fetchall()
    return {(str(date), heure): id_temps for id_temps, date, heure in rows}


def load_fait(conn, df: pd.DataFrame, ville_ids: dict, temps_ids: dict):
    # dict garde la DERNIÈRE valeur rencontrée pour une paire (id_ville, id_temps)
    lignes_par_cle = {}
    for _, row in df.iterrows():
        t = pd.to_datetime(row["timestamp"], utc=True)
        id_ville = ville_ids[(row["ville"], row["pays"])]
        id_temps = temps_ids[(str(t.date()), t.hour)]
        cle = (id_ville, id_temps)
        lignes_par_cle[cle] = (
            id_ville, id_temps, row["aqi"], row["co"], row["no"], row["no2"],
            row["o3"], row["so2"], row["pm2_5"], row["pm10"], row["nh3"],
        )

    lignes = list(lignes_par_cle.values())

    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO fait_qualite_air
              (id_ville, id_temps, aqi, co, no, no2, o3, so2, pm2_5, pm10, nh3)
            VALUES %s
            ON CONFLICT (id_ville, id_temps) DO UPDATE SET
              aqi = EXCLUDED.aqi, co = EXCLUDED.co, no = EXCLUDED.no,
              no2 = EXCLUDED.no2, o3 = EXCLUDED.o3, so2 = EXCLUDED.so2,
              pm2_5 = EXCLUDED.pm2_5, pm10 = EXCLUDED.pm10, nh3 = EXCLUDED.nh3
            """,
            lignes,
        )
    conn.commit()


def main():
    path = CLEAN_DIR / "aqi_clean.csv"
    if not path.exists():
        print(f"{path} introuvable. Lancez build_clean.py d'abord.")
        sys.exit(1)

    df = pd.read_csv(path)
    conn = get_connection()

    try:
        init_schema(conn)
        ville_ids = load_dim_ville(conn, df)
        temps_ids = load_dim_temps(conn, df)
        load_fait(conn, df, ville_ids, temps_ids)

        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM fait_qualite_air")
            total = cur.fetchone()[0]
        print(f"Warehouse chargé : {total} lignes dans fait_qualite_air, "
              f"{len(ville_ids)} villes, {len(temps_ids)} points temporels.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()