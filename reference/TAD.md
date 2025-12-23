# Technical Architecture Document

Financial PDFs Converter

TAD Version 1.1 (Combined)
Date 2025-12-23

## 1 Purpose and scope

- Purpose: production-ready pilot architecture implementing PRD requirements and Blueprint Section 7 guidance.
- Audience: engineers building and operating the pilot; future maintainers extending to vNext modules.
- In scope:
  - API-first PDF ingestion, async processing, results retrieval.
  - Minimal pilot web portal (upload, history, results view, CSV download).
  - Five-stage extraction engine (Stages 1–5), LLMWhisperer-only table extraction.
  - Dual-path storage: exact rows in `document_rows`, semantic chunks + embeddings in `documents`.
  - Retention enforcement: structured outputs deleted after 10 days; metadata retained.
  - Observability, security baseline, CI/CD, deployment, handover artifacts.
- Out of scope:
  - Durable storage of original PDFs.
  - Alternative extraction providers or open-source fallback extraction provider during pilot.
  - Billing/subscriptions, enterprise compliance artefacts, complex RBAC/SSO.
  - XLSX outputs, downstream analytics (AML/DCF/ratios/projections).

## 2 Open decisions requiring confirmation (blocking)

1. External API auth header standard: `Authorization: Bearer <api_key>` vs `X-API-Key`.
2. Results status for “in progress”: return `202 Accepted` vs `200` with `status=processing`.
3. Portal authentication mechanism: shared pilot login via Supabase Auth vs single shared basic-auth gate.

## 3 Constraints and feasibility assessment

### 3.1 Hard constraints (from PRD + Blueprint)

- No durable PDF storage; transient handling only; guaranteed cleanup.
- Structured outputs retained for max 10 days; metadata retained permanently.
- LLMWhisperer is the only enabled table extraction provider for pilot.
- Dual-path RAG design:
  - Structured path: normalized rows in `document_rows`.
  - Semantic path: text chunks + embeddings in `documents` (pgvector).
- Vertical-slice architecture.
- Per-organisation concurrency: at most one active extraction per `organisation_id`; FIFO for additional jobs.
- Single-builder constraint: architecture and ops sized for one engineer.

### 3.2 Explicit trade-off decisions

- **Single service codebase (API + worker in one repo)**
  - Alternatives: split API/worker services; separate queue infrastructure.
  - Trade-off: fewer scaling levers; simpler pilot ops; easier handover.
- **Per-org FIFO concurrency guard implemented with hybrid approach**
  - In-memory FIFO for immediate scheduling + DB-backed job records for crash recovery.
  - Trade-off: slightly more logic than pure in-memory; materially improves correctness after restarts.
- **Embeddings on ingest, feature-flagged**
  - Default ON to match dual-path contract; allow OFF for performance/cost tuning.
  - Trade-off: risk of higher latency/cost; avoids future backfill burden.
- **Portal is pilot-thin, admin-oriented**
  - No per-user roles; optional nullable `user_id` for future audit.
  - Trade-off: limited audit granularity; faster pilot delivery.

### 3.3 Known unknowns / validation risks

- PDF variability and scan quality driving accuracy variance.
- LLMWhisperer latency/outage impact on end-to-end SLA.
- Embeddings impact on runtime and cost under burst load.
- Canonical schema fit for edge-case statements/transactions.
- Restart/crash behavior with in-memory scheduler (mitigated via DB reconciliation).

## 4 Architecture overview

### 4.1 Components

- **API Service (FastAPI)**
  - External API endpoints: ingestion + results.
  - Portal-serving endpoints (or separate thin portal frontend calling API).
  - Auth (org API keys, portal session).
  - Validation, document registration, orchestration.
- **Worker Runtime (same codebase)**
  - Background job loop pulling queued documents.
  - Five-stage pipeline execution.
  - Retry policy, idempotency, status transitions.
- **Database (Supabase Postgres)**
  - RLS enforced by `organisation_id`.
  - pgvector enabled for embeddings.
  - Scheduled retention job.
- **External services**
  - LLMWhisperer: table extraction (only enabled provider).
  - Embeddings provider: OpenAI small embedding model (abstracted).

### 4.2 Vertical-slice repository structure

- `src/slices/auth/` (API keys, portal auth, middleware)
- `src/slices/ingestion/` (upload/url ingestion, validation, metadata)
- `src/slices/pipeline/` (job scheduler, per-org FIFO, status transitions)
- `src/slices/extraction_stage1/` (input discovery + run registration)
- `src/slices/extraction_stage2/` (table detection and table-map)
- `src/slices/extraction_stage3/` (LLMWhisperer extraction, retries, raw artefacts)
- `src/slices/extraction_stage4/` (normalisation, schema mapping, Pydantic validation)
- `src/slices/extraction_stage5/` (dual-path persistence, delivery artefact prep)
- `src/slices/results/` (results API, CSV generation, HTML view models)
- `src/slices/portal/` (minimal UI pages, server handlers)
- `src/slices/ops/` (retention, rate limits, kill-switch, health checks)
- `src/shared/` (db, config, logging, error codes, utilities)

### 4.3 Data flow

1. Ingest via API/portal → validate → create `documents` row (metadata-only) + create `extraction_runs` row.
2. Persist job state (`queued`) and enqueue into per-org FIFO scheduler.
3. Worker executes five stages; updates `extraction_runs` and `documents.status`.
4. Stage 5 writes:
   - `document_rows` (normalized rows).
   - `documents` semantic chunks + embeddings.
   - delivery artefacts metadata (for JSON/CSV/HTML rendering).
5. Client polls results endpoint; portal shows history and downloads.
6. Retention job deletes structured outputs after 10 days; keeps metadata and audit.

## 5 Interface contracts

### 5.1 External API endpoints

- `POST /api/v1/documents`

  - Auth: org API key.
  - Body: multipart PDF upload OR JSON with `file_url`.
  - Returns: `document_id`, `status=queued`, warnings.
  - Errors: 400/401/403/413/415/429/5xx.

- `GET /api/v1/documents/{document_id}`
  - Auth: org API key.
  - Returns:
    - If `succeeded`: `status=succeeded`, canonical JSON payload(s) + metadata.
    - If `processing|queued`: `status=processing|queued`, retry guidance.
    - If `failed`: `status=failed`, stable error code, high-level reason.
    - If `expired`: `status=expired`, retention explanation.
  - Status codes (default):
    - `200` for terminal states (succeeded/failed/expired).
    - `202` for queued/processing.

### 5.2 Portal endpoints (thin)

- `GET /portal/login`
- `POST /portal/login`
- `GET /portal/documents`
- `GET /portal/documents/{document_id}`
- `GET /portal/documents/{document_id}/download.csv?table=<name>`

### 5.3 Status model (single canonical)

- `queued` → `processing` → (`succeeded` | `failed`) → `expired` (retention post-processing)
- Prohibited terms: `completed`.

### 5.4 Error model

- Stable error code format: `STAGE{N}_{CATEGORY}_{DETAIL}` (e.g., `STAGE3_PROVIDER_TIMEOUT`).
- Response body includes:
  - `error_code`, `message`, `correlation_id`, `retryable`.
- Logs include full diagnostics; responses remain non-sensitive.

## 6 Data model

### 6.1 Core tables

- `organisations`

  - `id`, `name`, `created_at`.

- `api_keys`

  - `id`, `organisation_id`, `key_hash`, `created_at`, `revoked_at`, `last_used_at`.

- `documents` (metadata + semantic path)

  - `id`, `organisation_id`, `user_id` (nullable), `source_channel` (api|portal)
  - `document_type_hint` (nullable), `customer_reference` (nullable)
  - `status` (enum), `created_at`, `updated_at`, `deleted_at` (soft delete)
  - PDF metadata: `filename`, `size_bytes`, `content_hash`, `page_count`, `pdf_version`
  - QA flags: `scan_suspected`, `embedded_js_present`, `signature_present`, `xmp_present`
  - Semantic fields (for chunks): `chunk_id`, `chunk_text`, `embedding` (vector), `embedding_model`, `embedding_dim`
  - Retention: `expires_at`, `expired_at`.

- `extraction_runs` (transactions-style)

  - `id`, `document_id`, `organisation_id`, `user_id` (nullable)
  - `status`, `started_at`, `finished_at`
  - Stage timings: `stage1_ms`..`stage5_ms`
  - Provider fields: `llmwhisperer_request_ids[]`, `retry_count`
  - Quality: `quality_score`, `accuracy_sampled_bool` (optional)
  - Failure: `error_code`, `error_summary`, `retryable_bool`
  - Usage: `virtual_tokens_in`, `virtual_tokens_out`.

- `document_rows` (structured path)

  - `id`, `document_id`, `organisation_id`, `schema_family` (accounts|bank)
  - `table_name`, `row_index`, `row_json` (canonical)
  - `source_page_range` (optional), `confidence` (optional)
  - `created_at`, `deleted_at`, `expires_at`.

- `raw_artefacts` (pilot-safe raw outputs)

  - `id`, `document_id`, `extraction_run_id`, `artefact_type` (provider_output|table_map|debug)
  - `payload_json` (compressed) or `payload_text` (size bounded)
  - `created_at`, `expires_at` (treated as structured output; deleted by retention job).

- `audit_events`
  - `id`, `organisation_id`, `document_id` (nullable), `event_type`, `actor_type` (system|portal|api)
  - `correlation_id`, `payload_json`, `created_at`.

### 6.2 Row-Level Security

- All tenant-scoped tables include `organisation_id`.
- RLS policies:
  - API key maps to `organisation_id` in session claims.
  - Portal session maps to `organisation_id`.
  - Deny cross-org reads/writes.

### 6.3 Retention semantics

- Structured outputs subject to deletion:
  - `document_rows`, `documents` semantic chunks, `raw_artefacts`, delivery artefact rows/fields.
- Metadata retained:
  - `documents` base metadata row (with outputs removed), `extraction_runs` summary, `audit_events`.

## 7 Pipeline design (five stages)

### 7.1 Scheduler and concurrency

- Job state is persisted (`documents.status`, `extraction_runs.status`).
- In-memory per-org FIFO scheduler enforces single active job per org.
- Crash recovery:
  - On startup: reconcile `processing` jobs older than timeout → mark `failed` with `retryable=true` or requeue if safe.
  - Worker loop polls DB for `queued` documents and pushes into in-memory scheduler.

### 7.2 Stage 1 — Input discovery and run registration

- Create `extraction_runs` row.
- Capture PDF metadata and QA flags.
- Determine processing plan (doc type from hint/heuristic).
- Emit `correlation_id` for all subsequent logs.

### 7.3 Stage 2 — Table detection

- Identify candidate regions for financial statements and bank tables.
- Produce `table_map` artefact with page/bounds and table identifiers.
- Log confidence and scan-quality warnings.

### 7.4 Stage 3 — Table extraction (LLMWhisperer only)

- Provider interface exists; only LLMWhisperer implementation enabled.
- Call LLMWhisperer per candidate table region; store raw provider outputs in `raw_artefacts`.
- Retry policy: bounded retries for transient failures; stable error codes.
- Aggregate per-table quality into document-level quality score.

### 7.5 Stage 4 — Normalisation and schema mapping

- Translate provider output into semi-structured JSON.
- Validate against canonical Pydantic schemas by document family.
- Numeric precision: decimal/fixed precision only.
- Unknown labels preserved + flagged; mapping notes stored.

### 7.6 Stage 5 — Consolidation, dual-path persistence, delivery prep

- Persist canonical rows into `document_rows`.
- Generate semantic chunks from normalized rows; create embeddings; persist in `documents` chunk rows.
- Atomicity rule:
  - If semantic path fails, mark run failed and do not expose partial results.
  - Compensating deletes for any partial writes.
- Prepare delivery artefacts:
  - Canonical JSON payload for API.
  - CSV generation inputs.
  - HTML view model for portal.

## 8 Non-functional requirements mapping

### 8.1 Performance

- Ingestion API P95 < 500 ms:
  - Validate + persist metadata only; never block on extraction.
- Pipeline runtime target:
  - ≤ 5 minutes for 95% of PDFs ≤ 20 pages under pilot load; hard timeout 10 minutes.
- Per-org concurrency:
  - Single active extraction per org; FIFO queue.

### 8.2 Security

- HTTPS only; modern TLS.
- API keys:
  - Stored as hashes; rotation and revocation supported.
  - Rate limiting per org; 429 with retry-after.
- Least-privilege DB roles; RLS enforced.
- No durable PDF storage; transient file handling with guaranteed cleanup.
- Secrets in environment variables or managed secrets store.

### 8.3 Reliability and recovery

- Idempotency:
  - Content hash used for optional duplicate detection.
  - Retriable stages capture attempt counters.
- Restart recovery:
  - DB-backed job states + reconciliation logic.
- Backups:
  - DB PITR ≥ 7 days.

### 8.4 Observability

- Structured logs with `correlation_id`, `organisation_id`, `document_id`, `stage`, `duration_ms`, `error_code`.
- Metrics:
  - PDFs ingested, stage durations, success/failure rate, retry counts, retention deletions.
- Audit events:
  - Key lifecycle events stored in `audit_events` for pilot debugging.

### 8.5 Maintainability

- Vertical slices; minimal coupling; shared primitives in `src/shared` only.
- One-engineer operability: runbooks + clear local dev setup.

## 9 Dependency-risk mitigations

- LLMWhisperer outages/latency:
  - Timeouts + retries + circuit-breaker; clear error surfaces; operational alerts.
- Retention deletion defects:
  - Idempotent job; dry-run mode in non-prod; alerting on failure.
- In-memory scheduler loss on restart:
  - DB polling + reconciliation; stale-job detection.
- Embeddings cost/performance:
  - Feature flag; capture embedding timings and provider errors.

## 10 Testing and QA strategy

### 10.1 Test layers

- Unit tests: pure functions (parsers, mappers, schema validation helpers).
- Component tests: stage boundaries with mocked LLMWhisperer and embedding provider.
- E2E tests: upload → run pipeline → retrieve results → CSV download.

### 10.2 Golden dataset

- Curated PDF fixtures stored outside production tables.
- Expected outputs stored as canonical JSON snapshots.
- Regression tests enforce:
  - schema validity
  - numeric precision
  - stable status transitions
  - accuracy checks (field-level comparisons where labelled)

### 10.3 NFR verification

- Ingestion latency tests (P95).
- Pipeline runtime distribution under synthetic pilot load.
- Retention time-travel tests in non-prod with shortened window.
- RLS tests: cross-org access denied.

## 11 Implementation and delivery

### 11.1 Deployment model

- Containerised FastAPI application.
- One runtime process for API; one background worker process (same image).
- Supabase Postgres as managed DB.

### 11.2 Configuration

- Environment variables:
  - DB URL/keys
  - LLMWhisperer credentials
  - Embeddings credentials
  - Retention window (fixed 10 days in prod)
  - Feature flags: `ENABLE_SEMANTIC_STORAGE`, `ENABLE_OCR_READYNESS` (no provider fallback), `KILL_SWITCH_EXTRACTION`

### 11.3 CI/CD

- Lint + format + type check.
- Test suite (unit + component + E2E smoke).
- Build container image; deploy with rollback.

### 11.4 Runbooks (handover artifacts)

- Local dev setup.
- Deploy and rollback steps.
- Failure triage:
  - Identify stage failure from `extraction_runs`.
  - Inspect logs and `raw_artefacts` within retention window.
- Retention verification.
- Pilot metrics SQL queries.

## 12 Traceability matrix (PRD alignment)

- Feature A → `POST /api/v1/documents` + ingestion slice.
- Feature B/C → portal slice + history/results views.
- Feature D–H → stages 1–5 slices.
- Feature I → results slice + CSV generation.
- Feature J/K → logs/metadata/audit + transactions-style `extraction_runs`.
- Feature L → retention job + expired behavior.
