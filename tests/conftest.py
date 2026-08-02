import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch):
    # No DUMP_URL/DUMP_PATH set - main.py's lifespan hook leaves the store
    # empty on startup; tests populate it directly via main_module.store.load().
    monkeypatch.delenv("DUMP_URL", raising=False)
    monkeypatch.delenv("DUMP_PATH", raising=False)

    from app import main as main_module

    importlib.reload(main_module)

    with TestClient(main_module.app) as test_client:
        yield test_client, main_module
