from fastapi import APIRouter, Query, Request

from app.services.audit import list_audit_logs, write_audit_log

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


@router.get("")
def get_audit_logs(
    request: Request,
    request_id: str | None = None,
    user_id: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> dict[str, object]:
    logs = list_audit_logs(request_id=request_id, user_id=user_id, limit=limit)
    write_audit_log(
        method=request.method,
        path=request.url.path,
        action="audit_logs.query",
        status_code=200,
        message="Query audit logs",
        metadata={"request_id_filter": request_id, "user_id_filter": user_id, "count": len(logs)},
    )
    return {"request_id": request.state.request_id, "items": logs}
