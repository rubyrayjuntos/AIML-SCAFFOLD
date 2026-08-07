-- Run once per environment with an identity authorized to create catalogs/schemas.
CREATE CATALOG IF NOT EXISTS IDENTIFIER(:catalog);
CREATE SCHEMA IF NOT EXISTS IDENTIFIER(:catalog || '.bronze');
CREATE SCHEMA IF NOT EXISTS IDENTIFIER(:catalog || '.silver');
CREATE SCHEMA IF NOT EXISTS IDENTIFIER(:catalog || '.gold');
CREATE SCHEMA IF NOT EXISTS IDENTIFIER(:catalog || '.ml');
CREATE SCHEMA IF NOT EXISTS IDENTIFIER(:catalog || '.ops');
