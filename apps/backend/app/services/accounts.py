from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import HTTPException, Request, status
from sqlalchemy import text

from app.core.database import ensure_runtime_tables, get_engine
from app.core.settings import settings


ROLE_DEFINITIONS: dict[str, dict[str, object]] = {
    "platform_admin": {
        "name": "平台管理员",
        "description": "平台超管角色，具备所有权限。",
        "permissions": [
            "ops.upload_data",
            "ops.view_import_tasks",
            "ops.handle_exceptions",
            "ops.manage_users",
            "ops.manage_roles",
            "portal.data_query",
            "portal.dashboard",
        ],
        "ops_menus": ["数据上传", "导入任务", "数据异常处理", "用户账号管理", "角色权限设置"],
        "portal_menus": ["数据查询", "数据看板"],
    },
    "business_admin": {
        "name": "业务管理员",
        "description": "业务管理者，具备创建、管理用户账号的能力。",
        "permissions": [
            "ops.upload_data",
            "ops.view_import_tasks",
            "ops.handle_exceptions",
            "ops.manage_users",
            "portal.data_query",
            "portal.dashboard",
        ],
        "ops_menus": ["数据上传", "导入任务", "数据异常处理", "用户账号管理"],
        "portal_menus": ["数据查询", "数据看板"],
    },
    "salesperson": {
        "name": "业务员",
        "description": "普通业务人员，可以登录运营端上传数据。",
        "permissions": ["ops.upload_data", "ops.view_import_tasks", "portal.data_query"],
        "ops_menus": ["数据上传", "导入任务"],
        "portal_menus": ["数据查询"],
    },
}


def _hash_password(password: str) -> str:
    return hashlib.sha256(f"medical-data:{password}".encode("utf-8")).hexdigest()


def _default_users() -> list[dict[str, object]]:
    now = datetime.now(UTC).isoformat()
    return [
        {
            "id": "user-platform-admin",
            "username": "admin",
            "display_name": "平台管理员",
            "role": "platform_admin",
            "password_hash": _hash_password("admin123"),
            "status": "active",
            "created_at": now,
        },
        {
            "id": "user-business-admin",
            "username": "manager",
            "display_name": "业务管理员",
            "role": "business_admin",
            "password_hash": _hash_password("manager123"),
            "status": "active",
            "created_at": now,
        },
        {
            "id": "user-salesperson",
            "username": "sales",
            "display_name": "业务员",
            "role": "salesperson",
            "password_hash": _hash_password("sales123"),
            "status": "active",
            "created_at": now,
        },
    ]


def ensure_seed_data() -> None:
    ensure_runtime_tables()
    with get_engine().begin() as conn:
        for role, definition in ROLE_DEFINITIONS.items():
            conn.execute(
                text(
                    """
                    INSERT INTO app_roles (
                      role, name, description, permissions_json, ops_menus_json, portal_menus_json
                    )
                    VALUES (
                      :role, :name, :description, :permissions_json, :ops_menus_json, :portal_menus_json
                    )
                    ON CONFLICT (role) DO UPDATE SET
                      name = EXCLUDED.name,
                      description = EXCLUDED.description,
                      permissions_json = EXCLUDED.permissions_json,
                      ops_menus_json = EXCLUDED.ops_menus_json,
                      portal_menus_json = EXCLUDED.portal_menus_json,
                      updated_at = CURRENT_TIMESTAMP
                    """
                ),
                {
                    "role": role,
                    "name": definition["name"],
                    "description": definition["description"],
                    "permissions_json": json.dumps(definition["permissions"], ensure_ascii=False),
                    "ops_menus_json": json.dumps(definition["ops_menus"], ensure_ascii=False),
                    "portal_menus_json": json.dumps(definition["portal_menus"], ensure_ascii=False),
                },
            )

        for user in _default_users():
            conn.execute(
                text(
                    """
                    INSERT INTO app_users (
                      id, username, display_name, role, password_hash, status, created_at
                    )
                    VALUES (
                      :id, :username, :display_name, :role, :password_hash, :status, :created_at
                    )
                    ON CONFLICT (username) DO NOTHING
                    """
                ),
                user,
            )


def _load_role_map() -> dict[str, dict[str, object]]:
    ensure_seed_data()
    with get_engine().connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT role, name, description, permissions_json, ops_menus_json, portal_menus_json
                FROM app_roles
                ORDER BY role
                """
            )
        ).mappings().all()

    role_map: dict[str, dict[str, object]] = {}
    for row in rows:
        role_map[str(row["role"])] = {
            "name": row["name"],
            "description": row["description"],
            "permissions": json.loads(str(row["permissions_json"])),
            "ops_menus": json.loads(str(row["ops_menus_json"])),
            "portal_menus": json.loads(str(row["portal_menus_json"])),
        }
    return role_map


def _row_to_user(row) -> dict[str, object]:
    return {
        "id": row["id"],
        "username": row["username"],
        "display_name": row["display_name"],
        "role": row["role"],
        "password_hash": row["password_hash"],
        "status": row["status"],
        "created_at": row["created_at"],
    }


def serialize_user(user: dict[str, object]) -> dict[str, object]:
    role = str(user["role"])
    role_definition = _load_role_map()[role]
    return {
        "id": user["id"],
        "username": user["username"],
        "display_name": user["display_name"],
        "role": role,
        "role_name": role_definition["name"],
        "status": user["status"],
        "created_at": str(user["created_at"]),
        "permissions": role_definition["permissions"],
        "ops_menus": role_definition["ops_menus"],
        "portal_menus": role_definition["portal_menus"],
    }


def list_roles() -> list[dict[str, object]]:
    role_map = _load_role_map()
    return [
        {"role": role, **definition}
        for role, definition in role_map.items()
    ]


def list_users() -> list[dict[str, object]]:
    ensure_seed_data()
    with get_engine().connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, username, display_name, role, password_hash, status, created_at
                FROM app_users
                ORDER BY created_at DESC
                """
            )
        ).mappings().all()
    return [serialize_user(_row_to_user(row)) for row in rows]


def create_user(*, username: str, display_name: str, password: str, role: str) -> dict[str, object]:
    username = username.strip()
    display_name = display_name.strip()
    if not username or not display_name or not password:
        raise HTTPException(status_code=400, detail="用户名、姓名和密码不能为空")
    if role not in _load_role_map():
        raise HTTPException(status_code=400, detail="角色不存在")

    user = {
        "id": str(uuid4()),
        "username": username,
        "display_name": display_name,
        "role": role,
        "password_hash": _hash_password(password),
        "status": "active",
        "created_at": datetime.now(UTC).isoformat(),
    }

    try:
        with get_engine().begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO app_users (
                      id, username, display_name, role, password_hash, status, created_at
                    )
                    VALUES (
                      :id, :username, :display_name, :role, :password_hash, :status, :created_at
                    )
                    """
                ),
                user,
            )
    except Exception as exc:
        raise HTTPException(status_code=400, detail="用户名已存在") from exc
    return serialize_user(user)


def authenticate_user(username: str, password: str) -> dict[str, object] | None:
    ensure_seed_data()
    password_hash = _hash_password(password)
    with get_engine().connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT id, username, display_name, role, password_hash, status, created_at
                FROM app_users
                WHERE username = :username AND password_hash = :password_hash AND status = 'active'
                """
            ),
            {"username": username, "password_hash": password_hash},
        ).mappings().one_or_none()
    return _row_to_user(row) if row else None


def _token_signature(payload: str) -> str:
    return hmac.new(settings.auth_secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()


def create_token(user: dict[str, object]) -> str:
    payload = base64.urlsafe_b64encode(
        json.dumps({"user_id": user["id"], "username": user["username"]}, ensure_ascii=False).encode("utf-8")
    ).decode("ascii")
    return f"{payload}.{_token_signature(payload)}"


def get_user_by_token(token: str) -> dict[str, object] | None:
    try:
        payload, signature = token.split(".", 1)
    except ValueError:
        return None
    if not hmac.compare_digest(signature, _token_signature(payload)):
        return None
    try:
        data = json.loads(base64.urlsafe_b64decode(payload.encode("ascii")).decode("utf-8"))
    except (json.JSONDecodeError, ValueError):
        return None

    ensure_seed_data()
    with get_engine().connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT id, username, display_name, role, password_hash, status, created_at
                FROM app_users
                WHERE id = :id AND status = 'active'
                """
            ),
            {"id": data.get("user_id")},
        ).mappings().one_or_none()
    return _row_to_user(row) if row else None


def get_authenticated_user(request: Request) -> dict[str, object]:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")
    user = get_user_by_token(header.removeprefix("Bearer ").strip())
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已失效")
    return user


def require_permission(request: Request, permission: str) -> dict[str, object]:
    user = get_authenticated_user(request)
    permissions = _load_role_map()[str(user["role"])]["permissions"]
    if permission not in permissions:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有权限执行该操作")
    return user
