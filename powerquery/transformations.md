# Power Query — Transformations Documentation

## Connexion à la base de données

Power BI se connecte directement au schema `gold` de PostgreSQL :

```
Serveur  : localhost
Port     : 5432
Base     : darkom_dwh
Schema   : gold
Mode     : Import (recommandé pour les performances)
```

---

## Tables importées depuis `gold`

| Table | Rôle |
|-------|------|
| `fact_annonces` | Table de faits centrale |
| `dim_date` | Dimension temporelle |
| `dim_localisation` | Dimension géographique (clé FK) |
| `subdim_ville` | Ville |
| `subdim_quartier` | Quartier |
| `dim_bien` | Dimension bien immobilier (clé FK) |
| `subdim_type_bien` | Type de bien |
| `subdim_construction` | Année de construction |
| `subdim_caracteristique` | Chambres / SdB / étage |
| `dim_transaction` | Vente ou Location |
| `dim_category` | Catégorie prix + surface |
| `dim_anomalies` | Flag agrégé qualité par annonce |
| `subdim_anomalie_detail` | 9 flags de détail (outliers, anomalies logiques) |

> Importer toutes les tables du schema `gold` — ne pas importer `bronze` ni `silver`.

---

## Transformations appliquées dans Power Query

### fact_annonces

```
1. Changer type [prix], [surface], [prix_par_m2] → Decimal Number
2. Changer type [annonce_id] → Text
3. Vérifier que [prix_par_m2] ne contient pas de valeurs négatives
   (filtre : [prix_par_m2] = null ou [prix_par_m2] > 0)
```

### dim_date

```
1. Changer type [date_publication] → Date
2. Changer type [year], [quarter], [month], [day] → Integer
3. Créer colonne [periode_label] :
   = Text.From([year]) & " T" & Text.From([quarter])
4. Créer colonne [mois_label] :
   = Date.ToText([date_publication], "MMM yyyy", "fr-MA")
5. Créer colonne [mois_tri] (pour tri correct des axes) :
   = [year] * 100 + [month]
```

### dim_category

```
1. Créer colonne [ordre_prix] pour tri personnalisé de categorie_prix :
   = if [prix_category] = "economique"   then 1
     else if [prix_category] = "moyen"   then 2
     else if [prix_category] = "haut_standing" then 3
     else if [prix_category] = "luxe"    then 4
     else 0
```

### dim_anomalies

```
1. Changer type [is_anomaly] → True/False
2. Changer type [anomalie_id], [detail_id] → Integer
```

> **Note (v1.4.0) :** `dim_anomalies` ne contient plus les flags de détail directement.
> Ils ont été déplacés vers `subdim_anomalie_detail` (voir ci-dessous).

### subdim_anomalie_detail

```
1. Changer types booléens → True/False :
   prix_outlier, surface_outlier, nb_chambres_outlier,
   nb_salles_bain_outlier, etage_outlier, logic_anomaly,
   suspicious_price, suspicious_surface, prix_par_m2_broken
```

### subdim_quartier

```
1. Remplacer valeur "unknown" par "Non spécifié"
   (pour un affichage plus propre dans les visuels)
```

---

## Ordre de chargement recommandé

1. `subdim_ville`, `subdim_quartier`, `subdim_type_bien`, `subdim_construction`, `subdim_caracteristique`, `subdim_anomalie_detail`
2. `dim_date`, `dim_localisation`, `dim_bien`, `dim_transaction`, `dim_category`, `dim_anomalies`
3. `fact_annonces` (en dernier — dépend de toutes les dimensions)

---

## Modèle de relations (Star Schema dans Power BI)

```
fact_annonces
   ├── dim_date            (fact_annonces[date_id]         → dim_date[date_id])
   ├── dim_localisation    (fact_annonces[localisation_id] → dim_localisation[localisation_id])
   │       ├── subdim_ville    (dim_localisation[ville_id]    → subdim_ville[ville_id])
   │       └── subdim_quartier (dim_localisation[quartier_id] → subdim_quartier[quartier_id])
   ├── dim_bien            (fact_annonces[bien_id]          → dim_bien[bien_id])
   │       ├── subdim_type_bien      (dim_bien[type_id]           → subdim_type_bien[type_id])
   │       ├── subdim_construction   (dim_bien[construction_id]   → subdim_construction[construction_id])
   │       └── subdim_caracteristique(dim_bien[caracteristique_id]→ subdim_caracteristique[caracteristique_id])
   ├── dim_transaction     (fact_annonces[transaction_id]   → dim_transaction[transaction_id])
   ├── dim_category        (fact_annonces[prix_category_id] → dim_category[prix_category_id])
   └── dim_anomalies       (fact_annonces[anomalie_id]      → dim_anomalies[anomalie_id])
           └── subdim_anomalie_detail (dim_anomalies[detail_id] → subdim_anomalie_detail[detail_id])
```

---

## Filtres à exclure des analyses de prix

Pour des analyses de prix fiables, appliquer ces filtres dans les visuels ou mesures DAX :

```
dim_anomalies[is_anomaly]                  = FALSE
subdim_anomalie_detail[prix_par_m2_broken] = FALSE
```

> **Important :** `prix_par_m2_broken` se trouve dans `subdim_anomalie_detail`, pas dans `dim_anomalies`.
> Depuis v1.4.0, `dim_anomalies` ne contient que `anomalie_id`, `annonce_id`, `is_anomaly` et `detail_id`.

Ou créer une mesure de base filtrée :

```dax
Prix Moyen Propre =
CALCULATE(
    AVERAGE(fact_annonces[prix]),
    dim_anomalies[is_anomaly] = FALSE
)
```