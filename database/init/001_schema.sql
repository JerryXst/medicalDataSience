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
