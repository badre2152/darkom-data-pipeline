"""
utils/logger.py
get_logger(name) → writes to its own log file AND pipeline.log
"""

import logging
from pathlib import Path
from src.config import LOGS_DIR, LOG_PIPELINE

# Ensure logs directory exists
LOGS_DIR.mkdir(parents=True, exist_ok=True)

_LOG_MAP = {
    "staging"   : LOGS_DIR / "staging.log",
    "clean"     : LOGS_DIR / "clean.log",
    "bi_schema" : LOGS_DIR / "bi_schema.log",
    "migrations": LOGS_DIR / "migrations.log",
    "pipeline"  : LOG_PIPELINE,
}

_FMT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str) -> logging.Logger:
    """
    Returns a logger that writes to:
      - logs/<name>.log   (layer-specific)
      - logs/pipeline.log (global)
    """
    logger = logging.getLogger(name)

    if logger.handlers:          # avoid duplicate handlers on re-import
        return logger

    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(_FMT, datefmt=_DATE_FMT)

    # ── Layer-specific file handler ──────────────────────────
    layer_log = _LOG_MAP.get(name, LOGS_DIR / f"{name}.log")
    fh_layer = logging.FileHandler(layer_log, encoding="utf-8")
    fh_layer.setFormatter(formatter)
    logger.addHandler(fh_layer)

    # ── Global pipeline.log handler ──────────────────────────
    fh_pipeline = logging.FileHandler(LOG_PIPELINE, encoding="utf-8")
    fh_pipeline.setFormatter(formatter)
    logger.addHandler(fh_pipeline)

    # ── Console handler ──────────────────────────────────────
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger