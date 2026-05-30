from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from app.services.audit import write_audit_log
from app.services.ingestion import (
    UnsupportedFileTypeError,
    create_import_task,
    list_import_tasks,
)
from app.services.accounts import require_permission

router = APIRouter(prefix="/import-tasks", tags=["import-tasks"])


@router.post("")
def upload_import_task(request: Request, file: UploadFile = File(...)) -> dict[str, object]:
    user = require_permission(request, "ops.upload_data")
    try:
        task = create_import_task(
            file=file,
            request_id=request.state.request_id,
            user_id=str(user["id"]),
        )
    except UnsupportedFileTypeError as exc:
        write_audit_log(
            method=request.method,
            path=request.url.path,
            action="import_task.upload_rejected",
            status_code=400,
            message=str(exc),
            metadata={"filename": file.filename},
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"request_id": request.state.request_id, "item": task}


@router.get("")
def get_import_tasks(request: Request) -> dict[str, object]:
    user = require_permission(request, "ops.view_import_tasks")
    tasks = list_import_tasks()
    write_audit_log(
        method=request.method,
        path=request.url.path,
        action="import_task.list",
        status_code=200,
        message="List import tasks",
        metadata={"count": len(tasks)},
        user_id=str(user["id"]),
    )
    return {"request_id": request.state.request_id, "items": tasks}
