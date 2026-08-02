import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.store import nano_store, store


@pytest.fixture()
def client(monkeypatch):
    # No DUMP_URL/DUMP_PATH set - main.py's lifespan hook leaves the stores
    # empty on startup. Explicitly reset the shared store singletons before
    # each test too, since they're no longer recreated per-test the way a
    # locally-scoped module variable would be.
    monkeypatch.delenv("DUMP_URL", raising=False)
    monkeypatch.delenv("DUMP_PATH", raising=False)
    store.load([])
    nano_store.load([])

    with TestClient(app) as test_client:
        yield test_client
