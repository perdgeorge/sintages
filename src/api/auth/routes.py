from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from src.api.auth.services import authenticate_user, create_access_token
from src.api.auth.schemas import Token

router = APIRouter()


@router.post("/token", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = authenticate_user(form_data.username, form_data.password)
    access_token = create_access_token(user.username)
    return Token(access_token=access_token, token_type="bearer")
