import pytest
from src.db.models.users import User
from tests.factories import make_user_payload
from fastapi.testclient import TestClient


@pytest.mark.anyio
def test_create_user(client: TestClient):
    payload = make_user_payload()
    resp = client.post("/users", json=payload.model_dump())
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == payload.email
    assert data["full_name"] == payload.full_name
    assert "id" in data


@pytest.mark.anyio
def test_get_user(client: TestClient, user: User):
    resp = client.get(f"/users/{user.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == user.id
    assert data["username"] == user.username
    assert data["email"] == user.email


@pytest.mark.anyio
def test_list_users(client: TestClient, user_factory: callable):
    u1 = user_factory()
    u2 = user_factory()
    resp = client.get("/users")
    assert resp.status_code == 200
    assert len(resp.json()) == 2
    ids = {u["id"] for u in resp.json()}
    assert ids == {u1.id, u2.id}


@pytest.mark.anyio
def test_update_user(client: TestClient, user: User):
    new_payload = make_user_payload()
    resp = client.put(f"/users/{user.id}", json=new_payload.model_dump())
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == user.id
    assert data["username"] == new_payload.username
    assert data["email"] == new_payload.email
    assert data["full_name"] == new_payload.full_name


@pytest.mark.anyio
def test_login(client: TestClient, user: User):
    example_user = make_user_payload()
    response = client.post(
        "/token",
        json={"username": example_user.username, "password": example_user.password},
    )
    print(response.json())
    assert response.status_code == 200
    token = response.json()["access_token"]
    assert token is not None
    return token


@pytest.mark.anyio
def test_read_users_me(client: TestClient, user: User):
    token = test_login(client, user)
    resp = client.get("/users/me/", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == user.id
    assert data["username"] == user.username
    assert data["email"] == user.email
    assert data["full_name"] == user.full_name
