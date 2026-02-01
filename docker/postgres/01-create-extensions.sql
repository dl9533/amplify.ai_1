-- PostgreSQL Extensions for Discovery Module
-- This script enables required extensions for the discovery service

-- Enable uuid-ossp extension for UUID generation
-- Used for generating unique identifiers across the application
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pg_trgm extension for trigram-based text search
-- Used for fuzzy matching in occupation/job title searches
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Log successful extension creation
DO $$
BEGIN
    RAISE NOTICE 'Discovery extensions (uuid-ossp, pg_trgm) created successfully';
END $$;
