# Log Analysis Guide

Each pipeline run produces log files under `logs/`. Here is what to look for in each one.

## Log files

| File | Written by | Purpose |
|------|-----------|---------|
| `pipeline.log` | All layers | Global run trace; first place to check after a failure |
| `staging.log` | `load_staging.py` | Bronze CSV ingestion details |
| `clean.log` | `clean_data.py` | Silver transformation details |
| `bi_schema.log` | `bi_schema.py` | Gold DDL + row counts |
| `migrations.log` | `migrations.py` | Schema creation / migration steps |
| `db.log` | `db.py` | DB connection events |
| `validate.log` | `validate.py` | Post-load data quality checks |

## Common patterns to watch

### transaction encore NaN après Silver — si le bug réapparaît
Si tu modifies la logique d'imputation et que des NaN réapparaissent, cherche dans `clean.log` :
```
transaction distribution :
vente      NNN
location   NNN
```
Si une ligne `nan NNN` apparaît dans ce bloc, c'est que `fillna(mode())` a échoué — vérifie que la série `transaction` contient au moins une valeur non-nulle avant l'appel à `mode()`.

> **Note :** Dans les versions < 1.2.0, ce bug produisait `nan 10` dans ce log. Il est corrigé depuis.

### Anomaly rate > 30 %
Normal when `suspicious_price` catches short-term rental prices.
After the per-transaction IQR fix the rate should drop below ~20 %.
If still high, inspect `clean.log`:
```
Anomalies : NNN / 1500
```

### Gold layer runs on stale Silver data
Symptom: Gold row count equals the previous Silver run.
Cause: Silver failed silently (now fixed with `sys.exit(1)` in `pipeline.py`).
Check `pipeline.log` for `🥈 Silver FAILED`.

### prix_par_m2_broken rows
`clean.log` will print:
```
prix_par_m2_broken : NNN rows flagged (< 100 MAD/m²)
```
These are typically location prices divided by large surfaces. They are flagged but kept in the dataset so Power BI can filter them with a slicer.