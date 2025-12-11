# Financial PDFs Converter

Product Requirements Document

**Version** 0.5  
**Date** 2025-12-11  
**Owner** Rahul Parmar  
**Source documents** Project Blueprint v1.4, Marconi DCF PRP (benchmark)

---

## 1 Overview

### 1.1 Problem statement

Operations and risk teams at fintechs and financial institutions receive company accounts and bank statement PDFs that must be converted into structured data for onboarding, periodic reviews, and credit decisions. Today this conversion is manual, slow, error-prone, and inconsistent across analysts, which limits throughput and undermines confidence in downstream risk and analytics workflows.

The Financial PDFs Converter provides an API-first extraction service and minimal web portal that ingests financial PDFs and returns normalised structured datasets, backed by a dual-path storage model that supports both exact queries and LLM-driven contextual search. The initial pilot is focused on validating accuracy, speed, and usability rather than delivering a full production platform.

### 1.2 Goals and success metrics

**Primary business goals**

1. Reduce manual effort and time required to convert financial PDFs into usable structured data.

2. Improve extraction accuracy and consistency relative to manual processes.

3. Validate commercial interest in an API-first financial document extraction service.

4. Establish an architecture foundation that can support future KYC, AML, credit, and modelling products.

**Pilot success metrics**

- **G1 – Extraction accuracy**  
  Process ≥30 real-world financial PDFs (accounts \+ bank statements) with **≥99% field-level extraction accuracy** versus a human benchmark.

- **G2 – Time reduction**  
  Achieve **≥50% reduction** in average manual processing time per PDF for pilot users, measured externally by client.

- **G3 – Pilot engagement**  
  Onboard **≥2 organisations** that each process **≥5 PDFs** through the system during the pilot.

- **G4 – Commercial signal**  
  Capture **≥2 explicit commercial signals**, such as requests for pricing, integration workshops, or roadmap discussions.

- **G5 – Architecture readiness**  
  Deliver an architecture (ingestion, extraction, API, storage, retention, integration points) that engineering judges as suitable to extend for downstream KYC, AML, credit underwriting, and DCF-style modules without full re-architecture.

### 1.3 Non-goals and scope boundaries

The following are explicitly **out of scope** for this pilot and must not be implemented beyond minimal stubs where required:

- Pricing, billing, and subscription management (e.g. Stripe integration, token balances).

- Multi-tenant self-serve sign-up, complex roles/permissions, or SSO.

- Rich downstream analytics (full AML rules engine, credit spreading, DCF/IPO models, Excel exporters).

- Long-term archival of PDFs or structured data beyond the **10-day** retention window.

- Native mobile apps or heavy marketing website.

- Deep integrations into specific third-party platforms (core banking, CRMs, case-management), beyond generic API usage.

Any requirement that materially conflicts with these non-goals must trigger a scope negotiation before implementation.

---

## 2 Target users and personas

### 2.1 Primary persona – Operations Analyst

- **Role** Works in operations, onboarding, or middle office at a fintech or financial institution.

- **Context** Receives customer financial documents (company accounts, management accounts, bank statements) during onboarding and reviews.

- **Goals**

  - Quickly convert PDFs into structured data in Excel or internal tools.

  - Reduce manual copy/paste and re-keying work.

  - Avoid mistakes that could lead to wrong credit decisions or compliance issues.

- **Pain points today**

  - Time-consuming scanning, manual extraction, and reconciliation.

  - Inconsistent interpretations of line items between analysts.

  - Fragile one-off scripts that break on new document formats.

### 2.2 Secondary persona – Risk Analyst

- **Role** Performs KYC, creditworthiness analysis, AML reviews, and risk monitoring using financial statements and transaction histories.

- **Goals**

  - Access reliable, machine-usable structured data for analysis and modelling.

  - Trust that the same fields have the same meaning across different customers.

  - Request schema tweaks as new use-cases emerge.

- **Pain points today**

  - Must validate or re-do manual extractions from operations teams.

  - Difficult to automate rules/models when inputs are inconsistent.

### 2.3 Secondary persona – Client Engineering Team

- **Role** Engineers and data engineers at client organisations responsible for integrating the API into onboarding, risk, or analytics pipelines.

- **Goals**

  - Integrate a clearly documented, stable API using standard patterns (HTTPS, JSON, API keys).

  - Avoid brittle SDKs or ad-hoc schema changes.

  - Monitor extraction status and failure causes.

---

## 3 Functional scope and user stories

For each core feature this section defines user stories, functional behaviour, data requirements, acceptance criteria, and validation notes.

### 3.1 Feature F1 – PDF Ingestion & Validation API

**Description**  
Authenticated API endpoint(s) that accept financial PDFs, validate them, register documents, and enqueue them for extraction.

**Primary persona** Client Engineering Team.

**Key user stories**

- _US1.1_ As an engineer, I can POST a PDF (or URL) and metadata to an ingestion endpoint so that the system registers it and starts extraction.

- _US1.2_ As an engineer, I receive a synchronous response with a document_id, initial status, and any validation warnings so I can track progress.

**Functional requirements**

1. Provide an authenticated **POST /api/v1/documents** endpoint (exact path finalised in TAD) that accepts:

   - Multipart PDF upload **or** a URL to a PDF.

   - Minimum metadata fields: organisation_id (derived from auth), optional document_type hint ("company_accounts", "bank_statement"), optional customer_reference.

   - Optional mode flag (sandbox / production).

2. Enforce:

   - File type is PDF (magic bytes check).

   - File size ≤ 20 MB for guaranteed SLOs; reject inputs above hard limit (e.g. 30 MB) with clear error.

3. Persist a document record with status received then queued and enqueue an extraction job respecting per-organisation concurrency limits.

4. Implement basic validation warnings (e.g. suspected scan / low DPI, page count \> threshold) recorded against the document metadata.

5. Never persist the raw PDF to durable storage beyond ephemeral processing as per retention rules.

**Request / response (conceptual)**

- **Request**

  - POST /api/v1/documents

  - Headers: Authorization: Bearer \<org-level-api-key\>

  - Body: multipart/form-data containing file and JSON metadata.

- **Success response (201)**

  - JSON containing: document_id, status (queued), warnings (array), received_at timestamp, mode.

- **Error responses**

  - 400 for invalid input (non-PDF, file too large, missing file).

  - 401/403 for auth failures.

  - 429 if per-organisation concurrency/rate limits exceeded.

  - 5xx for internal failures (with correlation ID).

**Acceptance criteria**

- Given a valid PDF and API key, when I call the endpoint, then I receive a 201 response with a unique document_id, status \= queued, and my metadata echoed back.

- Given an oversized or non-PDF file, when I call the endpoint, then I receive a 4xx response with a human-readable error message.

- All accepted documents create records in the database with correct organisation_id, metadata, and timestamps.

- Per-organisation concurrency limits are enforced (at most one active extraction per organisation) and additional jobs are queued.

- No original PDF is stored in durable storage; QA can verify by inspecting storage configuration and logs.

**Validation & observability**

- Logs show one ingestion log entry per request with correlation IDs and validation outcome.

- Metrics expose count of ingested documents by organisation and mode, plus breakdown by validation result.

- QA uses synthetic and real PDFs to test success and error branches.

---

### 3.2 Feature F2 – PDF Ingestion via Web Portal

**Description**  
A minimal web interface that allows authenticated users to upload PDFs manually and see basic processing status.

**Primary persona** Operations Analyst.

**User stories**

- _US2.1_ As an operations analyst, I can upload a PDF via a browser form so I can use the system without writing code.

- _US2.2_ As an analyst, I see immediate confirmation that a file was received and whether it is being processed.

**Functional requirements**

1. Provide a simple **Upload** page within the portal:

   - File picker limited to PDFs with client-side size validation.

   - Fields for document_type and optional customer_reference.

   - Upload action and visible progress indicator.

2. On submit:

   - Call the same ingestion API as F1 using the organisation-level credentials.

   - Show upload confirmation and a link or navigation to the Document History (F3).

3. Show clear human-readable inline error messages for unsupported formats, size issues, or network failures.

**Acceptance criteria**

- When an authenticated portal user uploads a valid PDF, the portal calls the ingestion API and shows a success message with document_id or equivalent.

- Upload failures show a non-technical error message and a suggestion to retry or contact support.

- Portal enforces the same size/type constraints as the API.

**Validation & observability**

- Portal events are logged (user ID, organisation, filename, outcome).

- QA tests uploads under normal and adverse network conditions and verifies behaviour.

---

### 3.3 Feature F3 – Web Portal: Document History & Results Viewer

**Description**  
A portal view that lists recent documents, shows extraction status and quality score, and allows users to view HTML tables and download structured data.

**Primary persona** Operations Analyst; secondary Risk Analyst.

**User stories**

- _US3.1_ As an analyst, I can see a list of my organisation’s recent documents, their statuses, and quality scores so I can monitor progress.

- _US3.2_ As an analyst, I can click into a document to see extracted tables rendered as HTML and optionally download CSV.

**Functional requirements**

1. Document list view:

   - Columns: uploaded_at, customer_reference, document_type, status, quality_score, warnings indicator.

   - Filters: status (all, queued, processing, success, failed), date range.

   - Pagination appropriate to pilot scale.

   - Empty state: show empty-state message and provide link to Upload page.

2. Detail view for a document_id:

   - Display key metadata.

   - Render extracted tables as HTML (for at least the main statements / transaction tables).

   - Provide a download button for CSV (see F8).

3. Respect data retention: documents whose structured data has expired must be clearly indicated as expired with no data rendered or downloadable.

4. Enforce organisation scoping and basic access control (no cross-org visibility).

5. Unexpected errors (e.g. network failures, inaccessible records) show a human-readable message and correlation ID.

6. Portal must meet WCAG 2.1 Level AA basics for forms, contrast, keyboard navigation, alt text, and semantic HTML.

**Acceptance criteria**

- After uploading PDFs and waiting for extraction, users see those documents appear in the history list with correct statuses.

- For successful extractions, clicking a row shows rendered tables and provides working CSV downloads.

- For documents beyond the retention window, the UI clearly indicates that data has been deleted per policy and disables downloads.

- Users can only see documents from their own organisation.

**Validation & observability**

- QA seeds test data and verifies that list filters, detail views, and retention behaviour work as expected.

- Metrics include counts of viewed documents and download events for CSV.

---

### 3.4 Feature F4 – Table Detection

**Description**  
Identify relevant table regions in PDFs (income statement, balance sheet, cash flow, bank transactions) prior to extraction.

**User stories**

- _US4.1_ As a system owner, I need the extractor to robustly identify financial tables in diverse PDFs so that downstream extraction is accurate.

**Functional requirements**

1. Implement a table-detection stage that, given a registered document and document-type hint, identifies candidate table regions (coordinates, page indices) across pages.

2. Must support:

   - Multi-page tables.

   - Irregular or borderless tables.

   - Scanned images (with optional OCR).

3. Interface outputs a machine-readable representation (e.g. JSON) of detected tables and passes it into the extraction engine (F5).

4. Capture per-table confidence scores and reasons for low confidence (e.g. noisy OCR) in metadata.

**Acceptance criteria**

- For the pilot set of PDFs, relevant financial tables are detected such that downstream extraction achieves the global ≥99% field-level accuracy target.

- QA can inspect table-detection outputs in logs or debug views for a sample of PDFs.

- For scanned or low-quality PDFs, table-detection logs include confidence metrics and warnings.

**Validation & observability**

- Logs record number of tables detected per document and per table type.

- Metrics track detection failures and low-confidence counts.

---

### 3.5 Feature F5 – Extraction Engine

**Description**  
Extract cell-level data from detected tables using LLMWhisperer Text Extraction Service as the primary table extraction mechanism.

**User stories**

- _US5.1_ As an engineer, I need a reusable extraction engine that can be tuned and extended for new document types without changing the ingestion surface.

**Functional requirements**

1. Implement an extraction module that:

   - Accepts table regions and PDF content.

   - Invokes LLMWhisperer Text Extraction Service for table extraction.

   - Produces semi-structured JSON payloads preserving row/column structure and metadata.

2. For each extraction run, record an operation in a transactions\-style table including timings and outcome.

3. Capture per-field confidence where supported and aggregate a quality score per document.

4. Support retries for transient failures and mark documents as failed after configurable max attempts.

**Acceptance criteria**

- For the pilot PDF set, the extraction engine produces structured outputs that, after normalisation (F6), meet the ≥99% accuracy target.

- All extraction runs create corresponding operation records with timestamps and statuses.

- Failures are retried according to policy and surfaced in logs and portal views.

**Validation & observability**

- QA uses golden PDFs with human-labelled outputs to compare extracted data.

- Metrics track extraction success/failure rates, latency per stage, and average quality scores.

---

### 3.6 Feature F6 – Normalisation & Schema Mapping

**Description**  
Transform extraction outputs into canonical schemas per PDF family (company accounts, bank statements) using strongly typed Pydantic models as schema contracts.

**User stories**

- _US6.1_ As a risk analyst, I want consistent field names and formats regardless of document source so I can plug outputs into models with minimal mapping.

- _US6.2_ As an engineer, I want schema contracts enforced centrally so future changes are controlled.

**Functional requirements**

1. Define canonical Pydantic schemas for:

   - Company accounts (e.g. income statement, balance sheet, cash flow sections by period).

   - Bank statements (e.g. transactions with date, description, amount, currency, balance).

2. Implement mapping logic from semi-structured extraction outputs into these schemas, including:

   - Line item label normalisation.

   - Date parsing and normalisation.

   - Currency handling at the metadata level.

3. All structured outputs must validate against the relevant Pydantic schema before storage or delivery.

4. Unknown or ambiguous fields must be captured in a structured way (e.g. other_items / unmapped_columns) for inspection.

**Acceptance criteria**

- All successful extractions for pilot PDFs produce normalised JSON that passes validation against the canonical schemas.

- Schema validation failures are logged with clear diagnostics and mark the document as failed or partially successful.

- QA can inspect example outputs and confirm that core fields (revenue, net income, key transaction attributes) are correctly mapped.

**Validation & observability**

- Metrics track schema validation failure rates by document type.

- Logs record specific validation errors for troubleshooting.

---

### 3.7 Feature F7 – Structured Storage Integration (Dual-path RAG)

**Description**  
Persist normalised data into a dual-path RAG storage model: exact rows in document_rows and semantic chunks in documents.

**User stories**

- _US7.1_ As a future product owner, I want this pilot to create a solid foundation for both SQL-like queries and semantic search without rework.

**Functional requirements**

1. For each successful normalisation run:

   - Insert canonical rows into document_rows with appropriate dataset/document identifiers, organisation scoping, and metadata.

   - Construct textual chunks (e.g. 400-character segments) representing key rows/sections; compute embeddings; insert into documents.

2. Ensure both paths are written atomically so document_rows and documents stay in sync.

3. Include metadata to identify document type, organisation, source PDF hash, and extraction version.

**Acceptance criteria**

- All successful documents produce both document_rows and documents entries.

- For a sampled document, QA can join rows and chunks via identifiers and confirm consistency.

- Retention logic (see NFRs) deletes structured rows while respecting metadata policies.

**Validation & observability**

- Metrics report counts of rows and chunks written per document and per organisation.

- Logs flag any partial writes or failures in either path.

---

### 3.8 Feature F8 – Result Delivery & Export (API \+ CSV/JSON)

**Description**  
Expose normalised structured data via API and downloads from the portal.

**User stories**

- _US8.1_ As an engineer, I can call a results API with a document_id and receive the normalised JSON.

- _US8.2_ As an analyst, I can download CSVs from the portal for further Excel-based analysis.

**Functional requirements**

1. API endpoint, e.g. **GET /api/v1/documents/{document_id}**:

   - Returns normalised JSON dataset if within the retention window and authorised for the requesting organisation.

   - Returns 404 or 410 with a clear message if data has been deleted per retention policy or never existed.

2. Portal integrations:

   - From the document detail view, allow download of a CSV per main table (e.g. income statement, transactions).

3. Ensure no personally identifiable information or sensitive metadata beyond what exists in the structured outputs is added.

**Acceptance criteria**

- For a successful document, GET requests return the correct normalised JSON with appropriate HTTP status codes and headers.

- Portal downloads generate valid CSV files matching the underlying data.

- Requests for documents belonging to another organisation are rejected with 403\.

- Requests for expired data return a clear error without leaking metadata beyond what is allowed.

**Validation & observability**

- QA uses the pilot PDFs to verify round-tripping: upload → extract → normalise → GET → CSV/JSON compare.

- Metrics track API result calls and download counts.

---

### 3.9 Feature F9 – Logging, Metadata Capture & QA Support

**Description**  
Capture rich metadata for each PDF and extraction run to support debugging, QA, and future analysis.

**User stories**

- _US9.1_ As an LLM-based agetn, I need to inspect document-level metadata (hashes, OCR quality, table counts) when investigating issues.

**Functional requirements**

1. For each uploaded PDF, capture and persist:

   - File hash, page count, basic structural metadata.

   - Detection of encryption, embedded JavaScript, or suspicious content where feasible.

2. For each extraction run, capture:

   - Pipeline stage timings (ingestion, detection, extraction, normalisation, storage).

   - OCR confidence levels when OCR is used.

   - Quality scores and warnings.

3. Make a subset of metadata visible in the portal (e.g. quality score, basic warnings) and store full metadata in an internal table/API.

**Acceptance criteria**

- For any pilot document, the LLM agent can query and retrieve all relevant metadata for debugging.

- Portal surfaces a quality score badge and key warnings for each document.

- Logs include correlation IDs enabling traceability from ingestion to storage.

- Logs are structured with stage labels, error codes and sufficient context so that a new LLM session can reconstruct pipeline runs and propose fixes.

**Validation & observability**

- QA spot-checks metadata for a sample of documents and traces them through logs.

---

### 3.10 Feature F10 – Pilot Administration & Usage Reporting

**Description**  
Lightweight reporting for the project owner to monitor pilot activity and success metrics.

**User stories**

- _US10.1_ As the project owner, I want to see how many documents each pilot organisation has processed and basic success/failure counts.

**Functional requirements**

1. Backed by a transactions\-style table and/or summary views, provide the ability (via Supabase console, SQL scripts, or minimal admin view) to:

   - Count documents by organisation, status, and time period.

   - Summarise extraction success rates and average latencies.

2. No separate admin UI is required beyond what is needed for efficient pilot operations.

**Acceptance criteria**

- The project owner can run predefined SQL queries or use a simple admin screen to retrieve the pilot metrics.

- Metrics align with the counts observed in logs and portal usage.

**Validation & observability**

- QA verifies that metrics correctly aggregate underlying records for a test environment.

---

## 4 User flows & UX notes

### 4.1 API ingestion flow

1. Client system calls POST /api/v1/documents with PDF and metadata.

2. API validates auth, file type, and size.

3. API creates document record (received → queued), enqueues extraction, returns document_id.

4. Client polls status via a status endpoint or reuses the results endpoint; polling strategy to be defined in TAD.

5. On completion, status transitions to success or failed; results become available per F8.

### 4.2 Portal upload and history flow

1. Analyst logs into portal using organisation-scoped credentials.

2. Analyst uploads PDF via Upload page.

3. Portal calls ingestion API and shows confirmation.

4. Analyst navigates to Document History and sees the new document with queued status.

5. When extraction completes, status updates to success and quality score appears.

6. Analyst clicks into the document to view HTML tables and download CSV.

### 4.3 Result consumption flow (API)

1. Client system stores the document_id received during ingestion.

2. Once sufficient time has elapsed, client calls GET /api/v1/documents/{document_id}.

3. If extraction succeeded and data is within retention window, service returns normalised JSON.

4. If extraction failed, service returns an error status and high-level reason; detailed diagnostics in internal logs.

5. If data expired, service returns appropriate error status indicating retention expiry.

### 4.4 Pilot monitoring flow

1. Project owner connects to Supabase or admin view.

2. Runs prepared queries or views summarising document counts, success rates, and latency statistics.

3. Uses these to assess progress towards success metrics and decide on next steps.

UX should favour clarity and reliability over visual polish; minimal but coherent layout and styling is sufficient.

---

## 5 Assumptions, dependencies, and risks

### 5.1 Key assumptions

- Pilot organisations will provide at least 30 real, varied financial PDFs early in the project.

- Client engineering teams can integrate with standard HTTPS/JSON API patterns and manage API keys.

- UK/EU hosting with basic security best practices is sufficient for the pilot.

- Future KYC, AML, credit, and modelling features will build on the canonical schemas and dual-path RAG model defined here.

### 5.2 Dependencies and risks (summary)

Major dependencies and their risks are summarised:

- **Real pilot PDFs** – If too few or too homogeneous, accuracy validation is weakened.

- **Open-source libraries and LLMWhisperer** – Poor performance or API changes could reduce accuracy; mitigated by pluggable design and monitoring.

- **OCR engine** – Poor scan quality may degrade results; mitigated by quality flags and expectations.

- **Supabase/PostgreSQL and hosting platform** – Free-tier quotas and outages could affect reliability.

- **Single-builder constraint** – Increases schedule risk; mitigated by scope discipline and documentation.

- **Retention jobs and in-memory queue** – Misconfiguration can delete data prematurely or lose queued jobs; mitigated by idempotent jobs and restart reconciliation.

Each risk must appear in the project’s risk register with likelihood, impact, and mitigation plan, and be reviewed at least once mid-pilot.

---

## 6 Non-functional requirements (NFRs)

NFRs are adopted as PRD-level requirements. Engineering must demonstrate how each is satisfied in the TAD and test plan.

**NFR categories**

1. **Performance – API**

   - P95 response time \< 500 ms for ingestion requests up to 20 MB; ingestion must enqueue extraction and return immediately.

2. **Performance – Pipeline**

   - For PDFs ≤ 20 pages, 95% of extractions complete within 5 minutes under expected pilot load (≤ 200 PDFs/day).

3. **Concurrency**

   - At most one active extraction per organisation_id; additional jobs queued FIFO.

4. **Accuracy & Quality**

   - ≥99% field-level extraction accuracy on 30 real pilot PDFs, measured versus human-labelled benchmark.

5. **Data retention & storage**

   - Structured outputs retained for max 10 days. PDFs never persisted to durable storage. Metadata may be stored permanently.

6. **Security – transport & access**

   - All external access via HTTPS/TLS 1.2+; no unauthenticated endpoints.

   - Row-level security (RLS) and soft deletes enforced; no cross-org access.

7. **Secrets management**

   - All secrets stored in env vars or managed secrets store; none in source control.

8. **Structured storage / RAG**

   - Use document_rows and documents tables with schemas that can support future AML/credit/DCF modules.

9. **Numerical precision**

   - All financial amounts stored using decimal/fixed-precision types (no binary floats) to avoid rounding errors.

10. **Reliability & availability**

    - Target 99.0% uptime during UK business hours; planned maintenance outside those hours.

11. **Observability**

    - Structured logs for each pipeline stage; metrics for PDFs processed, timings, success/failure, retention deletions.

12. **Maintainability & extensibility**

    - Modular boundaries that a single engineer can understand and extend within 1–2 days.

    - Adding new document types should primarily affect extraction and schema mapping, not core ingestion/auth.

13. **Schema contracts**

    - All inputs and outputs must validate against canonical Pydantic schemas per PDF family; these schemas act as the canonical contracts for ingestion, normalisation, storage, and API responses.

14. **Deployment & recovery**

    - Automated deployment with rollback capability within 30 minutes; database backups with ≥7-day point-in-time recovery.

15. **Testing**

    - Permanent curated regression fixtures (sample PDFs \+ expected JSON) maintained outside production retention policies.

Each feature’s acceptance criteria and QA plan must be aligned with these NFRs where relevant.

---

## 7 Analytics and success measurement

### 7.1 Core product analytics

The system must provide enough logging and metrics to evaluate pilot success without introducing a full analytics platform.

**Events / metrics (minimum)**

- documents.ingested – Count of documents ingested by organisation, mode, and document type.

- documents.extracted – Count of successful extractions; distribution of quality scores.

- documents.failed – Count of failed extractions by error category.

- documents.viewed – Portal views of document detail pages.

- documents.downloaded – CSV download counts by type.

- pipeline.latency – Stage-wise timings (ingestion→queue, queue→start, start→finish).

These may be implemented as database-driven metrics and/or exported to a simple time-series tool if already in use.

### 7.2 Mapping to pilot goals

- **G1 (accuracy)** – Validated via golden test set and spot checks on real pilot PDFs; recorded in QA reports rather than runtime analytics.

- **G2 (time reduction)** – Measured externally by client through before/after studies; the system must provide enough usage data (e.g. document counts and timestamps) to support analysis.

- **G3 (pilot engagement)** – Derived from documents.ingested and organisation metadata.

- **G4 (commercial signal)** – Tracked manually through CRM or project notes.

- **G5 (architecture readiness)** – Assessed qualitatively by engineering and product at pilot end, based on how well dual-path RAG, schemas, and NFRs held up.

---

## 8 Phased delivery

The pilot will be delivered in three phases. Each phase builds on the previous one and must be usable in isolation for its intended audience.

### 8.1 Core extraction engine (API only)

**Objective**

Enable users to upload PDFs via API and retrieve validated structured JSON outputs, backed by the full five-stage extraction pipeline.

**Scope**

- Implement ingestion, detection, extraction, normalisation, and storage pipeline for company accounts and bank statements.
- Expose status and results via API only (no web portal).

**Phase 1 exit criteria**

- Pilot PDFs can be:
  - Uploaded via API,
  - Processed end-to-end through the five stages, and
  - Retrieved as validated normalised JSON within the pipeline performance NFRs.
- Core NFRs for API performance, schema contracts, numerical precision, and basic observability are met at expected pilot load.

### 8.2 Web portal and end-to-end UX

**Objective**

Allow users to use the system without writing code and give stakeholders a visible end-to-end experience suitable for pilot usage.

**Scope**

- Build minimal but coherent web portal on top of Phase 1 APIs.
- Implement basic empty states, error handling, and access control as described in Section 3\.

**Phase 2 exit criteria**

- Operations and risk analysts can:
  - Log into the portal,
  - Upload PDFs
  - See document status and quality scores, and
  - View and download structured outputs.
- Pilot stakeholders can walkthrough the full upload-to-result flow via the portal.

### 8.3 Pilot operationalisation

**Objective**

Operate the system reliably for the pilot, with sufficient monitoring, diagnostics, and reporting to assess success metrics and investigate failures.

**Scope**

- Complete and tune observability and operational features.
- Define and document runbooks for:
  - Monitoring throughput, latency, and error rates.
  - Diagnosing and triaging failed documents.
  - Producing pilot progress summaries aligned to Section 7.2.

**Phase 3 exit criteria**

- Pilot can run with:
  - Clear visibility of volumes, success/failure rates, and pipeline latency.
  - A repeatable process for investigating failures using logs and metadata.
  - Enough reporting to evaluate pilot success metrics and inform next-stage roadmap decisions.

---

## 9 Open questions and future considerations

The following items are **not required** for pilot delivery but should be considered when evaluating architecture and roadmap:

- What additional document families (e.g. tax returns, invoices) are highest priority after accounts and bank statements?

- Which downstream modules (AML rules, credit spreading, DCF-like modelling) are likely to be built first on top of this core engine?

- Do future versions require configurable retention windows per organisation or geography?

Any decisions on these points should be captured in future versions of this PRD or in separate PRDs for follow-on phases.

---

**End of PRD v0.5**
