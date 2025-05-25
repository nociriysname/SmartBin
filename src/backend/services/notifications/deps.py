from typing import Annotated

from fastapi import Depends

from src.backend.core.exc.exceptions.exceptions import NotFoundError
from src.backend.models.users import Users
from src.backend.repos.user_repo import UsersReposDep

__all__ = ("NotificationsDep",)


async def get_users_notifications(
    user_id: str,
    company_id: str,
    user_repo: UsersReposDep,
) -> Users:
    user = await user_repo.get_by_id(user_id)
    if (not user) or (user.company_id != company_id):
        raise NotFoundError(message=f"User {user_id} not found")

    return user


NotificationsDep = Annotated[Users, Depends(get_users_notifications)]
