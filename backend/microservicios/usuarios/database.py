import os
from typing import Annotated, Generator

from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine

# Base de datos PROPIA del servicio de usuarios.
# En local usa users.sqlite3; para produccion (Render) define DATABASE_URL.
db_url = os.getenv("DATABASE_URL", "sqlite:///users.sqlite3")

# Render entrega "postgres://", pero SQLAlchemy necesita "postgresql://"
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
engine = create_engine(db_url, connect_args=connect_args)


def create_tables():
    import models  # noqa: F401  (registra las tablas antes de crearlas)

    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]