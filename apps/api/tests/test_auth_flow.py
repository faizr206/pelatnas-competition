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

    response = client.post("/api/v1/auth/logout")
    assert response.status_code == 204

    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
