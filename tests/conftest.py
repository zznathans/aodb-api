import os
import tempfile

import pytest


@pytest.fixture()
def client(monkeypatch):
    fd, path = tempfile.mkstemp(suffix=".sqlite3")
    os.close(fd)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{path}")

    # main.py builds its SessionLocal at import time, so import must happen
    # after DATABASE_URL is set for each test's isolated sqlite file.
    import importlib

    from app import main as main_module

    importlib.reload(main_module)

    from fastapi.testclient import TestClient

    with TestClient(main_module.app) as test_client:
        yield test_client, main_module

    os.remove(path)
