"""
utils/migrations.py
Creates schemas (bronze / silver / gold) and the staging table.
Run ONCE before the pipeline: make migrate
"""

from sqlalchemy import text
from src.utils.db import get_engine
from src.utils.logger import get_logger

log = get_logger("migrations")


def run_migrations():
    log.info("═" * 60)
    log.info("Starting migrations …")

    engine = get_engine("public")

    with engine.begin() as conn:

        # ── 1. Schemas ────────────────────────────────────────
        for schema in ("bronze", "silver", "gold"):
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
            log.info(f"Schema '{schema}' — OK")

        # ── 2. Staging table (bronze) ─────────────────────────
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS bronze.stg_annonces (
                annonce_id          TEXT,
                date_publication    TEXT,
                titre               TEXT,
                ville               TEXT,
                quartier            TEXT,
                type_bien           TEXT,
                transaction         TEXT,
                prix                TEXT,
                surface             TEXT,
                nb_chambres         TEXT,
                nb_salles_bain      TEXT,
                etage               TEXT,
                annee_construction  TEXT,
                _loaded_at          TIMESTAMP DEFAULT NOW()
            )
        """))
        log.info("Table bronze.stg_annonces — OK")

        # ── 3. Load-logs table ────────────────────────────────
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS bronze.load_logs (
                log_id        SERIAL PRIMARY KEY,
                layer         VARCHAR(20),
                table_name    VARCHAR(100),
                rows_loaded   INTEGER,
                load_status   VARCHAR(10),
                error_message TEXT,
                logged_at     TIMESTAMP DEFAULT NOW()
            )
        """))
        log.info("Table bronze.load_logs — OK")

    log.info("All migrations completed ✓")
    log.info("═" * 60)


if __name__ == "__main__":
    run_migrations()