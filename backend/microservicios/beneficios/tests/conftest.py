import os
import sys

# Permite `import main`, `import models`... (el servicio no es un paquete)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

import database
import models  # noqa: F401  (registra las tablas)
from main import app


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def override_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[database.get_session] = override_session
    # TestClient sin `with` => no ejecuta el lifespan (que apunta a la BD real)
    yield TestClient(app)
    app.dependency_overrides.clear()
