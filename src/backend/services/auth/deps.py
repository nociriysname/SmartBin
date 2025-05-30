import json
from typing import Annotated

from aioredis import Redis
from fastapi import Depends, Security
from fastapi.security import APIKeyHeader
from jwt import PyJWTError

from src.backend.core.exc.exceptions.exceptions import (NotFoundError,
                                                        UnauthorizedError)
from src.backend.core.utils.jwt import validate_jwt
from src.backend.core.utils.redis import get_redis_client
from src.backend.models.users import Users
from src.backend.repos.users import UsersReposDep

__all__ = ("AuthUserDep",)

api_key = APIKeyHeader(name="Authorization")


async def get_current_user(
    token: str = Security(api_key),
    user_repo: UsersReposDep = Depends(),
    redis: Redis = Depends(get_redis_client),
) -> Users:
    try:
        payload = validate_jwt(token)
        user_number = payload.get("sub")
        if not user_number:
            raise UnauthorizedError("Invalid token: sub ex")
    except PyJWTError:
        raise UnauthorizedError("Invalid token")

    cache_key = f"user:{user_number}"
    cached_user = await redis.get(cache_key)
    if cached_user:
        return Users(**json.loads(cached_user))

    user = await user_repo.get_by_number(user_number)
    if not user:
        raise NotFoundError(f"User with {user_number} number not exist")

    await redis.setex(cache_key, 3600, json.dumps(user.dict()))
    return user

AuthUserDep = Annotated[Users, Depends(get_current_user)]
