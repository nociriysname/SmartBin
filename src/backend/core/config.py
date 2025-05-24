import firebase_admin
from firebase_admin import credentials
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    postgres_db: str = ""
    postgres_host: str = "db"
    postgres_port: int = 5432
    postgres_user: str = ""
    postgres_password: str = ""

    minio_endpoint: str = ""
    minio_access_key: str = ""
    minio_secret_key: str = ""
    minio_bucket: str = "SmartBin"
    minio_secure: bool = False

    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""

    redis_host: str = "localhost"
    redis_port: int = 6379

    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/0"

    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expires: int = 60 * 10

    fcm_service_account_path: str = ""
    fcm_project_id: str = ""

    @property
    def db_url(self):
        return (
            f"postgresql+asyncpg://{self.postgres_user}:"
            f"{self.postgres_password}@{self.postgres_host}:"
            f"{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self):
        return f"redis://{self.redis_host}:{self.redis_port}"

    @property
    def firebase_app(self):
        if not firebase_admin._apps:
            cred = credentials.Certificate(self.fcm_service_account_path)
            firebase_admin.initialize_app(
                cred,
                {"projectId": self.fcm_project_id},
            )

        return firebase_admin.get_app()

    config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid",
    )


settings = Settings()
