# Tech Stack

Minimum set of tech stack decisions to setup an AI-optimized codebase for this project.

## Backend

- Backend language: Python 3.12
- Backend deps/tooling: `uv`
- API framework: FastAPI 0.133
- Backend lint/format: Ruff
- Backend type checking: MyPy + Pyright
- Backend tests: pytest + pytest-cov + pytest-asyncio
- Backend structured logging: structlog (JSON + `request_id` + `extraction_run_id`)

## Frontend

- Frontend language: TypeScript (strict)
- Frontend deps/tooling: Bun
- UI delivery approach: Next.js portal app + FastAPI API; deploy both; portal calls FastAPI
- Framework: Next.js 16
- Frontend lint/format: Biome
- Frontend type checking: TypeScript `strict: true` + `tsc --noEmit`
- Frontend tests: `bun test` + Testing Library (React) + happy-dom
- Frontend validation/forms: React Hook Form + Zod
- Frontend structured logging: Pino (JSON)
- Portal data access: API-only (no direct database access)

## Database

- Provider: Supabase Postgres (managed)
- Tenant isolation: Postgres RLS enforced by `organisation_id`
- DB access layer: SQLAlchemy (async) + asyncpg
- Migrations: Supabase CLI migrations
- Local dev DB strategy: Supabase remote (dev project)

## Containerization & Deployment

- Single repo/codebase: API + worker runtime built into a single container image
- Process model: two deployable services from the same image — api runs FastAPI server; worker runs extraction worker runtime

## Health checks / Monitoring

- Primary operational interface: health endpoints + structured JSON logs + alerts
- Secondary operational interface: Supabase console + documented SQL queries
