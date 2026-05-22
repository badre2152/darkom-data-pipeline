"""
clean/clean_data.py — 🥈 Silver Layer
Exact logic from new.ipynb + 4 fixes:
  1. remove_accents handles NaN safely
  2. transaction deduction uses original nulls only
  3. nb_salles_bain cast to int after fill
  4. etage_outlier column name consistency
Outputs:
  - data/silver/data_clean.csv
  - silver.annonces_clean (PostgreSQL)
"""

import datetime
import unicodedata
import numpy as np
import pandas as pd
from sqlalchemy import text

from src.config import (
    BRONZE_CSV, SILVER_CSV, SCHEMA_BRONZE, SCHEMA_SILVER,
    SUSPICIOUS_PRICE_THRESHOLD, SUSPICIOUS_SURFACE_THRESHOLD,
    IQR_MULTIPLIER, SURFACE_BINS, SURFACE_LABELS,
)
from src.utils.db import get_engine
from src.utils.logger import get_logger

log = get_logger("clean")


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────
def _remove_accents(text_val):
    """FIX 1 : handles NaN safely."""
    if pd.isna(text_val):
        return text_val
    return "".join(
        c for c in unicodedata.normalize("NFD", str(text_val))
        if unicodedata.category(c) != "Mn"
    )


def _log_nulls(df: pd.DataFrame, step: str):
    nulls = df.isnull().sum()
    nulls = nulls[nulls > 0]
    if nulls.empty:
        log.info(f"[{step}] No nulls remaining ✓")
    else:
        log.info(f"[{step}] Remaining nulls:\n{nulls.to_string()}")


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
def clean_data() -> int:
    log.info("═" * 60)
    log.info("🥈 SILVER LAYER — Starting …")

    # ── 0. Read from bronze.stg_annonces ─────────────────────
    engine_bronze = get_engine(SCHEMA_BRONZE)
    df = pd.read_sql("SELECT * FROM bronze.stg_annonces", engine_bronze)
    log.info(f"Read {len(df)} rows from bronze.stg_annonces")

    # ── 1. Drop staging metadata column ──────────────────────
    df.drop(columns=["_loaded_at"], errors="ignore", inplace=True)

    # ── 2. Duplicates (cell 8-9) ──────────────────────────────
    before = len(df)
    df.drop_duplicates(keep="first", inplace=True)
    log.info(f"Duplicates removed : {before - len(df)} | Remaining : {len(df)}")

    # ── 3. Fix types (cell 11) ────────────────────────────────
    df["date_publication"] = pd.to_datetime(df["date_publication"], errors="coerce")
    for col in ["prix", "surface", "nb_chambres", "nb_salles_bain", "etage", "annee_construction"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    log.info("Types corrected")

    # ── 4. date_publication — ffill + bfill (cell 12) ─────────
    df["date_publication"] = df["date_publication"].ffill().bfill()
    log.info("date_publication : ffill+bfill applied")

    # ── 5. Ville — normalize (cells 16-19) ───────────────────
    df["ville"] = df["ville"].str.lower().str.strip().apply(_remove_accents)
    df["ville"] = df["ville"].replace({
        "casa":        "casablanca",
        "casablanca":  "casablanca",
        "marrakech":   "marrakech",
        "meknes":      "meknes",
        "tanger":      "tanger",
        "tetouan":     "tetouan",
        "rabat":       "rabat",
        "oujda":       "oujda",
        "fes":         "fes",
        "agadir":      "agadir",
        "kenitra":     "kenitra",
    })
    df["ville"] = df["ville"].replace(to_replace=r".*casa.*", value="casablanca", regex=True)
    log.info(f"Villes standardized : {sorted(df['ville'].unique().tolist())}")

    # ── 6. Quartier — impute mode by ville (cells 24-26) ──────
    ville_quartier_map = (
        df.groupby("ville")["quartier"]
        .agg(lambda x: x.mode().iloc[0] if not x.mode().empty else "unknown")
        .to_dict()
    )
    df["quartier"] = df["quartier"].fillna(df["ville"].map(ville_quartier_map))
    log.info(f"quartier nulls after fill : {df['quartier'].isnull().sum()}")

    # ── 7. type_bien — lower + deduce from titre (cells 30-33) ─
    df["type_bien"] = df["type_bien"].str.lower().str.strip()
    types = ["villa", "appartement", "terrain", "duplex", "bureau"]
    for t in types:
        mask = df["type_bien"].isnull() & df["titre"].str.lower().str.contains(t, na=False)
        df.loc[mask, "type_bien"] = t
    df["type_bien"] = df["type_bien"].astype("category")
    log.info(f"type_bien nulls after fill : {df['type_bien'].isnull().sum()}")
    log.info(f"type_bien distribution :\n{df['type_bien'].value_counts().to_string()}")

    # ── 8. transaction — FIX 2: only fill where originally null ─
    #    (cells 35-40 — use original nulls, not the full column)
    original_null_mask = df["transaction"].isnull()
    df["transaction"] = df["transaction"].str.lower().str.strip()

    low  = df["prix"].quantile(0.4)
    high = df["prix"].quantile(0.6)

    imputed = np.where(
        df["prix"] <= low,  "location",
        np.where(df["prix"] >= high, "vente", np.nan)
    )
    df.loc[original_null_mask, "transaction"] = pd.Series(
        imputed, index=df.index
    ).loc[original_null_mask]
    df["transaction"] = df["transaction"].fillna(df["transaction"].mode()[0])
    df["transaction"] = df["transaction"].astype("category")
    log.info(f"transaction distribution :\n{df['transaction'].value_counts().to_string()}")

    # ── 9. nb_chambres — median by (ville, type_bien) (cells 46-49) ─
    median_chambres = df.groupby(["ville", "type_bien"])["nb_chambres"].transform("median")
    df["nb_chambres"] = df["nb_chambres"].fillna(median_chambres).astype(int)

    # ── 10. nb_salles_bain — FIX 3: cast to int (cells 52-56) ──
    median_bain = df.groupby(["ville", "type_bien"])["nb_salles_bain"].transform("median")
    df["nb_salles_bain"] = df["nb_salles_bain"].fillna(median_bain).astype(int)

    # ── 11. etage — median by (ville, type_bien) (cells 58-61) ─
    median_etage = df.groupby(["ville", "type_bien"])["etage"].transform("median")
    df["etage"] = df["etage"].fillna(median_etage).astype(int)

    # ── 12. annee_construction — mode by (ville, type_bien) (cells 63-66) ─
    mode_annee = df.groupby(["ville", "type_bien"])["annee_construction"].transform(
        lambda x: x.mode().iloc[0] if not x.mode().empty else np.nan
    )
    df["annee_construction"] = df["annee_construction"].fillna(mode_annee).astype(int)

    _log_nulls(df, "After imputation")

    # ── 13. Outlier detection — IQR (cell 76) ────────────────
    num_cols = ["prix", "surface", "nb_chambres", "nb_salles_bain", "etage"]
    for col in num_cols:
        Q1  = df[col].quantile(0.25)
        Q3  = df[col].quantile(0.75)
        IQR = Q3 - Q1
        df[f"{col}_outlier"] = (
            (df[col] < Q1 - IQR_MULTIPLIER * IQR) |
            (df[col] > Q3 + IQR_MULTIPLIER * IQR)
        )
    log.info("IQR outlier flags computed")

    # ── 14. Logic anomaly (cell 77) ───────────────────────────
    df["logic_anomaly"] = (
        ((df["nb_salles_bain"] == 0) & (df["surface"] > 30)) |
        ((df["nb_chambres"]   == 0) & (df["surface"] > 40))
    )

    # ── 15. Luxury & suspicious (cells 78-79) ─────────────────
    p99 = df["prix"].quantile(0.99)
    df["luxury"]             = df["prix"]    > p99
    df["suspicious_price"]   = df["prix"]    < SUSPICIOUS_PRICE_THRESHOLD
    df["suspicious_surface"] = df["surface"] < SUSPICIOUS_SURFACE_THRESHOLD

    # ── 16. is_anomaly (cell 80) ──────────────────────────────
    df["is_anomaly"] = (
        df["prix_outlier"]          |
        df["surface_outlier"]       |
        df["nb_chambres_outlier"]   |
        df["nb_salles_bain_outlier"]|
        df["logic_anomaly"]         |
        df["suspicious_price"]      |
        df["suspicious_surface"]
    )
    log.info(f"Anomalies : {df['is_anomaly'].sum()} / {len(df)}")

    # ── 17. Feature Engineering (cells 84-95) ─────────────────
    df["prix_par_m2"]  = (df["prix"] / df["surface"]).round(2)

    current_year       = datetime.datetime.now().year
    df["age_estime"]   = current_year - df["annee_construction"]

    df["categorie_surface"] = pd.cut(
        df["surface"], bins=SURFACE_BINS, labels=SURFACE_LABELS
    )

    df["year"]    = df["date_publication"].dt.year
    df["month"]   = df["date_publication"].dt.strftime("%B")
    df["quarter"] = "Q" + df["date_publication"].dt.quarter.astype(str)
    df["day"]     = df["date_publication"].dt.day

    q1 = df["prix"].quantile(0.25)
    q2 = df["prix"].quantile(0.50)
    q3 = df["prix"].quantile(0.75)
    df["categorie_prix"] = pd.cut(
        df["prix"],
        bins=[0, q1, q2, q3, df["prix"].max()],
        labels=["economique", "moyen", "haut_standing", "luxe"],
    )
    log.info("Feature engineering done")

    # ── 18. Category types (cell 96) ──────────────────────────
    df["ville"]       = df["ville"].astype("category")
    df["quartier"]    = df["quartier"].astype("category")
    df["type_bien"]   = df["type_bien"].astype("category")
    df["transaction"] = df["transaction"].astype("category")

    # ── 19. Save to data/silver/data_clean.csv ────────────────
    SILVER_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(SILVER_CSV, index=False)
    log.info(f"Saved → {SILVER_CSV}")

    # ── 20. Load into silver.annonces_clean ───────────────────
    df_pg = df.copy()
    for col in df_pg.select_dtypes(include="category").columns:
        df_pg[col] = df_pg[col].astype(str)
    for col in ["categorie_prix", "categorie_surface"]:
        df_pg[col] = df_pg[col].astype(str)

    engine_silver = get_engine(SCHEMA_SILVER)
    with engine_silver.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS silver.annonces_clean CASCADE"))

    df_pg.to_sql(
        name="annonces_clean", schema=SCHEMA_SILVER,
        con=engine_silver, if_exists="replace", index=False, chunksize=500,
    )
    log.info(f"Loaded {len(df_pg)} rows → silver.annonces_clean")

    # ── 21. Log entry ──────────────────────────────────────────
    engine_bronze = get_engine(SCHEMA_BRONZE)
    with engine_bronze.begin() as conn:
        conn.execute(text("""
            INSERT INTO bronze.load_logs (layer, table_name, rows_loaded, load_status)
            VALUES ('silver', 'silver.annonces_clean', :n, 'SUCCESS')
        """), {"n": len(df_pg)})

    log.info("🥈 SILVER LAYER — Done ✓")
    log.info("═" * 60)
    return len(df_pg)


if __name__ == "__main__":
    clean_data()