from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.core.settings import settings


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    return create_engine(settings.database_url, pool_pre_ping=True)


def ensure_runtime_tables() -> None:
    engine = get_engine()
    with engine.begin() as conn:
        if engine.dialect.name == "postgresql":
            conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS source_platforms (
                  id VARCHAR(36) PRIMARY KEY,
                  name TEXT NOT NULL UNIQUE,
                  platform_type TEXT NOT NULL DEFAULT 'manual',
                  status TEXT NOT NULL DEFAULT 'active',
                  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS app_roles (
                  role TEXT PRIMARY KEY,
                  name TEXT NOT NULL,
                  description TEXT NOT NULL,
                  permissions_json TEXT NOT NULL,
                  ops_menus_json TEXT NOT NULL,
                  portal_menus_json TEXT NOT NULL,
                  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS app_users (
                  id TEXT PRIMARY KEY,
                  username TEXT NOT NULL UNIQUE,
                  display_name TEXT NOT NULL,
                  role TEXT NOT NULL,
                  password_hash TEXT NOT NULL,
                  status TEXT NOT NULL DEFAULT 'active',
                  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS audit_logs (
                  id TEXT PRIMARY KEY,
                  request_id TEXT NOT NULL,
                  user_id TEXT NOT NULL,
                  method TEXT NOT NULL,
                  path TEXT NOT NULL,
                  action TEXT NOT NULL,
                  status_code INTEGER,
                  entity_type TEXT,
                  entity_id TEXT,
                  message TEXT,
                  metadata_json TEXT NOT NULL DEFAULT '{}',
                  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_audit_logs_request_id ON audit_logs(request_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id)"))
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS import_batches (
                  id VARCHAR(36) PRIMARY KEY,
                  source_platform_id VARCHAR(36),
                  original_filename TEXT NOT NULL,
                  storage_path TEXT NOT NULL,
                  status TEXT NOT NULL DEFAULT 'pending',
                  total_rows INTEGER NOT NULL DEFAULT 0,
                  error_message TEXT,
                  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  completed_at TIMESTAMP
                )
                """
            )
        )
