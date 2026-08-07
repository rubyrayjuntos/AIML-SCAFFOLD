-- Run once per environment with an identity authorized to create catalogs/schemas.
CREATE CATALOG IF NOT EXISTS IDENTIFIER(:catalog);
CREATE SCHEMA IF NOT EXISTS IDENTIFIER(:catalog || '.bronze');
CREATE SCHEMA IF NOT EXISTS IDENTIFIER(:catalog || '.silver');
CREATE SCHEMA IF NOT EXISTS IDENTIFIER(:catalog || '.gold');
CREATE SCHEMA IF NOT EXISTS IDENTIFIER(:catalog || '.ml');
CREATE SCHEMA IF NOT EXISTS IDENTIFIER(:catalog || '.ops');

CREATE TABLE IF NOT EXISTS IDENTIFIER(:catalog || '.ops.feature_registry') (
  feature_version STRING NOT NULL,
  feature_contract STRING NOT NULL,
  feature_schema_json STRING NOT NULL,
  builder STRING NOT NULL,
  source_datasets ARRAY<STRING> NOT NULL,
  registered_at TIMESTAMP NOT NULL,
  owner STRING NOT NULL
) USING DELTA;
