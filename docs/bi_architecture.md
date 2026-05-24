# Architecture BI — Darkom.ma Dashboard

## Flux de données complet

```
[darkom_annonces_raw.csv]
    ↓ load_staging.py
[PostgreSQL — bronze.stg_annonces]
    ↓ clean_data.py
[PostgreSQL — silver.annonces_clean]
    ↓ bi_schema.py
[PostgreSQL — gold (Snowflake Schema)]
    ├── fact_annonces
    ├── dim_date
    ├── dim_localisation → subdim_ville, subdim_quartier
    ├── dim_bien         → subdim_type_bien, subdim_construction, subdim_caracteristique
    ├── dim_transaction
    ├── dim_category
    └── dim_anomalies
    ↓ Power Query (nettoyage léger + colonnes calculées)
[Modèle Power BI — Snowflake Schema]
    ↓ DAX Measures
[4 Dashboards Interactifs]
```

---

## Modèle Snowflake Schema (Power BI)

```
                  dim_date
                  (date_id, date_publication,
                   year, quarter, month, day)
                       │
subdim_ville ──┐        │        ┌── subdim_type_bien
               ↓        │        ↓
subdim_quartier → dim_localisation ── fact_annonces ── dim_bien ← subdim_construction
                                          │                     ← subdim_caracteristique
                                    dim_transaction
                                    dim_category
                                    dim_anomalies
```

---

## Tables Gold disponibles

### fact_annonces
| Colonne | Type | Description |
|---------|------|-------------|
| annonce_id | VARCHAR | Identifiant unique |
| date_id | INT | FK → dim_date |
| localisation_id | INT | FK → dim_localisation |
| bien_id | INT | FK → dim_bien |
| transaction_id | INT | FK → dim_transaction |
| anomalie_id | INT | FK → dim_anomalies |
| prix_category_id | INT | FK → dim_category |
| prix | NUMERIC | Prix en MAD |
| surface | NUMERIC | Surface en m² |
| prix_par_m2 | NUMERIC | Prix calculé / m² |

### dim_date
| Colonne | Type | Description |
|---------|------|-------------|
| date_id | SERIAL | Clé primaire |
| date_publication | DATE | Date de publication |
| year | INT | Année |
| quarter | INT | Trimestre (1-4) |
| month | INT | Mois (1-12) |
| day | INT | Jour |

### dim_localisation
| Colonne | Type | Description |
|---------|------|-------------|
| localisation_id | SERIAL | Clé primaire |
| ville_id | INT | FK → subdim_ville |
| quartier_id | INT | FK → subdim_quartier |

### subdim_ville / subdim_quartier
Dimensions texte simples (ville, quartier).

### dim_bien
| Colonne | Type | Description |
|---------|------|-------------|
| bien_id | SERIAL | Clé primaire |
| type_id | INT | FK → subdim_type_bien |
| construction_id | INT | FK → subdim_construction |
| caracteristique_id | INT | FK → subdim_caracteristique |
| age_estime | INT | Âge estimé du bien |

### dim_transaction
Valeurs : `vente` / `location`

### dim_category
| Colonne | Type | Description |
|---------|------|-------------|
| prix_category_id | SERIAL | Clé primaire |
| prix_category | VARCHAR | economique / moyen / haut_standing / luxe |
| surface_category | VARCHAR | petit / moyen / grand |
| luxury | BOOLEAN | Annonce de luxe (> P99 prix) |

### dim_anomalies
Flags booléens par annonce : `is_anomaly`, `prix_outlier`, `surface_outlier`,
`nb_chambres_outlier`, `etage_outlier`, `logic_anomaly`, `suspicious_price`,
`suspicious_surface`, `prix_par_m2_broken`

---

## Connexion Power BI → PostgreSQL

```
Serveur  : localhost
Port     : 5432
Base     : darkom_dwh
Schema   : gold
Mode     : Import
```

**Étapes :**
1. Power BI Desktop → **Obtenir des données** → **Base de données PostgreSQL**
2. Serveur : `localhost`, Base : `darkom_dwh`
3. Navigateur : déplier `gold` et sélectionner toutes les tables `dim_*`, `subdim_*`, `fact_annonces`
4. Cliquer **Transformer les données** pour appliquer les transformations Power Query

**Alternative (fichier plat) :**
Importer directement `data/gold/bi/data_warehouse_ready.csv` pour un modèle à table unique
(moins optimal pour les filtres croisés mais plus simple pour les démos).
