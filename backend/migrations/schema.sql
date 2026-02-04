-- closetGPT Database Schema
-- PostgreSQL with pgvector extension for vector similarity search

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (for Phase 6 - Authentication)
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),  -- NULL for OAuth users
    full_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true
);

-- Create index on email for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Clothing items table
CREATE TABLE IF NOT EXISTS clothing_items (
    item_id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    image_name VARCHAR(255) NOT NULL,
    image_url VARCHAR(512) NOT NULL,  -- URL in MinIO/R2
    item_category VARCHAR(50) NOT NULL,
    weather_label INTEGER DEFAULT 0,
    formality_label INTEGER DEFAULT 0,
    vote_score INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_clothing_items_user_id ON clothing_items(user_id);
CREATE INDEX IF NOT EXISTS idx_clothing_items_category ON clothing_items(item_category);
CREATE INDEX IF NOT EXISTS idx_clothing_items_weather ON clothing_items(weather_label);
CREATE INDEX IF NOT EXISTS idx_clothing_items_formality ON clothing_items(formality_label);
CREATE INDEX IF NOT EXISTS idx_clothing_items_created_at ON clothing_items(created_at DESC);

-- Item embeddings table with vector columns
CREATE TABLE IF NOT EXISTS item_embeddings (
    item_id BIGINT PRIMARY KEY REFERENCES clothing_items(item_id) ON DELETE CASCADE,
    clip_embedding vector(512) NOT NULL,  -- CLIP embeddings (512 dimensions)
    fashion_embedding vector(512) NOT NULL,  -- FashionCLIP embeddings (512 dimensions)
    embedding_version VARCHAR(50) DEFAULT 'v1',  -- Track embedding model version
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create vector similarity search indexes using HNSW
-- HNSW (Hierarchical Navigable Small World) is faster than IVFFlat for most use cases
CREATE INDEX IF NOT EXISTS idx_embeddings_clip_hnsw
    ON item_embeddings USING hnsw (clip_embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_embeddings_fashion_hnsw
    ON item_embeddings USING hnsw (fashion_embedding vector_cosine_ops);

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update trigger to clothing_items
CREATE TRIGGER update_clothing_items_updated_at
    BEFORE UPDATE ON clothing_items
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Apply update trigger to users
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create a default user for Phase 1 (before authentication)
-- This user will own all items uploaded during development
INSERT INTO users (user_id, email, full_name, is_active)
VALUES (
    '00000000-0000-0000-0000-000000000000',
    'dev@closetgpt.local',
    'Development User',
    true
)
ON CONFLICT (user_id) DO NOTHING;

-- Useful views for analytics (optional)
CREATE OR REPLACE VIEW wardrobe_stats AS
SELECT
    u.user_id,
    u.email,
    COUNT(ci.item_id) as total_items,
    COUNT(DISTINCT ci.item_category) as unique_categories,
    AVG(ci.vote_score) as avg_vote_score,
    MAX(ci.created_at) as last_upload
FROM users u
LEFT JOIN clothing_items ci ON u.user_id = ci.user_id
GROUP BY u.user_id, u.email;

-- Grant permissions (adjust as needed)
-- For development, we'll use the default postgres user
-- For production, you should create a specific app user with limited permissions

COMMENT ON TABLE users IS 'User accounts for closetGPT';
COMMENT ON TABLE clothing_items IS 'Wardrobe items with metadata';
COMMENT ON TABLE item_embeddings IS 'Vector embeddings for similarity search';
COMMENT ON COLUMN item_embeddings.clip_embedding IS 'CLIP model embeddings (512-dim)';
COMMENT ON COLUMN item_embeddings.fashion_embedding IS 'FashionCLIP model embeddings (512-dim)';

-- End of schema
