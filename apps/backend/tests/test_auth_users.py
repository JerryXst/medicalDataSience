from fastapi.testclient import TestClient

from app.core.settings import settings
from app.core.database import get_engine
from app.main import app


def configure_auth_store(tmp_path) -> None:
    settings.database_url = f"sqlite:///{tmp_path / 'test.db'}"
    get_engine.cache_clear()


def test_login_returns_role_menus(tmp_path: Path) -> None:
    configure_auth_store(tmp_path)
    client = TestClient(app)

    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin123", "entry": "portal"},
        headers={"X-Request-ID": "req-login-test"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["request_id"] == "req-login-test"
    assert payload["token"]
    assert payload["user"]["role"] == "platform_admin"
    assert "数据查询" in payload["user"]["portal_menus"]
    assert "角色权限设置" in payload["user"]["ops_menus"]


def test_business_admin_can_create_user(tmp_path: Path) -> None:
    configure_auth_store(tmp_path)
    client = TestClient(app)

    login_response = client.post(
        "/api/auth/login",
        json={"username": "manager", "password": "manager123", "entry": "ops"},
    )
    token = login_response.json()["token"]

    create_response = client.post(
        "/api/users",
        json={"username": "new_sales", "display_name": "新业务员", "password": "pwd123", "role": "salesperson"},
        headers={"Authorization": f"Bearer {token}", "X-Request-ID": "req-create-user-test"},
    )

    assert create_response.status_code == 200
    assert create_response.json()["item"]["role"] == "salesperson"

    list_response = client.get("/api/users", headers={"Authorization": f"Bearer {token}"})
    assert list_response.status_code == 200
    assert any(item["username"] == "new_sales" for item in list_response.json()["items"])
