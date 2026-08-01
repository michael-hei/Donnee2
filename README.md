# Pipeline AQI — Documentation du stockage

## Villes suivies

| Ville | Pays | Latitude | Longitude |
|---|---|---|---|
| Antananarivo | Madagascar | -18.8792 | 47.5079 |
| Toamasina | Madagascar | -18.1492 | 49.4023 |
| Antsirabe | Madagascar | -19.8659 | 47.0333 |
| Mahajanga | Madagascar | -15.7167 | 46.3167 |
| Fianarantsoa | Madagascar | -21.4536 | 47.0854 |

(Modifiable dans `config/villes.py` — tous les scripts lisent ce fichier.)

## Colonnes de `clean/aqi_clean.csv`

| Colonne | Description | Unité |
|---|---|---|
| `ville` | Nom de la ville | — |
| `pays` | Pays | — |
| `lat`, `lon` | Coordonnées de la ville | degrés décimaux |
| `timestamp` | Horodatage de la mesure (UTC, ISO 8601) | — |
| `aqi` | Indice de qualité de l'air | échelle OpenWeather 1–5 (1=Good, 2=Fair, 3=Moderate, 4=Poor, 5=Very Poor) — **ce n'est pas l'échelle US AQI 0-500** |
| `co` | Monoxyde de carbone | µg/m³ |
| `no` | Monoxyde d'azote | µg/m³ |
| `no2` | Dioxyde d'azote | µg/m³ |
| `o3` | Ozone | µg/m³ |
| `so2` | Dioxyde de soufre | µg/m³ |
| `pm2_5` | Particules fines ≤ 2.5 µm | µg/m³ |
| `pm10` | Particules fines ≤ 10 µm | µg/m³ |
| `nh3` | Ammoniac | µg/m³ |

Une ligne = une ville + une heure. Fichier trié chronologiquement par
ville, sans doublons (clé `ville` + `timestamp`), validé par
`scripts/validate_clean.py`.

## Schéma du warehouse (étoile)

- **`fait_qualite_air`** (id_ville FK, id_temps FK, aqi, co, no, no2, o3, so2, pm2_5, pm10, nh3)
- **`dim_ville`** (id_ville, nom, pays, latitude, longitude)
- **`dim_temps`** (id_temps, date, heure, jour_semaine, est_weekend, mois, annee)

Voir `scripts/init_warehouse.sql` pour le DDL complet.

## Période couverte

Données du **27 février 2026** au **1er août 2026** (mise à jour continue
via le cron horaire). 3 613 mesures par ville à la dernière exécution de
`validate_clean.py`, soit 18 065 lignes au total sur les 5 villes.

| Ville | Mesures | Première mesure | Dernière mesure |
|---|---|---|---|
| Antananarivo | 3 613 | 2026-02-27 05:00 UTC | en continu |
| Toamasina | 3 613 | 2026-02-27 05:00 UTC | en continu |
| Antsirabe | 3 613 | 2026-02-27 05:00 UTC | en continu |
| Mahajanga | 3 613 | 2026-02-27 05:00 UTC | en continu |
| Fianarantsoa | 3 613 | 2026-02-27 05:00 UTC | en continu |

Ces chiffres évoluent à chaque run ; relancer `scripts/validate_clean.py`
pour les valeurs à jour.

## Trous connus

Les 5 villes ont exactement le même nombre de mesures et les mêmes
coupures — signe qu'il s'agit de pannes du runner GitHub Actions (ou de
l'API) plutôt que d'un souci propre à une ville. Coupures d'environ 1h
autour de minuit UTC, identifiées via `validate_clean.py` :

- 2026-03-01 → 2026-03-02
- 2026-03-04 → 2026-03-05
- 2026-04-06 → 2026-04-07
- 2026-05-11 → 2026-05-12
- 2026-05-19 → 2026-05-20
- 2026-07-10 → 2026-07-11

Aucune ville n'accuse de retard par rapport aux autres à ce jour.

## Connexion à la base (warehouse)

- Moteur : PostgreSQL
- Hébergeur : Supabase / Neon (plan gratuit) — _à compléter avec l'URL réelle du projet_
- Chaîne de connexion : fournie séparément à l'évaluateur (jamais dans
  ce README ni dans Git), stockée en `DATABASE_URL` dans les secrets
  GitHub et dans un `.env` local pour le développement.
- Exemple de requête de vérification :
  ```sql
  select v.nom, count(*) as nb_mesures, min(t.date) as premiere_date, max(t.date) as derniere_date
  from fait_qualite_air f
  join dim_ville v on v.id_ville = f.id_ville
  join dim_temps t on t.id_temps = f.id_temps
  group by v.nom
  order by v.nom;
  ```

## Comment relancer le pipeline en local

```bash
cp .env.example .env   # puis remplir OWM_API_KEY et DATABASE_URL
pip install -r requirements.txt

python scripts/backfill.py --months 12   # une fois, pour l'historique
python scripts/collecte.py               # collecte ponctuelle (current)
python scripts/build_clean.py            # reconstruit clean/aqi_clean.csv
python scripts/validate_clean.py         # vérifie le contrat de données
python scripts/load_warehouse.py         # charge le warehouse
```
