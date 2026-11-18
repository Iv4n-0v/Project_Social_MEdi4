import os
from typing import Annotated, Generator

from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine

# Base de datos PROPIA del servicio de analisis.
# En local usa analysis.sqlite3; para produccion (Render) define DATABASE_URL.
db_url = os.getenv("DATABASE_URL", "sqlite:///analysis.sqlite3")

# Render entrega "postgres://", pero SQLAlchemy necesita "postgresql://"
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
engine = create_engine(db_url, connect_args=connect_args)


def create_tables():
    import models  # noqa: F401  (registra las tablas antes de crearlas)

    SQLModel.metadata.create_all(engine)
    ensure_owner_column("analysis")


def ensure_owner_column(table: str) -> None:
    """Agrega owner_account_id a una tabla que ya existia (create_all no altera tablas).

    Es seguro repetirlo: solo actua si la columna falta. No borra ni cambia datos.
    """
    from sqlalchemy import inspect, text

    cols = {c["name"] for c in inspect(engine).get_columns(table)}
    if "owner_account_id" not in cols:
        with engine.begin() as conn:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN owner_account_id INTEGER"))
            conn.execute(
                text(f"CREATE INDEX IF NOT EXISTS ix_{table}_owner_account_id ON {table} (owner_account_id)")
            )


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
