"""
pipeline.py — Master orchestrator
Runs Migrations → Bronze → Silver → Gold with a single command:
    python -m src.pipeline --csv path/to/darkom_annonces.csv
or via Makefile:
    make pipeline CSV=path/to/file.csv
"""

import argparse
import sys
import time

from src.utils.logger import get_logger
from src.staging.load_staging import load_staging
from src.clean.clean_data import clean_data
from src.warehouse.bi_schema import build_warehouse
from src.utils.migrations import run_migrations

log = get_logger("pipeline")


def run_pipeline(csv_path: str):
    log.info("╔" + "═" * 58 + "╗")
    log.info("║  DARKOM.MA — Full Pipeline  Bronze → Silver → Gold    ║")
    log.info("╚" + "═" * 58 + "╝")
    start = time.time()

    # ── 🔧 Migrations ─────────────────────────────────────────
    t0 = time.time()
    run_migrations()
    log.info(f"🔧 Migrations done  [{time.time()-t0:.1f}s]")

    # ── 🥉 Bronze ─────────────────────────────────────────────
    t0 = time.time()
    bronze_rows = load_staging(csv_path)
    log.info(f"🥉 Bronze done  [{time.time()-t0:.1f}s]  rows={bronze_rows}")

    # ── 🥈 Silver ─────────────────────────────────────────────
    t0 = time.time()
    silver_rows = clean_data()
    log.info(f"🥈 Silver done  [{time.time()-t0:.1f}s]  rows={silver_rows}")

    # ── 🥇 Gold ───────────────────────────────────────────────
    t0 = time.time()
    gold_rows = build_warehouse()
    log.info(f"🥇 Gold done    [{time.time()-t0:.1f}s]  rows={gold_rows}")

    elapsed = time.time() - start
    log.info("╔" + "═" * 58 + "╗")
    log.info(f"║  ✅  Pipeline completed in {elapsed:.1f}s" + " " * (31 - len(f"{elapsed:.1f}")) + "║")
    log.info(f"║  Bronze : {bronze_rows} rows" + " " * (47 - len(str(bronze_rows))) + "║")
    log.info(f"║  Silver : {silver_rows} rows" + " " * (47 - len(str(silver_rows))) + "║")
    log.info(f"║  Gold   : {gold_rows} rows" + " " * (47 - len(str(gold_rows))) + "║")
    log.info("╚" + "═" * 58 + "╝")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Darkom.ma — Data Pipeline")
    parser.add_argument(
        "--csv", required=True,
        help="Path to the raw CSV file (darkom_annonces.csv)"
    )
    args = parser.parse_args()
    run_pipeline(args.csv)