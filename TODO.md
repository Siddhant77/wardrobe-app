# closetGPT TODO List

**Current Phase**: Phase 1 - Local Development with Docker Compose

**Last Updated**: 2026-02-02

**Progress**: 13/17 tasks completed (76%)

---

## Summary of Completed Work

### Files Created (13 new files)
1. `docker-compose.yml` - Full stack orchestration
2. `backend/Dockerfile` - FastAPI container
3. `backend/.dockerignore` - Docker build exclusions
4. `backend/.env.dev` - Local development config
5. `backend/.env.prod.example` - Production config template
6. `backend/config.py` - Environment configuration loader
7. `backend/storage.py` - Storage abstraction (MinIO/R2)
8. `backend/db.py` - Database operations layer
9. `backend/migrations/schema.sql` - PostgreSQL schema with pgvector
10. `backend/migrations/migrate_to_postgres.py` - Migration script
11. `wardrobe-app/Dockerfile` - Next.js container
12. `wardrobe-app/.dockerignore` - Docker build exclusions

### Files Updated (3 files)
1. `backend/requirements.txt` - Added PostgreSQL, Redis, boto3, pgvector dependencies
2. `backend/main.py` - Complete refactor for PostgreSQL + storage
3. `.gitignore` - Added env files, Docker, Python cache

### Architecture Changes
- **Database**: CSV → PostgreSQL with pgvector extension
- **Storage**: Local filesystem → MinIO (dev) / R2 (prod)
- **Embeddings**: .npy files → PostgreSQL vector columns
- **Configuration**: Hardcoded → Environment-based (dev/prod)
- **API**: Added health check, database connection pooling, proper error handling

---

## Phase 1 Tasks (In Progress)

### 1. Docker Infrastructure Setup ✅
- [x] Create `docker-compose.yml` with:
  - PostgreSQL (with pgvector extension)
  - Redis (for caching/job queue)
  - MinIO (S3-compatible local storage)
  - FastAPI backend
  - Next.js frontend
- [x] Create `/backend/Dockerfile` (FastAPI + ML models)
- [x] Create `/wardrobe-app/Dockerfile` (Next.js with multi-stage build)
- [x] Create `/backend/.dockerignore`
- [x] Create `/wardrobe-app/.dockerignore`
- [x] Update `.gitignore` with env files, Docker, Python cache

### 1.5 Environment Configuration ✅
- [x] Create `/backend/.env.dev` - Local development config:
  - DATABASE_URL (local PostgreSQL)
  - REDIS_URL (local Redis)
  - STORAGE_PROVIDER=minio
  - MINIO_ENDPOINT (local MinIO)
- [x] Create `/backend/.env.prod.example` - Production template:
  - DATABASE_URL (Supabase)
  - REDIS_URL (Upstash)
  - STORAGE_PROVIDER=r2
  - R2 credentials (no S3, R2 only)
- [x] Create `/backend/config.py` - Environment loader with validation
- [x] Create `/backend/storage.py` - Storage abstraction (MinIO + R2)
- [x] Update `/backend/requirements.txt` - Added PostgreSQL, Redis, boto3, pgvector

### 2. Database Setup ✅
- [x] Create `/backend/migrations/schema.sql` - PostgreSQL schema with pgvector
  - Users table (with default dev user)
  - Clothing items table
  - Item embeddings table (with vector(512) columns)
  - HNSW indexes for vector similarity search
  - Triggers for auto-updating timestamps

### 3. Migration Script ✅
- [x] Create `/backend/migrations/migrate_to_postgres.py`
  - Read metadata.csv
  - Load .npy embedding files (CLIP + FashionCLIP)
  - Upload images to storage (MinIO/R2)
  - Insert into PostgreSQL with embeddings
  - Progress tracking with tqdm

### 4. Backend Refactoring ✅
- [x] Create `/backend/db.py` - Database abstraction layer:
  - Connection pooling with psycopg2
  - CRUD operations for items and embeddings
  - Helper functions for queries
- [x] Update `/backend/main.py`:
  - ✅ Added startup/shutdown events for DB connection pooling
  - ✅ Replace CSV file reads with PostgreSQL queries
  - ✅ Update CORS to use config
  - ✅ Update GET /items endpoint
  - ✅ Update GET /items/{item_id} endpoint
  - ✅ Update POST /vote endpoint
  - ✅ Update POST /upload-image endpoint (storage + PostgreSQL)
  - ✅ Update DELETE /delete-item endpoint (PostgreSQL + storage)
  - ✅ Update POST /update-metadata endpoint
  - ✅ Update load_metadata() to query PostgreSQL
  - ✅ Update load_embeddings() to query PostgreSQL
  - ✅ Add /health endpoint

### 5. Testing & Validation 🚧
- [ ] Test: `docker-compose up` brings up all services
- [ ] Test: Can connect to PostgreSQL from backend
- [ ] Test: Migration script successfully transfers all 163 items
- [ ] Test: Backend API endpoints work with PostgreSQL
- [ ] Test: Frontend can fetch and display wardrobe items
- [ ] Test: Can upload new image and generate embeddings
- [ ] Test: Can delete items

**Next Steps**: Ready to start testing! All infrastructure and code is in place.

---

## Phase 2 Tasks (Not Started)

- [ ] Create Supabase project
- [ ] Create Upstash Redis instance
- [ ] Update environment variables
- [ ] Run migration against Supabase
- [ ] Test with cloud services
- [ ] **SECURITY: Implement presigned URLs for image access** (Issue #11)
  - Replace public bucket URLs with temporary signed URLs
  - Update storage.py to generate presigned URLs (1-hour expiration)
  - Ensure images are not publicly accessible without authentication
  - Critical before multi-user deployment (Phase 6)

---

## Phase 3 Tasks (Not Started)

- [ ] Create Cloudflare R2 bucket
- [ ] Upload images to R2
- [ ] Update upload logic
- [ ] Test image serving

---

## Phases 4-6 (Not Started)

See ROADMAP.md for details.

---

## Notes & Blockers

**Current Blockers**: None

**Ready for Testing**: All infrastructure and code complete. Next step is to test the stack.

**Questions**:
- None

**Decisions Made**:
- Using lean stack (Supabase, Fly.io, R2, Vercel, Upstash)
- PostgreSQL with pgvector for embeddings (no separate vector DB)
- Docker Compose for local development with MinIO
- R2 only for production storage (no S3 support)
- HNSW indexing for vector similarity search (faster than IVFFlat)
- Database connection pooling with psycopg2
- Storage abstraction layer for seamless dev/prod switching

---

## Useful Commands

```bash
# Development mode (local services)
export ENV=dev
docker-compose up

# Start in detached mode
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop all services
docker-compose down

# Rebuild containers
docker-compose up --build

# Access PostgreSQL
docker-compose exec postgres psql -U closetgpt -d closetgpt

# Access MinIO (local S3)
# Web UI: http://localhost:9001
# Credentials: minioadmin / minioadmin

# Run migration
docker-compose exec backend python migrations/migrate_to_postgres.py

# Test with production config (using cloud services)
# Update backend container to use .env.prod
docker-compose run -e ENV=prod backend uvicorn main:app --reload
```
