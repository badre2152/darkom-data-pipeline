"""
config.py — Project constants and paths
"""

from pathlib import Path

# ─── Root ────────────────────────────────────────────────────
# Resolved relative to this file so the project runs on any machine.
ROOT_DIR = Path(__file__).parent.parent

# ─── Data paths ──────────────────────────────────────────────
DATA_DIR          = ROOT_DIR / "data"
BRONZE_DIR        = DATA_DIR / "bronze"
SILVER_DIR        = DATA_DIR / "silver"
GOLD_DIR          = DATA_DIR / "gold" / "bi"

BRONZE_CSV        = BRONZE_DIR / "darkom_annonces_raw.csv"
SILVER_CSV        = SILVER_DIR / "data_clean.csv"
GOLD_CSV          = GOLD_DIR   / "data_warehouse_ready.csv"

# ─── Log paths ───────────────────────────────────────────────
LOGS_DIR          = ROOT_DIR / "logs"
LOG_STAGING       = LOGS_DIR / "staging.log"
LOG_CLEAN         = LOGS_DIR / "clean.log"
LOG_BI_SCHEMA     = LOGS_DIR / "bi_schema.log"
LOG_PIPELINE      = LOGS_DIR / "pipeline.log"
LOG_MIGRATIONS    = LOGS_DIR / "migrations.log"
LOG_DB            = LOGS_DIR / "db.log"
LOG_VALIDATE      = LOGS_DIR / "validate.log"

# ─── Database schemas ────────────────────────────────────────
SCHEMA_BRONZE     = "bronze"
SCHEMA_SILVER     = "silver"
SCHEMA_GOLD       = "gold"

# ─── Cleaning thresholds ─────────────────────────────────────
SUSPICIOUS_PRICE_THRESHOLD   = 5_000      # MAD
SUSPICIOUS_SURFACE_THRESHOLD = 15         # m²
IQR_MULTIPLIER               = 1.5

# ─── Feature engineering ─────────────────────────────────────
SURFACE_BINS   = [0, 80, 150, float("inf")]
SURFACE_LABELS = ["petit", "moyen", "grand"]