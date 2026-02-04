# closetGPT

Be extremely concise. Sacrifice grammar for brevity. Don't write code unless requested.
At end of plans: list unresolved questions (succinct, sacrifice grammar).

## Stack
FastAPI + Next.js + PostgreSQL/pgvector + Redis + MinIO(dev)/R2(prod)

## Critical Constraints
- Logger: Use `log_info/debug/error/warning` from logger.py (never print/logging directly)
- DB: All ops through db.py abstraction (never raw SQL in main.py)
- Storage: All ops through storage.py (handles MinIO/R2 switching)
- Config: Use `get_settings()` from config.py (never os.getenv directly)
- Embeddings: 512-dim vectors, HNSW indexes
- Deletes: CASCADE from clothing_items removes embeddings

## Env Config
Dev: `.env.dev` (postgres/redis/minio in docker)
Prod: `.env.prod` (supabase/upstash/r2)

## Ports
postgres:5433 redis:6379 minio:9000/9001 backend:8000 frontend:3000

## Status
See TODO.md for current work, ROADMAP.md for phases.