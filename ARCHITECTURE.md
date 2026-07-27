# Architecture du pipeline AQI

## Stack choisie

| Brique | Choix | Justification |
|---|---|---|
| Source de données | OpenWeatherMap Air Pollution API | fournit AQI + 8 polluants (CO, NO, NO2, O3, SO2, PM2.5, PM10, NH3) pour n'importe quelle coordonnée, sur un plan gratuit suffisant pour ce projet. L'API fonctionne par coordonnées GPS (pas de liste de villes imposée), ce qui permet de suivre 5 villes malgaches (Antananarivo, Toamasina, Antsirabe, Mahajanga, Fianarantsoa) réparties sur l'île. Historique disponible sur ~5 mois glissants avec le plan gratuit utilisé (au-delà du minimum de 3 mois exigé). |
| Langage | Python (requests, pandas, psycopg2) | écosystème simple et largement connu du groupe pour appeler une API REST, manipuler des données tabulaires et écrire dans PostgreSQL. |
| Orchestrateur | GitHub Actions (cron horaire) | tourne indéfiniment sans qu'un membre du groupe n'ait à héberger ou laisser un serveur allumé ; fournit nativement l'historique des exécutions demandé en livrable (onglet *Actions* du repo) ; gratuit pour un repo public/étudiant. |
| Stockage raw/clean | Dossiers versionnés dans le repo Git | simple à auditer, raw/ n'est jamais modifié et sert de sauvegarde, chaque commit automatique montre l'évolution du dataset dans le temps. |
| Data warehouse | PostgreSQL hébergé (Supabase ou Neon, plan gratuit) | accessible 24h/24 depuis n'importe où pour la vérification du livrable et pour la consommation par le cours IA1, sans serveur à administrer. |
| Secrets | GitHub Secrets (`OWM_API_KEY`, `DATABASE_URL`) | jamais dans le code ni dans l'historique Git, injectés uniquement au moment de l'exécution du workflow. |

## Schéma du pipeline

```
OpenWeatherMap Air Pollution API
        │  collecte horaire (current) + backfill (history)
        ▼
GitHub Actions (cron '5 * * * *')
        │
        ├─ scripts/collecte.py  ──────► raw/*.json (jamais modifié)
        │
        ├─ scripts/build_clean.py ────► clean/aqi_clean.csv (reconstruit à chaque run)
        │
        ├─ scripts/validate_clean.py ─► vérifie le contrat de données
        │
        └─ scripts/load_warehouse.py ─► PostgreSQL (dim_ville, dim_temps, fait_qualite_air)
```

## Modélisation dimensionnelle

Schéma en **étoile** (pas de flocon) : les deux dimensions (`dim_ville`, `dim_temps`)
ont une cardinalité faible et ne bénéficient d'aucune normalisation
supplémentaire ; un flocon aurait ajouté de la complexité sans gain réel
pour 5 villes et un axe temporel simple.

- `fait_qualite_air` : uniquement des mesures (aqi + 8 polluants) et des
  clés étrangères vers les dimensions — aucune colonne descriptive.
- `dim_ville` : nom, pays, latitude, longitude — aucune mesure.
- `dim_temps` : date, heure, jour de semaine, weekend, mois, année — aucune mesure.

## Rejouabilité

- `backfill.py` peut être relancé avec n'importe quelle plage de dates
  (`--start`/`--end` ou `--months`) sans dupliquer les fichiers raw.
- `build_clean.py` reconstruit entièrement `clean/aqi_clean.csv` depuis
  `raw/` à chaque exécution : aucune perte possible, `clean/` est
  toujours dérivable à 100 % de `raw/`.
- `load_warehouse.py` utilise `ON CONFLICT DO UPDATE` / `DO NOTHING` sur
  des clés uniques : le réexécuter ne crée jamais de doublons dans le
  warehouse.
