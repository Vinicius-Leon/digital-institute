from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ProblemDetail(BaseModel):
    """
    Standard error format following RFC 7807 (HTTP Problem Details).

    Having a consistent error format means that any client
    that consumes the API knows exactly how to handle errors, without needing
    to deal with different formats for different situations.
    """

    type: str = "about:blank"
    title: str
    status: int
    detail: str
    instance: str | None = None
    request_id: str | None = None


class AppError(Exception):
    """Base error for the application."""

    def __init__(
        self,
        title: str,
        detail: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_type: str = "about:blank",
    ) -> None:
        self.title = title
        self.detail = detail
        self.status_code = status_code
        self.error_type = error_type
        super().__init__(detail)


class NotFoundError(AppError):
    def __init__(self, resource: str, identifier: str | int) -> None:
        super().__init__(
            title="Resource Not Found",
            detail=f"{resource} with identifier '{identifier}' was not found.",
            status_code=status.HTTP_404_NOT_FOUND,
            error_type="/errors/not-found",
        )


class UnauthorizedError(AppError):
    def __init__(self, detail: str = "Authentication required.") -> None:
        super().__init__(
            title="Unauthorized",
            detail=detail,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_type="/errors/unauthorized",
        )


class ForbiddenError(AppError):
    def __init__(
        self, detail: str = "You don't have permission to perform this action."
    ) -> None:
        super().__init__(
            title="Forbidden",
            detail=detail,
            status_code=status.HTTP_403_FORBIDDEN,
            error_type="/errors/forbidden",
        )


class ConflictError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(
            title="Conflict",
            detail=detail,
            status_code=status.HTTP_409_CONFLICT,
            error_type="/errors/conflict",
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Registers all error handlers in the FastAPI application."""

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=exc.status_code,
            content=ProblemDetail(
                type=exc.error_type,
                title=exc.title,
                status=exc.status_code,
                detail=exc.detail,
                instance=str(request.url),
                request_id=request_id,
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        import logging

        logger = logging.getLogger(__name__)
        request_id = getattr(request.state, "request_id", None)
        logger.exception(
            "Unhandled exception",
            extra={"request_id": request_id},
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ProblemDetail(
                title="Internal Server Error",
                status=500,
                detail="An unexpected error occurred. Please try again later.",
                instance=str(request.url),
                request_id=request_id,
            ).model_dump(),
        )
