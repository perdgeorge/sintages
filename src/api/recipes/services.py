from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from src.db.models.recipes import Recipe, RecipeIngredient
from src.db.models.ingredients import Ingredient
from src.db.models.users import User
from src.api.recipes.schemas import (
    GetRecipeSchema,
    CreateRecipeSchema,
    DeleteRecipeSchema,
    RecipeIngredientPayload,
    UpdateRecipeSchema,
)
from src.core.exceptions import ErrorException
from src.core.enums import ErrorKind


class RecipeRepository:
    def __init__(self, db: Session):
        self.db = db

    @property
    def repo_name(self) -> str:
        return "RecipeRepository"

    def get_all_recipes(self) -> list[GetRecipeSchema]:
        recipes = self.db.query(Recipe).all()
        return [GetRecipeSchema.model_validate(recipe) for recipe in recipes]

    def get_recipe_by_id(self, recipe_id: int) -> GetRecipeSchema | None:
        recipe = self.db.query(Recipe).filter(Recipe.id == recipe_id).first()
        if recipe:
            return GetRecipeSchema.model_validate(recipe)
        else:
            raise ErrorException(
                code=status.HTTP_404_NOT_FOUND,
                message="Recipe not found",
                kind=ErrorKind.NOT_FOUND,
                source=f"{self.repo_name}.get_recipe_by_id",
            )

    def get_recipes_by_user(self, recipe_user_id: int) -> list[GetRecipeSchema]:
        recipes = self.db.query(Recipe).filter(Recipe.user_id == recipe_user_id).all()
        if recipes:
            return [GetRecipeSchema.model_validate(recipe) for recipe in recipes]
        raise ErrorException(
            code=status.HTTP_404_NOT_FOUND,
            message="Recipe not found for the user",
            kind=ErrorKind.NOT_FOUND,
            source=f"{self.repo_name}.get_recipes_by_user",
        )

    def add_recipe(self, recipe: Recipe) -> GetRecipeSchema:
        self.db.add(recipe)
        self.db.commit()
        self.db.refresh(recipe)
        return GetRecipeSchema.model_validate(recipe)

    def make_recipe_ingredients(
        self, items: list[RecipeIngredientPayload]
    ) -> list[RecipeIngredient]:
        if not items:
            return []

        ingredient_ids = [item.ingredient_id for item in items]

        ingredients = (
            self.db.query(Ingredient)
            .filter(Ingredient.id.in_(set(ingredient_ids)))
            .all()
        )
        ingredient_map = {ingredient.id: ingredient for ingredient in ingredients}
        missing_ids = [
            ing_id for ing_id in ingredient_ids if ing_id not in ingredient_map
        ]
        if missing_ids:
            raise ErrorException(
                code=status.HTTP_404_NOT_FOUND,
                message=f"Ingredients not found: {missing_ids}",
                kind=ErrorKind.NOT_FOUND,
                source=f"{self.repo_name}.make_recipe_ingredients",
            )
        return [
            RecipeIngredient(
                ingredient=ingredient_map[item.ingredient_id],
                quantity=item.quantity,
            )
            for item in items
        ]

    def create_recipe(
        self, recipe_data: CreateRecipeSchema, current_user_id: int
    ) -> GetRecipeSchema:
        user = self.db.query(User).filter(User.id == current_user_id.id).first()
        if not user:
            raise ErrorException(
                code=status.HTTP_404_NOT_FOUND,
                message="User not found",
                kind=ErrorKind.NOT_FOUND,
                source=f"{self.repo_name}.create_recipe",
            )
        try:
            new_recipe = Recipe(
                name=recipe_data.name,
                cooking_time=recipe_data.cooking_time,
                difficulty_level=recipe_data.difficulty_level,
                portions=recipe_data.portions,
                instructions=recipe_data.instructions,
                user_id=current_user_id.id,
                user=user,
            )
            new_recipe.recipe_ingredients = self.make_recipe_ingredients(
                recipe_data.ingredients
            )
            return self.add_recipe(new_recipe)
        except IntegrityError:
            raise ErrorException(
                code=status.HTTP_409_CONFLICT,
                message="Recipe name already exists",
                kind=ErrorKind.CONFLICT,
                source=f"{self.repo_name}.create_recipe",
            )

    def delete_recipe_by_id(
        self, recipe_id: int, current_user_id: int
    ) -> DeleteRecipeSchema:
        recipe = self.db.query(Recipe).filter(Recipe.id == recipe_id).first()
        if not recipe:
            raise ErrorException(
                code=status.HTTP_404_NOT_FOUND,
                message="Recipe not found",
                kind=ErrorKind.NOT_FOUND,
                source=f"{self.repo_name}.delete_recipe_by_id",
            )
        user = (
            self.db.query(Recipe).filter(Recipe.user_id == current_user_id.id).first()
        )
        if not user:
            raise ErrorException(
                code=status.HTTP_403_FORBIDDEN,
                message="You do not have permission to delete this recipe.",
                kind=ErrorKind.AUTHORIZATION,
                source=f"{self.repo_name}.delete_recipe_by_id",
            )
        response = DeleteRecipeSchema.model_validate(recipe)
        self.db.delete(recipe)
        self.db.commit()
        return response

    def update_recipe_by_id(
        self, recipe_id: int, recipe_data: UpdateRecipeSchema, current_user_id: int
    ) -> GetRecipeSchema:
        user = (
            self.db.query(Recipe).filter(Recipe.user_id == current_user_id.id).first()
        )
        if not user:
            raise ErrorException(
                code=status.HTTP_403_FORBIDDEN,
                message="You do not have permission to update this recipe.",
                kind=ErrorKind.AUTHORIZATION,
                source=f"{self.repo_name}.update_recipe",
            )
        recipe = self.db.query(Recipe).filter(Recipe.id == recipe_id).first()
        if not recipe:
            raise HTTPException(
                status_code=404,
                detail="Recipe not found",
                kind=ErrorKind.NOT_FOUND,
                source=f"{self.repo_name}.update_recipe",
            )
        try:
            if recipe_data.name is not None:
                recipe.name = recipe_data.name
            if recipe_data.cooking_time is not None:
                recipe.cooking_time = recipe_data.cooking_time
            if recipe_data.difficulty_level is not None:
                recipe.difficulty_level = recipe_data.difficulty_level
            if recipe_data.portions is not None:
                recipe.portions = recipe_data.portions
            if recipe_data.instructions is not None:
                recipe.instructions = recipe_data.instructions
            if recipe_data.ingredients is not None:
                recipe.recipe_ingredients = self.make_recipe_ingredients(
                    recipe_data.ingredients
                )
            self.db.commit()
            self.db.refresh(recipe)
            return GetRecipeSchema.model_validate(recipe)
        except IntegrityError:
            raise ErrorException(
                code=status.HTTP_409_CONFLICT,
                message="Recipe name already exists",
                kind=ErrorKind.CONFLICT,
                source=f"{self.repo_name},update_recipe",
            )
