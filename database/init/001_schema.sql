CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS source_platforms (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL UNIQUE,
  platform_type TEXT NOT NULL DEFAULT 'manual',
  status TEXT NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS import_batches (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  source_platform_id UUID REFERENCES source_platforms(id),
  original_filename TEXT NOT NULL,
  storage_path TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  total_rows INTEGER NOT NULL DEFAULT 0,
  error_message TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS standard_customers (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  standard_name TEXT NOT NULL,
  province TEXT,
  city TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS customer_aliases (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  standard_customer_id UUID NOT NULL REFERENCES standard_customers(id),
  source_platform_id UUID REFERENCES source_platforms(id),
  raw_name TEXT NOT NULL,
  confidence NUMERIC(5, 4),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (source_platform_id, raw_name)
);

CREATE TABLE IF NOT EXISTS standard_products (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  standard_name TEXT NOT NULL,
  specification TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (standard_name, specification)
);

CREATE TABLE IF NOT EXISTS flow_records (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  import_batch_id UUID NOT NULL REFERENCES import_batches(id),
  source_platform_id UUID REFERENCES source_platforms(id),
  flow_date DATE NOT NULL,
  raw_customer_name TEXT NOT NULL,
  raw_product_name TEXT NOT NULL,
  raw_specification TEXT,
  standard_customer_id UUID REFERENCES standard_customers(id),
  standard_product_id UUID REFERENCES standard_products(id),
  quantity NUMERIC(18, 4) NOT NULL DEFAULT 0,
  amount NUMERIC(18, 4),
  match_status TEXT NOT NULL DEFAULT 'needs_review',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_flow_records_flow_date ON flow_records(flow_date);
CREATE INDEX IF NOT EXISTS idx_flow_records_match_status ON flow_records(match_status);
CREATE INDEX IF NOT EXISTS idx_customer_aliases_raw_name ON customer_aliases(raw_name);

CREATE TABLE IF NOT EXISTS app_roles (
  role TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  permissions_json TEXT NOT NULL,
  ops_menus_json TEXT NOT NULL,
  portal_menus_json TEXT NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS app_users (
  id TEXT PRIMARY KEY,
  username TEXT NOT NULL UNIQUE,
  display_name TEXT NOT NULL,
  role TEXT NOT NULL REFERENCES app_roles(role),
  password_hash TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

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
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_request_id ON audit_logs(request_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);

INSERT INTO app_roles (role, name, description, permissions_json, ops_menus_json, portal_menus_json)
VALUES
  (
    'platform_admin',
    '平台管理员',
    '平台超管角色，具备所有权限。',
    '["ops.upload_data","ops.view_import_tasks","ops.handle_exceptions","ops.manage_users","ops.manage_roles","portal.data_query","portal.dashboard"]',
    '["数据上传","导入任务","数据异常处理","用户账号管理","角色权限设置"]',
    '["数据查询","数据看板"]'
  ),
  (
    'business_admin',
    '业务管理员',
    '业务管理者，具备创建、管理用户账号的能力。',
    '["ops.upload_data","ops.view_import_tasks","ops.handle_exceptions","ops.manage_users","portal.data_query","portal.dashboard"]',
    '["数据上传","导入任务","数据异常处理","用户账号管理"]',
    '["数据查询","数据看板"]'
  ),
  (
    'salesperson',
    '业务员',
    '普通业务人员，可以登录运营端上传数据。',
    '["ops.upload_data","ops.view_import_tasks","portal.data_query"]',
    '["数据上传","导入任务"]',
    '["数据查询"]'
  )
ON CONFLICT (role) DO NOTHING;

INSERT INTO app_users (id, username, display_name, role, password_hash, status)
VALUES
  (
    'user-platform-admin',
    'admin',
    '平台管理员',
    'platform_admin',
    '5af09bbab1a26da764436e939468b4f1d0f79dd869ac99e9e1d6a9b7e56b1815',
    'active'
  ),
  (
    'user-business-admin',
    'manager',
    '业务管理员',
    'business_admin',
    '7c80a35b30a76fe0487213da8358415f1bc9ef910a4c378a0eefb6d645675ec0',
    'active'
  ),
  (
    'user-salesperson',
    'sales',
    '业务员',
    'salesperson',
    '4757d3f6399f805b44fe63053a3609a85b7ef7e34ebea7c5b8b23a2749c3a671',
    'active'
  )
ON CONFLICT (username) DO NOTHING;
