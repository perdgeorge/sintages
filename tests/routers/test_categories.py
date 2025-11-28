import pytest
from src.db.models.categories import Category
from tests.factories import make_category_payload
from fastapi.testclient import TestClient


@pytest.mark.anyio
def test_create_category(client: TestClient):
    payload = make_category_payload()
    resp = client.post("/categories", json=payload.model_dump())
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == payload.name.capitalize()
    assert "id" in data


@pytest.mark.anyio
def test_get_category(client: TestClient, category: Category):
    resp = client.get(f"/categories/{category.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == category.id
    assert data["name"] == category.name.capitalize()


@pytest.mark.anyio
def test_list_categories(client: TestClient, category_factory: callable):
    c1 = category_factory()
    c2 = category_factory()
    resp = client.get("/categories")
    assert resp.status_code == 200
    assert len(resp.json()) == 2
    ids = {c["id"] for c in resp.json()}
    assert ids == {c1.id, c2.id}


@pytest.mark.anyio
def test_update_category(client: TestClient, category: Category):
    new_payload = make_category_payload()
    resp = client.put(f"/categories/{category.id}", json=new_payload.model_dump())
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == category.id
    assert data["name"] == new_payload.name.capitalize()
