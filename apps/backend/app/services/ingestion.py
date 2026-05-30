from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4

import pandas as pd
from fastapi import UploadFile
from sqlalchemy import text

from app.core.database import ensure_runtime_tables, get_engine
from app.core.settings import settings
from app.services.audit import write_audit_log


ALLOWED_FILE_SUFFIXES = {".csv", ".xls", ".xlsx"}


class UnsupportedFileTypeError(ValueError):
    pass


def archive_raw_file(source: Path, storage_root: Path) -> Path:
    storage_root.mkdir(parents=True, exist_ok=True)
    target = storage_root / source.name
    target.write_bytes(source.read_bytes())
    return target


def _safe_filename(filename: str | None) -> str:
    raw_name = filename or "uploaded-file"
    name = Path(raw_name).name
    path_name = Path(name)
    suffix = path_name.suffix.lower()
    stem = path_name.stem or "uploaded-file"
    sanitized_stem = re.sub(r"[^\w.-]+", "_", stem, flags=re.UNICODE).strip("._-")
    return f"{sanitized_stem or 'uploaded-file'}{suffix}"


def _read_csv(path: Path) -> pd.DataFrame:
    last_error: Exception | None = None
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError as exc:
            last_error = exc
    if last_error:
        raise last_error
    return pd.read_csv(path)


def _read_table_row_count(path: Path) -> int:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        frame = _read_csv(path)
    elif suffix in {".xls", ".xlsx"}:
        frame = pd.read_excel(path)
    else:
        raise UnsupportedFileTypeError(f"仅支持 CSV、XLS、XLSX 文件，当前文件类型为 {suffix or '未知'}")

    if frame.empty:
        raise ValueError("文件没有可解析的数据行")
    return int(len(frame.index))


def _manual_source_platform_id() -> str:
    ensure_runtime_tables()
    platform_id = str(uuid4())
    with get_engine().begin() as conn:
        existing = conn.execute(
            text("SELECT id FROM source_platforms WHERE name = :name"),
            {"name": "manual-upload"},
        ).scalar_one_or_none()
        if existing:
            return str(existing)

        conn.execute(
            text(
                """
                INSERT INTO source_platforms (id, name, platform_type, status)
                VALUES (:id, :name, 'manual', 'active')
                """
            ),
            {"id": platform_id, "name": "manual-upload"},
        )
    return platform_id


def create_import_task(*, file: UploadFile, request_id: str, user_id: str) -> dict[str, object]:
    original_filename = _safe_filename(file.filename)
    suffix = Path(original_filename).suffix.lower()
    if suffix not in ALLOWED_FILE_SUFFIXES:
        raise UnsupportedFileTypeError("仅支持上传 Excel 或 CSV 文件")

    task_id = str(uuid4())
    storage_dir = settings.raw_file_storage_path / task_id
    storage_dir.mkdir(parents=True, exist_ok=True)
    storage_path = storage_dir / original_filename
    storage_path.write_bytes(file.file.read())

    source_platform_id = _manual_source_platform_id()
    ensure_runtime_tables()
    with get_engine().begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO import_batches (
                  id, source_platform_id, original_filename, storage_path, status, total_rows
                )
                VALUES (
                  :id, :source_platform_id, :original_filename, :storage_path, 'processing', 0
                )
                """
            ),
            {
                "id": task_id,
                "source_platform_id": source_platform_id,
                "original_filename": original_filename,
                "storage_path": str(storage_path),
            },
        )

    write_audit_log(
        method="POST",
        path="/api/import-tasks",
        action="import_task.created",
        status_code=202,
        entity_type="import_batch",
        entity_id=task_id,
        message="Created import parsing task",
        metadata={"filename": original_filename},
        request_id=request_id,
        user_id=user_id,
    )

    try:
        total_rows = _read_table_row_count(storage_path)
    except Exception as exc:  # noqa: BLE001 - error detail is part of the task result.
        error_message = str(exc)
        with get_engine().begin() as conn:
            conn.execute(
                text(
                    """
                    UPDATE import_batches
                    SET status = 'failed',
                        error_message = :error_message,
                        completed_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                    """
                ),
                {"id": task_id, "error_message": error_message},
            )
        write_audit_log(
            method="POST",
            path="/api/import-tasks",
            action="import_task.failed",
            status_code=200,
            entity_type="import_batch",
            entity_id=task_id,
            message=error_message,
            metadata={"filename": original_filename},
            request_id=request_id,
            user_id=user_id,
        )
    else:
        error_message = None
        with get_engine().begin() as conn:
            conn.execute(
                text(
                    """
                    UPDATE import_batches
                    SET status = 'completed',
                        total_rows = :total_rows,
                        error_message = NULL,
                        completed_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                    """
                ),
                {"id": task_id, "total_rows": total_rows},
            )
        write_audit_log(
            method="POST",
            path="/api/import-tasks",
            action="import_task.completed",
            status_code=200,
            entity_type="import_batch",
            entity_id=task_id,
            message="Import file parsed successfully",
            metadata={"filename": original_filename, "total_rows": total_rows},
            request_id=request_id,
            user_id=user_id,
        )

    return get_import_task(task_id)


def get_import_task(task_id: str) -> dict[str, object]:
    ensure_runtime_tables()
    with get_engine().connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT id, original_filename, status, total_rows, error_message, created_at, completed_at
                FROM import_batches
                WHERE id = :id
                """
            ),
            {"id": task_id},
        ).mappings().one()

    return _serialize_task(row)


def list_import_tasks() -> list[dict[str, object]]:
    ensure_runtime_tables()
    with get_engine().connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, original_filename, status, total_rows, error_message, created_at, completed_at
                FROM import_batches
                ORDER BY created_at DESC
                LIMIT 100
                """
            )
        ).mappings().all()
    return [_serialize_task(row) for row in rows]


def _serialize_task(row) -> dict[str, object]:
    return {
        "id": str(row["id"]),
        "filename": row["original_filename"],
        "status": row["status"],
        "total_rows": row["total_rows"],
        "error_message": row["error_message"],
        "created_at": str(row["created_at"]),
        "completed_at": str(row["completed_at"]) if row["completed_at"] else None,
    }
