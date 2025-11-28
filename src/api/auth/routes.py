from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from src.api.auth.services import authenticate_user, create_access_token, get_user
from src.api.auth.schemas import Token
from src.core.dependencies import get_db

router = APIRouter()


@router.post("/token", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
) -> Token:
    user = get_user(form_data.username, db)
    user = authenticate_user(
        username=form_data.username, password=form_data.password, user=user
    )
    access_token = create_access_token(username=user.username)
    return Token(access_token=access_token, token_type="bearer")
