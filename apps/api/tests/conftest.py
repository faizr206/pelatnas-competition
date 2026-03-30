from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from apps.api.app.config import get_settings
from packages.db import models  # noqa: F401
from packages.db.base import Base
from packages.db.session import get_engine


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{db_path}")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/15")
    monkeypatch.setenv("LOCAL_STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("DEFAULT_ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("DEFAULT_ADMIN_PASSWORD", "admin1234")
    monkeypatch.setenv("DEFAULT_ADMIN_NAME", "Phase Zero Admin")
    monkeypatch.setenv("DEFAULT_COMPETITION_SLUG", "test-comp")
    monkeypatch.setenv("DEFAULT_COMPETITION_TITLE", "Test Competition")
    monkeypatch.setenv("DEFAULT_COMPETITION_DESCRIPTION", "Test Competition Description")

    get_settings.cache_clear()
    get_engine.cache_clear()

    engine = get_engine()
    Base.metadata.create_all(bind=engine)

    from apps.api.app.main import app

    with TestClient(app) as test_client:
        yield test_client

    Base.metadata.drop_all(bind=engine)
    get_settings.cache_clear()
    get_engine.cache_clear()
