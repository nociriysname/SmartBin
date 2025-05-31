from datetime import datetime, timezone
from typing import Annotated, Optional
import uuid

from aioredis import Redis as AioRedis
from fastapi import Depends
from pydantic_extra_types.phone_numbers import PhoneNumber
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.core.config import settings
from src.backend.core.database.async_engine import SessionDep
from src.backend.core.exc.exceptions.exceptions import (ForbiddenError,
                                                        NotFoundError,
                                                        UnauthorizedError)
from src.backend.core.utils.jwt import create_jwt
from src.backend.core.utils.redis import get_redis_client, Redis
from src.backend.models.users import Users
from src.backend.repos.users import RepoUsers, UsersReposDep
from src.backend.schemes.authy import (AuthPushCodeDTO,
                                       AuthPushCodeTokenResponseDTO,
                                       AuthPushDTO)
from src.backend.services.notifications.service import (NotificationService,
                                                        NotificationServiceDep)

__all__ = ("AuthenticationService", "AuthenticationServiceDep")


class AuthenticationService:
    def __init__(
        self,
        session: AsyncSession,
        user_repo: RepoUsers,
        notifications_service: NotificationService,
        redis_client: AioRedis,
    ):
        self.session = session
        self.user_repo = user_repo
        self.redis_client = redis_client
        self.notifications_service = notifications_service

    async def get_user_by_phone(
            self, phonenumber: PhoneNumber,
    ) -> Optional[Users]:
        return await self.user_repo.get_by_number(str(phonenumber))

    async def request_code(self, data: AuthPushDTO, company_id: str) -> str:
        user = await self.user_repo.get_by_number(data.number)
        if not user:
            raise NotFoundError(message="User not found")

        if user.date_jwt_unactivate and (
            user.date_jwt_unactivate > datetime.now(timezone.utc)
        ):
            raise ForbiddenError(message="User's jwt deactivated")

        authy_code = str(uuid.uuid4())[:6]

        await self.redis_client.setex(
            f"otp:{str(data.number)}", 600, authy_code,
        )

        title = "Confirmation code"
        body = (
            f"Your confirmation code: {authy_code}. Time expired: 10 minutes"
        )

        sending_code = await self.notifications_service.send_notification(
            user=user,
            company_id=company_id,
            title=title,
            body=body,
        )
        if not sending_code:
            raise UnauthorizedError("Code not sent")

        return "Code was sent correctly"

    async def verify_code(
        self,
        data: AuthPushCodeDTO,
    ) -> AuthPushCodeTokenResponseDTO:
        user = await self.user_repo.get_by_number(data.number)

        if not user:
            raise NotFoundError(message="User not found")

        code = await self.redis_client.get(f"otp:{str(data.number)}")

        if (not code) or (code.decode("utf-8") != data.code):
            raise UnauthorizedError("Incorrect code")

        if user.date_jwt_unactivate > datetime.now(timezone.utc):
            raise ForbiddenError("JWT deactivated")

        jwt_token = await create_jwt(user)

        await self.redis_client.delete(f"otp:{str(data.number)}")

        return AuthPushCodeTokenResponseDTO(
            access_token=jwt_token,
            token_type="bearer",
            expires_in=settings.jwt_expires,
        )


async def create_authentication_service(
    session: SessionDep,
    user_repo: UsersReposDep,
    notifications_service: NotificationServiceDep,
    redis_client: Redis = Depends(get_redis_client),
) -> AuthenticationService:
    return AuthenticationService(
        session=session,
        user_repo=user_repo,
        notifications_service=notifications_service,
        redis_client=redis_client,
    )


AuthenticationServiceDep = Annotated[
    AuthenticationService,
    Depends(create_authentication_service),
]
