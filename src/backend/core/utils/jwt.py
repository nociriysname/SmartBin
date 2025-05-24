from datetime import datetime, timedelta
from typing import Dict

import jwt
import pytz

from src.backend.core.config import settings
from src.backend.models.users import Users

__all__ = ("create_jwt", "validate_jwt")


async def create_jwt(user: Users) -> str:
    try:
        payload = {
            "sub": user.number,
            "exp": (
                datetime.now(pytz.UTC) + timedelta(
                    seconds=settings.jwt_expires,
                )
            ),
        }
        token = jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        return token
    except Exception as e:
        raise ValueError(f"Error while creating jwt: {e}")


def validate_jwt(token: str) -> Dict:
    try:
        return jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.ExpiredSignatureError:
        raise ValueError("Token expired")
    except jwt.InvalidKeyError:
        raise ValueError("Invalid token")
