# Guide de contribution — Darkom.ma Pipeline

## Prérequis
- Python 3.11+
- PostgreSQL 16+
- Environnement virtuel activé (`python -m venv venv && source venv/bin/activate`)
- Fichier `.env` configuré à partir de `.env.example`

## Lancer le projet localement
```bash
make install
make migrate
make pipeline CSV=data/bronze/darkom_annonces_raw.csv
make validate
```

## Ajouter une transformation Silver
1. Modifier `src/clean/clean_data.py`
2. Ajouter les colonnes dérivées dans la section Feature Engineering (étape 17)
3. Si la colonne est un flag de qualité, l'ajouter dans `validate_required_columns` dans `validate.py`
4. Documenter dans `CHANGELOG.md`

## Ajouter une table Gold
1. Ajouter le DDL dans `bi_schema.py` dans le bloc DROP/CREATE
2. Ajouter la table dans la liste DROP en tête de `build_warehouse()`
3. Ajouter la population et le merge vers `fact_annonces`
4. Mettre à jour la requête d'export `data_warehouse_ready.csv`
5. Ajouter la vérification FK dans `validate.py` si c'est une FK de `fact_annonces`

## Conventions
- Logs : utiliser `get_logger("nom_couche")` — ne jamais utiliser `print()`
- Toutes les erreurs bloquantes : lever une exception (le pipeline s'arrêtera via `sys.exit(1)`)
- Nommage SQL : snake_case, préfixe par couche (`stg_`, `dim_`, `subdim_`, `fact_`)
- Pas de secrets dans le code — toujours lire depuis `.env` via `os.getenv()`