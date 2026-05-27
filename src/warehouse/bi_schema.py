import numpy as np
import pandas as pd
from sqlalchemy import text

from src.config import GOLD_CSV, SCHEMA_SILVER, SCHEMA_GOLD, SCHEMA_BRONZE
from src.utils.db import get_engine
from src.utils.logger import get_logger

log = get_logger("bi_schema")


# ─────────────────────────────────────────────────────────────
# DDL HELPERS
# ─────────────────────────────────────────────────────────────
def _drop_create(conn, ddl: str, name: str):
    conn.execute(text(ddl))
    log.info(f"Table {name} — created ✓")


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
def build_warehouse() -> int:
    log.info("═" * 60)
    log.info(" GOLD LAYER — Starting …")

    # ── 0. Load from silver ───────────────────────────────────
    engine_silver = get_engine(SCHEMA_SILVER)
    df = pd.read_sql("SELECT * FROM silver.annonces_clean", engine_silver)
    log.info(f"Read {len(df)} rows from silver.annonces_clean")

    
    df["prix_par_m2"] = df["prix_par_m2"].replace([np.inf, -np.inf], np.nan)
    bad_ppm2 = df["prix_par_m2"].isna().sum()
    if bad_ppm2 > 0:
        log.warning(f"prix_par_m2 : {bad_ppm2} inf/NaN values replaced with NULL before Gold load")

    engine = get_engine(SCHEMA_GOLD)

    with engine.begin() as conn:

        # ════════════════════════════════════════════════════
        # DROP all tables in dependency order
        # ════════════════════════════════════════════════════
        for t in [
            "gold.fact_annonces",
            "gold.dim_bien", "gold.dim_localisation", "gold.dim_date",
            "gold.dim_transaction", "gold.dim_category", "gold.dim_anomalies",
            "gold.subdim_anomalie_detail",
            "gold.subdim_ville", "gold.subdim_quartier", "gold.subdim_type_bien",
            "gold.subdim_construction", "gold.subdim_caracteristique",
        ]:
            conn.execute(text(f"DROP TABLE IF EXISTS {t} CASCADE"))

        # ════════════════════════════════════════════════════
        # SUB-DIMENSIONS
        # ════════════════════════════════════════════════════

        _drop_create(conn, """
            CREATE TABLE gold.subdim_ville (
                ville_id SERIAL PRIMARY KEY,
                ville    VARCHAR(100) NOT NULL UNIQUE
            )""", "subdim_ville")

        _drop_create(conn, """
            CREATE TABLE gold.subdim_quartier (
                quartier_id SERIAL PRIMARY KEY,
                quartier    VARCHAR(200) NOT NULL UNIQUE
            )""", "subdim_quartier")

        _drop_create(conn, """
            CREATE TABLE gold.subdim_type_bien (
                type_id   SERIAL PRIMARY KEY,
                type_bien VARCHAR(50) NOT NULL UNIQUE
            )""", "subdim_type_bien")

        _drop_create(conn, """
            CREATE TABLE gold.subdim_construction (
                construction_id    SERIAL PRIMARY KEY,
                annee_construction INTEGER NOT NULL UNIQUE
            )""", "subdim_construction")

        _drop_create(conn, """
            CREATE TABLE gold.subdim_caracteristique (
                caracteristique_id SERIAL PRIMARY KEY,
                nb_chambres        INTEGER,
                nb_salles_bain     INTEGER,
                etage              INTEGER,
                UNIQUE (nb_chambres, nb_salles_bain, etage)
            )""", "subdim_caracteristique")

        # ════════════════════════════════════════════════════
        # MAIN DIMENSIONS
        # ════════════════════════════════════════════════════

        _drop_create(conn, """
            CREATE TABLE gold.dim_date (
                date_id          SERIAL PRIMARY KEY,
                date_publication DATE    NOT NULL UNIQUE,
                year             INTEGER NOT NULL,
                quarter          INTEGER NOT NULL,
                month            INTEGER NOT NULL,
                day              INTEGER NOT NULL
            )""", "dim_date")

        _drop_create(conn, """
            CREATE TABLE gold.dim_localisation (
                localisation_id SERIAL PRIMARY KEY,
                ville_id        INTEGER NOT NULL REFERENCES gold.subdim_ville(ville_id),
                quartier_id     INTEGER NOT NULL REFERENCES gold.subdim_quartier(quartier_id),
                UNIQUE (ville_id, quartier_id)
            )""", "dim_localisation")

        _drop_create(conn, """
            CREATE TABLE gold.dim_transaction (
                transaction_id SERIAL PRIMARY KEY,
                transaction    VARCHAR(20) NOT NULL UNIQUE
            )""", "dim_transaction")

        _drop_create(conn, """
            CREATE TABLE gold.dim_category (
                prix_category_id SERIAL PRIMARY KEY,
                prix_category    VARCHAR(30) NOT NULL,
                surface_category VARCHAR(20),
                luxury           BOOLEAN,
                UNIQUE (prix_category, surface_category)
            )""", "dim_category")

        _drop_create(conn, """
            CREATE TABLE gold.subdim_anomalie_detail (
                detail_id              SERIAL  PRIMARY KEY,
                prix_outlier           BOOLEAN NOT NULL DEFAULT FALSE,
                surface_outlier        BOOLEAN NOT NULL DEFAULT FALSE,
                nb_chambres_outlier    BOOLEAN NOT NULL DEFAULT FALSE,
                nb_salles_bain_outlier BOOLEAN NOT NULL DEFAULT FALSE,
                etage_outlier          BOOLEAN NOT NULL DEFAULT FALSE,
                logic_anomaly          BOOLEAN NOT NULL DEFAULT FALSE,
                suspicious_price       BOOLEAN NOT NULL DEFAULT FALSE,
                suspicious_surface     BOOLEAN NOT NULL DEFAULT FALSE,
                prix_par_m2_broken     BOOLEAN NOT NULL DEFAULT FALSE,
                UNIQUE (prix_outlier, surface_outlier, nb_chambres_outlier,
                        nb_salles_bain_outlier, etage_outlier, logic_anomaly,
                        suspicious_price, suspicious_surface, prix_par_m2_broken)
            )""", "subdim_anomalie_detail")

        _drop_create(conn, """
            CREATE TABLE gold.dim_anomalies (
                anomalie_id SERIAL  PRIMARY KEY,
                annonce_id  VARCHAR(20) NOT NULL UNIQUE,
                is_anomaly  BOOLEAN NOT NULL DEFAULT FALSE,
                detail_id   INTEGER NOT NULL REFERENCES gold.subdim_anomalie_detail(detail_id)
            )""", "dim_anomalies")

        _drop_create(conn, """
            CREATE TABLE gold.dim_bien (
                bien_id            SERIAL PRIMARY KEY,
                type_id            INTEGER NOT NULL REFERENCES gold.subdim_type_bien(type_id),
                construction_id    INTEGER NOT NULL REFERENCES gold.subdim_construction(construction_id),
                caracteristique_id INTEGER NOT NULL REFERENCES gold.subdim_caracteristique(caracteristique_id),
                age_estime         INTEGER NOT NULL,
                UNIQUE (type_id, construction_id, caracteristique_id)
            )""", "dim_bien")

        # ════════════════════════════════════════════════════
        # FACT TABLE
        # ════════════════════════════════════════════════════

        _drop_create(conn, """
            CREATE TABLE gold.fact_annonces (
                annonce_id       VARCHAR(20)   PRIMARY KEY,
                date_id          INTEGER       NOT NULL REFERENCES gold.dim_date(date_id),
                localisation_id  INTEGER       NOT NULL REFERENCES gold.dim_localisation(localisation_id),
                bien_id          INTEGER       NOT NULL REFERENCES gold.dim_bien(bien_id),
                transaction_id   INTEGER       NOT NULL REFERENCES gold.dim_transaction(transaction_id),
                anomalie_id      INTEGER       NOT NULL REFERENCES gold.dim_anomalies(anomalie_id),
                prix_category_id INTEGER       NOT NULL REFERENCES gold.dim_category(prix_category_id),
                prix             DECIMAL(15,2),
                surface          DECIMAL(10,2),
                prix_par_m2      DECIMAL(12,2)
            )""", "fact_annonces")

    # ════════════════════════════════════════════════════════
    # POPULATE — using pandas for simplicity + safety
    # ════════════════════════════════════════════════════════

    
    def insert_subdim(table, col, values):
        rows = pd.DataFrame({col: sorted(values)})
        with engine.begin() as _conn:
            rows.to_sql(table.split(".")[1], schema="gold", con=_conn,
                        if_exists="append", index=False)
        result = pd.read_sql(f"SELECT * FROM {table}", engine)
        log.info(f"  {table} : {len(result)} rows")
        return result

    # ── subdim_ville ──────────────────────────────────────────
    villes = df["ville"].dropna().unique()
    sv = insert_subdim("gold.subdim_ville", "ville", villes)

    # ── subdim_quartier ───────────────────────────────────────
    quartiers = df["quartier"].fillna("unknown").unique()
    sq = insert_subdim("gold.subdim_quartier", "quartier", quartiers)

    # ── subdim_type_bien ──────────────────────────────────────
    types = df["type_bien"].dropna().unique()
    st = insert_subdim("gold.subdim_type_bien", "type_bien", types)

    # ── subdim_construction ───────────────────────────────────
    
    annees = df["annee_construction"].dropna().astype(int).unique()
    sc_df = pd.DataFrame({"annee_construction": sorted(annees)})
    sc_df.to_sql("subdim_construction", schema="gold", con=engine,
                 if_exists="append", index=False)
    sc = pd.read_sql("SELECT * FROM gold.subdim_construction", engine)
    log.info(f"  gold.subdim_construction : {len(sc)} rows")

    # ── subdim_caracteristique ────────────────────────────────
    
    caract = df[["nb_chambres", "nb_salles_bain", "etage"]].drop_duplicates().dropna()
    caract = caract.astype(int)
    caract.to_sql("subdim_caracteristique", schema="gold", con=engine,
                  if_exists="append", index=False)
    sca = pd.read_sql("SELECT * FROM gold.subdim_caracteristique", engine)
    log.info(f"  gold.subdim_caracteristique : {len(sca)} rows")

    # ── dim_date ──────────────────────────────────────────────
    dates = df[["date_publication"]].drop_duplicates().dropna().copy()
    dates["date_publication"] = pd.to_datetime(dates["date_publication"])
    dates["year"]    = dates["date_publication"].dt.year
    dates["quarter"] = dates["date_publication"].dt.quarter
    dates["month"]   = dates["date_publication"].dt.month
    dates["day"]     = dates["date_publication"].dt.day
    dates.to_sql("dim_date", schema="gold", con=engine,
                 if_exists="append", index=False)
    dim_date = pd.read_sql("SELECT * FROM gold.dim_date", engine)
    dim_date["date_publication"] = pd.to_datetime(dim_date["date_publication"])
    log.info(f"  gold.dim_date : {len(dim_date)} rows")

    # ── dim_localisation ──────────────────────────────────────
    loc = df[["ville", "quartier"]].fillna({"quartier": "unknown"}).drop_duplicates()
    loc = loc.merge(sv, on="ville").merge(sq, on="quartier")
    loc[["ville_id", "quartier_id"]].to_sql(
        "dim_localisation", schema="gold", con=engine, if_exists="append", index=False)
    dim_loc = pd.read_sql("SELECT * FROM gold.dim_localisation", engine)
    log.info(f"  gold.dim_localisation : {len(dim_loc)} rows")

    # ── dim_transaction ───────────────────────────────────────
    tr = df["transaction"].dropna().unique()
    tr = [t for t in tr if str(t).strip().lower() != "nan"]
    pd.DataFrame({"transaction": sorted(tr)}).to_sql(
        "dim_transaction", schema="gold", con=engine, if_exists="append", index=False)
    dim_tr = pd.read_sql("SELECT * FROM gold.dim_transaction", engine)
    log.info(f"  gold.dim_transaction : {len(dim_tr)} rows")

    # ── dim_category ──────────────────────────────────────────
    cat = df[["categorie_prix", "categorie_surface", "luxury"]].drop_duplicates().dropna(
        subset=["categorie_prix"])
    cat = cat.rename(columns={"categorie_prix": "prix_category", "categorie_surface": "surface_category"})
    # Dédoublonnage sur la clé unique (prix_category, surface_category) — on garde luxury=True en priorité
    cat = (cat
           .sort_values("luxury", ascending=False)          # True avant False
           .drop_duplicates(subset=["prix_category", "surface_category"])
           .reset_index(drop=True))
    cat.to_sql("dim_category", schema="gold", con=engine, if_exists="append", index=False)
    dim_cat = pd.read_sql("SELECT * FROM gold.dim_category", engine)
    log.info(f"  gold.dim_category : {len(dim_cat)} rows")

    # ── subdim_anomalie_detail ────────────────────────────────
    detail_flag_cols = ["prix_outlier", "surface_outlier", "nb_chambres_outlier",
                        "nb_salles_bain_outlier", "etage_outlier", "logic_anomaly",
                        "suspicious_price", "suspicious_surface", "prix_par_m2_broken"]
    for col in detail_flag_cols:
        if col not in df.columns:
            df[col] = False
    for col in detail_flag_cols:
        df[col] = df[col].fillna(False).astype(bool)

    detail_unique = df[detail_flag_cols].drop_duplicates().copy()
    detail_unique.to_sql("subdim_anomalie_detail", schema="gold", con=engine,
                         if_exists="append", index=False)
    dim_detail = pd.read_sql("SELECT * FROM gold.subdim_anomalie_detail", engine)
    log.info(f"  gold.subdim_anomalie_detail : {len(dim_detail)} rows")

    # ── dim_anomalies ─────────────────────────────────────────
    anom = df[["annonce_id", "is_anomaly"] + detail_flag_cols].copy()
    anom["is_anomaly"] = anom["is_anomaly"].fillna(False).astype(bool)
    anom = anom.merge(dim_detail, on=detail_flag_cols, how="left")
    anom = anom[["annonce_id", "is_anomaly", "detail_id"]]
    anom.to_sql("dim_anomalies", schema="gold", con=engine,
                if_exists="append", index=False)
    dim_anom = pd.read_sql("SELECT * FROM gold.dim_anomalies", engine)
    log.info(f"  gold.dim_anomalies : {len(dim_anom)} rows  "
             f"(anomalies={dim_anom['is_anomaly'].sum()})")

    # ── dim_bien ──────────────────────────────────────────────
    bien = df[["type_bien", "annee_construction", "nb_chambres",
               "nb_salles_bain", "etage", "age_estime"]].drop_duplicates().dropna()
    bien = bien.astype({"annee_construction": int, "nb_chambres": int,
                        "nb_salles_bain": int, "etage": int, "age_estime": int})
    bien = (bien
            .merge(st, on="type_bien")
            .merge(sc, on="annee_construction")
            .merge(sca, on=["nb_chambres", "nb_salles_bain", "etage"]))
    bien[["type_id", "construction_id", "caracteristique_id", "age_estime"]].to_sql(
        "dim_bien", schema="gold", con=engine, if_exists="append", index=False)
    dim_bien = pd.read_sql("SELECT * FROM gold.dim_bien", engine)
    log.info(f"  gold.dim_bien : {len(dim_bien)} rows")

    # ── fact_annonces ─────────────────────────────────────────
    fact = df[["annonce_id", "date_publication", "ville", "quartier",
               "type_bien", "annee_construction", "nb_chambres", "nb_salles_bain",
               "etage", "age_estime", "transaction", "is_anomaly",
               "categorie_prix", "categorie_surface", "luxury",
               "prix", "surface", "prix_par_m2"]].copy()

    fact["date_publication"] = pd.to_datetime(fact["date_publication"])
    fact["quartier"]         = fact["quartier"].fillna("unknown")
    fact = fact.dropna(subset=["annonce_id", "date_publication",
                               "categorie_prix", "categorie_surface"])
    fact = fact.astype({"annee_construction": int, "nb_chambres": int,
                        "nb_salles_bain": int, "etage": int, "age_estime": int})

    fact = (fact
            .merge(dim_date.rename(columns={"date_publication": "date_publication"})[
                ["date_id", "date_publication"]], on="date_publication")
            .merge(sv, on="ville")
            .merge(sq, on="quartier")
            .merge(dim_loc, on=["ville_id", "quartier_id"])
            .merge(st, on="type_bien")
            .merge(sc, on="annee_construction")
            .merge(sca, on=["nb_chambres", "nb_salles_bain", "etage"])
            .merge(dim_bien, on=["type_id", "construction_id", "caracteristique_id"])
            .merge(dim_tr, on="transaction")
            .merge(dim_cat.rename(columns={
                "prix_category":    "categorie_prix",
                "surface_category": "categorie_surface"}),
                on=["categorie_prix", "categorie_surface", "luxury"])
            .merge(dim_anom[["annonce_id", "anomalie_id"]], on="annonce_id"))

    fact_final = fact[["annonce_id", "date_id", "localisation_id", "bien_id",
                        "transaction_id", "anomalie_id", "prix_category_id",
                        "prix", "surface", "prix_par_m2"]]
    fact_final.to_sql("fact_annonces", schema="gold", con=engine,
                      if_exists="append", index=False, chunksize=500)
    log.info(f"  gold.fact_annonces : {len(fact_final)} rows")

    # ── Indexes ───────────────────────────────────────────────
    with engine.begin() as conn:
        for idx_sql in [
            "CREATE INDEX IF NOT EXISTS idx_fact_date         ON gold.fact_annonces(date_id)",
            "CREATE INDEX IF NOT EXISTS idx_fact_loc          ON gold.fact_annonces(localisation_id)",
            "CREATE INDEX IF NOT EXISTS idx_fact_bien         ON gold.fact_annonces(bien_id)",
            "CREATE INDEX IF NOT EXISTS idx_fact_transaction  ON gold.fact_annonces(transaction_id)",
            "CREATE INDEX IF NOT EXISTS idx_fact_anomaly      ON gold.fact_annonces(anomalie_id)",
            "CREATE INDEX IF NOT EXISTS idx_fact_category     ON gold.fact_annonces(prix_category_id)",
            "CREATE INDEX IF NOT EXISTS idx_subdim_ville      ON gold.subdim_ville(ville)",
        ]:
            conn.execute(text(idx_sql))
    log.info("Indexes created ✓")

    # ── Export data_warehouse_ready.csv ───────────────────────
    dw_ready = pd.read_sql("""
        SELECT
            f.annonce_id,
            d.date_publication, d.year, d.quarter, d.month, d.day,
            sv.ville, sq.quartier,
            st.type_bien,
            tr.transaction,
            sc2.annee_construction,
            sca.nb_chambres, sca.nb_salles_bain, sca.etage,
            b.age_estime,
            cat.prix_category, cat.surface_category, cat.luxury,
            a.is_anomaly,
            f.prix, f.surface, f.prix_par_m2
        FROM gold.fact_annonces f
        JOIN gold.dim_date            d    ON d.date_id          = f.date_id
        JOIN gold.dim_localisation    l    ON l.localisation_id  = f.localisation_id
        JOIN gold.subdim_ville        sv   ON sv.ville_id        = l.ville_id
        JOIN gold.subdim_quartier     sq   ON sq.quartier_id     = l.quartier_id
        JOIN gold.dim_bien            b    ON b.bien_id          = f.bien_id
        JOIN gold.subdim_type_bien    st   ON st.type_id         = b.type_id
        JOIN gold.subdim_construction sc2  ON sc2.construction_id = b.construction_id
        JOIN gold.subdim_caracteristique sca ON sca.caracteristique_id = b.caracteristique_id
        JOIN gold.dim_transaction     tr   ON tr.transaction_id  = f.transaction_id
        JOIN gold.dim_category        cat  ON cat.prix_category_id = f.prix_category_id
        JOIN gold.dim_anomalies       a    ON a.anomalie_id      = f.anomalie_id
    """, engine)

    GOLD_CSV.parent.mkdir(parents=True, exist_ok=True)
    dw_ready.to_csv(GOLD_CSV, index=False)
    log.info(f"Exported → {GOLD_CSV}  ({len(dw_ready)} rows)")

    # ── Log entry ──────────────────────────────────────────────
    engine_bronze = get_engine(SCHEMA_BRONZE)
    with engine_bronze.begin() as conn:
        conn.execute(text("""
            INSERT INTO audit.load_logs (layer, table_name, rows_loaded, load_status, error_message)
            VALUES ('gold', 'gold.fact_annonces', :n, 'SUCCESS', NULL)
        """), {"n": len(fact_final)})

    log.info(" GOLD LAYER — Done ✓")
    log.info("═" * 60)
    return len(fact_final)


if __name__ == "__main__":
    build_warehouse()