from minio import Minio, S3Error
from src.backend.core.config import settings
from src.backend.core.utils.date import date_time

__all__ = ("get_minio_client", "ensure_bucket", "upload_file", "download_file")


def get_minio_client() -> Minio:
    client = Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )
    ensure_bucket(client, settings.minio_bucket)
    return client


def ensure_bucket(client: Minio, bucket_name: str) -> None:
    try:
        if not (client.bucket_exists(bucket_name)):
            client.make_bucket(bucket_name)
    except S3Error as e:
        raise Exception(
            f"{date_time()}.Failed of creating the bucket: {str(e)}",
        )


# Для загрузки файла на сервер. Возвращает url - доступ к файлу
def upload_file(
    client: Minio,
    bucket_name: str,
    object_name: str,
    file_path: str,
) -> str:
    try:
        client.fput_object(bucket_name, object_name, file_path)
        url = client.get_presigned_url("GET", bucket_name, object_name)
        return url
    except S3Error as e:
        raise Exception(
            f"{date_time()}.Failed of uploading file to the MinIO: {str(e)}",
        )


# Для скачивания файла
def download_file(
    client: Minio,
    bucket_name: str,
    object_name: str,
    file_path: str,
) -> None:
    try:
        client.fget_object(bucket_name, object_name, file_path)
    except S3Error as e:
        raise Exception(
            f"{date_time()}.Failed of downloading file from MinIO: {str(e)}",
        )
