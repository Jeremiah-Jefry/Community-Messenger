from conftest import TEST_USER, register_user


def test_register_success(client):
    response = client.post("/register", json=TEST_USER)

    assert response.status_code == 200
    body = response.json()
    assert body["username"] == TEST_USER["username"]
    assert isinstance(body["id"], int)
    assert "password" not in body
    assert "password_hash" not in body


def test_register_duplicate_username_rejected(client):
    register_user(client)

    response = client.post("/register", json=TEST_USER)

    assert response.status_code == 400
    assert response.json()["detail"] == "Username already registered"


def test_login_success(client):
    register_user(client)

    response = client.post(
        "/login", data={"username": TEST_USER["username"], "password": TEST_USER["password"]}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_failure(client):
    register_user(client)

    wrong_password = client.post(
        "/login", data={"username": TEST_USER["username"], "password": "wrong-password"}
    )
    unknown_user = client.post(
        "/login", data={"username": "nobody_here", "password": TEST_USER["password"]}
    )

    assert wrong_password.status_code == 401
    assert unknown_user.status_code == 401
    assert wrong_password.json()["detail"] == "Incorrect username or password"


def test_me_with_valid_token(client):
    user = register_user(client)
    token = client.post(
        "/login", data={"username": TEST_USER["username"], "password": TEST_USER["password"]}
    ).json()["access_token"]

    response = client.get("/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["username"] == user["username"]


def test_me_with_invalid_token(client):
    register_user(client)
    malformed = client.get("/me", headers={"Authorization": "Bearer not-a-jwt"})
    bad_signature = client.get(
        "/me",
        headers={
            "Authorization": (
                "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
                ".eyJzdWIiOiJ0ZXN0X3VzZXIifQ.invalidsignature"
            )
        },
    )
    missing = client.get("/me")

    assert malformed.status_code == 401
    assert bad_signature.status_code == 401
    assert missing.status_code == 401
    assert malformed.json()["detail"] == "Could not validate credentials"