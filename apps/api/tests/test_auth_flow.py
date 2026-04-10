import importlib
from pathlib import Path

from fastapi.testclient import TestClient

from apps.api.app.config import get_settings
from packages.db.base import Base
from packages.db.session import get_engine
from packages.security.login_rate_limit import login_rate_limiter
from packages.storage.service import get_storage


def test_login_me_logout_flow(client) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "admin1234"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "admin@example.com"
    assert response.json()["must_change_password"] is False

    response = client.get("/api/v1/auth/me")
    assert response.status_code == 200
    assert response.json()["display_name"] == "Phase Zero Admin"
    assert response.json()["must_change_password"] is False
    assert response.json()["hide_from_leaderboard"] is False

    response = client.post("/api/v1/auth/logout")
    assert response.status_code == 204

    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_login_rate_limit_blocks_repeated_failed_attempts(client) -> None:
    for _ in range(10):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "wrong-password"},
        )
        assert response.status_code == 401

    blocked_response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "wrong-password"},
    )
    assert blocked_response.status_code == 429
    assert blocked_response.headers["retry-after"]


def test_session_cookie_can_be_marked_secure(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "secure-session.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{db_path}")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/15")
    monkeypatch.setenv("GARAGE_ENDPOINT", "memory://")
    monkeypatch.setenv("GARAGE_ACCESS_KEY", "test-access")
    monkeypatch.setenv("GARAGE_SECRET_KEY", "test-secret")
    monkeypatch.setenv("GARAGE_BUCKET", "test-bucket")
    monkeypatch.setenv("WORKER_LOCAL_TMP_DIR", str(tmp_path / "worker-tmp"))
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("SESSION_HTTPS_ONLY", "true")
    monkeypatch.setenv("DEFAULT_ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("DEFAULT_ADMIN_PASSWORD", "admin1234")
    monkeypatch.setenv("DEFAULT_ADMIN_NAME", "Phase Zero Admin")
    monkeypatch.setenv("DEFAULT_COMPETITION_SLUG", "test-comp")
    monkeypatch.setenv("DEFAULT_COMPETITION_TITLE", "Test Competition")
    monkeypatch.setenv("DEFAULT_COMPETITION_DESCRIPTION", "Test Competition Description")

    get_settings.cache_clear()
    get_engine.cache_clear()
    get_storage.cache_clear()
    login_rate_limiter.reset()

    engine = get_engine()
    Base.metadata.create_all(bind=engine)

    from apps.api.app import main as main_module

    main_module = importlib.reload(main_module)
    try:
        with TestClient(main_module.app) as secure_client:
            response = secure_client.post(
                "/api/v1/auth/login",
                json={"email": "admin@example.com", "password": "admin1234"},
            )
            assert response.status_code == 200
            assert "secure" in response.headers["set-cookie"]
    finally:
        Base.metadata.drop_all(bind=engine)
        monkeypatch.setenv("SESSION_HTTPS_ONLY", "false")
        get_settings.cache_clear()
        get_engine.cache_clear()
        get_storage.cache_clear()
        login_rate_limiter.reset()
        importlib.reload(main_module)


def test_admin_can_hide_own_submissions_from_leaderboard(client) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "admin1234"},
    )
    assert response.status_code == 200

    update_response = client.patch(
        "/api/v1/auth/me/leaderboard-visibility",
        json={"hide_from_leaderboard": True},
    )
    assert update_response.status_code == 200
    assert update_response.json()["hide_from_leaderboard"] is True
