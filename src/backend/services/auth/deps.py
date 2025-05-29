from fastapi import Depends
from fastapi.params import Security
from jwt import PyJWTError

from src.backend.core.config import settings
from src.backend.core.exc.exceptions.exceptions import (NotFoundError,
                                                        UnauthorizedError)
from src.backend.core.utils.jwt import validate_jwt
from src.backend.models.users import Users
from src.backend.repos.users import UsersReposDep

__all__ = ("AuthUserDep",)


async def get_user(
        token: str = Security(settings.api_key),
        user_repo: UsersReposDep = Depends(),
) -> Users:
    try:
        payload = validate_jwt(token)
        user_number = payload.get("sub")
        if not user_number:
            raise UnauthorizedError("Invalid token")

    except PyJWTError:
        raise UnauthorizedError("Invalid token")

    user = await user_repo.get_by_number(user_number)
    if not user:
        raise NotFoundError(f"User {user_number} not found")

    return user


AuthUserDep = Depends(get_user, type_=Users)
