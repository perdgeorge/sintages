from typing import Annotated
from fastapi import APIRouter, Depends
from src.api.auth import services
from src.api.users.schemas import (
    CreateUserSchema,
    GetUserSchema,
    UpdateUserSchema,
)
from src.api.users.services import UserRepository
from src.api.users.dependencies import get_user_repository
from src.core.schemas import ErrorResponse
from src.db.models.users import User

router = APIRouter()


@router.get(
    "/",
    response_model=list[GetUserSchema],
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_users(
    user_repository: UserRepository = Depends(get_user_repository),
) -> list[GetUserSchema]:
    return user_repository.get_all_users()


@router.get(
    "/{user_id}",
    response_model=GetUserSchema,
    responses={
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_user(
    user_id: int, user_repository: UserRepository = Depends(get_user_repository)
):
    user = user_repository.get_user_by_id(user_id)
    return user


@router.post(
    "/",
    response_model=GetUserSchema,
    status_code=201,
    responses={
        409: {
            "model": ErrorResponse,
            "description": "Username or email already exists",
        },
        422: {"model": ErrorResponse, "description": "Invalid user input format"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def create_user(
    user: CreateUserSchema,
    user_repository: UserRepository = Depends(get_user_repository),
) -> GetUserSchema:
    return user_repository.create_user(user)


@router.put(
    "/{user_id}",
    response_model=GetUserSchema,
    responses={
        409: {
            "model": ErrorResponse,
            "description": "Username or email already exists",
        },
        422: {"model": ErrorResponse, "description": "Invalid user input format"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def update_user(
    user_id: int,
    user: UpdateUserSchema,
    user_repository: UserRepository = Depends(get_user_repository),
) -> GetUserSchema:
    return user_repository.update_user(user_id, user)


@router.get(
    "/me/",
    response_model=GetUserSchema,
    responses={
        401: {"model": ErrorResponse, "description": "User lacks valid authentication"},
    },
)
async def read_users_me(
    current_user: Annotated[User, Depends(services.get_current_user)],
):
    return current_user
