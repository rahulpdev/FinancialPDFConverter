# Technical Architecture Document

Financial PDFs Converter

TAD Version 1.2
Date 2025-01-17

## 1 Purpose and scope

- Purpose: production-ready pilot architecture implementing PRD requirements.
- Audience: engineers building and operating the pilot; future maintainers extending to vNext modules.
- In scope:
  - See PRD Sections 5 and 6 for definitive in-scope requirements.
- Out of scope:
  - See PRD Sections 5 and 6 for definitive out-of-scope requirements.

## 2 Open decisions requiring confirmation (blocking)

1. External API auth header standard: `Authorization: Bearer <api_key>` vs `X-API-Key`.
2. Results status for “in progress”: return `202 Accepted` vs `200` with `status=processing`.
3. Portal authentication mechanism: shared pilot login via Supabase Auth vs single shared basic-auth gate.

## 3 Constraints and feasibility assessment

### 3.1 Hard constraints

- Inherited from PRD Features A to L.
- Vertical-slice architecture.

### 3.2 Explicit trade-off decisions

- **Single service codebase (API + worker in one repo)**
  - Alternatives: split API/worker services; separate queue infrastructure.
  - Trade-off: fewer scaling levers; simpler pilot ops; easier handover.
- **Per-org FIFO concurrency guard implemented with hybrid approach**
  - In-memory FIFO for immediate scheduling + DB-backed job records for crash recovery.
  - Trade-off: slightly more logic than pure in-memory; materially improves correctness after restarts.
- **Non-resumable batch execution model**
  - Job execution is intentionally non-resumable; interruption or page refresh results in a full restart.
  - Trade-off: forfeits mid-run recovery in exchange for simpler orchestration, predictable behaviour, and lower implementation risk during pilot.
- **Embeddings on ingest, feature-flagged**
  - Default ON to match dual-path contract; allow OFF for performance/cost tuning.
  - Trade-off: risk of higher latency/cost; avoids future backfill burden.
- **Dual-path translation in Stage 4 (hybrid parsing)**
  - Alternatives: single Pydantic AI translation path only.
  - Trade-off: higher implementation complexity; stronger output trust via independent-path agreement; catches drift and edge cases that schema validation and cross-check rulesets alone may miss.
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
  - Parallel-ready backend service executing batch-style extraction jobs.
  - Designed for concurrent processing across documents; not intended for real-time or streaming workloads.
  - Five-stage pipeline execution.
  - Executes full pipeline runs atomically; interrupted runs restart from the beginning.
- **Database (Supabase Postgres)**
  - RLS enforced by `organisation_id`.
  - pgvector enabled for embeddings.
  - Scheduled retention job.
- **External services**
  - LLMWhisperer: table extraction (only enabled provider).
  - Embeddings provider: OpenAI small embedding model (abstracted).

### 4.2 Vertical-slice repository structure

- `app/core/` (universal infrastructure)
  - Configuration
  - Database connection/session management
  - Logging setup
  - Middleware (request logging, rate limiting primitives)
  - Exception base classes and canonical error primitives
  - Global dependencies
  - Application lifecycle helpers (startup/shutdown)
  - Health checks
  - Kill switch / feature flag client (client/config in core; checks executed in feature slices)
  - Retention job runner infrastructure (universal scheduling/runner; retention business logic stays with the owning slice)
- `app/shared/` (cross-feature utilities only; not universal infrastructure)
  - Reusable, non-foundational helpers used across multiple slices (e.g., base models/mixins, common schemas, small utils)
- Feature slices (product code)
  - `app/auth/` (API keys, portal auth, auth middleware)
  - `app/ingestion/` (upload/url ingestion, validation, metadata)
  - `app/pipeline/` (job scheduler, per-org FIFO, status transitions)
  - `app/extraction_stage1/` (input discovery + run registration)
  - `app/extraction_stage2/` (table detection and table-map)
  - `app/extraction_stage3/` (LLMWhisperer extraction, retries, raw artefacts)
  - `app/extraction_stage4/` (dual-method translation, discrepancy comparison, schema mapping, Pydantic validation)
  - `app/extraction_stage5/` (dual-path persistence, delivery artefact prep)
  - `app/results/` (results API, CSV generation, HTML view models)
  - `app/portal/` (minimal UI pages, server handlers)

### 4.3 Data flow

1. Ingest via API/portal → validate → compute `content_hash`; on cache hit (same org, `succeeded` within retention) return existing `document_id`, otherwise create `documents` row (metadata-only) + create `extraction_runs` row.
2. Persist job state (`queued`) and enqueue into per-org FIFO scheduler.
3. Worker executes five stages; updates `extraction_runs` and `documents.status`.
4. Stage 5 writes:
   - `document_rows` (normalized rows).
   - `document_chunks` semantic chunks + embeddings.
   - delivery artefacts metadata (for JSON/CSV/HTML rendering).
5. Client polls results endpoint; portal shows history and downloads.
6. Retention job deletes structured outputs after 10 days; keeps metadata and audit.

## 5 Interface contracts

### 5.1 External API endpoints

- `POST /api/v1/documents`
  - Auth: org API key.
  - Body: multipart PDF upload OR JSON with `file_url`.
  - Returns: `document_id`, `status=queued` (or `succeeded` on cache hit), warnings.

- `GET /api/v1/documents/{document_id}`
  - Auth: org API key.
  - Returns:
    - If `succeeded`: canonical JSON payload(s) + metadata.
    - If `processing|queued`: retry guidance.
    - If `failed`: stable error code, high-level reason.
    - If `expired`: retention explanation.

### 5.2 Portal endpoints (thin)

- `GET /portal/login`
- `POST /portal/login`
- `GET /portal/documents`
- `GET /portal/documents/{document_id}`
- `GET /portal/documents/{document_id}/download.csv?table=<name>`

### 5.3 Status model (single canonical)

- `queued` → `processing` → (`succeeded` | `failed`) → `expired` (retention post-processing)
- Prohibited terms: `completed`.
- Status reflects the lifecycle of a single batch execution attempt.

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

- `documents`
  - `id`, `organisation_id`, `user_id` (nullable), `source_channel` (api|portal), `environment` (sandbox|production)
  - `document_type_hint` (nullable), `customer_reference` (nullable)
  - `status` (enum), `created_at`, `updated_at`, `deleted_at` (soft delete)
  - PDF metadata: `filename`, `size_bytes`, `content_hash`, `page_count`, `pdf_version`
  - Statement metadata (nullable until extraction resolves): `entity_name`, `entity_identifier` (nullable), `statement_period_start`, `statement_period_end`, `currency`
  - QA flags: `scan_suspected`, `embedded_js_present`, `signature_present`, `xmp_present`
  - Retention: `expires_at`, `expired_at`.

- `document_chunks` (semantic path)
  - `id`, `organisation_id`, `document_id`,
  - Semantic fields (for chunks): `chunk_index`, `chunk_text`, `embedding` (vector), `embedding_model`, `embedding_dim`
  - `created_at`, `expires_at`, `deleted_at`

- `extraction_runs` (transactions-style)
  - `id`, `document_id`, `organisation_id`, `user_id` (nullable)
  - `status`, `started_at`, `finished_at`
  - Stage timings: `stage1_ms`..`stage5_ms`
  - Statement metadata snapshot (nullable until resolved): `entity_name`, `statement_period_start`, `statement_period_end`, `currency`
  - Provider fields: `llmwhisperer_request_ids[]`, `retry_count`
  - Quality: `quality_score`, `accuracy_sampled_bool` (optional)
  - Failure: `error_code`, `error_summary`, `retryable_bool`
  - Usage: `virtual_tokens_in`, `virtual_tokens_out`.

- `document_statements` (statement headers; persistence gate)
  - `id`, `document_id`, `organisation_id`, `schema_family` (accounts|bank), `table_name`, `entity_name` (NOT NULL), `currency` (NOT NULL), `statement_period_start` (NOT NULL), `statement_period_end` (NOT NULL), `entity_identifier` (nullable), `created_at`, `deleted_at`, `expires_at`.

- `document_rows` (structured path)
  - `id`, `document_id`, `organisation_id`, `schema_family` (accounts|bank)
  - `statement_id`, `table_name`, `row_index`, `row_json` (canonical; accounts rows include `indent_level`, `row_type`, `parent_row_index` (optional))
  - `source_page_range` (optional), `confidence` (optional)
  - `created_at`, `deleted_at`, `expires_at`.

- `raw_artefacts` (pilot-safe raw outputs)
  - `id`, `document_id`, `extraction_run_id`, `artefact_type` (provider_output|table_map|debug|validation_report)
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
  - `document_rows`, `document_chunks` semantic chunks, `raw_artefacts`.
- Metadata retained:
  - `documents`, `extraction_runs` summary, `audit_events`.

## 7 Pipeline design (five stages)

### 7.1 Scheduler and concurrency

- Job state is persisted (`documents.status`, `extraction_runs.status`).
- The system is parallel-ready and supports multiple extraction jobs executing concurrently across documents.
- In-memory per-org FIFO scheduler enforces single active job per org.
- Job execution is non-resumable by design:
  - If a worker process terminates mid-run, the extraction is marked failed and may be re-submitted as a new run.
  - No partial progress is persisted or reused between runs.

### 7.2 Stage 1 — Input discovery and run registration

- Create `extraction_runs` row (unless served from cache).
- Capture PDF metadata and QA flags.
- Determine processing plan (doc type from hint, heuristic validation or warning only).
- Best-effort inference of entity_name, statement_period_start, statement_period_end and currency for logging and downstream hints; values may be null.
- Emit `correlation_id` for all subsequent logs.

### 7.3 Stage 2 — Table detection

- Identify candidate regions for financial statements and bank tables.
- Produce `table_map` artefact with page/bounds and table identifiers.
- Log confidence and scan-quality warnings.

### 7.4 Stage 3 — Table extraction (LLMWhisperer only)

- Provider interface exists; only LLMWhisperer implementation enabled.
- LLMWhisperer calls for all candidate table regions within a single document execute concurrently via an async wrapper around the synchronous SDK (using `asyncio.to_thread` or equivalent thread-pool dispatch); per-document wall-clock time is bounded by the slowest individual call, not the sum of all calls.
- Call LLMWhisperer per candidate table region; store raw provider outputs in `raw_artefacts`.
- Retry policy: bounded retries with exponential backoff for transient failures; stable error codes.
- Aggregate per-table quality into document-level quality score.

### 7.5 Stage 4 — Normalisation and schema mapping

- Translate raw provider outputs using two independent paths: a deterministic rule-based parser and a Pydantic AI translation path; compare outputs and select a primary result using a documented selection policy, recording comparison results in `validation_report`.
- Resolve statement metadata and validate the selected output against canonical Pydantic schemas by document family; run deterministic, format-specific cross-check rulesets for company accounts; write `validation_report` at Stage 4 end for every run that completes Stage 4.
- Numeric precision: decimal/fixed precision only.
- Unknown labels preserved + flagged; mapping notes stored.

### 7.6 Stage 5 — Consolidation, dual-path persistence, delivery prep

- Persist statement headers into `document_statements` (required metadata is NOT NULL), then persist canonical rows into `document_rows` within the same transaction.
- Generate semantic chunks from normalized rows; create embeddings; persist in `document_chunks` chunk rows.
- Atomicity rule:
  - If semantic path fails, mark run failed and do not expose partial results.
  - Compensating deletes for any partial writes.
- Prepare delivery artefacts:
  - Canonical JSON payload for API.
  - CSV generation inputs.
  - HTML view model for portal.
- CSV files and HTML-rendered tables are generated on demand from `document_rows` and are not persisted as stored artefacts.

## 8 Non-functional requirements mapping

### 8.1 Performance

- Typical batch processing time::
  - ~1–2 minutes for full company accounts PDFs under pilot conditions.
- System is optimized for batch-style throughput, not real-time or interactive processing.
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
  - Content hash used to short-circuit re-extraction within retention window (org-scoped).
  - Retriable stages capture attempt counters.
- Restart recovery:
  - DB-backed job states solely for observability, failure marking, and auditability.
- Backups:
  - DB PITR ≥ 7 days.

### 8.4 Observability

- Primary operational interface (AI-optimized): health/readiness checks via HTTP endpoints + structured JSON logs with correlation IDs; alerts are built on these signals.
- Health/readiness checks cover at minimum: API/service liveness, database connectivity, and dependency readiness for extraction.
- Structured JSON logs with `correlation_id`, `organisation_id`, `document_id`, `stage`, `duration_ms`, `error_code`.
- Secondary operational interface (ad-hoc): Supabase console + documented SQL queries for investigation and pilot reporting (not primary system health).
- Metrics:
  - PDFs ingested, stage durations, success/failure rate, retry counts, retention deletions.
- Audit events:
  - Key lifecycle events stored in `audit_events` for pilot debugging.

### 8.5 Maintainability

- Vertical slices; minimal coupling; universal infrastructure in `app/core/`, cross-feature utilities in `app/shared/`.
- One-engineer operability: runbooks + clear local dev setup.

### 8.6 Accessibility

- Portal must meet WCAG 2.1 AA baseline requirements, including keyboard navigation, sufficient colour contrast, semantic markup, and screen-reader compatibility.

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
  - Use runbook SQL queries to pull `documents`, `extraction_runs`, and `raw_artefacts` for a single failure, within retention window.
- Retention verification.
- Pilot metrics SQL queries.

## 12 Traceability matrix (PRD alignment)

- Feature A → `POST /api/v1/documents` + ingestion slice.
- Feature B/C → portal slice + history/results views.
- Feature D–H → stages 1–5 slices.
- Feature I → results slice + CSV generation.
- Feature J/K → logs/metadata/audit + transactions-style `extraction_runs`.
- Feature L → retention job + expired behavior.

## Appendix A — Error code taxonomy

All codes follow the format `STAGE{N}_{CATEGORY}_{DETAIL}`. The `retryable` flag indicates whether the system should attempt automatic retry without a change to the request or configuration.

| Error code                            | Retryable | Meaning                                                                                          |
| ------------------------------------- | --------- | ------------------------------------------------------------------------------------------------ |
| STAGE0_AUTH_INVALID_KEY               | No        | API key missing or invalid.                                                                      |
| STAGE0_AUTH_FORBIDDEN                 | No        | Cross-org access denied by auth or RLS.                                                          |
| STAGE0_DB_UNAVAILABLE                 | Yes       | Database unavailable during auth, ingestion, or results retrieval.                               |
| STAGE0_KILL_SWITCH_ENABLED            | No        | Extraction blocked by KILL_SWITCH_EXTRACTION feature flag; no retry until flag is cleared.       |
| STAGE0_INPUT_NOT_PDF                  | No        | Input is not a PDF.                                                                              |
| STAGE0_INPUT_TOO_LARGE                | No        | Input exceeds configured size limit.                                                             |
| STAGE0_INPUT_ENCRYPTED                | No        | PDF is encrypted or password protected.                                                          |
| STAGE0_INPUT_URL_FETCH_FAILED         | Yes       | File URL could not be fetched or timed out.                                                      |
| STAGE0_DUPLICATE_ACTIVE_EXTRACTION    | No        | Same content hash already has an active (not yet succeeded) extraction in progress for this org. |
| STAGE0_RATE_LIMITED                   | Yes       | Per-org API rate limit exceeded; retry after the indicated interval.                             |
| STAGE0_DOCUMENT_EXPIRED               | No        | Document structured outputs deleted after retention window; 410 returned.                        |
| STAGE0_DOCUMENT_NOT_FOUND             | No        | Document ID does not exist or belongs to another organisation.                                   |
| STAGE0_CSV_EXPORT_FAILED              | Yes       | On-demand CSV generation failed for a succeeded document.                                        |
| STAGE0_HTML_RENDER_FAILED             | Yes       | On-demand HTML rendering failed for a succeeded document.                                        |
| STAGE0_RETENTION_JOB_FAILED           | Yes       | Scheduled retention deletion job failed during a batch run.                                      |
| STAGE1_RUN_REGISTRATION_FAILED        | Yes       | Failed to create run record or persist stage-1 metadata.                                         |
| STAGE1_ENQUEUE_FAILED                 | Yes       | Failed to enqueue job into per-org FIFO scheduler after run registration.                        |
| STAGE1_CONCURRENCY_GUARD_FAILED       | Yes       | Per-org concurrency guard check failed unexpectedly (distinct from normal FIFO queuing).         |
| STAGE1_METADATA_PARSE_FAILED          | No        | PDF metadata extraction failed in a non-retryable way.                                           |
| STAGE2_TABLE_DETECTION_FAILED         | Yes       | Table detection tool failed unexpectedly.                                                        |
| STAGE2_NO_RELEVANT_TABLES_FOUND       | No        | No relevant statement tables detected for declared document type.                                |
| STAGE2_TABLE_MAP_WRITE_FAILED         | Yes       | Failed to persist table_map artefact after detection completed.                                  |
| STAGE3_PROVIDER_TIMEOUT               | Yes       | LLMWhisperer call timed out.                                                                     |
| STAGE3_PROVIDER_RATE_LIMITED          | Yes       | LLMWhisperer per-minute rate limit exceeded.                                                     |
| STAGE3_PROVIDER_QUOTA_EXCEEDED        | No        | LLMWhisperer account quota exhausted; requires quota resolution before retrying.                 |
| STAGE3_PROVIDER_AUTH_FAILED           | No        | LLMWhisperer rejected our API key; requires credential check before retrying.                    |
| STAGE3_PROVIDER_BAD_REQUEST           | No        | LLMWhisperer rejected our request as malformed; requires request fix before retrying.            |
| STAGE3_PROVIDER_INTERNAL_ERROR        | Yes       | LLMWhisperer returned a 5xx server-side error.                                                   |
| STAGE3_PROVIDER_UNAVAILABLE           | Yes       | LLMWhisperer unavailable or unreachable.                                                         |
| STAGE3_PROVIDER_BAD_RESPONSE          | Yes       | LLMWhisperer response was malformed or unparseable.                                              |
| STAGE3_PROVIDER_OUTPUT_WRITE_FAILED   | Yes       | Failed to persist provider_output artefact for a table.                                          |
| STAGE3_RETRY_EXHAUSTED                | No        | Bounded retries exhausted for a transient provider failure.                                      |
| STAGE4_TRANSLATION_FAILED             | No        | Pydantic AI translation failed for the provider output.                                          |
| STAGE4_SCHEMA_VALIDATION_FAILED       | No        | Canonical schema validation failed.                                                              |
| STAGE4_NUMERIC_PARSE_FAILED           | No        | Numeric parsing or normalisation failed.                                                         |
| STAGE4_VALIDATION_REPORT_WRITE_FAILED | Yes       | Failed to persist validation_report artefact at end of Stage 4.                                  |
| STAGE5_DB_WRITE_FAILED                | Yes       | Failed to persist canonical rows or chunks to document_rows or document_chunks.                  |
| STAGE5_EMBEDDINGS_PROVIDER_FAILED     | Yes       | Embeddings provider call failed.                                                                 |
| STAGE5_ATOMICITY_VIOLATION            | Yes       | Partial-write detected across dual paths; compensating deletes required.                         |

## Appendix B — Raw artefact content specification

| Artefact type       | Mandatory | When written            | Required contents (minimum)                                                                                                                                                                                                                                                                                                       |
| ------------------- | --------- | ----------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `provider_output`   | Yes       | Stage 3, per table      | Provider request id(s), raw provider payload, page range/table id, timing, retry count.                                                                                                                                                                                                                                           |
| `table_map`         | Yes       | End of Stage 2, per run | Table list with page/bounds identifiers, detection confidence/warnings, doc-type assumption.                                                                                                                                                                                                                                      |
| `debug`             | No        | Any stage, as needed    | Redacted diagnostics snapshot (stage inputs/outputs, config flags, timing).                                                                                                                                                                                                                                                       |
| `validation_report` | Yes       | End of Stage 4, per run | Translation-path success/failure, comparison outcome (agreement count, discrepancy count and list, selected primary path), schema validation outcome, required statement metadata resolution status, row counts per table, unmapped/flagged label counts, validation warnings, cross-check discrepancies (company accounts only). |
