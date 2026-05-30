from __future__ import annotations

import json
from uuid import uuid4

from sqlalchemy import text

from app.core.database import ensure_runtime_tables, get_engine
from app.core.request_context import current_request_id, current_user_id


def write_audit_log(
    *,
    method: str,
    path: str,
    action: str,
    status_code: int | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    message: str | None = None,
    metadata: dict[str, object] | None = None,
    request_id: str | None = None,
    user_id: str | None = None,
) -> None:
    ensure_runtime_tables()
    with get_engine().begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO audit_logs (
                  id, request_id, user_id, method, path, action, status_code,
                  entity_type, entity_id, message, metadata_json
                )
                VALUES (
                  :id, :request_id, :user_id, :method, :path, :action, :status_code,
                  :entity_type, :entity_id, :message, :metadata_json
                )
                """
            ),
            {
                "id": str(uuid4()),
                "request_id": request_id or current_request_id(),
                "user_id": user_id or current_user_id(),
                "method": method,
                "path": path,
                "action": action,
                "status_code": status_code,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "message": message,
                "metadata_json": json.dumps(metadata or {}, ensure_ascii=False),
            },
        )


def list_audit_logs(
    *,
    request_id: str | None = None,
    user_id: str | None = None,
    limit: int = 100,
) -> list[dict[str, object]]:
    ensure_runtime_tables()

    filters = []
    params: dict[str, object] = {"limit": min(max(limit, 1), 500)}
    if request_id:
        filters.append("request_id = :request_id")
        params["request_id"] = request_id
    if user_id:
        filters.append("user_id = :user_id")
        params["user_id"] = user_id

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    query = text(
        f"""
        SELECT id, request_id, user_id, method, path, action, status_code,
               entity_type, entity_id, message, metadata_json, created_at
        FROM audit_logs
        {where_clause}
        ORDER BY created_at DESC
        LIMIT :limit
        """
    )

    with get_engine().connect() as conn:
        rows = conn.execute(query, params).mappings().all()

    items: list[dict[str, object]] = []
    for row in rows:
        item = dict(row)
        item["created_at"] = str(item["created_at"])
        try:
            item["metadata"] = json.loads(str(item.pop("metadata_json") or "{}"))
        except json.JSONDecodeError:
            item["metadata"] = {}
        items.append(item)
    return items
