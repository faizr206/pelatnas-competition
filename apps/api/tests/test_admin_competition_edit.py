def _login_admin(client) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "admin1234"},
    )
    assert response.status_code == 200


def test_admin_can_update_competition_and_phase_details(client) -> None:
    _login_admin(client)

    create_response = client.post(
        "/api/v1/competitions",
        json={
            "slug": "editable-comp",
            "title": "Editable Competition",
            "description": "Original description",
            "visibility": "public",
            "status": "draft",
            "scoring_metric": "row_count",
            "scoring_direction": "max",
            "best_submission_rule": "best_score",
            "max_submissions_per_day": 5,
            "max_runtime_minutes": 20,
            "max_memory_mb": 4096,
            "max_cpu": 2,
            "allow_csv_submissions": True,
            "allow_notebook_submissions": True,
            "source_retention_days": 30,
            "log_retention_days": 14,
            "artifact_retention_days": 14,
            "phase": {
                "name": "main",
                "starts_at": "2026-01-01T00:00:00Z",
                "ends_at": "2026-12-31T00:00:00Z",
                "submission_limit_per_day": 5,
                "scoring_version": "v1",
                "rules_version": "v1",
            },
        },
    )
    assert create_response.status_code == 201

    update_response = client.patch(
        "/api/v1/competitions/editable-comp",
        json={
            "title": "Edited Competition",
            "description": "Updated description",
            "visibility": "private",
            "status": "active",
            "scoring_metric": "f1_score",
            "scoring_direction": "min",
            "best_submission_rule": "latest_submission",
            "max_submissions_per_day": 3,
            "max_runtime_minutes": 45,
            "max_memory_mb": 8192,
            "max_cpu": 4,
            "allow_csv_submissions": False,
            "allow_notebook_submissions": True,
            "source_retention_days": 60,
            "log_retention_days": 21,
            "artifact_retention_days": 30,
            "private_leaderboard_opens_at": "2026-10-15T12:00:00Z",
            "phase": {
                "name": "playoffs",
                "starts_at": "2026-02-01T00:00:00Z",
                "ends_at": "2026-11-30T00:00:00Z",
                "submission_limit_per_day": 2,
                "scoring_version": "v2",
                "rules_version": "v3",
            },
        },
    )
    assert update_response.status_code == 200

    payload = update_response.json()
    assert payload["title"] == "Edited Competition"
    assert payload["visibility"] == "private"
    assert payload["max_runtime_minutes"] == 45
    assert payload["allow_csv_submissions"] is False
    assert payload["private_leaderboard_opens_at"].startswith("2026-10-15T12:00:00")
    assert payload["phases"][0]["name"] == "playoffs"
    assert payload["phases"][0]["submission_limit_per_day"] == 2
    assert payload["phases"][0]["scoring_version"] == "v2"
