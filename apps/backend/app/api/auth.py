from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Request

from app.services.accounts import authenticate_user, create_token, get_authenticated_user, list_roles, serialize_user
from app.services.audit import write_audit_log

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str
    entry: str = "portal"


@router.post("/login")
def login(request: Request, payload: LoginRequest) -> dict[str, object]:
    user = authenticate_user(payload.username, payload.password)
    if user is None:
        write_audit_log(
            method=request.method,
            path=request.url.path,
            action="auth.login_failed",
            status_code=401,
            message="Login failed",
            metadata={"username": payload.username, "entry": payload.entry},
        )
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    serialized = serialize_user(user)
    token = create_token(user)
    write_audit_log(
        method=request.method,
        path=request.url.path,
        action="auth.login_success",
        status_code=200,
        entity_type="user",
        entity_id=str(user["id"]),
        message="Login success",
        metadata={"username": payload.username, "entry": payload.entry, "role": user["role"]},
        user_id=str(user["id"]),
    )
    return {"request_id": request.state.request_id, "token": token, "user": serialized}


@router.get("/me")
def me(request: Request) -> dict[str, object]:
    user = get_authenticated_user(request)
    return {"request_id": request.state.request_id, "user": serialize_user(user)}


@router.get("/roles")
def roles(request: Request) -> dict[str, object]:
    return {"request_id": request.state.request_id, "items": list_roles()}
