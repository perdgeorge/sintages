from fastapi import APIRouter, Depends
from src.api.auth.services import get_current_user
from src.api.recipes.schemas import (
    CreateRecipeSchema,
    GetRecipeSchema,
    DeleteRecipeSchema,
    UpdateRecipeSchema,
)
from src.api.recipes.services import RecipeRepository
from src.api.recipes.dependencies import get_recipe_repository
from src.core.schemas import ErrorResponse

router = APIRouter()


@router.get(
    "/",
    response_model=list[GetRecipeSchema],
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_recipes(
    recipe_repository: RecipeRepository = Depends(get_recipe_repository),
) -> list[GetRecipeSchema]:
    return recipe_repository.get_all_recipes()


@router.get(
    "/{recipe_id}",
    response_model=GetRecipeSchema,
    responses={
        404: {"model": ErrorResponse, "description": "Recipe not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_recipe(
    recipe_id: int,
    recipe_repository: RecipeRepository = Depends(get_recipe_repository),
):
    recipe = recipe_repository.get_recipe_by_id(recipe_id)
    return recipe


@router.get(
    "/user/{user_id}",
    response_model=list[GetRecipeSchema],
    responses={
        404: {"model": ErrorResponse, "description": "Recipe not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_recipes_user(
    user_id: int,
    recipe_repository: RecipeRepository = Depends(get_recipe_repository),
) -> list[GetRecipeSchema]:
    return recipe_repository.get_recipes_by_user(user_id)


@router.post(
    "/",
    response_model=GetRecipeSchema,
    status_code=201,
    responses={
        401: {"model": ErrorResponse, "description": "User lacks valid authentication"},
        409: {"model": ErrorResponse, "description": "Recipe name already exists"},
        422: {"model": ErrorResponse, "description": "Invalid recipe input format"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def create_recipe(
    recipe: CreateRecipeSchema,
    recipe_repository: RecipeRepository = Depends(get_recipe_repository),
    current_user_id=Depends(get_current_user),
) -> GetRecipeSchema:
    return recipe_repository.create_recipe(recipe, current_user_id)


@router.put(
    "/{recipe_id}",
    response_model=UpdateRecipeSchema,
    responses={
        401: {"model": ErrorResponse, "description": "User lacks valid authentication"},
        403: {
            "model": ErrorResponse,
            "description": "User does not have permission to update this recipe",
        },
        409: {"model": ErrorResponse, "description": "Ingredient already exists"},
        422: {"model": ErrorResponse, "description": "Invalid Ingredient input format"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def update_recipe(
    recipe_id: int,
    recipe: UpdateRecipeSchema,
    recipe_repository: RecipeRepository = Depends(get_recipe_repository),
    current_user_id=Depends(get_current_user),
) -> GetRecipeSchema:
    return recipe_repository.update_recipe_by_id(recipe_id, recipe, current_user_id)


@router.delete(
    "/{recipe_id}",
    response_model=DeleteRecipeSchema,
    responses={
        401: {"model": ErrorResponse, "description": "User lacks valid authentication"},
        403: {
            "model": ErrorResponse,
            "description": "User does not have permission to update this recipe",
        },
        404: {"model": ErrorResponse, "description": "Recipe not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def delete_recipe(
    recipe_id: int,
    recipe_repository: RecipeRepository = Depends(get_recipe_repository),
    current_user_id=Depends(get_current_user),
) -> DeleteRecipeSchema:
    return recipe_repository.delete_recipe_by_id(recipe_id, current_user_id)
