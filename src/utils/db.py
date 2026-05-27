import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from src.utils.logger import get_logger

load_dotenv()
log = get_logger("db")


def get_engine(schema: str = "public"):
   
    user     = os.getenv("DB_USER",     "postgres")
    password = os.getenv("DB_PASSWORD", "")
    host     = os.getenv("DB_HOST",     "localhost")
    port     = os.getenv("DB_PORT",     "5432")
    dbname   = os.getenv("DB_NAME",     "darkom_dwh")

    url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"

    engine = create_engine(
        url,
        connect_args={"options": f"-csearch_path={schema}"},
        pool_pre_ping=True,
    )

    log.debug("Engine created → schema=%s  db=%s@%s:%s user=%s", schema, dbname, host, port, user)
    return engine


def execute_sql(engine, sql: str):
    
    with engine.begin() as conn:
        conn.execute(text(sql))