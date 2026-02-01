-- PostgreSQL Initialization Script for Discovery Module
-- This script runs automatically when the container starts for the first time

-- Create the discovery schema
CREATE SCHEMA IF NOT EXISTS discovery;

-- Set up search path for the discovery schema
ALTER DATABASE discovery SET search_path TO discovery, public;

-- Grant necessary privileges
GRANT ALL PRIVILEGES ON DATABASE discovery TO discovery;
GRANT ALL ON SCHEMA discovery TO discovery;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA discovery GRANT ALL ON TABLES TO discovery;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Discovery database initialized successfully';
END $$;
