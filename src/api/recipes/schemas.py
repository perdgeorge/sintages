from datetime import datetime
from pydantic import Field, field_serializer, field_validator
from src.api.recipes.enums import DifficultyLevel
from src.api.schemas import BaseSchema


class RecipeIngredientPayload(BaseSchema):
    ingredient_id: int = Field(..., examples=[1])
    quantity: str = Field(..., examples=["100 grams"])


class RecipeBaseSchema(BaseSchema):
    name: str = Field(max_length=183, examples=["Tzatziki"])
    cooking_time: int = Field(..., examples=[30], ge=1)
    difficulty_level: DifficultyLevel = Field(..., examples=["EASY", "MEDIUM", "HARD"])
    portions: int = Field(..., examples=[4], ge=1)
    instructions: str = Field(..., examples=["Mix all ingredients."])

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return value.lower()

    @field_serializer("name")
    def serialize_name(self, value: str) -> str:
        return value.capitalize()


class CreateRecipeSchema(RecipeBaseSchema):
    ingredients: list[RecipeIngredientPayload] = Field(
        default_factory=list,
        examples=[[{"ingredient_id": 1, "quantity": "100 grams"}]],
    )


class GetRecipeSchema(RecipeBaseSchema):
    is_vegan: bool = Field(..., examples=[False])
    id: int = Field(..., examples=[1])
    created_at: datetime = Field(..., examples=["2023-10-01T12:00:00Z"])
    ingredients: list[RecipeIngredientPayload] = Field(
        default_factory=list,
        alias="recipe_ingredients_payload",
        serialization_alias="ingredients",
    )
    user_id: int = Field(..., examples=[1])


class UpdateRecipeSchema(RecipeBaseSchema):
    ingredients: list[RecipeIngredientPayload] = Field(
        default_factory=list, examples=[[{"ingredient_id": 1, "quantity": "100 grams"}]]
    )


class DeleteRecipeSchema(GetRecipeSchema):
    pass
