# Troubleshooting Guide

## Setup issues

### `ModuleNotFoundError: No module named 'src'`
Run all commands from the project root (where `Makefile` lives), not from inside `src/`:
```bash
cd jeury-brief
python -m src.pipeline --csv data/bronze/darkom_annonces_raw.csv
```

### `could not connect to server: Connection refused`
PostgreSQL is not running or credentials are wrong.
1. Start PostgreSQL: `brew services start postgresql` (macOS) or `sudo service postgresql start` (Linux).
2. Check your `.env` file — copy `.env.example` and fill in real values.
3. Confirm the database exists: `psql -U postgres -c "\l" | grep darkom_dwh`.

### `ROOT_DIR` pointing to the wrong place
This was a bug in the original project (hardcoded `/Users/mac/Desktop/…`).
It is fixed — `config.py` now uses `Path(__file__).parent.parent`.

## Pipeline failures

### `🥉 Bronze FAILED` in pipeline.log
- CSV file path passed to `--csv` does not exist.
- CSV encoding issue: the file must be UTF-8. Convert with `iconv -f latin1 -t utf-8 file.csv > file_utf8.csv`.

### `🥈 Silver FAILED` in pipeline.log
Check `clean.log` for the traceback. Common causes:
- Bronze table `bronze.stg_annonces` is empty (Bronze stage failed before).
- A column expected by the cleaning script is missing from the CSV.

### `🥇 Gold FAILED` in pipeline.log
Check `bi_schema.log`. Common causes:
- Silver table is empty or missing a required column such as `prix_par_m2_broken` (regenerate Silver first).
- Unique constraint violation in a sub-dimension table — usually means the pipeline was interrupted mid-run. Run `make clean-db` (drops bronze/silver/gold schemas) then `make pipeline` to restart cleanly.

## Data quality issues

### 39% anomaly rate
Expected before the per-transaction IQR fix. After the fix the rate should be ≤ 20%.
If still high, check that `transaction` has no NaN rows (see `clean.log`).

### prix_par_m2 < 100 MAD/m²
These are flagged in `prix_par_m2_broken`. In Power BI add a filter `prix_par_m2_broken = FALSE` to exclude them from price analyses.

### duplex not in Power BI type_bien slicer
Duplex is intentionally kept as a valid type. It is included in `gold.subdim_type_bien`. If it does not appear, refresh the Power BI dataset.