import shutil
import pandas as pd
from pathlib import Path
from sqlalchemy import text

from src.config import BRONZE_CSV, SCHEMA_BRONZE
from src.utils.db import get_engine
from src.utils.logger import get_logger

log = get_logger("staging")


def load_staging(source_csv_path: str) -> int:
   
    log.info("═" * 60)
    log.info(" BRONZE LAYER — Starting …")

    # ── 1. Copy raw CSV to data/bronze/ (read-only reference) ─
    BRONZE_CSV.parent.mkdir(parents=True, exist_ok=True)
    if Path(source_csv_path).resolve() != BRONZE_CSV.resolve():
        shutil.copy2(source_csv_path, BRONZE_CSV)
        log.info(f"Raw CSV copied → {BRONZE_CSV}")
    else:
        log.info("CSV already in bronze directory — skipping copy.")

    # ── 2. Read CSV (all columns as str to avoid type errors) ─
    log.info(f"Reading CSV from {source_csv_path} …")
    df = pd.read_csv(source_csv_path, dtype=str)
    log.info(f"CSV loaded : {len(df)} rows × {len(df.columns)} columns")

    # ── 3. Load into bronze.stg_annonces ─────────────────────
    engine = get_engine(SCHEMA_BRONZE)

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE bronze.stg_annonces"))
        log.info("bronze.stg_annonces truncated (fresh load)")

    df.to_sql(
        name      = "stg_annonces",
        schema    = SCHEMA_BRONZE,
        con       = engine,
        if_exists = "append",
        index     = False,
        chunksize = 500,
    )
    log.info(f"Loaded {len(df)} rows → bronze.stg_annonces")

    # ── 4. Log entry ──────────────────────────────────────────
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO audit.load_logs (layer, table_name, rows_loaded, load_status, error_message)
            VALUES ('bronze', 'bronze.stg_annonces', :n, 'SUCCESS', NULL)
        """), {"n": len(df)})

    log.info(" BRONZE LAYER — Done ✓")
    log.info("═" * 60)
    return len(df)


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else str(BRONZE_CSV)
    load_staging(path)