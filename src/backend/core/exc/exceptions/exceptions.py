from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

__all__ = (
    "HTTPError",
    "ModelHTTPError",
    "ValidationModelHTTPError",
    "BadRequestError",
    "ValidationError",
    "ForbiddenError",
    "NotFoundError",
    "UnauthorizedError",
    "UniqueViolationError",
)


class HTTPError(Exception):
    def __init__(
        self,
        http_code: int = 400,
        message: str = None,
        additional_details: dict | None = None,
        headers: dict[str, str] = None,
        commit_db: bool = False,
    ) -> None:
        self.http_code = http_code
        self.message = message
        self.additional_details = additional_details | {}
        self.headers = headers | {}
        self.commit_db = commit_db

    @staticmethod
    async def handler(_: Request, exc: "HTTPError") -> JSONResponse:
        return JSONResponse(
            content={
                "code": exc.http_code,
                **({"message": exc.message} if exc.message else {}),
                **exc.additional_details,
            },
            status_code=exc.http_code,
            headers=exc.headers,
        )


class ModelHTTPError(BaseModel):
    code: int
    message: str


class ValidationModelHTTPError(ModelHTTPError):
    details: list[dict] | None


class BadRequestError(HTTPError):
    def __init__(self, message: str = "Bad Request"):
        super().__init__(400, message)


class UnauthorizedError(HTTPError):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(401, message)


class ForbiddenError(HTTPError):
    def __init__(self, message: str = "Forbidden Error"):
        super().__init__(403, message)


class NotFoundError(HTTPError):
    def __init__(self, message: str = "Not Found"):
        super().__init__(404, message)


class UniqueViolationError(HTTPError):
    def __init__(self, message: str = "Unique Violation"):
        super().__init__(409, message)


class ValidationError(HTTPError):
    def __init__(self, message: str = "Validation Error"):
        super().__init__(423, message)
