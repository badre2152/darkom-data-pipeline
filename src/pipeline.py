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
    try:
        run_migrations()
    except Exception as exc:
        log.error(f"🔧 Migrations FAILED: {exc}", exc_info=True)
        sys.exit(1)
    log.info(f"🔧 Migrations done  [{time.time()-t0:.1f}s]")

    # ── 🥉 Bronze ─────────────────────────────────────────────
    t0 = time.time()
    try:
        bronze_rows = load_staging(csv_path)
    except Exception as exc:
        log.error(f"🥉 Bronze FAILED: {exc}", exc_info=True)
        sys.exit(1)
    log.info(f"🥉 Bronze done  [{time.time()-t0:.1f}s]  rows={bronze_rows}")

    # ── 🥈 Silver ─────────────────────────────────────────────
    t0 = time.time()
    try:
        silver_rows = clean_data()
    except Exception as exc:
        log.error(f"🥈 Silver FAILED: {exc}", exc_info=True)
        sys.exit(1)
    log.info(f"🥈 Silver done  [{time.time()-t0:.1f}s]  rows={silver_rows}")

    # ── 🥇 Gold ───────────────────────────────────────────────
    t0 = time.time()
    try:
        gold_rows = build_warehouse()
    except Exception as exc:
        log.error(f"🥇 Gold FAILED: {exc}", exc_info=True)
        sys.exit(1)
    log.info(f"🥇 Gold done    [{time.time()-t0:.1f}s]  rows={gold_rows}")

    elapsed = time.time() - start
    W = 58  # inner width (between ╔ and ╗)
    log.info("╔" + "═" * W + "╗")
    log.info(f"║  {'✅  Pipeline completed in ' + f'{elapsed:.1f}s':<{W-2}}║")
    log.info(f"║  {'Bronze : ' + str(bronze_rows) + ' rows':<{W-2}}║")
    log.info(f"║  {'Silver : ' + str(silver_rows) + ' rows':<{W-2}}║")
    log.info(f"║  {'Gold   : ' + str(gold_rows)   + ' rows':<{W-2}}║")
    log.info("╚" + "═" * W + "╝")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Darkom.ma — Data Pipeline")
    parser.add_argument(
        "--csv", required=True,
        help="Path to the raw CSV file (darkom_annonces.csv)"
    )
    args = parser.parse_args()
    run_pipeline(args.csv)