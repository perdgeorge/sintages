import pytest
from src.db.models.ingredients import Ingredient
from tests.factories import make_ingredient_payload
from fastapi.testclient import TestClient


@pytest.mark.anyio
def test_create_ingredient(client: TestClient, category_factory: callable):
    c1 = category_factory()
    c2 = category_factory()
    categories_ids = [c1.id, c2.id]
    categories_names = [c1.name, c2.name]
    payload = make_ingredient_payload(
        categories_ids=categories_ids, categories_names=categories_names
    )

    resp = client.post("/ingredients", json=payload.model_dump())
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == payload.name.capitalize()
    expected_categories = [{"id": c.id, "name": c.name} for c in [c1, c2]]
    assert "id" in data
    assert data["categories"] == expected_categories


@pytest.mark.anyio
def test_get_ingredient(client: TestClient, ingredient: Ingredient):
    resp = client.get(f"/ingredients/{ingredient.id}")
    assert resp.status_code == 200
    data = resp.json()

    assert data["id"] == ingredient.id
    assert data["name"] == ingredient.name.capitalize()
    expected_categories = [{"id": c.id, "name": c.name} for c in ingredient.categories]
    assert data["categories"] == expected_categories


@pytest.mark.anyio
def test_list_ingredients(client: TestClient, ingredient_factory: callable):
    i1 = ingredient_factory()
    i2 = ingredient_factory()
    resp = client.get("/ingredients")
    assert resp.status_code == 200
    assert len(resp.json()) == 2
    ids = {i["id"] for i in resp.json()}
    assert ids == {i1.id, i2.id}


@pytest.mark.anyio
def test_update_ingredient(
    client: TestClient, ingredient: Ingredient, category_factory: callable
):
    c1 = category_factory()
    c2 = category_factory()
    categories_ids = [c1.id, c2.id]
    categories_names = [c1.name, c2.name]
    new_payload = make_ingredient_payload(
        categories_ids=categories_ids, categories_names=categories_names
    )
    resp = client.put(f"/ingredients/{ingredient.id}", json=new_payload.model_dump())
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == ingredient.id
    assert data["name"] == new_payload.name.capitalize()
    assert data["is_vegan"] == new_payload.is_vegan
    expected_categories = [
        {"id": cat.id, "name": cat.name} for cat in new_payload.categories
    ]
    assert data["categories"] == expected_categories
