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
from storage import get_storage


class FakeStorage:
    """Almacenamiento falso: no toca Supabase."""

    def __init__(self):
        self.uploads = []

    async def upload(self, content, filename, content_type, folder):
        self.uploads.append((filename, content_type, folder, len(content)))
        return f"https://fake.test/{folder}/{filename}"


@pytest.fixture()
def storage():
    return FakeStorage()


@pytest.fixture()
def client(storage):
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
    app.dependency_overrides[get_storage] = lambda: storage
    # TestClient sin `with` => no ejecuta el lifespan (que apunta a la BD real)
    yield TestClient(app)
    app.dependency_overrides.clear()
