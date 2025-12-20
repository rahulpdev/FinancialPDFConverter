# Product Requirements Document

Financial PDFs Converter

Prepared by Rahul Parmar  
Date 2025-12-19  
Version 1.1

## 1 Context recap

Financial PDFs Converter is an API-first service, and minimal web portal, that ingests financial PDFs (company accounts and bank statements) and returns clean structured datasets, backed by a dual-path storage model that supports both exact queries and LLM-driven contextual search. The pilot validates accuracy, time savings, and integration feasibility while preserving a foundation for future modules.

## 2 Problem statement

Operations and risk teams manually re-key data from PDFs into spreadsheets or internal systems. This work is slow, error-prone, inconsistent, and hard to automate.

## 3 Goals and non-goals

### 3.1 Goals

- G1 Process at least 30 real-world PDFs with at least 99% field extraction accuracy versus a human benchmark.
- G2 Reduce average manual processing time per PDF by at least 50% for pilot users measured externally.
- G3 Onboard at least 2 organisations who each process at least 5 PDFs through the system during the pilot.
- G4 Produce at least 2 commercial signals such as an integration request or pricing discussion.
- G5 Deliver a production-ready core five-stage extraction engine and API that can support future downstream modules without a re-architecture.

### 3.2 Non-goals

- NG1 Billing, pricing, token deduction, or subscription management.
- NG2 Advanced downstream analytics or modelling modules including DCF, ratio analysis, AML rules, projections, or Excel model generation.
- NG3 Multi-tenant self-serve onboarding, SSO, granular RBAC, or complex account management.
- NG4 Storage of original PDFs in durable storage.
- NG5 Any open-source or alternative provider fallback for table extraction in the pilot.
- NG6 Live progress bar for pilot processing.
- NG7 Native mobile apps or heavy marketing website.

## 4 Users and personas

### 4.1 Primary user

Operations analysts at fintechs and financial services firms.

Needs \- Upload or submit PDFs and receive structured output quickly. \- Trust extraction quality without deep technical debugging.

### 4.2 Secondary users

Risk analysts consuming the output.

Needs \- Consistent canonical schema, reliable numeric precision and machine-usable structured data.

Internal engineering and data teams integrating the API.

Needs \- Clear API contracts, stable auth pattern, predictable status transitions. \- Monitor extraction status and failure causes.

## 5 Scope boundaries

### 5.1 In scope

- API ingestion and results retrieval.
- Thin web portal for pilot upload and viewing over the same API.
- Five-stage extraction engine implemented as five co-equal product features.
- Canonical schema mapping for bank statements and company accounts.
- Dual-path RAG storage of structured rows and semantic chunks.
- Export formats JSON via API and CSV via portal.
- Rich metadata capture and QA support.
- Pilot administration reporting via database queries.
- Retention job that deletes structured outputs after 10 days while retaining metadata permanently.

### 5.2 Out of scope

Items listed in non-goals plus anything excluded in the blueprint out-of-scope section.

## 6 Product requirements

### 6.1 Feature A - PDF ingestion and validation API

**User story**

As a client engineering team I want to submit a financial PDF file or URL and receive a document ID immediately so that I can integrate extraction into an existing onboarding or risk workflow.

**Functional requirements**

- A1 Provide an authenticated POST endpoint to ingest PDFs.
- A2 Accept either multipart upload or a file URL.
- A3 Validate input \- File must be PDF \- Size must be within configured limit 20 MB for pilot API P95 target \- Reject encrypted or password-protected PDFs with a clear error
- A4 Register a document record with \- organisation_id \- optional user_id nullable \- document_type_hint optional \- customer_reference optional \- source channel api or portal \- content hash \- environment sandbox or production \- size_bytes \- filename \- created timestamps
- A5 Return response within P95 500 ms for valid requests \- document_id \- queued status \- validation warnings if any
- A6 Enqueue the extraction job respecting per-organisation concurrency limits.
- A7 Status transitions must be explicit: `queued`, `processing`, `succeeded`, `failed`, `expired`.

**Error handling**

- A8 4xx errors for user faults \- 400 invalid file or size \- 401 or 403 auth failure \- 409 duplicate hash optional behaviour documented \- 429 per-organisation concurrency/rate limits exceeded
- A9 5xx errors for system faults \- return generic message \- log internal diagnostics with correlation id

**Acceptance criteria**

- A10 For a valid PDF and API key, the API responds within 500 ms P95 with a document_id and queued status.
- A11 For non-PDF or encrypted PDF input the API returns 4xx with human-readable actionable guidance.
- A12 Accepted documents create records in database with correct organisation_id and metadata.
- A13 Per-organisation concurrency limits enforced (at most one active extraction per organisation), additional jobs queued.
- A14 No original PDF is stored in durable storage.

Validation notes \- QA verifies response time and status transitions. \- Logs include request id, organisation_id, document_id, validation result, stage timings.

Analytics and metrics \- Event document_ingested and document_ingest_rejected with fields: organisation_id, channel, size_bytes, document_type_hint. \- Metric ingestion_p95_ms.

### 6.2 Feature B - Pilot web portal upload

**User story**

As an operations analyst I want a simple portal to upload a PDF so that I can try the system without writing code.

**Functional requirements**

- B1 Provide minimal portal login.
- B2 File picker limited to PDFs with client-side size validation.
- B3 Portal upload calls the same ingestion API.
- B4 Portal requires a document type tag selection.
- B5 Portal displays upload confirmation, visible progress indicator and link or nav to Document History (Feature C).
- B6 Portal displays human-readable inline error messages for unsupported formats, size issues, or network failures.
- B7 Portal refresh behaviour \- if the user refreshes the page during processing, the client restarts the process from the beginning.

**Acceptance criteria**

- B8 A user can upload a PDF and see latest status.
- B9 Refresh during processing results in a restart on the client side, with a clear UI message.

Validation notes \- QA tests refresh behaviour and verifies restart and messaging.

Analytics and metrics \- Event portal_upload_failure, portal_upload_started and portal_upload_completed \- Event logs include organisation, filename, outcome, timestamp

### 6.3 Feature C - Portal document history and results viewer

**User story**

As a pilot user I want to see prior documents and view results so that I can review outputs and download data.

**Functional requirements**

- C1 Show a list of documents for the logged-in organisation.
- C2 Filter list by status.
- C3 Pagination appropriate to pilot scale.
- C4 Each list row shows \- file name or label \- document type \- created time \- status \- quality score badge
- C5 Clicking a row shows \- human-readable HTML view of extracted tables \- download link for CSV
- C6 If structured output expired \- show expired status \- explain outputs were deleted after 10 days \- keep metadata visible
- C7 Unexpected errors (e.g. network failures, inaccessible records) show a human-readable message
- C8 Portal must meet WCAG 2.1 Level AA basics for forms, contrast, keyboard navigation, alt text, and semantic HTML

**Acceptance criteria**

- C9 After uploading PDF and waiting for extraction, users see the document in the history list with correct status.
- C10 For successful extractions, clicking a row shows rendered tables and provides working CSV downloads.
- C11 Expired outputs are not accessible but metadata and status remain visible.

Validation notes \- QA tests expired states and org access control.

Analytics and metrics \- Event portal_view_document, portal_download_csv and portal_download_csv_failed

### 6.4 Feature D - Input discovery and document registration (Extraction stage 1)

**User story**

As the system I want to identify document properties and prepare an extraction run so that downstream stages receive consistent inputs.

**Functional requirements**

- D1 Create an extraction run record.
- D2 Capture document metadata \- hash \- digital signatures if present \- XMP metadata if present \- embedded JS flag if present \- PDF version \- page count \- suspected scan quality flags
- D3 Determine processing plan \- document type from hint or heuristic \- page ranges
- D4 Emit correlation id used across all stages.

**Acceptance criteria**

- D5 A run record exists in a transactions-style table before calling any extraction provider.
- D6 Metadata fields populate when present and missing fields do not fail the run.

Validation notes \- QA verifies records and logs for stage boundaries.

Analytics and metrics \- Metric extraction_stage1_duration_ms, extraction_stage1_failure with failure_type, and extraction_stage1_document_type with fields: document_type, confidence, used_hint_bool.

### 6.5 Feature E - Table detection (Extraction stage 2)

**User story**

As the system I want to identify relevant table regions so that only relevant content is sent for extraction.

**Functional requirements**

- E1 Identify candidate table regions for \- income statement \- balance sheet \- cash flow \- bank transaction tables
- E2 Support tables spanning pages.
- E3 Support irregular or borderless tables.
- E4 Produce a table map \- page number \- bounding boxes or selectors compatible with the extraction provider \- table id
- E5 Log confidence metrics and warnings for scanned or low-quality PDFs.

**Acceptance criteria**

- E6 For a known sample the stage outputs at least one candidate region per relevant statement table.
- E7 QA can inspect table-detection outputs in logs or debug views for a sample of PDFs.
- E8 For scanned or low-quality PDFs, table-detection logs include low confidence metrics.

Validation notes \- QA validates detection outputs on the golden dataset.

Analytics and metrics \- Metric extraction_stage2_duration_ms and extraction_stage2_failure with failure_type.

### 6.6 Feature F - LLMWhisperer table extraction (Extraction stage 3)

**User story**

As the system I want to extract structured table data using LLMWhisperer so that the pilot relies on a single primary extraction service.

**Functional requirements**

- F1 Implement a pluggable table extraction provider interface.
- F2 Enable only the LLMWhisperer implementation for the pilot.
- F3 No open-source fallback extraction provider is permitted in the pilot.
- F4 For each candidate table region \- call LLMWhisperer \- store raw LLMWhisperer output as a raw artefact associated to the extraction run
- F5 The system must be parallel-ready \- allow multiple requests to be handled efficiently under pilot load \- enforce at most one active extraction per organisation via FIFO queue
- F6 Not real-time \- jobs are batch style \- portal can poll status
- F7 If processing is interrupted by client actions such as refresh, the client restarts and does not attempt to resume partial work.
- F8 Support retries for transient failures and mark as failed after configurable max attempts.
- F9 Produce per table quality scores from extraction and aggregate a quality score per document.

**Acceptance criteria**

- F8 For typical PDFs under 20 pages, 95% complete end to end under 2 minutes and achieves the global ≥99% field-level accuracy target.
- F9 The provider interface exists and the only enabled provider is LLMWhisperer.
- F10 Failures are retried according to policy and surfaced in logs and portal views.

Validation notes \- QA verifies LLMWhisperer call per table and captures raw artefacts \- QA uses golden PDFs with human-labelled outputs to compare extracted data

Analytics and metrics \- Metric extraction_stage3_duration_ms, extraction_stage3_retry_attempt, extraction_stage3_quality_score and extraction_stage3_llmwhisperer_error.

### 6.7 Feature G - Processing, normalization, and schema mapping (Extraction stage 4)

**User story**

As a downstream consumer I want extracted data normalized into canonical schemas so that I can reliably use the data in analysis and automation.

**Functional requirements**

- G1 Translate LLMWhisperer raw output to semi-structured JSON using Pydantic AI.
- G2 Validate and enforce all structured outputs using Pydantic schemas, ensuring type safety, required fields and numeric precision
- G3 Canonical schemas \- company accounts schema (e.g. income statement, balance sheet, cash flow by period) \- bank statement schema (e.g. transactions with date, description, amount, currency)
- G4 Normalize formats \- dates \- currency codes at metadata level \- numeric parsing as decimal fixed precision
- G5 Provide per-field confidence and mapping notes.
- G6 Handle unknown labels \- preserve source label \- map to canonical when confident \- flag unmapped labels for inspection

**Acceptance criteria**

- G7 All semi-structured JSON outputs validate against canonical Pydantic schemas.
- G8 Schema validation failures are logged with clear diagnostics. Document marked as failed or partially successful.
- G9 All financial amounts are stored and returned using decimal fixed precision representations.

Validation notes \- QA runs schema validation tests on golden dataset \- Logs record specific validation errors that include distinguishing Pydantic AI translation and Pydantic validation failures.

Analytics and metrics \- Metric extraction_stage4_duration_ms, extraction_stage4_failure with fields: tool, document_type

### 6.8 Feature H - Consolidation, storage, and delivery preparation (Extraction stage 5)

**User story**

As the system I want outputs persisted in a dual-path RAG architecture and made deliverable so that users can SQL-like query exact rows or semantic context search.

**Functional requirements**

- H1 Dual-path RAG ingestion \- structured rows into `document_rows` with appropriate dataset/document identifiers, organisation scoping, and metadata \- semantic chunks plus embeddings into `documents`
- H2 Both paths must remain consistent \- ingestion must be atomic or compensating \- if semantic ingestion fails, mark run failed and do not expose partial results
- H3 Prepare delivery artefacts \- JSON payload for API retrieval \- CSV generation for portal download \- HTML view model for portal rendering

**Acceptance criteria**

- H4 For a succeeded run (Extraction stage 4), `document_rows` and `documents` contain the expected records and share identifiers.
- H5 For a sampled document, QA can join rows and chunks via identifiers and confirm consistency.

Validation notes \- QA verifies both storage paths and consistency checks \- Logs flag any partial writes or failures in either path

Analytics and metrics \- Metric extraction_stage5_duration_ms, extraction_stage5_partial_write with path, and extraction_stage5_atomicity_violation.

### 6.9 Feature I - Result delivery and export

**User story**

As a client I want to retrieve results by document id so that I can feed structured data into internal systems.

**Functional requirements**

- I1 Provide authenticated GET endpoint for results.
- I2 Support \- JSON response \- CSV link generation per main table (e.g. income statement, balance sheet) for portal
- I3 Handle status \- if processing return 202 with retry guidance \- if failed return error code and high-level reason \- if expired return 410 with retention explanation

**Acceptance criteria**

- I4 A completed document can be retrieved as JSON with correct schema and basic metadata, HTTP status codes and headers.
- I5 Portal downloads generate valid CSV files matching the underlying data.
- I6 An expired document returns a clear error code and does not return structured data.
- I7 Requests for documents belonging to another organisation are rejected with clear error code.

Validation notes \- QA tests each status response.

Analytics and metrics \- Event results_retrieved and results_retrieval_failure.

### 6.10 Feature J - Logging, metadata capture, and QA support

**User story**

As the project owner I want an LLM-based agent to have access to rich document-level logs and metadata so that issues can be investigated and diagnosed.

**Functional requirements**

- J1 Structured logs for each stage \- correlation id \- organisation_id \- document_id \- document type \- source channel \- timings \- error codes
- J2 Metadata captured permanently \- hashes \- digital signatures \- XMP metadata \- OCR mismatch logs when relevant \- embedded JS presence flags
- J3 Metadata for each extraction run \- confidence levels (OCR) \- quality scores
- J4 Surface minimal quality flags in portal and full metadata in internal table

**Acceptance criteria**

- J5 LLM can query and retrieve all metadata for debugging.
- J6 Failed run logs includes stage of failure and a stable error code.
- J7 Logs contain sufficient context so that new LLM agent sessions can reconstruct engine runs and propose fixes.

Validation notes \- QA asserts logs contain required fields.

Analytics and metrics \- Metric stage_failure_rate by stage and metadata_parse_failure_count by field.

### 6.11 Feature K - Pilot administration and usage reporting

**User story**

As the project owner I want visibility into pilot usage and performance per orgnaisation so that I can evaluate success metrics.

**Functional requirements**

- K1 Maintain a transactions-style operations table recording \- organisation_id \- optional user_id \- document_id \- source channel \- stage timings \- outcome \- virtual token counts for future usage analytics
- K2 Provide ability (via Supabase console or documented SQL queries) to compute \- number of PDFs processed \- success rate \- average and p95 pipeline time \- accuracy sampling metadata \- retention deletions count

**Acceptance criteria**

- K3 Non-technical project owner can run predefined SQL queries or use Supabase console to retrieve pilot metrics.
- K4 Queries produce correct counts for a test dataset that align with logs.

Validation notes \- QA validates table writes and query outputs.

### 6.12 Feature L - Retention and deletion

**User story**

As the client I want structured outputs deleted after (configurable) 10 days while metadata persists so that we minimise data retention risk without losing audit context.

**Functional requirements**

- L1 Structured outputs retention \- delete structured outputs after 10 days \- outputs include normalized JSON, CSV, HTML view model, `document_rows`, `documents`
- L2 Metadata retention \- retain all metadata permanently including document record, hashes, signatures, and run summaries
- L3 No PDF persistence \- PDFs must not be stored to durable storage \- ephemeral scratch storage permitted only during processing and must be cleaned up
- L4 Scheduled job \- idempotent \- observable \- logs each deletion batch with counts
- L5 API behaviour post expiry \- results endpoint returns 410 \- portal shows expired state

**Acceptance criteria**

- L6 A document older than 10 days returns expired and has no structured outputs present in storage tables.
- L7 Metadata remains queryable for the same document.

Validation notes \- QA runs time-travel tests with short retention in non-prod.

Analytics and metrics \- Metric retention_deletions_count and retention_deletion_error_count.

## 7 User flows & UX notes

### 7.1 API ingestion flow

1. Client system calls endpoint (Feature A) with PDF and metadata.
2. API validates auth, file type, size, and rejects encrypted/password-protected PDFs with error.
3. API creates document record with queued status, enqueues extraction job, and returns `document_id` within performance targets.
4. System processes document asynchronously through five extraction stages and updates status transitions.
5. If processing is interrupted, job may restart rather than resume.
6. Client polls status via results endpoint; on completion, status transitions to success or failed (Feature I).

### 7.2 Portal upload and history flow

1. Analyst logs into pilot portal.
2. Analyst uploads PDF and selects required document type.
3. Portal submits file through ingestion API and shows confirmation.
4. Analyst navigates to Document History, where document appears with queued status.
5. If analyst refreshes during processing, portal restarts client-side process.
6. When extraction completes, Document History shows final status plus quality indicators.
7. Analyst clicks into document to view HTML tables and download CSV.

### 7.3 Result consumption flow (API)

1. Client system stores returned `document_id`.
2. Client calls results endpoint with `document_id`.
3. If successful status and within retention, service returns validated normalised JSON.
4. If failure status, service returns an error status with a high-level reason, detailed diagnostics in internal logs.
5. If expired status, service returns appropriate error status and does not return structured outputs.

## 8 API requirements

### 8.1 Authentication model

- Organisation-level API key for API calls.
- Minimal portal login.
- Row-level security enforced by organisation_id.
- user_id is nullable and reserved for future per-user audit.

### 8.2 Transport security

- External API and web portal access over HTTPS.
- Modern TLS enforced (TLS 1.2 or higher).
- No unauthenticated or unencrypted endpoints.

### 8.3 Rate limits

- Pilot defaults to conservative per-organisation limits.
- Return 429 with retry-after.

### 8.4 Status model

`queued` `processing` `succeeded` `failed` `expired`.

## 9 Assumptions, dependencies, and risks

### 8.1 Assumptions

- Pilot success measurement relies on a golden test set plus spot checks and QA reports.
- Pilot users accept batch-style processing and polling/status checks rather than real-time extraction.
- Refresh behaviour is intentionally restart-only, and pilot users will tolerate this with clear messaging.

### 9.2 Dependencies

- LLMWhisperer is only enabled table extraction provider for pilot; no open-source fallback used.
- Supabase supports organisation scoping, operational queries, and retention enforcement.
- Portal uses same ingestion/results APIs as API-first service.
- Scheduled deletion mechanism runs reliably and is observable.

### 9.3 Risks

- Accuracy target not met on real-world PDFs, especially scanned/low-quality inputs, or validation weakened if too few PDFs or too homogeneous.
- Provider latency/outages cause end-to-end runtime to exceed pilot NFR targets.
- Restart-on-refresh causes user confusion or duplicate submissions if messaging is unclear.
- Retention enforcement defects lead to over-retention or premature deletion.
- Gaps between “measured externally” goals (time saved, commercial signals) and what’s instrumented internally create ambiguity if reporting isn’t disciplined.

Each risk must appear in the project’s risk register with likelihood, impact, and mitigation plan, and be reviewed at least once mid-pilot.

## 10 Phased Delivery

Each phase builds on the previous one and must be usable in isolation for its intended audience.

### 10.1 Core extraction engine (API only)

**Objective**

Enable users to upload PDFs via API and retrieve validated structured JSON outputs, backed by the full five-stage extraction pipeline.

**Scope**

- Implement ingestion, detection, extraction, normalisation, and storage pipeline for company accounts and bank statements.
- Expose status and results via API only (no web portal).

**Phase 1 exit criteria**

- Pilot PDFs can be:

  - Uploaded via API,
  - Processed end-to-end through the five stages, and
  - Retrieved as validated normalised JSON within pipeline performance NFRs.

- Core NFRs for API performance, schema contracts, numerical precision, retention enforcement, and basic observability are met at expected pilot load.

### 10.2 Web portal and end-to-end UX

**Objective**

Allow users to use the system without writing code and give stakeholders a visible end-to-end experience suitable for pilot usage.

**Scope**

- Build minimal, pilot-only web portal on top of Phase 1 APIs.
- Support manual PDF upload, document history, status visibility, quality indicators, and result viewing/downloading.
- Implement access control, empty states, failure states, and retention-related messaging consistent described elsewhere.

**Phase 2 exit criteria**

- Operations and risk analysts can:

  - Log into portal,
  - Upload PDFs,
  - See document processing status and quality indicators, and
  - View and download structured outputs.

- Pilot stakeholders can walkthrough the full upload-to-result flow via portal without engineering assistance.

### 10.3 Pilot operationalisation

**Objective**

Operate the system reliably for the pilot, with sufficient monitoring, diagnostics, and reporting to assess success metrics and investigate failures.

**Scope**

- Complete and tune observability and operational features.

- Define and document runbooks for:

  - Monitoring throughput, latency, and error rates.
  - Diagnosing and triaging failed documents.
  - Verifying retention and deletion behaviour.
  - Producing pilot progress summaries aligned to success metrics.

**Phase 3 exit criteria**

- Pilot can run with:

  - Clear visibility of volumes, success/failure rates, and pipeline latency.
  - A repeatable process for investigating failures using logs and metadata.
  - Sufficient reporting to evaluate pilot success metrics and inform next-stage roadmap decisions.

## 11 Success Metrics & Analytics

### 11.1 Goal-to-measurement interpretation

Each pilot goal is validated through explicit, predefined mechanisms. Not all goals are measured via runtime analytics.

- **G1 Accuracy (≥99% field-level accuracy)**

  - Validated via a golden test set and spot checks on real pilot PDFs.
  - Evidence captured in QA reports and review logs, not user-facing analytics.

- **G2 Time reduction (≥50%)**

  - Measured externally by the client using before/after baselines.
  - Not instrumented within the application.

- **G3 Pilot adoption**

  - Validated via document counts, organisation activity, and confirmed pilot usage.

- **G4 Commercial signals**

  - Validated qualitatively via client communications.

### 11.2 Operational monitoring flows

**Pilot monitoring flow**

1. Project owner accesses Supabase console.
2. Runs prepared queries against extraction and operation tables.
3. Reviews volumes, success/failure rates, and latency distributions.
4. Compares observed metrics against success targets.
5. Records findings in pilot progress summaries.

**Failure investigation flow**

1. Identify failed documents via status fields or error logs.
2. Inspect structured logs and metadata for the relevant pipeline stage.
3. Determine whether failure is input-related, extraction-related, specific-tool-related, or systemic.
4. Decide on retry, exclusion, or remediation actions.

## 12 Future Considerations (Non-Blocking)

The following items are explicitly out of scope for pilot delivery but should be considered when evaluating architecture and roadmap decisions:

- Extended document types beyond company accounts and bank statements.
- Resumable or long-running extraction jobs across client refreshes.
- Advanced analytics, financial modelling, or downstream decisioning modules.
- Per-user role management, SSO, or enterprise access controls.
- Long-term data retention or archival strategies beyond the fixed pilot window.
