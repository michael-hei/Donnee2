# Rapport de projet — Pipeline AQI

_Template à compléter par le groupe avant le rendu._

## Méthode de travail du groupe

_Ex : réunions hebdomadaires, outil de suivi des tâches utilisé, rythme de commits..._

## Répartition des tâches

| Membre | Rôle / tâches |
|---|---|
| ... | ex : collecte + backfill |
| ... | ex : build_clean + validation |
| ... | ex : warehouse + SQL |
| ... | ex : orchestrateur GitHub Actions |
| ... | ex : documentation + vidéo |

## Difficultés rencontrées et solutions

_Ex : limite de débit de l'API, choix du découpage du backfill en tranches de 30 jours,
gestion des doublons entre current et history, hébergement de la base..._

## Choix techniques justifiés

_Voir ARCHITECTURE.md pour le détail — résumer ici les points discutés en groupe et
les alternatives envisagées (ex : Airflow vs GitHub Actions, SQLite vs PostgreSQL)._

## Cohérence des données

_Comparer : nombre de villes × nombre d'heures couvertes vs nombre de lignes réel
dans fait_qualite_air, et expliquer les écarts (pannes API, début du backfill, etc.)._
