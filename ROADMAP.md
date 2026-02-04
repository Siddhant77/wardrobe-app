# closetGPT Implementation Roadmap

**Goal**: Transform closetGPT into a globally-accessible distributed system

**Timeline**: 5-6 weeks to full deployment

---

## Phase 1: Local Development with Docker Compose (Week 1-2)

**Goal:** Containerize everything and run the full stack locally with dev/prod environment support

### Tasks
1. Create `docker-compose.yml` with all services:
   - PostgreSQL with pgvector extension
   - Redis (for future job queue)
   - MinIO (S3-compatible local storage for development)
   - FastAPI backend
   - Next.js frontend
2. Create environment configuration:
   - `/backend/.env.dev` - Local development (Docker services)
   - `/backend/.env.prod` - Production (cloud services)
   - Environment-based service switching
3. Create Dockerfiles:
   - `/backend/Dockerfile` (FastAPI + ML models)
   - `/wardrobe-app/Dockerfile` (Next.js)
3. Create PostgreSQL schema (users, clothing_items, item_embeddings)
4. Write migration script to move CSV → PostgreSQL
5. Update backend to use PostgreSQL instead of CSV
6. Test full stack locally

### Learning Outcomes
- Docker containerization
- Multi-container orchestration
- Local development environment

### Files to Create/Modify
- Create `/docker-compose.yml` - Include MinIO for local S3
- Create `/backend/Dockerfile`
- Create `/wardrobe-app/Dockerfile`
- Create `/backend/.env.dev` - Local development config
- Create `/backend/.env.prod.example` - Production template
- Create `/backend/config.py` - Environment-based configuration loader
- Create `/backend/storage.py` - Abstraction for local (MinIO) vs cloud (R2) storage
- Create `/backend/migrations/migrate_to_postgres.py`
- Create `/backend/migrations/schema.sql`
- Modify `/backend/main.py` - Replace CSV reads with PostgreSQL queries
- Modify `/backend/embeddings.py` - Store/retrieve embeddings from DB

### Success Criteria
✅ Full app running locally via `docker-compose up`
✅ Can switch between dev (local MinIO) and prod (R2) via environment variable

---

## Phase 2: Cloud Database & Cache Migration (Week 3)

**Goal:** Replace local PostgreSQL/Redis with Supabase/Upstash

### Tasks
1. Create Supabase project (free tier)
   - Enable pgvector extension
   - Create schema (same as local)
2. Create Upstash Redis instance (free tier)
3. Run migration script against Supabase DB
4. Update `docker-compose.yml` to point to cloud services
5. Update environment variables (.env file)
6. Test locally with cloud database

### Learning Outcomes
- Cloud database setup
- Connection string management
- Environment variable configuration
- Supabase Auth basics

### Files to Modify
- Update `/backend/.env` - Add Supabase & Upstash credentials
- Update `/docker-compose.yml` - Point to cloud services
- Update `/backend/main.py` - Use Supabase connection string

### Success Criteria
✅ Local app using cloud database/cache

---

## Phase 3: Storage Migration to Cloudflare R2 (Week 3-4)

**Goal:** Add production cloud storage while maintaining local dev setup

### Tasks
1. Create Cloudflare R2 bucket
2. Configure CORS for browser uploads
3. Upload existing 329 images to R2
4. Update backend storage abstraction:
   - Already supports MinIO (local) and R2 (prod)
   - Switch via `STORAGE_PROVIDER` environment variable
   - Generate pre-signed URLs for uploads
   - Save URLs in database
5. Update frontend to use storage URLs (works with both MinIO and R2)
6. Test image upload/display flow in both environments

### Learning Outcomes
- Object storage (S3-compatible)
- Pre-signed URLs
- CORS configuration

### Files to Create/Modify
- Update `/backend/.env.prod` - Add R2 credentials
- Update `/backend/storage.py` - Add R2 provider (MinIO already implemented)
- Modify `/backend/main.py` - Already using storage abstraction
- Modify `/wardrobe-app/components/ImageUpload.tsx` - Use dynamic storage URLs
- Database schema already uses `image_url`

### Success Criteria
✅ All images served from R2 in production
✅ All images served from MinIO in local development
✅ Can switch between environments seamlessly

---

## Phase 4: Deploy Backend to Fly.io (Week 4)

**Goal:** Deploy FastAPI backend globally

### Tasks
1. Install Fly CLI: `brew install flyctl`
2. Create Fly.io account (get $5 free credits)
3. Create `fly.toml` configuration
4. Set environment secrets:
   ```bash
   fly secrets set DATABASE_URL=<supabase-url>
   fly secrets set REDIS_URL=<upstash-url>
   fly secrets set R2_ACCESS_KEY=<cloudflare-key>
   fly secrets set JWT_SECRET=<random-secret>
   ```
5. Deploy backend: `fly deploy`
6. Test API endpoints: `curl https://your-app.fly.dev/items`
7. Update local frontend to use Fly.io backend URL

### Learning Outcomes
- Cloud deployment
- Secrets management
- Global edge compute

### Files to Create/Modify
- Create `/backend/fly.toml`
- Create `/backend/.dockerignore`
- Update `/backend/Dockerfile` - Production optimizations

### Success Criteria
✅ Backend API accessible globally at https://closetgpt.fly.dev

---

## Phase 5: Deploy Frontend to Vercel (Week 5)

**Goal:** Deploy Next.js frontend globally

### Tasks
1. Create Vercel account (free)
2. Connect GitHub repository
3. Configure environment variables:
   - `NEXT_PUBLIC_API_URL=https://closetgpt.fly.dev`
4. Deploy: `vercel deploy --prod`
5. Configure custom domain (optional)
6. Test full flow: signup → upload → recommend outfit

### Learning Outcomes
- CI/CD (auto-deploy on git push)
- Environment variables in serverless
- CDN and edge caching

### Files to Modify
- Create `/wardrobe-app/.env.production`
- Update `/wardrobe-app/next.config.js` - Production settings

### Success Criteria
✅ Full app live at https://closetgpt.vercel.app

---

## Phase 6: Authentication & Multi-User (Week 5-6)

**Goal:** Add user authentication using Supabase Auth

### Tasks
1. Enable Supabase Auth in dashboard
2. Update backend to use Supabase JWT verification
3. Add auth endpoints (register/login) or use Supabase client directly
4. Update frontend:
   - Add login/signup pages
   - Store JWT in localStorage
   - Add auth headers to API requests
5. Add `user_id` filtering to all database queries
6. Test multi-user isolation

### Learning Outcomes
- JWT authentication
- Row-level security
- User session management

### Files to Create/Modify
- Create `/backend/auth.py` - JWT verification
- Create `/wardrobe-app/app/login/page.tsx`
- Create `/wardrobe-app/app/signup/page.tsx`
- Modify `/backend/main.py` - Add `current_user` dependency to all routes
- Update `/wardrobe-app/lib/api.ts` - Add auth headers

### Success Criteria
✅ Multiple users can sign up and have isolated wardrobes

---

## Optional Future Enhancements (Post-MVP)

**After Phase 6:**
1. **Message Queue** - Add Kafka/RabbitMQ when needed for:
   - Async embedding generation (currently synchronous)
   - Event-driven architecture
   - Analytics pipeline
2. **Email Verification** - Add to Supabase Auth (simple config)
3. **Demo Mode** - Public wardrobe with sample data (good for portfolio)
4. **Monitoring** - Add Sentry (error tracking) + Upstash Analytics
5. **ML Improvements** - Fine-tune outfit recommendation algorithm
6. **Social Features** - Share outfits, follow other users

**Resume-Boosting Additions:**
- CI/CD pipeline with GitHub Actions
- End-to-end tests (Playwright)
- API documentation (FastAPI auto-docs + custom README)
- Performance monitoring (Vercel Analytics + Fly.io metrics)
