# Changelog — Darkom.ma Data Pipeline

Toutes les modifications notables de ce projet sont documentées dans ce fichier.
Format basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/).

---

## [1.6.0] — 2026-05-28

### Corrigé — Documentation
- `docs/bi_architecture.md` — `dim_anomalies` corrigée : ne liste plus les 9 flags directement ; nouvelle section `subdim_anomalie_detail` ajoutée avec description complète des colonnes
- `docs/bi_architecture.md` — diagrammes flux et Snowflake Schema mis à jour (`dim_anomalies → subdim_anomalie_detail`)
- `docs/TROUBLESHOOTING.md` — titres des sections `Bronze/Silver/Gold FAILED` corrigés : emoji 🥉🥈🥇 supprimées (absentes des vrais messages de log dans `pipeline.py`)
- `docs/TROUBLESHOOTING.md` — filtre `prix_par_m2_broken` corrigé : référence `subdim_anomalie_detail[prix_par_m2_broken]` au lieu de `dim_anomalies`
- `docs/TROUBLESHOOTING.md` — ajout note sur `make clean-db` : précise que le schema `audit` n'est pas supprimé et comment le supprimer manuellement
- `docs/log-analysis.md` — `NNN / 1500` remplacé par `NNN / TOTAL` (1500 était un nombre figé ne reflétant pas la taille réelle du dataset)
- `powerquery/transformations.md` — `subdim_anomalie_detail` ajoutée dans la liste des tables importées et dans le bloc de transformations
- `powerquery/transformations.md` — section `dim_anomalies` corrigée (ne liste plus que `is_anomaly` et les FKs)
- `powerquery/transformations.md` — ordre de chargement mis à jour (ajout `subdim_anomalie_detail` en étape 1)
- `powerquery/transformations.md` — diagramme de relations mis à jour (`subdim_anomalie_detail` ajoutée sous `dim_anomalies`)
- `powerquery/transformations.md` — section "Filtres à exclure des analyses de prix" corrigée : `prix_par_m2_broken` référencé sur `subdim_anomalie_detail` et non sur `dim_anomalies`
- `dax/price_analysis.dax` — mesure `Prix Moyen m2 Propre` corrigée : `dim_anomalies[prix_par_m2_broken]` remplacé par `subdim_anomalie_detail[prix_par_m2_broken]`
- `README.md` — arborescence du projet complétée : ajout `Schema_Diagrame.png`, `bi_architecture.md`, `rapport_screenshots/` (5 captures), `dax/`, `powerquery/`, `powerbi/`

### Ajouté
- `.env.example` — fichier modèle de configuration manquant (référencé dans le README depuis v1.2.0 mais absent du dépôt)

---

## [1.5.0] — 2026-05-24

### Modifié
- `migrations.py` — `load_logs` déplacé de `bronze` vers le nouveau schema `audit` ; bronze ne contient plus que les tables de staging
- `load_staging.py`, `clean_data.py`, `bi_schema.py` — toutes les insertions `bronze.load_logs` remplacées par `audit.load_logs`
- `README.md` — tableau des schemas mis à jour (ajout schema `audit`)

---

## [1.4.0] — 2026-05-24

### Modifié
- `bi_schema.py` — `dim_anomalies` refactorisée : ne contient plus que `annonce_id`, `is_anomaly` et `detail_id` (FK)
- `bi_schema.py` — ajout de `subdim_anomalie_detail` contenant les 9 flags de détail (`prix_outlier`, `surface_outlier`, `nb_chambres_outlier`, `nb_salles_bain_outlier`, `etage_outlier`, `logic_anomaly`, `suspicious_price`, `suspicious_surface`, `prix_par_m2_broken`) — dédoublonnage sur la combinaison unique de flags
- `README.md` — Snowflake Schema mis à jour (ajout `subdim_anomalie_detail` sous `dim_anomalies`)
- `README.md` — section Gold mise à jour (description du nouveau découpage `dim_anomalies` / `subdim_anomalie_detail`)

---

## [1.3.0] — 2026-05-24

### Corrigé
- `load_staging.py` — `shutil.copy2` levait `SameFileError` quand le CSV source se trouvait déjà dans `data/bronze/` ; ajout d'une vérification `Path.resolve()` avant la recopie (skip si même fichier)
- `clean_data.py` — les lignes dont `transaction` reste indéterminée après imputation (valeur string `"nan"` ou NaN réel) sont désormais **supprimées** du dataset Silver au lieu d'être propagées ; seules `vente` et `location` sont acceptées
- `bi_schema.py` — `dim_transaction` ne contenait plus que 2 valeurs valides (`location`, `vente`) après le fix Silver ; suppression du filtre défensif côté Gold (devenu inutile)
- `README.md` — section Bronze mise à jour (comportement skip-copy documenté)
- `README.md` — section Silver mise à jour (règle de suppression des transactions indéterminées)
- `README.md` — section Gold mise à jour (`dim_transaction` = 2 lignes exactement)
- `README.md` — ajout commande `make clean-db` dans la section lancement

---

## [1.2.0] — 2026-05-23

### Corrigé
- `validate.py` — crash sur `is_anomaly` dans `fact_annonces` (remplacé par JOIN sur `dim_anomalies.anomalie_id`)
- `validate.py` — ajout de la vérification FK `anomalie_id → dim_anomalies` dans `validate_foreign_keys`
- `validate.py` — ajout de `prix_par_m2_broken` et `etage_outlier` dans `validate_required_columns`
- `clean_data.py` — `etage_outlier` désormais inclus dans `is_anomaly` (bug silencieux depuis v1.0.0)
- `clean_data.py` — `age_estime` clampé à 0 minimum avec warning log si `annee_construction` future
- `load_staging.py` — le fichier CSV bronze est toujours remplacé (corrige le bug de cache lors du rechargement avec un nouveau CSV)
- `bi_schema.py` — `insert_subdim` utilise maintenant `engine.begin()` explicite pour éviter les inserts partiels non rollbackés
- `bi_schema.py` — `prix_par_m2` inf/-inf remplacés par NULL avant chargement Gold
- `bi_schema.py` — suppression de `subdim_age_bien` (redondant avec `subdim_construction`) ; `age_estime` stocké directement dans `dim_bien`
- `bi_schema.py` — requête d'export `data_warehouse_ready.csv` mise à jour (suppression JOIN `subdim_age_bien`, ajout JOIN `dim_anomalies`)
- `README.md` — logs `db.log` et `validate.log` ajoutés à la section Logs
- `README.md` — arborescence du projet mise à jour (`.env.example`, `docs/log-analysis.md`, `docs/TROUBLESHOOTING.md`)
- `docs/log-analysis.md` — correction de l'exemple trompeur `nan 10`

### Ajouté
- `src/utils/validate.py` — script de validation complet du Data Warehouse :
  - Contrôle des volumes Silver → Gold
  - Vérification de l'intégrité des clés étrangères (FK orphelines)
  - Contrôle des colonnes requises dans Silver
  - Validation des plages de valeurs (prix, surface, age_estime)
  - Détection des NULLs dans les colonnes critiques de fact_annonces
  - Vérification des doublons sur les PKs
  - Résumé statistique du DWH (prix min/moy/max, villes, anomalies)
- `make validate` dans le Makefile pour lancer la validation
- `prix_par_m2` ajouté comme mesure dans `gold.fact_annonces` (DDL + population + export CSV)
- `prix_par_m2` inclus dans la requête d'export `data_warehouse_ready.csv`

### Modifié
- `README.md` — réécrit entièrement :
  - Contenu aligné avec le vrai projet Darkom.ma (suppression références Avito/Docker/Selenium)
  - Architecture Medallion documentée (Bronze/Silver/Gold)
  - Snowflake Schema documenté avec toutes les tables
  - Instructions d'installation et de lancement complètes
  - Section connexion Power BI
  - Table des features engineered
  - Table des transformations Silver

---

## [1.0.0] — 2026-05-21

### Ajouté — Infrastructure

- `src/utils/migrations.py` — création des schemas PostgreSQL (`bronze`, `silver`, `gold`) et des tables `bronze.stg_annonces` et `bronze.load_logs`
- `src/utils/db.py` — factory SQLAlchemy avec gestion de la connexion par schema
- `src/utils/logger.py` — système de logging centralisé par couche (fichiers séparés + console)
- `src/config.py` — constantes du projet (chemins, schemas, seuils IQR, bins de surface)
- `Makefile` — automatisation des commandes pipeline (`migrate`, `bronze`, `silver`, `gold`, `pipeline`, `install`, `clean-db`)
- `requirements.txt` — dépendances fixées (pandas, sqlalchemy, psycopg2-binary, python-dotenv, unicodedata2)
- `.env` — configuration de la connexion PostgreSQL (non versionné)

### Ajouté — Bronze Layer (`src/staging/load_staging.py`)

- Copie du CSV source dans `data/bronze/darkom_annonces_raw.csv` (fichier immuable, write-once)
- Chargement du CSV brut dans `bronze.stg_annonces` (toutes colonnes en TEXT)
- Truncate + rechargement idempotent
- Log de chargement dans `bronze.load_logs`
- Sortie : `logs/staging.log`

### Ajouté — Silver Layer (`src/clean/clean_data.py`)

**Nettoyage :**
- Suppression des doublons (`drop_duplicates`)
- Conversion des types : `date_publication` → DATE, colonnes numériques → FLOAT/INT
- Normalisation des villes (lower, strip, suppression accents, regex `casa*` → `casablanca`)
- Imputation quartiers manquants par mode par ville
- Déduction de `type_bien` depuis le titre si null (villa, appartement, terrain, duplex, bureau)
- Imputation de `transaction` par quantile de prix si null
- Imputation de `nb_chambres`, `nb_salles_bain`, `etage` par médiane (ville, type_bien)
- Imputation de `annee_construction` par mode (ville, type_bien)

**Détection d'anomalies :**
- Flags outliers IQR × 1.5 sur prix, surface, nb_chambres, nb_salles_bain, etage
- Anomalie logique (surface > 30m² avec 0 sdb, surface > 40m² avec 0 chambre)
- Flag `luxury` (prix > P99), `suspicious_price` (< 5 000 MAD), `suspicious_surface` (< 15 m²)
- Colonne agrégée `is_anomaly`

**Feature Engineering :**
- `prix_par_m2` = prix / surface
- `age_estime` = année courante − annee_construction
- `categorie_prix` = Q1/Q2/Q3 → economique / moyen / haut_standing / luxe
- `categorie_surface` = < 80m² → petit, 80–150m² → moyen, > 150m² → grand
- `year`, `month`, `quarter`, `day` extraits de `date_publication`

- Sortie : `data/silver/data_clean.csv` + `silver.annonces_clean`
- Sortie : `logs/clean.log`

### Ajouté — Gold Layer (`src/warehouse/bi_schema.py`)

**Snowflake Schema dans le schema `gold` :**

*Sub-dimensions :*
- `subdim_ville` (ville_id, ville)
- `subdim_quartier` (quartier_id, quartier)
- `subdim_type_bien` (type_id, type_bien)
- `subdim_construction` (construction_id, annee_construction)
- `subdim_caracteristique` (caracteristique_id, nb_chambres, nb_salles_bain, etage)

*Dimensions principales :*
- `dim_date` (date_id, date_publication, year, quarter, month, day)
- `dim_localisation` (localisation_id → subdim_ville, subdim_quartier)
- `dim_bien` (bien_id → subdim_type_bien, subdim_construction, subdim_caracteristique)
- `dim_transaction` (transaction_id, transaction) — valeurs : `location`, `vente`
- `dim_category` (prix_category_id, prix_category, surface_category, luxury)
- `dim_anomalies` (anomalie_id PK, annonce_id UNIQUE, is_anomaly + 9 flags de détail)

*Table de faits :*
- `fact_annonces` (annonce_id PK, FKs vers toutes dimensions, prix, surface, prix_par_m2)

*Indexes créés :* fact_annonces sur date_id, localisation_id, bien_id, transaction_id, is_anomaly, prix_category_id ; subdim_ville sur ville.

- Sortie : `data/gold/bi/data_warehouse_ready.csv` (vue dénormalisée pour Power BI)
- Sortie : `logs/bi_schema.log`

### Ajouté — Notebook

- `notebook/Data_preparation_logic.ipynb` — exploration, tests de logique de nettoyage et visualisations préliminaires

---

## [0.1.0] — 2026-05-01

### Initialisé
- Structure du dépôt créée (dossiers src/, data/, docs/, logs/, notebook/)
- Fichiers scaffolding : LICENSE, CONTRIBUTING.md, CHANGELOG.md, README.md, .gitignore