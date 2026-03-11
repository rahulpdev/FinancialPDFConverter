# Tech Stack

Minimum set of tech stack decisions to enable setup of AI-optimized codebase for this project.

## Backend

- Language: Python 3.12
- Deps/tooling: uv
- API framework: FastAPI 0.120
- ASGI server: Uvicorn 0.38
- Validation / schemas: Pydantic 2
- Lint/format: Ruff
- Type checking: MyPy + Pyright
- Tests: pytest + pytest-cov + pytest-asyncio
- Structured logging: structlog (JSON).
- Required logging fields: `request_id` (from `X-Request-ID`), `extraction_run_id`, `organisation_id`, `document_id`, `stage`, `duration_ms`, `error_code`.

## Frontend

- Language: TypeScript 5.9
- Deps/runtime: Bun
- UI Library: React 19
- Framework: Next.js 16
- Validation/forms: React Hook Form 7.68.0 + Zod 4.2.1
- Lint/format: Biome
- Type checking: TypeScript `strict: true` + `tsc --noEmit`
- Tests: `bun test` + Testing Library (React) + happy-dom
- Structured logging: Pino (JSON)
- UI delivery approach: Next.js portal app + FastAPI API; deploy both; portal calls FastAPI
- Portal data access: API-only (no direct database access)

## Database

- Provider: Supabase Postgres 15
- Migrations: Supabase CLI (schema managed via migrations)
- DB access layer: SQLAlchemy 2.0 (async) + asyncpg 0.30
- Dev DB strategy: local Supabase stack via Supabase CLI
- Integration/staging DB strategy: remote Supabase project
- Extensions: `pgvector` enabled
- Tenant isolation: Postgres RLS enforced by `organisation_id`

## Containerization & Deployment

- Container: Docker
- Image model: single image for API + worker
- Process model: two deployable services from single image — `api` runs FastAPI server; `worker` runs extraction worker runtime

## Health checks / Monitoring

- Primary operational interface: health endpoints + structured JSON logs + alerts
- Secondary operational interface: Supabase console + documented SQL queries
- Health endpoints: liveness + db + readiness
