def _login_admin(client) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "admin1234"},
    )
    assert response.status_code == 200


def _login_user(client, *, email: str, password: str):
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )


def test_admin_can_create_user_and_user_can_rotate_default_password(client) -> None:
    _login_admin(client)

    create_response = client.post(
        "/api/v1/admin/users",
        json={
            "email": "participant@example.com",
            "display_name": "Participant One",
            "default_password": "temp-pass-123",
            "is_admin": False,
            "status": "active",
        },
    )
    assert create_response.status_code == 201
    created_user = create_response.json()
    assert created_user["email"] == "participant@example.com"
    assert created_user["must_change_password"] is True
    assert created_user["status"] == "active"

    client.post("/api/v1/auth/logout")

    login_response = _login_user(
        client,
        email="participant@example.com",
        password="temp-pass-123",
    )
    assert login_response.status_code == 200
    assert login_response.json()["must_change_password"] is True

    change_password_response = client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "temp-pass-123",
            "new_password": "new-secure-456",
        },
    )
    assert change_password_response.status_code == 200
    assert change_password_response.json()["must_change_password"] is False

    client.post("/api/v1/auth/logout")

    old_login_response = _login_user(
        client,
        email="participant@example.com",
        password="temp-pass-123",
    )
    assert old_login_response.status_code == 401

    new_login_response = _login_user(
        client,
        email="participant@example.com",
        password="new-secure-456",
    )
    assert new_login_response.status_code == 200
    assert new_login_response.json()["must_change_password"] is False


def test_admin_can_list_update_and_reset_user_password(client) -> None:
    _login_admin(client)

    create_response = client.post(
        "/api/v1/admin/users",
        json={
            "email": "mentor@example.com",
            "display_name": "Mentor Account",
            "default_password": "mentor-pass-123",
            "is_admin": True,
            "status": "active",
        },
    )
    assert create_response.status_code == 201
    user_id = create_response.json()["id"]

    list_response = client.get("/api/v1/admin/users")
    assert list_response.status_code == 200
    assert [user["email"] for user in list_response.json()] == [
        "mentor@example.com",
        "admin@example.com",
    ]

    update_response = client.patch(
        f"/api/v1/admin/users/{user_id}",
        json={
            "display_name": "Mentor Reviewer",
            "is_admin": False,
            "status": "suspended",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["display_name"] == "Mentor Reviewer"
    assert update_response.json()["is_admin"] is False
    assert update_response.json()["status"] == "suspended"

    reset_response = client.post(
        f"/api/v1/admin/users/{user_id}/reset-password",
        json={"default_password": "mentor-pass-999"},
    )
    assert reset_response.status_code == 200
    assert reset_response.json()["must_change_password"] is True

    client.post("/api/v1/auth/logout")

    suspended_login_response = _login_user(
        client,
        email="mentor@example.com",
        password="mentor-pass-999",
    )
    assert suspended_login_response.status_code == 403


def test_non_admin_cannot_access_user_management_endpoints(client) -> None:
    _login_admin(client)
    create_response = client.post(
        "/api/v1/admin/users",
        json={
            "email": "member@example.com",
            "display_name": "Member",
            "default_password": "member-pass-123",
            "is_admin": False,
            "status": "active",
        },
    )
    assert create_response.status_code == 201

    client.post("/api/v1/auth/logout")
    login_response = _login_user(
        client,
        email="member@example.com",
        password="member-pass-123",
    )
    assert login_response.status_code == 200

    response = client.get("/api/v1/admin/users")
    assert response.status_code == 403


def test_admin_cannot_remove_own_admin_access_or_reset_own_password(client) -> None:
    _login_admin(client)

    me_response = client.get("/api/v1/auth/me")
    admin_id = me_response.json()["id"]

    demote_response = client.patch(
        f"/api/v1/admin/users/{admin_id}",
        json={
            "display_name": "Phase Zero Admin",
            "is_admin": False,
            "status": "active",
        },
    )
    assert demote_response.status_code == 422

    reset_response = client.post(
        f"/api/v1/admin/users/{admin_id}/reset-password",
        json={"default_password": "admin-reset-123"},
    )
    assert reset_response.status_code == 422
