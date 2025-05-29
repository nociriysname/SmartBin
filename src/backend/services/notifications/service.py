from typing import Annotated

from fastapi import Depends
from firebase_admin import messaging
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.core.config import settings
from src.backend.core.database.async_engine import SessionDep
from src.backend.core.exc.exceptions.exceptions import NotFoundError
from src.backend.repos.storages import RepoStorage, StorageRepoDep
from src.backend.repos.users import RepoUsers, UsersReposDep
from src.backend.services.notifications.deps import NotificationsUserDep


__all__ = ("NotificationService",
           "NotificationServiceDep")


class NotificationService:
    def __init__(
        self,
        session: AsyncSession,
        storage_repo: RepoStorage,
        user_repo: RepoUsers,
    ):
        self.session = session
        self.storage_repo = storage_repo
        self.user_repo = user_repo
        self.firebase_app = settings.firebase_app

    async def send_notification(
        self,
        user: NotificationsUserDep,
        company_id: str,
        title: str,
        body: str,
    ) -> bool:
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            token=user.firebase_token,
        )

        try:
            response = messaging.send(message, app=self.firebase_app)
            print(f"Notification has been sent: {response}")
            return True
        except Exception as e:
            print(f"Error while notification was send: {e}")
            return False

    async def notify_about_stoplist_expired(
        self,
        stoplist_id: str,
        user_id: str,
        company_id: str,
    ) -> bool:
        stoplist_entry = await self.storage_repo.get_stoplist_entry_by_id(
            stoplist_id,
        )
        if not stoplist_entry:
            raise NotFoundError(message=f"Stoplist {stoplist_id} not found")

        product = await self.storage_repo.get_product_by_id(
            stoplist_entry.product_id,
        )
        if not product:
            raise NotFoundError(message=f"Product {product} not found")

        title = "Stop list timeout"
        body = f"Product {product.name} is not in stoplist this time"
        return await self.send_notification(user_id, company_id, title, body)

    async def notify_about_product(
        self,
        company_id: str,
        user_id: str,
        product_id: str,
        operation: str,
    ) -> bool:
        product = await self.storage_repo.get_product_by_id(product_id)

        if not product:
            raise NotFoundError(message="Product not found")

        title = "Product had given"
        body = (
            f"Product {product.name, product.article} had given. "
            f"Operation: {operation}"
        )

        return await self.send_notification(user_id, company_id, title, body)


async def create_service_of_notification(
    session: SessionDep,
    storage_repo: StorageRepoDep,
    user_repo: UsersReposDep,
) -> NotificationService:
    return NotificationService(
        session=session,
        storage_repo=storage_repo,
        user_repo=user_repo,
    )


NotificationServiceDep = Annotated[
    NotificationService,
    Depends(create_service_of_notification),
]
