from pydantic import BaseModel
from fastapi import APIRouter, Request

from app.services.accounts import create_user, list_users, require_permission
from app.services.audit import write_audit_log

router = APIRouter(prefix="/users", tags=["users"])


class CreateUserRequest(BaseModel):
    username: str
    display_name: str
    password: str
    role: str


@router.get("")
def get_users(request: Request) -> dict[str, object]:
    user = require_permission(request, "ops.manage_users")
    items = list_users()
    write_audit_log(
        method=request.method,
        path=request.url.path,
        action="user.list",
        status_code=200,
        entity_type="user",
        entity_id=str(user["id"]),
        message="List users",
        metadata={"count": len(items)},
        user_id=str(user["id"]),
    )
    return {"request_id": request.state.request_id, "items": items}


@router.post("")
def post_user(request: Request, payload: CreateUserRequest) -> dict[str, object]:
    user = require_permission(request, "ops.manage_users")
    created = create_user(
        username=payload.username,
        display_name=payload.display_name,
        password=payload.password,
        role=payload.role,
    )
    write_audit_log(
        method=request.method,
        path=request.url.path,
        action="user.created",
        status_code=200,
        entity_type="user",
        entity_id=str(created["id"]),
        message="Created user",
        metadata={"username": created["username"], "role": created["role"]},
        user_id=str(user["id"]),
    )
    return {"request_id": request.state.request_id, "item": created}
