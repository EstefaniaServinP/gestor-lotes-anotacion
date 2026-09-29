"""
Fixtures de pytest.

Las pruebas usan una base de datos aparte (gestor_lotes_test) en el MongoDB
indicado por TEST_MONGO_URI (por defecto localhost). La BD se borra al terminar.
Si MongoDB no está disponible, las pruebas se omiten.
"""

import json
import os
import sys

import pytest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
TEST_DB = "gestor_lotes_test"
TEST_URI = os.environ.get("TEST_MONGO_URI", "mongodb://localhost:27017")

# Configurar el entorno ANTES de importar app/db (load_dotenv no sobrescribe variables ya definidas)
os.environ["MONGO_URI"] = TEST_URI
os.environ["MONGO_DB"] = TEST_DB
os.environ["MASKS_URI"] = TEST_URI
os.environ["MASKS_DB"] = TEST_DB
os.environ["MASKS_COLLECTION"] = "masks.files"
os.environ["ADMIN_PASSWORD"] = "contraseña-de-prueba"

sys.path.insert(0, ROOT)


@pytest.fixture(scope="session")
def app_module():
    from pymongo import MongoClient

    client = MongoClient(TEST_URI, serverSelectionTimeoutMS=2000)
    try:
        client.admin.command("ping")
    except Exception as e:
        pytest.skip(f"MongoDB no disponible en {TEST_URI}: {e}")

    client.drop_database(TEST_DB)

    import app as app_module
    app_module.app.config["TESTING"] = True
    app_module.init_db()

    yield app_module

    client.drop_database(TEST_DB)
    client.close()


@pytest.fixture
def client(app_module):
    """Cliente de Flask con la colección de batches vacía en cada prueba."""
    app_module.batches_col.delete_many({})
    with app_module.app.test_client() as c:
        yield c


@pytest.fixture
def upload_payload():
    with open(os.path.join(FIXTURES, "test_batches_upload.json"), encoding="utf-8") as f:
        return json.load(f)
