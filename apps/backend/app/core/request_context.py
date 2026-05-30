from contextvars import ContextVar
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


REQUEST_ID_HEADER = "X-Request-ID"
USER_ID_HEADER = "X-User-ID"

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")
user_id_ctx: ContextVar[str] = ContextVar("user_id", default="anonymous")


def current_request_id() -> str:
    return request_id_ctx.get() or str(uuid4())


def current_user_id() -> str:
    return user_id_ctx.get() or "anonymous"


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid4())
        user_id = request.headers.get(USER_ID_HEADER) or "anonymous"
        authorization = request.headers.get("Authorization", "")
        if authorization.startswith("Bearer "):
            try:
                from app.services.accounts import get_user_by_token

                token_user = get_user_by_token(authorization.removeprefix("Bearer ").strip())
            except Exception:  # noqa: BLE001 - request context must not block request handling.
                token_user = None
            if token_user is not None:
                user_id = str(token_user["id"])

        request.state.request_id = request_id
        request.state.user_id = user_id

        request_token = request_id_ctx.set(request_id)
        user_token = user_id_ctx.set(user_id)
        try:
            response = await call_next(request)
        finally:
            request_id_ctx.reset(request_token)
            user_id_ctx.reset(user_token)

        response.headers[REQUEST_ID_HEADER] = request_id
        return response
