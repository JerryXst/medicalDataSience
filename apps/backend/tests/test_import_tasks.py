from pathlib import Path

from fastapi.testclient import TestClient

from app.core.database import get_engine
from app.core.settings import settings
from app.main import app
from app.services.ingestion import _safe_filename


def configure_test_database(tmp_path: Path) -> None:
    settings.database_url = f"sqlite:///{tmp_path / 'test.db'}"
    settings.raw_file_storage = str(tmp_path / "uploads")
    get_engine.cache_clear()


def test_upload_csv_creates_completed_task_and_audit_logs(tmp_path: Path) -> None:
    configure_test_database(tmp_path)
    client = TestClient(app)
    login = client.post("/api/auth/login", json={"username": "sales", "password": "sales123", "entry": "ops"})
    token = login.json()["token"]

    response = client.post(
        "/api/import-tasks",
        files={"file": ("sample.csv", "customer,product,qty\nAspirin Store,Aspirin,2\n", "text/csv")},
        headers={"Authorization": f"Bearer {token}", "X-Request-ID": "req-test-1"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "req-test-1"
    payload = response.json()
    assert payload["request_id"] == "req-test-1"
    assert payload["item"]["status"] == "completed"
    assert payload["item"]["total_rows"] == 1
    assert payload["item"]["id"]

    logs_response = client.get("/api/audit-logs", params={"request_id": "req-test-1"})
    assert logs_response.status_code == 200
    actions = {item["action"] for item in logs_response.json()["items"]}
    assert "import_task.created" in actions
    assert "import_task.completed" in actions


def test_upload_bad_csv_creates_failed_task(tmp_path: Path) -> None:
    configure_test_database(tmp_path)
    client = TestClient(app)
    login = client.post("/api/auth/login", json={"username": "sales", "password": "sales123", "entry": "ops"})
    token = login.json()["token"]

    response = client.post(
        "/api/import-tasks",
        files={"file": ("broken.csv", '"unterminated', "text/csv")},
        headers={"Authorization": f"Bearer {token}", "X-Request-ID": "req-test-2"},
    )

    assert response.status_code == 200
    item = response.json()["item"]
    assert item["status"] == "failed"
    assert item["error_message"]

    list_response = client.get("/api/import-tasks", headers={"Authorization": f"Bearer {token}"})
    assert list_response.status_code == 200
    assert list_response.json()["items"][0]["status"] == "failed"


def test_safe_filename_preserves_chinese_csv_suffix() -> None:
    assert _safe_filename("普拉洛芬滴眼液.csv") == "普拉洛芬滴眼液.csv"
