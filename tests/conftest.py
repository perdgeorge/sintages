from __future__ import annotations
from typing import Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from alembic.config import Config
from alembic import command
from testcontainers.postgres import PostgresContainer

from main import app as fastapi_app
from src.db.models.users import User


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    with TestClient(fastapi_app) as c:
        yield c


@pytest.fixture(scope="session")
def _pg_container() -> Generator[PostgresContainer, None, None]:
    with PostgresContainer(
        image="postgres:17-alpine",
        username="test",
        password="test",
        dbname="app_test",
    ) as pg:
        yield pg


@pytest.fixture(scope="session")
def pg_url(_pg_container) -> str:
    return _pg_container.get_connection_url()


@pytest.fixture(scope="session")
def engine(pg_url: str):
    engine = create_engine(pg_url, pool_pre_ping=True, future=True)

    cfg = Config("./alembic.ini")
    cfg.set_main_option("sqlalchemy.url", pg_url)
    cfg.set_main_option("script_location", "alembic")

    command.upgrade(cfg, "head")

    return engine


@pytest.fixture(scope="session")
def session_factory(engine: Engine):
    return sessionmaker(
        bind=engine,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
        class_=Session,
    )


@pytest.fixture()
def db(session_factory) -> Generator[Session, None, None]:
    """
    Per-test DB session wrapped in a transaction.
    Everything is rolled back after each test for isolation & speed.
    """
    connection = session_factory.kw["bind"].connect()
    trans = connection.begin()
    try:
        session: Session = session_factory(bind=connection)
        yield session
    finally:
        session.close()
        trans.rollback()
        connection.close()


@pytest.fixture(autouse=True)
def override_get_db(db: Session):
    from src.core.dependencies import get_db as app_get_db

    def _override():
        yield db

    fastapi_app.dependency_overrides[app_get_db] = _override
    yield
    fastapi_app.dependency_overrides.clear()


@pytest.fixture()
def user(db: Session):
    from src.db.models.users import User
    from src.core.security import hash_password
    from tests.factories import make_user_payload

    payload = make_user_payload()
    hashed_password = hash_password(payload.password)
    row = User(
        username=payload.username,
        email=payload.email,
        full_name=payload.full_name,
        is_active=payload.is_active,
        hashed_password=hashed_password,
    )
    # Keep the plaintext password on the instance for authentication tests.
    row.raw_password = payload.password
    db.add(row)
    db.flush()
    return row


@pytest.fixture()
def auth_token(client: TestClient, user: User) -> str:
    resp = client.post(
        "/token",
        data={
            "username": user.username,
            "password": user.raw_password,
            "grant_type": "password",
        },
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest.fixture()
def auth_headers(auth_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture()
def user_factory(db):
    from src.db.models.users import User
    from src.core.security import hash_password
    from tests.factories import make_user_payload

    def _create(**overrides):
        payload = make_user_payload(**overrides)
        row = User(
            username=payload.username,
            email=payload.email,
            full_name=payload.full_name,
            is_active=payload.is_active,
            hashed_password=hash_password(payload.password),
        )
        db.add(row)
        db.flush()
        return row

    return _create


@pytest.fixture()
def ingredient(db: Session, category_factory):
    from src.db.models.ingredients import Ingredient
    from tests.factories import make_ingredient_payload

    categories = [category_factory(), category_factory()]
    categories_ids = [cat.id for cat in categories]
    categories_names = [cat.name for cat in categories]
    payload = make_ingredient_payload(
        categories_ids=categories_ids, categories_names=categories_names
    )
    ingredient = Ingredient(name=payload.name, is_vegan=payload.is_vegan)
    categories = [category_factory(), category_factory()]
    ingredient.categories = categories
    db.add(ingredient)
    db.flush()
    return ingredient


@pytest.fixture()
def ingredient_factory(db, category_factory):
    from src.db.models.ingredients import Ingredient
    from tests.factories import make_ingredient_payload

    def _create(**overrides):
        categories = [category_factory() for _ in range(2)]
        categories_ids = [cat.id for cat in categories]
        categories_names = [cat.name for cat in categories]

        payload = make_ingredient_payload(
            categories_ids=categories_ids,
            categories_names=categories_names,
            **overrides,
        )

        ingredient = Ingredient(
            name=payload.name, is_vegan=payload.is_vegan, categories=categories
        )
        db.add(ingredient)
        db.flush()
        return ingredient

    return _create


@pytest.fixture()
def recipe(db: Session, user, ingredient_factory):
    from src.db.models.recipes import Recipe, RecipeIngredient
    from src.api.recipes.enums import DifficultyLevel

    ingredients = [ingredient_factory(), ingredient_factory()]
    recipe = Recipe(
        name=f"recipe-{uuid4().hex[:6]}",
        cooking_time=30,
        difficulty_level=DifficultyLevel.EASY,
        portions=2,
        instructions="Mix everything",
        user=user,
        user_id=user.id,
    )
    recipe.recipe_ingredients = [
        RecipeIngredient(ingredient=ingredient, quantity=qty)
        for ingredient, qty in zip(ingredients, ["200 g", "1 cup"], strict=True)
    ]
    db.add(recipe)
    db.flush()
    return recipe


@pytest.fixture()
def recipe_factory(db: Session, user_factory, ingredient_factory):
    from src.db.models.recipes import Recipe, RecipeIngredient
    from src.api.recipes.enums import DifficultyLevel

    def _create(**overrides):
        user = overrides.pop("user", user_factory())
        ingredients = overrides.pop(
            "ingredients", [ingredient_factory(), ingredient_factory()]
        )
        quantities = overrides.pop(
            "quantities", ["1 unit" for _ in range(len(ingredients))]
        )
        data = {
            "name": overrides.pop("name", f"recipe-{uuid4().hex[:6]}"),
            "cooking_time": overrides.pop("cooking_time", 25),
            "difficulty_level": overrides.pop("difficulty_level", DifficultyLevel.EASY),
            "portions": overrides.pop("portions", 4),
            "instructions": overrides.pop("instructions", "Mix well"),
            "user": user,
            "user_id": user.id,
        }
        data.update(overrides)
        recipe = Recipe(**data)
        recipe.recipe_ingredients = [
            RecipeIngredient(ingredient=ingredient, quantity=qty)
            for ingredient, qty in zip(ingredients, quantities, strict=True)
        ]
        db.add(recipe)
        db.flush()
        return recipe

    return _create


@pytest.fixture()
def category(db: Session):
    from src.db.models.categories import Category
    from tests.factories import make_category_payload

    payload = make_category_payload()
    row = Category(
        name=payload.name,
    )
    db.add(row)
    db.flush()
    return row


@pytest.fixture()
def category_factory(db):
    from src.db.models.categories import Category
    from tests.factories import make_category_payload

    def _create(**overrides):
        payload = make_category_payload(**overrides)
        row = Category(
            name=payload.name,
        )
        db.add(row)
        db.flush()
        return row

    return _create
