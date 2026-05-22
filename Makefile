# ============================================================
#  Darkom.ma — Makefile
#  Usage:
#    make migrate
#    make pipeline CSV=data/bronze/darkom_annonces_raw.csv
#    make bronze   CSV=data/bronze/darkom_annonces_raw.csv
#    make silver
#    make gold
# ============================================================

.PHONY: migrate pipeline bronze silver gold install

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
	python -m src.staging.load_staging $(CSV)

silver:
	python -m src.clean.clean_data

gold:
	python -m src.warehouse.bi_schema