from datetime import datetime, timezone
import os
import tempfile
from typing import Annotated, Tuple, Union
from uuid import uuid4

from fastapi import Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.core.config import settings
from src.backend.core.database.async_engine import SessionDep
from src.backend.core.exc.exceptions.exceptions import (BadRequestError,
                                                        ForbiddenError)
from src.backend.core.utils.minio import upload_file
from src.backend.models.users import Users
from src.backend.repos.companies import CompanyRepoDep, RepoCompany
from src.backend.repos.users import RepoUsers, UsersReposDep
from src.backend.schemes.files import FileResponseDTO, XLSProductDTO
from src.backend.services.files.deps import MinIOClientDep, ValidatedXLSFileDep
from src.backend.services.users.deps import CEODep, RegManagerDep
from src.backend.services.warehouses.deps import WarehouseDep

__all__ = ("FilesService", "FilesServiceDep")


class FilesService:
    def __init__(
        self,
        session: AsyncSession,
        user_repo: RepoUsers,
        company_repo: RepoCompany,
        minio_client: MinIOClientDep,
    ):
        self.session = session
        self.user_repo = user_repo
        self.minio_client = minio_client
        self.company_repo = company_repo
        self.bucket_name = settings.minio_bucket

    async def _check_access(
        self, user: Users, warehouse_id: str, company_id: str,
    ) -> None:
        company = await self.company_repo.get_by_id(company_id)
        if company and company.owner_id == user.uuid:
            return

        access = await self.user_repo.get_user_access(user.uuid, warehouse_id)
        if not access or access.access_level not in ("regional_manager",):
            raise ForbiddenError("User have no access to this warehouse")

    async def _save_temp_file(self, file: UploadFile) -> str:
        try:
            with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=f".{file.filename.split('.')[-1]}",
            ) as temp_file:
                content = await file.read()
                temp_file.write(content)
                return temp_file.name
        except Exception as e:
            raise BadRequestError(
                f"Error while saving file: {str(e)}",
            )

    async def upload_warehouse_photo(
        self,
        user: Union[CEODep, RegManagerDep],
        warehouse: WarehouseDep,
        company_id: str,
        file: UploadFile,
    ) -> FileResponseDTO:
        if file.content_type not in ["image/png", "image/jpeg"]:
            raise BadRequestError(
                "Invalid file type. Waiting PNG or JPEG",
            )

        await self._check_access(user, warehouse.warehouse_id, company_id)

        file_id = str(uuid4())
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        object_name = (f"{warehouse.warehouse_id}/photos/{timestamp}_{file_id}"
                       f".{file.content_type.split('/')[-1]}")

        temp_file_path = await self._save_temp_file(file)
        try:
            file_url = upload_file(
                self.minio_client,
                self.bucket_name,
                object_name,
                temp_file_path,
            )
            return FileResponseDTO(
                file_id=file_id,
                file_url=file_url,
                file_type="image",
                warehouse_id=warehouse.warehouse_id,
                uploaded_at=datetime.now(timezone.utc),
            )
        except Exception as e:
            raise BadRequestError(str(e))
        finally:
            await file.close()
            os.unlink(temp_file_path)

    async def upload_product_xls(
        self,
        user: Union[CEODep, RegManagerDep],
        warehouse: WarehouseDep,
        company_id: str,
        file: UploadFile,
        products: ValidatedXLSFileDep,
    ) -> Tuple[FileResponseDTO, list[XLSProductDTO]]:
        await self._check_access(user, warehouse.warehouse_id, company_id)

        file_id = str(uuid4())
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        obj_name = f"{warehouse.warehouse_id}/xls/{timestamp}_{file_id}.xlsx"

        temp_file_path = await self._save_temp_file(file)
        try:
            file_url = upload_file(
                self.minio_client,
                self.bucket_name,
                obj_name,
                temp_file_path,
            )
            file_response = FileResponseDTO(
                file_id=file_id,
                file_url=file_url,
                file_type="xls",
                warehouse_id=warehouse.warehouse_id,
                uploaded_at=datetime.now(timezone.utc),
            )
            return file_response, products
        except Exception as e:
            raise BadRequestError(str(e))
        finally:
            await file.close()
            os.unlink(temp_file_path)


async def get_files_service(
    session: SessionDep,
    user_repo: UsersReposDep,
    company_repo: CompanyRepoDep,
    minio_client: MinIOClientDep,
) -> FilesService:
    return FilesService(
        session=session,
        user_repo=user_repo,
        minio_client=minio_client,
        company_repo=company_repo,
    )

FilesServiceDep = Annotated[FilesService, Depends(get_files_service)]
