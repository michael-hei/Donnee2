# Guide complet — De zéro au livrable final

Ce guide suit l'ordre exact dans lequel exécuter les étapes. Cochez au
fur et à mesure. Chaque étape indique **l'outil utilisé** et **pourquoi**,
et renvoie à la consigne du sujet qu'elle satisfait.

---

## Étape 0 — Ce que vous avez déjà

- [x] Compte OpenWeatherMap créé, plan **Free** actif
- [x] Clé API testée et fonctionnelle (⚠️ si vous avez utilisé la clé collée
      dans le chat plus tôt, régénérez-la avant d'aller plus loin —
      Clés API → supprimer l'ancienne → en créer une nouvelle)
- [x] Projet complet préparé (scripts, workflows, docs) — dans le zip fourni
- [x] 5 villes malgaches choisies : Antananarivo, Toamasina, Antsirabe,
      Mahajanga, Fianarantsoa

---

## Étape 1 — Créer le dépôt Git (outil : GitHub)

*Consigne : "Dépôt Git complet : tout le code, commits réguliers des 5 membres"*

1. Un membre du groupe crée un nouveau repo sur https://github.com/new
   - Nom : par exemple `aqi-pipeline-madagascar`
   - Visibilité : **Public** (obligatoire — un repo privé inaccessible au
     correcteur = livrable invérifiable = zéro)
2. Ajouter les 4 autres membres comme collaborateurs :
   **Settings → Collaborators → Add people**
3. Décompresser le zip fourni, puis dans le dossier :
   ```bash
   git init
   git add .
   git commit -m "Structure initiale du projet"
   git branch -M main
   git remote add origin https://github.com/VOTRE_ORG/aqi-pipeline-madagascar.git
   git push -u origin main
   ```
4. Chaque membre clone ensuite le repo chez lui :
   ```bash
   git clone https://github.com/VOTRE_ORG/aqi-pipeline-madagascar.git
   ```

**Pourquoi GitHub** : hébergement de code gratuit, standard académique,
et permet d'utiliser GitHub Actions comme orchestrateur (voir étape 5)
sans changer d'outil.

---

## Étape 2 — Créer la base de données PostgreSQL (outil : Supabase, gratuit)

*Consigne : "DATA WAREHOUSE (base de données)" + "infos de connexion à la base"*

1. Aller sur https://supabase.com et cliquer **Start your project**
2. Se connecter avec GitHub (le plus rapide)
3. **New project** :
   - Name : `aqi-warehouse`
   - Database Password : générez-en un solide et **notez-le** (vous en
     aurez besoin juste après, il n'est affiché qu'une fois)
   - Region : choisissez la plus proche (Europe si dispo)
   - Plan : **Free**
4. Attendre ~2 minutes que le projet se provisionne
5. Récupérer la chaîne de connexion :
   **Project Settings (icône engrenage) → Database → Connection string → URI**
   Elle ressemble à :
   ```
   postgresql://postgres:[VOTRE-MOT-DE-PASSE]@db.xxxxxxxxxxxx.supabase.co:5432/postgres
   ```
   Remplacez `[VOTRE-MOT-DE-PASSE]` par le mot de passe noté à l'étape 3.

**Pourquoi Supabase plutôt que SQLite local** : SQLite ne serait pas
accessible par le correcteur ni par le cours IA1 depuis l'extérieur —
un des cas explicites de "livrable invérifiable = zéro". Supabase donne
une base Postgres accessible 24h/24 depuis n'importe où, gratuitement.

*(Alternative équivalente : https://neon.tech, même principe si vous préférez.)*

---

## Étape 3 — Configurer les secrets (outil : GitHub Secrets)

*Consigne : "Clé API en secret (jamais dans le code ni dans l'historique Git)"*

Dans votre repo GitHub : **Settings → Secrets and variables → Actions
→ New repository secret**, créez ces deux secrets :

| Nom du secret | Valeur |
|---|---|
| `OWM_API_KEY` | votre clé OpenWeatherMap (régénérée si besoin) |
| `DATABASE_URL` | l'URI Supabase complète de l'étape 2 |

Ces secrets seront injectés automatiquement dans les workflows
(`.github/workflows/*.yml`) sans jamais apparaître dans le code.

**En local**, pour tester avant de pousser sur GitHub :
```bash
cp .env.example .env
```
Puis éditez `.env` :
```
OWM_API_KEY=votre_cle_ici
DATABASE_URL=postgresql://postgres:motdepasse@db.xxxxx.supabase.co:5432/postgres
```
`.env` est déjà dans `.gitignore` — il ne sera jamais committé.

---

## Étape 4 — Tester en local avant d'automatiser (outil : Python)

*Objectif : vérifier que tout fonctionne avant de compter sur le cron*

```bash
pip install -r requirements.txt --break-system-packages   # ou dans un venv

# 1. Backfill historique (récupère tout ce que l'API accepte, ~5 mois)
python scripts/backfill.py --months 5

# 2. Reconstruire clean/ depuis raw/
python scripts/build_clean.py

# 3. Valider le contrat de données
python scripts/validate_clean.py

# 4. Charger le warehouse
python scripts/load_warehouse.py
```

Si `validate_clean.py` affiche `[OK]`, le contrat de données est respecté.
Si `load_warehouse.py` affiche un nombre de lignes chargées, la base est prête.

**Vérification rapide dans Supabase** : Table Editor → vous devez voir
`dim_ville` (5 lignes), `dim_temps` (des centaines/milliers de lignes),
`fait_qualite_air` (≈ 5 villes × nombre d'heures couvertes).

---

## Étape 5 — Committer et pousser (déclenche l'automatisation)

```bash
git add .
git commit -m "Backfill initial + premier chargement du warehouse"
git push
```

**Pourquoi committer raw/ et clean/** : la consigne l'exige explicitement
("Backfill ... dans raw/", "clean/ : votre fichier CSV unique") — ce
sont des livrables versionnés, pas juste des fichiers locaux.

---

## Étape 6 — Vérifier que l'orchestrateur tourne (outil : GitHub Actions)

*Consigne : "Preuve du pipeline déployé et automatique ... plusieurs runs
réussis sur au moins 5 jours différents"*

1. Dans le repo → onglet **Actions**
2. Vous devez voir le workflow **collecte-aqi-horaire** se déclencher
   automatiquement toutes les heures (`cron: '5 * * * *'`)
3. Cliquez sur un run pour voir le détail : collecte → build_clean →
   validation → chargement warehouse → commit
4. Si un run échoue (croix rouge), cliquez dessus pour voir le message
   d'erreur exact (souvent : secret mal nommé, clé API pas encore
   active, ou mot de passe Supabase mal encodé dans l'URL)

**À partir de maintenant, laissez tourner au moins 5 jours** avant de
faire la capture d'écran finale — c'est ce qui prouve le "24h/24" exigé.

Pour lancer le backfill via GitHub (au lieu de le faire en local) :
**Actions → backfill-aqi-manuel → Run workflow**.

---

## Étape 7 — Compléter la documentation (outil : éditeur de texte / Markdown)

Dans `README.md`, remplacer les sections `_à compléter_` :

- **Période couverte** : copiez le résultat affiché par
  `validate_clean.py` (min/max des timestamps)
- **Trous connus** : notez les runs GitHub Actions échoués (s'il y en a),
  ou "aucun trou identifié à ce jour"
- **Connexion à la base** : ajoutez l'URI Supabase (celle-ci peut être
  partagée avec l'évaluateur — normal pour un accès en lecture pédagogique ;
  gardez cependant le mot de passe hors de tout post public si vous
  préférez créer un utilisateur Postgres en lecture seule dédié)

Dans `RAPPORT_PROJET.md`, chaque membre remplit sa partie :
répartition des tâches, difficultés rencontrées, choix techniques.

Committez ces mises à jour normalement (`git add . && git commit -m "..." && git push`).

---

## Étape 8 — Vérifier la cohérence des données (outil : SQL, dans Supabase)

*Consigne : "nombre de lignes de la table de faits ≈ nombre de villes ×
nombre d'heures couvertes"*

Dans Supabase : **SQL Editor → New query** :

```sql
select
  (select count(*) from dim_ville) as nb_villes,
  (select count(*) from dim_temps) as nb_heures_distinctes,
  (select count(*) from fait_qualite_air) as nb_lignes_faits,
  (select count(*) from dim_ville) * (select count(*) from dim_temps) as attendu_theorique;
```

Si `nb_lignes_faits` est proche de `attendu_theorique`, c'est cohérent.
S'il y a un écart, expliquez-le dans le README (ex : une ville ajoutée
plus tard que les autres, un run GitHub Actions en échec un jour donné).

---

## Étape 9 — Vidéo de démonstration (3 min max)

*Consigne : "le pipeline qui tourne → les zones de stockage → une requête SQL"*

Plan suggéré (un membre peut l'enregistrer avec l'enregistreur d'écran
Windows intégré, ou OBS Studio) :

1. **0:00–0:45** — Montrer l'onglet **Actions** de GitHub : plusieurs
   runs verts, à des heures différentes, sur plusieurs jours
2. **0:45–1:30** — Montrer le repo : dossier `raw/` (fichiers par ville),
   `clean/aqi_clean.csv` ouvert (montrer les colonnes, le tri, l'absence
   de doublons)
3. **1:30–2:30** — Dans Supabase, **Table Editor** : montrer `dim_ville`,
   `dim_temps`, `fait_qualite_air`
4. **2:30–3:00** — Exécuter la requête SQL de cohérence de l'étape 8 (ou
   une requête plus parlante, ex : AQI moyen par ville) et montrer le résultat

---

## Étape 10 — Checklist finale avant soumission

| Livrable exigé | Où le trouver |
|---|---|
| `ARCHITECTURE.md` | racine du repo |
| Dépôt Git complet, commits des 5 membres | historique des commits GitHub |
| Notebook(s) éventuels | `notebooks/` (si vous en ajoutez pour l'exploration) |
| Preuve pipeline automatique (5 jours différents) | capture d'écran de l'onglet Actions |
| Backfill (raw/, rejouable) | dossier `raw/` + `scripts/backfill.py` |
| `clean/` validé | `clean/aqi_clean.csv` + sortie de `validate_clean.py` |
| `load_warehouse.py` rejouable | `scripts/load_warehouse.py` |
| README du stockage complet | `README.md` mis à jour (étape 7) |
| Rapport de projet | `RAPPORT_PROJET.md` complété |
| Vidéo de démo | lien à ajouter dans le README ou dans le rendu Moodle |

Une fois tout coché, soumettez le lien du repo GitHub (public) et la
vidéo via le formulaire indiqué dans le sujet.
