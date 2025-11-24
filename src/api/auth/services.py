from datetime import datetime, timedelta, timezone
import logging
from src.api.auth.schemas import JWTData
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from src.core.security import verify_password
from src.db.models.users import User
from src.core.config import config
from src.core.dependencies import get_db_context
from src.api.auth.enums import JWTType

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_credentials_exception(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def confirm_token_expire_minutes() -> int:
    return 1440


def create_access_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(config.ACCESS_TOKEN_EXPIRE_MINUTES)
    jwt_data = JWTData(
        username=username, expire=expire, type=JWTType.ACCESS
    ).model_dump(mode="json")
    encoded_jwt = jwt.encode(
        jwt_data, key=config.SECRET_KEY, algorithm=config.ALGORITHM
    )
    return encoded_jwt


def create_confirmation_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=confirm_token_expire_minutes()
    )
    jwt_data = JWTData(
        username=username, expire=expire, type=JWTType.CONFIRMATION
    ).model_dump(mode="json")
    encoded_jwt = jwt.encode(
        jwt_data, key=config.SECRET_KEY, algorithm=config.ALGORITHM
    )
    return encoded_jwt


def get_subject_for_token_type(
    token: str,
    type: JWTType,
) -> str:
    try:
        payload = jwt.decode(
            token, key=config.SECRET_KEY, algorithms=[config.ALGORITHM]
        )
    except jwt.ExpiredSignatureError as e:
        raise create_credentials_exception("Token has expired") from e
    except jwt.PyJWTError as e:
        raise create_credentials_exception("Invalid token") from e

    username = payload.get("username")
    if username is None:
        raise create_credentials_exception("Token is missing 'username' field")

    token_type = payload.get("type")
    if token_type is None or token_type != type:
        raise create_credentials_exception(
            f"Token has incorrect type, expected '{type}'"
        )

    return username


def get_user(username: str) -> User | None:
    logger.debug("Fetching user from the database", extra={"username": username})
    with get_db_context() as db:
        user = db.query(User).filter(User.username == username).first()
    if user:
        return user


def authenticate_user(username: str, password: str) -> User:
    logger.debug("Authenticating user", extra={"username": username})
    user = get_user(username=username)
    if not user:
        raise create_credentials_exception("Invalid username or password")
    if not verify_password(password, user.hashed_password):
        raise create_credentials_exception("Invalid password")
    return user


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    username = get_subject_for_token_type(token, "access")
    user = get_user(username=username)
    if user is None:
        raise create_credentials_exception("Could not find user for this token")
    return user


# def get_current_active_user(
#     current_user: Annotated[User, Depends(get_current_user)],
# ) -> User:
#     if not current_user.is_active:
#         raise HTTPException(status_code=400, detail="Inactive user")
#     return current_user
