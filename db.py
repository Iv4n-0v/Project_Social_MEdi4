from fastapi import FastAPI, Depends
from sqlmodel import SQLModel, create_engine, Session
from typing import Generator, Annotated

db_name = "social_impact.sqlite3"
db_url = f"sqlite:///{db_name}"

engine = create_engine(db_url, echo=True)

# Crear tablas al iniciar la app
def create_tables(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield

# Sesión de DB
def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

# Dependencia para routers
SessionDep = Annotated[Session, Depends(get_session)]