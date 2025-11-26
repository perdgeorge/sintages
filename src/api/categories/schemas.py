from datetime import datetime
from pydantic import Field, field_validator, field_serializer
from src.api.schemas import BaseSchema
from src.api.common.schemas import IngredientRelationshipSchema


class CategorySchema(BaseSchema):
    name: str = Field(max_length=50, examples=["Veggies"])

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return value.lower()

    @field_serializer("name")
    def serialize_name(self, value: str) -> str:
        return value.capitalize()


class GetCategorySchema(CategorySchema):
    id: int = Field(..., examples=[1])
    created_at: datetime = Field(..., examples=["2023-10-01T12:00:00Z"])
    updated_at: datetime | None = Field(..., examples=["2023-10-01T12:00:00Z"])
    ingredients: list["IngredientRelationshipSchema"] = Field(
        default_factory=list,
        examples=[[{"id": 1, "name": "Broccoli"}]],
    )


class CreateCategorySchema(CategorySchema):
    pass


class UpdateCategorySchema(CategorySchema):
    name: str = Field(..., examples=["Veggies"])
