"""Database engine construction and transactional SQL execution."""

import os

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, text

from src.utils.logger import get_logger

load_dotenv()
log = get_logger("db")

_ALLOWED_SCHEMAS = frozenset({"public", "bronze", "silver", "gold", "audit"})


def get_engine(schema: str = "public"):
    if schema not in _ALLOWED_SCHEMAS:
        raise ValueError(f"Unsupported database schema: {schema!r}")

    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "")
    host = os.getenv("DB_HOST", "localhost")
    port = int(os.getenv("DB_PORT", "5432"))
    dbname = os.getenv("DB_NAME", "darkom_dwh")

    url = URL.create(
        drivername="postgresql+psycopg2",
        username=user,
        password=password,
        host=host,
        port=port,
        database=dbname,
    )

    engine = create_engine(
        url,
        connect_args={"options": f"-csearch_path={schema}"},
        pool_pre_ping=True,
    )

    log.debug(
        "Engine created for schema=%s db=%s host=%s port=%s user=%s",
        schema, dbname, host, port, user,
    )
    return engine


def execute_sql(engine, sql: str):
    with engine.begin() as conn:
        conn.execute(text(sql))
