import pytest
from fastapi.testclient import TestClient
from src.db.models.recipes import Recipe
from tests.factories import make_recipe_payload


@pytest.mark.anyio
def test_create_recipe(client: TestClient, user, ingredient_factory):
    ingredients = [ingredient_factory(), ingredient_factory()]
    ingredient_ids = [ingredient.id for ingredient in ingredients]
    payload = make_recipe_payload(user_id=user.id, ingredient_ids=ingredient_ids)

    resp = client.post("/recipes", json=payload.model_dump(mode="json"))
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == payload.name.capitalize()
    expected_ingredients = [
        {"ingredient_id": item.ingredient_id, "quantity": item.quantity}
        for item in payload.ingredients
    ]
    assert data["ingredients"] == expected_ingredients
    assert data["user_id"] == user.id
    assert data["is_vegan"] is False


@pytest.mark.anyio
def test_get_recipe(client: TestClient, recipe: Recipe):
    resp = client.get(f"/recipes/{recipe.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == recipe.id
    assert data["user_id"] == recipe.user_id
    assert data["ingredients"] == recipe.recipe_ingredients_payload
    assert data["is_vegan"] == recipe.is_vegan


@pytest.mark.anyio
def test_list_recipes(client: TestClient, recipe_factory):
    r1 = recipe_factory()
    r2 = recipe_factory()

    resp = client.get("/recipes")
    assert resp.status_code == 200
    data = resp.json()
    ids = {item["id"] for item in data}
    assert ids == {r1.id, r2.id}
    assert all("is_vegan" in item for item in data)


@pytest.mark.anyio
def test_get_user_recipes(client: TestClient, recipe_factory, user_factory):
    user = user_factory()
    recipe_factory(user=user)
    recipe_factory(user=user)

    resp = client.get(f"/recipes/user/{user.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert all(item["user_id"] == user.id for item in data)


@pytest.mark.anyio
def test_delete_recipe(client: TestClient, recipe: Recipe):
    resp = client.delete(f"/recipes/{recipe.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == recipe.id
    assert data["ingredients"] == recipe.recipe_ingredients_payload
    assert data["is_vegan"] == recipe.is_vegan

    follow_up = client.get(f"/recipes/{recipe.id}")
    assert follow_up.status_code == 404
