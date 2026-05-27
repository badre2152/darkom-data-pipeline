import sys
import pandas as pd
from sqlalchemy import text

from src.config import SCHEMA_SILVER, SCHEMA_GOLD
from src.utils.db import get_engine
from src.utils.logger import get_logger

log = get_logger("validate")

# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def _check(label: str, passed: bool, detail: str = ""):
    status = " PASS" if passed else " FAIL"
    msg = f"  {status}  |  {label}"
    if detail:
        msg += f"  →  {detail}"
    if passed:
        log.info(msg)
    else:
        log.error(msg)
    return passed


# ─────────────────────────────────────────────────────────────
# VALIDATIONS
# ─────────────────────────────────────────────────────────────

def validate_row_counts(engine_silver, engine_gold) -> bool:
    
    log.info("── 1. Validation des volumes ──────────────────────────")

    silver_count = pd.read_sql(
        "SELECT COUNT(*) AS n FROM silver.annonces_clean", engine_silver
    )["n"].iloc[0]

    gold_count = pd.read_sql(
        "SELECT COUNT(*) AS n FROM gold.fact_annonces", engine_gold
    )["n"].iloc[0]

    ok = 0 < gold_count <= silver_count
    _check(
        "fact_annonces <= silver.annonces_clean",
        ok,
        f"silver={silver_count}  gold={gold_count}"
    )

    # Dimensions non vides
    dims = [
        "dim_date", "dim_localisation", "dim_bien",
        "dim_transaction", "dim_category", "dim_anomalies",
        "subdim_ville", "subdim_quartier", "subdim_type_bien",
    ]
    all_ok = ok
    for dim in dims:
        cnt = pd.read_sql(f"SELECT COUNT(*) AS n FROM gold.{dim}", engine_gold)["n"].iloc[0]
        ok_dim = cnt > 0
        _check(f"{dim} non vide", ok_dim, f"{cnt} lignes")
        all_ok = all_ok and ok_dim

    return all_ok


def validate_foreign_keys(engine_gold) -> bool:
    
    log.info("── 2. Intégrité des clés étrangères ───────────────────")

    checks = {
        "date_id":          ("dim_date",        "date_id"),
        "localisation_id":  ("dim_localisation", "localisation_id"),
        "bien_id":          ("dim_bien",         "bien_id"),
        "transaction_id":   ("dim_transaction",  "transaction_id"),
        "prix_category_id": ("dim_category",     "prix_category_id"),
        "anomalie_id":      ("dim_anomalies",    "anomalie_id"),
    }

    all_ok = True
    for fk_col, (dim_table, pk_col) in checks.items():
        sql = f"""
            SELECT COUNT(*) AS orphans
            FROM gold.fact_annonces f
            WHERE f.{fk_col} NOT IN (
                SELECT {pk_col} FROM gold.{dim_table}
            )
        """
        orphans = pd.read_sql(sql, engine_gold)["orphans"].iloc[0]
        ok = orphans == 0
        _check(f"fact_annonces.{fk_col} → gold.{dim_table}", ok,
               f"{orphans} orphelins" if not ok else "OK")
        all_ok = all_ok and ok

    return all_ok


def validate_required_columns(engine_silver) -> bool:
    
    log.info("── 3. Colonnes requises (Silver) ──────────────────────")

    required = [
        "prix_par_m2", "prix_par_m2_broken", "age_estime",
        "categorie_prix", "categorie_surface",
        "year", "month", "quarter", "day",
        "is_anomaly", "luxury", "suspicious_price", "suspicious_surface",
        "prix_outlier", "surface_outlier", "nb_chambres_outlier",
        "etage_outlier",
    ]

    existing_cols = pd.read_sql(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = 'silver' AND table_name = 'annonces_clean'",
        engine_silver
    )["column_name"].tolist()

    all_ok = True
    for col in required:
        ok = col in existing_cols
        _check(f"Colonne silver.annonces_clean.{col}", ok)
        all_ok = all_ok and ok

    return all_ok


def validate_value_ranges(engine_silver) -> bool:
    
    log.info("── 4. Plages de valeurs (Silver) ──────────────────────")

    
    sql_checks = [
        ("prix > 0",           "SELECT COUNT(*) AS n FROM silver.annonces_clean WHERE prix IS NOT NULL AND prix <= 0"),
        ("surface > 0",        "SELECT COUNT(*) AS n FROM silver.annonces_clean WHERE surface IS NOT NULL AND surface <= 0"),
        ("age_estime >= 0",    "SELECT COUNT(*) AS n FROM silver.annonces_clean WHERE age_estime IS NOT NULL AND age_estime < 0"),
        ("prix_par_m2 > 0",    "SELECT COUNT(*) AS n FROM silver.annonces_clean WHERE prix_par_m2 IS NOT NULL AND prix_par_m2 <= 0"),
        ("nb_chambres >= 0",   "SELECT COUNT(*) AS n FROM silver.annonces_clean WHERE nb_chambres IS NOT NULL AND nb_chambres < 0"),
        ("Aucun prix négatif", "SELECT COUNT(*) AS n FROM silver.annonces_clean WHERE prix IS NOT NULL AND prix < 0"),
    ]

    all_ok = True
    for label, sql in sql_checks:
        bad = pd.read_sql(sql, engine_silver)["n"].iloc[0]
        ok = int(bad) == 0
        _check(label, ok, f"{bad} violations" if not ok else "OK")
        all_ok = all_ok and ok

    return all_ok


def validate_no_nulls_in_fact(engine_gold) -> bool:
    
    log.info("── 5. Nulls dans fact_annonces ────────────────────────")

    critical_cols = [
        "annonce_id", "date_id", "localisation_id",
        "bien_id", "transaction_id", "prix_category_id",
        "prix", "surface"
    ]

    all_ok = True
    for col in critical_cols:
        null_count = pd.read_sql(
            f"SELECT COUNT(*) AS n FROM gold.fact_annonces WHERE {col} IS NULL",
            engine_gold
        )["n"].iloc[0]
        ok = null_count == 0
        _check(f"fact_annonces.{col} sans NULL", ok,
               f"{null_count} nulls" if not ok else "OK")
        all_ok = all_ok and ok

    return all_ok


def validate_duplicates(engine_silver, engine_gold) -> bool:
    
    log.info("── 6. Doublons sur les clés primaires ─────────────────")

    checks = [
        (engine_silver, "SELECT COUNT(*) - COUNT(DISTINCT annonce_id) AS dup FROM silver.annonces_clean",
         "silver.annonces_clean.annonce_id"),
        (engine_gold,   "SELECT COUNT(*) - COUNT(DISTINCT annonce_id) AS dup FROM gold.fact_annonces",
         "gold.fact_annonces.annonce_id"),
        (engine_gold,   "SELECT COUNT(*) - COUNT(DISTINCT ville) AS dup FROM gold.subdim_ville",
         "gold.subdim_ville.ville"),
    ]

    all_ok = True
    for engine, sql, label in checks:
        dup = pd.read_sql(sql, engine)["dup"].iloc[0]
        ok = dup == 0
        _check(f"Pas de doublons — {label}", ok, f"{dup} doublons" if not ok else "OK")
        all_ok = all_ok and ok

    return all_ok


def print_summary(engine_silver, engine_gold):
    
    log.info("── 7. Résumé du Data Warehouse ────────────────────────")

    silver_rows = pd.read_sql("SELECT COUNT(*) AS n FROM silver.annonces_clean", engine_silver)["n"].iloc[0]
    gold_rows   = pd.read_sql("SELECT COUNT(*) AS n FROM gold.fact_annonces", engine_gold)["n"].iloc[0]
    anomalies   = pd.read_sql(
        "SELECT COUNT(*) AS n FROM gold.fact_annonces f "
        "JOIN gold.dim_anomalies a ON a.anomalie_id = f.anomalie_id "
        "WHERE a.is_anomaly = TRUE",
        engine_gold
    )["n"].iloc[0]
    villes      = pd.read_sql("SELECT COUNT(*) AS n FROM gold.subdim_ville", engine_gold)["n"].iloc[0]
    dates       = pd.read_sql("SELECT COUNT(*) AS n FROM gold.dim_date", engine_gold)["n"].iloc[0]

    log.info(f"  Silver (annonces_clean)   : {silver_rows} lignes")
    log.info(f"  Gold (fact_annonces)      : {gold_rows} lignes")
    log.info(f"  Anomalies détectées       : {anomalies} ({anomalies/gold_rows*100:.1f}%)" if gold_rows else "  Gold vide")
    log.info(f"  Villes distinctes         : {villes}")
    log.info(f"  Dates distinctes          : {dates}")

    prix_stats = pd.read_sql(
        "SELECT MIN(prix) AS min_prix, MAX(prix) AS max_prix, "
        "ROUND(AVG(prix)::numeric, 0) AS avg_prix FROM gold.fact_annonces",
        engine_gold
    )
    row = prix_stats.iloc[0]
    log.info(f"  Prix min/moy/max (MAD)    : {int(row['min_prix']):,} / {int(row['avg_prix']):,} / {int(row['max_prix']):,}")


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def run_validation() -> bool:
    log.info("═" * 60)
    log.info(" VALIDATION DU DATA WAREHOUSE — Démarrage …")

    engine_silver = get_engine(SCHEMA_SILVER)
    engine_gold   = get_engine(SCHEMA_GOLD)

    results = [
        validate_row_counts(engine_silver, engine_gold),
        validate_foreign_keys(engine_gold),
        validate_required_columns(engine_silver),
        validate_value_ranges(engine_silver),
        validate_no_nulls_in_fact(engine_gold),
        validate_duplicates(engine_silver, engine_gold),
    ]

    print_summary(engine_silver, engine_gold)

    passed = sum(results)
    total  = len(results)

    log.info("═" * 60)
    if all(results):
        log.info(f" VALIDATION RÉUSSIE — {passed}/{total} contrôles passés")
    else:
        log.error(f"❌ VALIDATION ÉCHOUÉE — {passed}/{total} contrôles passés")

    log.info("═" * 60)
    return all(results)


if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 1)