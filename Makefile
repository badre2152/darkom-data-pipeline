# ============================================================
#  Darkom.ma — Makefile
#  Usage:
#    make migrate
#    make pipeline CSV=data/bronze/darkom_annonces_raw.csv
#    make bronze   CSV=data/bronze/darkom_annonces_raw.csv
#    make silver
#    make gold
#    make validate
# ============================================================

.PHONY: migrate pipeline bronze silver gold validate install clean-db

# Default CSV path (override with CSV=path/to/file.csv)
CSV ?= data/bronze/darkom_annonces_raw.csv

# ── Install dependencies ──────────────────────────────────────
install:
	pip install -r requirements.txt

# ── Run migrations (once) ────────────────────────────────────
migrate:
	python -m src.utils.migrations

# ── Full pipeline: Bronze → Silver → Gold ────────────────────
pipeline:
	python -m src.pipeline --csv $(CSV)

# ── Individual layers ─────────────────────────────────────────
bronze:
ifndef CSV
	$(error CSV is not set. Usage: make bronze CSV=path/to/file.csv)
endif
	python -m src.staging.load_staging $(CSV)

silver:
	python -m src.clean.clean_data

gold:
	python -m src.warehouse.bi_schema

# ── Validate Data Warehouse ───────────────────────────────────
validate:
	python -m src.utils.validate

# ── Drop all DWH schemas (bronze / silver / gold) ────────────
# Use before a full re-run from scratch to avoid stale data.
clean-db:
	python -c "\
from src.utils.db import get_engine; from sqlalchemy import text; \
e = get_engine('public'); \
[e.connect().execute(text(f'DROP SCHEMA IF EXISTS {s} CASCADE')) or print(f'Dropped {s}') \
 for s in ('gold','silver','bronze')]"