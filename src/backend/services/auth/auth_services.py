from datetime import datetime, timezone
from typing import Annotated
import uuid

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.core.config import settings
from src.backend.core.database.async_engine import SessionDep
from src.backend.core.exc.exceptions.exceptions import (
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)
from src.backend.core.utils.jwt import create_jwt
from src.backend.models.users import Users
from src.backend.repos.user_repo import RepoUsers, UsersReposDep
from src.backend.schemes.authy import (
    AuthPushCodeDTO,
    AuthPushCodeTokenResponseDTO,
    AuthPushDTO,
)
from src.backend.schemes.employee import EmployeeModelDTO
from src.backend.services.auth.notifications import (
    NotificationService,
    NotificationServiceDep,
)


__all__ = ("AuthenticationService", "AuthenticationServiceDep")


class AuthenticationService:
    def __init__(
        self,
        session: AsyncSession,
        user_repo: RepoUsers,
        notifications_service: NotificationService,
    ):
        self.session = session
        self.user_repo = user_repo
        self.notifications_service = notifications_service

    async def request_code(self, data: AuthPushDTO, company_id: str) -> str:
        user = await self.user_repo.get_by_number(data.number, company_id)
        if not user:
            raise NotFoundError(message="User not found")

        if user.date_jwt_unactivate and (
            user.date_jwt_unactivate > datetime.now(timezone.utc)
        ):
            raise ForbiddenError(message="User's jwt deactivated")

        authy_code = str(uuid.uuid4())[:6]
        title = "Confirmation code"
        body = (
            f"Your confirmation code: {authy_code}. Time expired: 10 minutes"
        )

        if await self.notifications_service.send_notification(
            user.uuid,
            company_id,
            title,
            body,
        ):
            await self.user_repo.update_firetoken(
                user.number,
                company_id,
                authy_code,
                title,
            )

            return "Code was sent correctly"

        raise UnauthorizedError(message="Wouldn't send JWT token")

    async def verify_code(
        self,
        data: AuthPushCodeDTO,
        company_id: str,
    ) -> AuthPushCodeTokenResponseDTO:
        user = await self.user_repo.get_by_number(data.number, company_id)

        if not user:
            raise NotFoundError(message="User not found")

        if user.firebase_token != data.code:
            raise UnauthorizedError(message="JWT token is not valid")

        if (
            user.date_jwt_unactivate > datetime.now(timezone.utc)
        ) and user.date_jwt_unactivate:

            raise ForbiddenError(
                message="User's JWT deactivated to the specified date",
            )

        if not isinstance(user, Users):
            raise ValueError(
                f"Was waited Users object, transfered {type(user)} object",
            )

        jwt_token = create_jwt(user)
        await self.user_repo.update_firetoken(user.number, company_id, None)
        return AuthPushCodeTokenResponseDTO(
            access_token=jwt_token,
            token_type="bearer",
            expires_in=settings.jwt_expires_in,
        )

    async def updating(
        self,
        user_id: str,
        company_id: str,
        data: EmployeeModelDTO,
    ) -> None:
        user = await self.user_repo.get_by_uuid(user_id, company_id)
        if not user:
            raise NotFoundError(message="User not found")

        if data.name is not None:
            user.name = data.name

        if data.number is not None:
            user.number = str(data.number)

        if data.company_id is not None:
            user.company_id = company_id

        await self.session.commit()
        await self.session.refresh(user)


async def create_authentication_service(
    session: SessionDep,
    user_repo: UsersReposDep,
    notifications_service: NotificationServiceDep,
) -> AuthenticationService:
    return AuthenticationService(
        session=session,
        user_repo=user_repo,
        notifications_service=notifications_service,
    )


AuthenticationServiceDep = Annotated[
    AuthenticationService,
    Depends(create_authentication_service),
]
