# Project Blueprint: Financial PDFs Converter

**Prepared By:** Rahul Parmar  
**Date:** 2025-12-05  
**Version:** 1.4

## Introduction 🧭

_This blueprint is the initial definition for the standalone software project "**Financial PDFs Converter**" to be delivered by our full-service agency for the client. Its purpose is to establish a clear, shared understanding of the project's context, objectives, constraints, and scope. This document serves as the foundation for our Product Management team to create a detailed **PRD**, which will then guide our Engineering team to create a detailed **Technical Architecture Document** for building the specified production-ready software for client handover._

---

## 1. Project Context & Objective 🎯

- **1.1. Project Name:**
  - 🏷️ Financial PDFs Converter
- **1.2. Stated Purpose for this Software:**
  - ❓ Q: What problem/need does the client want this software to address? What core function should it perform for them?
  - ✅ A:
    - Reduce the time, manual toil, and error rate involved in extracting financial data from customer PDFs (company accounts and bank statements) by providing an API-first service that ingests PDFs and outputs clean, structured datasets.
    - Provide a reusable, production-ready core extraction engine that downstream business workflows (operational, risk, credit, analytics, etc.) can call programmatically, instead of relying on people and spreadsheets.
    - Validate, within a tightly scoped pilot, that this extraction service delivers measurable time savings and data quality improvements and generates enough commercial interest to justify a broader product build.
- **1.3. Primary Delivery Objective:**
  - 🚀 Design, build, test and deliver a high-quality, production-ready software application meeting the agreed scope (detailed in Section 3), suitable for successful handover to the client.
  - ❓ Q: What measurable business or operational outcomes define success from the client’s perspective
  - ✅ A:
    - Success Metric 1: Process at least 30 real-world financial PDFs (company accounts + bank statements) with ≥99% field extraction accuracy compared to a human benchmark.
    - Success Metric 2: Reduce average manual processing time per PDF by at least 50% for pilot users, measured via before/after baseline.
    - Success Metric 3: Onboard at least 2 organisations who each process ≥5 PDFs through the system during the pilot.
    - Success Metric 4: Obtain at least 2 concrete commercial signals (e.g. "How do we integrate this into production?" / request for pricing or technical integration discussion).
    - Success Metric 5: Produce an architecture foundation (ingestion, extraction, API design, storage and retention model, integration points) robust enough to support future downstream modules (e.g. AML, financial modelling, credit spreading) without a full re-architecture.
- **1.4. Target Users (As Defined by Client):**
  - ❓ Q: Who are the client's primary users and secondary users? What are their goals and typical use scenarios?
  - ✅ A:
    - Primary User:
      - Operations / onboarding analysts at fintechs and financial services firms who receive customer PDFs (company accounts + bank statements) as part of customer onboarding, periodic reviews, customer funding rounds or credit renewals.
      - Typical use: Upload or send PDFs via API, receive a structured dataset (JSON/CSV) they can feed into internal tools or spreadsheets with minimal manual correction.
      - Goal: Increase throughput and reduce error rate when handling financial documents, so they can approve, decline and service customers faster and with more confidence.
    - Secondary User(s):
      - Risk, credit, and compliance analysts who rely on financial statement line items and transaction data for AML reviews, creditworthiness assessments, and financial projections.
        - Typical use: Consume structured data produced by this service to power downstream rules, models, and analysis; may review extraction quality and request schema tweaks.
        - Goal: Rely on consistent, machine-usable data instead of ad hoc manual extractions.
      - Internal engineering / data teams at client organisations.
        - Typical use: Integrate the API into existing onboarding, risk, or analytics pipelines  (for customer segmentation, risk checks, automated 3rd party verification, etc.) and maintain the integration.
        - Goal: Have a well-defined, stable API and data schema that is easy to integrate with existing systems.
- **1.5. Current User Workflow:**
  - ❓ Q: How do users address their problems today and what are their key pain points?
  - ✅ A:
    - Users currently rely on manual processes and spreadsheets. Customer financial information arrives as long, often messy PDF documents (annual reports, management accounts, multi-page bank statements).
    - Operations or risk team members open each PDF, visually scan for relevant tables or line items, and then re-key or copy/paste data into Excel or internal systems.
    - Key pain points:
      - Time-consuming: high-friction work that scales linearly with volume of PDFs. _(This is the primary pain point.)_
      - Error-prone: every manual copy/paste or re-keying step introduces the risk of mistakes.
      - Inconsistent: different analysts may interpret or structure data differently, leading to downstream reconciliation work.
      - Hard to automate: current ad hoc scripts or one-off tools are brittle, limited to specific formats, and not reusable as a core service.

---

## 2. Client Requirements & Constraints 📋

- **2.1. Specific Client Priorities:**
  - ❓ Q: Has the _client_ emphasized specific priorities impacting the build?
  - ✅ A:
    - Prioritise technical and commercial validation over polish: ship a lean but robust MVP that proves accuracy, speed, and user value rather than building a fully featured platform.
    - Ruthless scope control: focus only on ingesting financial PDFs and returning structured datasets via API and a simple web interface; defer alternative output data formats, downstream analytics modules and complex user account management.
    - API-first design: ensure the core extraction engine is exposed via stable, well-documented API endpoints that mirror real-world usage and are optimised for readability by LLMs.
    - Reuse learnings from an existing similar solution (Marconi’s system: @project_docs/financial-dcf-system.md) where beneficial, while acknowledging that direct code access is not available.
    - Respect strict data-handling constraints: fixed period (e.g. 10-day) retention for extracted data, no long-term storage of original PDFs.
    - Design architecture for future modular product/feature add-ons post-pilot e.g. output formatted Excel spreadsheet, calculate credit analysis ratios, build financial projection models, etc.
- **2.2. Technical or Functional Constraints:**
  - ❓ Q: _Client-mandated_ technologies, platforms, performance expectations, compliance needs, etc., that directly impact the build.
  - ✅ A:
    - Budget constraints require use of free or low-cost infrastructure and primarily open-source libraries; no reliance on expensive proprietary APIs for core extraction.
    - Core tech stack expected to align with client’s existing skills and comfort: Python backend (e.g. FastAPI), open-source PDF extraction tools, and a simple database layer (e.g. Supabase / PostgreSQL), with a simple cloud deployment strategy appropriate for an MVP-style pilot.
    - Learn from the notes of conversations with Marconi (to be shared) when making technical architecture decisions on the systems workflow and tech stack for this project.
    - The system must implement a dual-path RAG storage design for the structured data that supports hybrid retrieval (exact row queries + LLM contextual search):
      - Structured path → normalised rows stored in `document_rows`.
      - Semantic path → text chunks + embeddings stored in `documents`.
    - The system must be API-callable and support both sandbox and production-style endpoints, even in pilot form.
    - The system must not store PDFs; instead it should store structured outputs and rich metadata (e.g. hashes, digital signatures, XMP metadata, OCR mismatch logs). Structured output data is subject to a defined retention policy (e.g. 10 days). Metadata can be stored permanently.
    - A vertical-slice architectural pattern must be used across the application.
    - EU/GDPR-grade compliance and enterprise security certifications are explicitly out of scope for this pilot, but standard good practices (HTTPS, basic access control, least-privilege data access) are still required.
    - Single-builder constraint: the entire system must be buildable and maintainable by one engineer.
- **2.3. Client Assumptions:**
  - ❓ Q: List each assumption that may affect delivery, why it matters and its impact if false
  - ✅ A:
    - Assumption: Pilot users can supply a sufficiently diverse but manageable set of real financial PDFs (accounts and bank statements) early in the project.
      - Why it matters: Without real-world documents, accuracy and robustness cannot be validated.
      - Impact if false: Risk of overfitting to synthetic or narrow examples; pilot results may not generalise, requiring additional rework later.
    - Assumption: The existing similar solution’s high-level architecture and implementation details can be understood via documentation and conversation, even without direct code access.
      - Why it matters: Reusing proven patterns de-risks design decisions and accelerates build.
      - Impact if false: More experimentation and design time required; risk of reinventing suboptimal patterns.

---

## 3. Core Functional Requirements (In-Scope) 🧩

- **3.1. High-Level Features:**

  - ❓ Q: List each major feature/functionality constituting the _complete_ production-ready deliverable. Note the core purpose briefly if helpful. Features deferred to later, separate releases should be listed in Section 4.
  - ✅ A:

    1.  **PDF Ingestion & Validation API**

        - Description & purpose: Accept financial PDFs (company accounts + bank statements) via authenticated API endpoints, perform basic validation, register and enqueue them for extraction.
        - Inputs: Authenticated request with PDF file (multipart upload or file URL), metadata (e.g. document type hint, customer ID), and optional flags (e.g. sandbox vs production).
        - Outputs: Synchronous acknowledgement containing document ID, initial status, and any validation warnings (e.g. file too large, suspected scan quality issues).
        - Edge cases: Non-PDF files, encrypted/password-protected PDFs, files exceeding size limits, network timeouts, duplicate uploads.

    2.  **PDF Ingestion via Web Portal**

        - Description & purpose: Provide a simple browser-based interface to manually upload PDFs and observe extracted results.
        - Inputs: User uploads a PDF through the portal and tags it (e.g. "bank statement", "company accounts").
        - Outputs: Confirmation of upload, and visible processing status.
        - Edge cases: Browser upload failures, users closing the page during processing, unsupported file types, missing tags.

    3.  **Web Portal: Document History & Results Viewer**

        - Description & purpose: Provide a simple browser-based interface to view all successful uploads, select an upload and view the resulting HTML table and/or download the structured data as a CSV file.
        - Inputs: User navigates to document history list and selects a list entry.
        - Outputs: A scrolling list of past uploads with their extraction quality score displayed, ability to select an upload and view each result's HTML data, link to download structured data.
        - Edge cases: Missing records due to retention policy, malformed stored data, access control violations.

    4.  **Table Detection**

        - Description & purpose: Identify and isolate relevant table regions within financial PDFs (e.g. income statement, balance sheet, cash flow, bank transaction tables) before extraction.
        - Inputs: Registered document ID, document type hints; internal configuration for table-detection heuristics.
        - Outputs: Coordinates, structure maps and candidate table regions passed into the extraction engine.
        - Edge cases: tables spanning pages, irregular table borders, partially corrupted pages, scanned images requiring OCR.

    5.  **Extraction Engine**

        - Description & purpose: Extract cell-level data from detected tables and transform them into structured JSON.
        - Inputs: Detected table regions from the table detection module.
        - Outputs: Semi-structured extraction payloads (JSON) with rows, columns reflecting page layout and metadata; per-field confidence scores.
        - Edge cases: Inconsistent headers, merged cells, OCR uncertainty, partially unreadable tables.

    6.  **Normalization & Schema Mapping**

        - Description & purpose: Transform extracted data into consistent schemas suitable for downstream use (e.g. standardised field names, date formats, currency normalisation at the metadata level).
        - Inputs: Extraction payloads from the extraction engine, including document metadata.
        - Outputs: Normalised JSON datasets for financial statements and bank transactions, including mapping tables and data dictionaries.
        - Edge cases: Unknown or custom line item labels, mixed currencies within a document, missing or misaligned column headers, ambiguous dates.

    7.  **Structured Storage Integration**

        - Description & purpose: Persist normalised data into the dual-path RAG architecture: (i) insert canonical rows into `document_rows`; (ii) construct semantic text chunks from normalized rows, generate embedding objects, and store objects in `documents`.
        - Inputs: Canonical normalized rows from the normalization module.
        - Outputs: Durable, queryable structured rows and embedding vectors that enable both exact SQL-like retrieval and semantic LLM retrieval.
        - Edge cases: Embedding failures, chunking inconsistencies, schema drift, retention-window deletion logic.

    8.  **Result Delivery & Export (API + CSV/JSON)**

        - Description & purpose: Deliver extracted, normalised data back to clients either through the API or via downloads in the web portal.
        - Inputs: Request for results by document ID and desired format (API JSON response, CSV file, or both).
        - Outputs: Machine-readable structured data (JSON responses, CSV files) and where appropriate a human-readable HTML summary view.
        - Edge cases: Requests for documents still processing or failed, requests for expired data beyond retention window, unauthorised access to other organisations’ documents.

    9.  **Logging, Metadata Capture & QA Support**

        - Description & purpose: Capture rich metadata about each PDF and extraction run (e.g. hashes, digital signatures, XMP metadata, OCR mismatch logs, embedded Javascript) to support debugging, QA, auditability, and future use-cases.
        - Inputs: Document file and parsing pipeline outputs.
        - Outputs: Metadata records stored in a database, accessible via internal tools or API, and surfaced in minimal form in the portal for pilot users (e.g. quality flags).
        - Edge cases: Missing metadata, malformed PDFs, failures in specific parsing steps, storage saturation on free tiers.

    10. **Pilot Administration & Usage Reporting (Lightweight)**

    - Description & purpose: Provide the project owner with visibility into pilot usage to evaluate success metrics performance and commercial potential.
    - Inputs: System logs, processing records, and database table data.
    - Outputs: On-demand SQL queries or CSV downloads sumamrising key metrics, backed by a dedicated `transactions`-style table that records extraction operations and virtual token usage.
    - Edge cases: Partial data due to log rotation or retention, or inconsistent clocks between systems.

- **3.2. User Scenarios:**

  - ❓ Q: Briefly, what key actions must users be able to perform within the scope above? What should the system do in response to successful actions and to error conditions?
  - ✅ A:

    1.  **API-based ingestion by client engineering team**

        - When: A client engineering team sends a POST request to the ingestion API with a valid PDF and auth token.
        - Then: The system validates the file, registers a document record, returns a document ID and status, and enqueues it for extraction.
        - If Error (user input): The system returns a descriptive 4xx error (e.g. unsupported file type, file too large, missing auth) with guidance on how to fix.
        - If Error (system failure): The system logs the failure, returns a 5xx error with a generic message, and marks the document as failed with diagnostic details in internal logs suitable for guiding an LLM to thoroughly investigate and resolve the failure.

    2.  **Manual upload and review by customer**

        - When: A user logs in to the web portal and uploads a valid PDF.
        - Then: The system shows upload confirmation and a processing status indicator; once complete, the analyst can view the successful upload by redirecting themselves to a results page where they can see a list of all successful uploads and retrieve an HTML table of the structured data and download CSV.
        - If Error (user input): The portal clearly indicates issues such as unsupported format or corrupt PDF and prompts the user to try a different file.
        - If Error (system failure): The portal displays a non-technical error message, logs the incident with diagnostic details suitable for guiding an LLM to thoroughly investigate and resolve the failure, and instructs the user to retry or contact support.

    3.  **Consumption of structured data by user**

        - When: A user calls the results API with a valid document ID.
        - Then: The system returns the appropriate normalised structured dataset in JSON format.
        - If Error (user input): For invalid or expired IDs, the system returns a clear 4xx error indicating that the document does not exist or data has been deleted due to retention policy.
        - If Error (system failure): The system logs the failure, returns a 5xx error with a generic message, ensures no partial or corrupted data is returned, and adds diagnostic details in internal logs suitable for guiding an LLM to thoroughly investigate and resolve the failure.

    4.  **Pilot monitoring by project owner**

        - When: The project owner runs saved or ad-hoc Supabase SQL queries (or exports CSVs) against pilot tables.
        - Then: They obtain clear summaries of the performance of defined success metrics and user-level usage where available.
        - If Error (data issues): The system surfaces that some metrics are partial and clearly indicates data ranges, avoiding misleading reports.

---

## 4. Out-of-Scope Items 🚫

- **4.1. Excluded Features/Functionality:**
  - ❓ Q: List specific features, functions, platforms, or integrations explicitly _not_ included in _this_ delivery. This may include items planned for subsequent, separately agreed releases.
  - ✅ A:
    - Full pricing, billing, and subscription management (e.g. Stripe integration, token-based billing, enterprise invoicing).
    - Multi-tenant user management with granular roles, permissions, and self-service account signup beyond the minimal access control needed for the pilot.
    - Alternative file formats for the structured output data e.g. XLSX files.
    - Advanced downstream analytics modules such as:
      - Full AML rules engine.
      - Full credit spreading product or automated financial ratio analysis.
      - Full financial projections / DCF or IPO modelling modules.
    - EU-grade data protection compliance artefacts (e.g. formal DPAs, detailed DPIAs) beyond basic good practice for a UK-focused pilot.
    - Long-term archival storage of PDFs or extracted data beyond the agreed short retention window.
    - Highly polished marketing site, complex branding work, or public self-serve onboarding flows.
    - Native mobile applications (iOS/Android) or desktop clients.
    - Complex integrations into specific third-party platforms (e.g. direct integrations into core banking systems, CRM platforms, or case management tools) beyond generic API usage.
    - Any functionality not explicitly covered in Section 3.1 or required to support the core pilot outcomes.
- **4.2. Rationale for Exclusion (If known/relevant):**
  - ❓ Q: Briefly state why these are out of scope _for this_ delivery, if useful for clarity.
  - ✅ A:
    - The primary goal of this phase is to validate the core extraction engine and API-first delivery model, not to build a full end-to-end production platform.
    - The project operates under tight time (12-week) and budget constraints with a single builder; adding billing, multi-tenant management, or advanced analytics would dilute focus and delay validation.
    - Integrations into specific third-party systems vary by client and are best treated as follow-on projects after the generic service has been validated in real-world pilots.

---

## 5. Internal Agency Questions 🤔

_Task: Review this blueprint thoroughly and complete this section._

- **5.1. Non-Functional Requirements (NFRs):** 🔒

  - These NFRs are intentionally scoped for a pilot but should be robust enough to form the foundation of a future production platform.

    | #   | NFR Category               | Quantitative Target / Requirement                                                                                                                                                                                    | Owner | Status |
    | --- | -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----- | ------ |
    | 1   | Performance – API          | Ingestion API: P95 response time < **500 ms** for requests up to **20 MB**; API must immediately enqueue extraction and return document ID.                                                                          | ENG   | Open   |
    | 2   | Performance – Pipeline     | For PDFs ≤ **20 pages**, 95% of extractions complete within **5 minutes** end-to-end under expected pilot load (≤ 200 PDFs/day).                                                                                     | ENG   | Open   |
    | 3   | Performance – Concurrency  | Enforce at most one active extraction per `organisation_id` via an in-memory queue; additional jobs are queued and processed FIFO.                                                                                   | ENG   | Open   |
    | 4   | Accuracy & Quality         | Achieve **≥99% field-level extraction accuracy** on the 30 real-world pilot PDFs compared to a human benchmark.                                                                                                      | ENG   | Open   |
    | 5   | Data Retention & Storage   | Structured outputs retained for **max 10 days**. PDFs must never be persisted to durable storage. Metadata may be stored permanently.                                                                                | ENG   | Open   |
    | 6   | Security – Transport       | All external access over **HTTPS** with modern TLS (1.2+). No unauthenticated endpoints.                                                                                                                             | ENG   | Open   |
    | 7   | Security – Data Access     | **Row-Level Security (RLS)** and soft deletes (`deleted_at`). No cross-org access to records.                                                                                                                        | ENG   | Open   |
    | 8   | Security – Secrets         | All secrets stored in environment variables or a managed secrets store; none committed to source control.                                                                                                            | ENG   | Open   |
    | 9   | Multi-User Isolation       | All data, logs, and processing paths must be strictly scoped by `organisation_id`, with key tables and operation logs also including a nullable `user_id` field to support future per-user access control and audit. | ENG   | Open   |
    | 10  | Structured Storage / RAG   | Normalised rows stored in `document_rows`; embeddings & chunks stored in `documents`. Schema must support future AML/credit/DCF modules.                                                                             | ENG   | Open   |
    | 11  | Numerical Precision        | All financial amounts use **decimal/fixed-precision types** (no binary floats).                                                                                                                                      | ENG   | Open   |
    | 12  | Reliability & Availability | Target **99.0% uptime** during UK business hours (08:00–18:00). Planned maintenance outside these hours.                                                                                                             | ENG   | Open   |
    | 13  | Observability – Logging    | Structured logs for each pipeline stage, including correlation IDs, timing, and error codes.                                                                                                                         | ENG   | Open   |
    | 14  | Observability – Metrics    | Metrics for: PDFs processed, stage timings, success/failure rates, retention deletions.                                                                                                                              | ENG   | Open   |
    | 15  | Maintainability            | Clear modular boundaries; a single engineer must understand/extend each module within **1–2 days** using documentation.                                                                                              | ENG   | Open   |
    | 16  | Extensibility              | Adding new doc types must not require changes to core ingestion/auth layers—only extraction + schema mapping layers.                                                                                                 | ENG   | Open   |
    | 17  | Schema Contracts           | All inputs and outputs must validate against typed Pydantic models defined per PDF document family layers.                                                                                                           | ENG   | Open   |
    | 18  | Deployment & Recovery      | Automated deployment with rollback capability within **30 minutes**; DB backups with ≥ **7-day** point-in-time recovery.                                                                                             | ENG   | Open   |
    | 19  | Testing                    | Maintain a permanent, curated set of regression-test fixtures (samples PDFs + JSON outputs) stored outside production tables and retention policies.                                                                 | ENG   | Open   |

- **5.2. Dependency-Risk Register** ⚠️

  | #   | Dependency / Pattern                                | Risk Description                                                                      | Likelihood (L/M/H) | Impact (L/M/H) | Mitigation / Fallback                                                                                                | Owner | Status |
  | --- | --------------------------------------------------- | ------------------------------------------------------------------------------------- | ------------------ | -------------- | -------------------------------------------------------------------------------------------------------------------- | ----- | ------ |
  | 1   | Real pilot PDFs from client organisations           | Pilot may provide too few or too-homogeneous PDFs, weakening accuracy validation.     | M                  | H              | Secure diverse samples early; supplement with anonymised public PDFs if allowed.                                     | PM    | Open   |
  | 2   | Open-source PDF/table extraction libraries          | Libraries may perform poorly on messy or scanned PDFs.                                | M                  | H              | Prototype early; choose pluggable extraction layers; keep budget/time to swap libraries if needed.                   | ENG   | Open   |
  | 3   | OCR engine for scanned statements                   | Poor scans or unusual fonts may reduce accuracy or break OCR.                         | M                  | H              | Set client expectations; add quality flags; log OCR confidence; allow manual re-run triggers.                        | ENG   | Open   |
  | 4   | Supabase/PostgreSQL                                 | Free-tier limits or outages may affect ingestion, storage, or retention jobs.         | M                  | M              | Monitor quotas; keep schema portable; plan clean upgrade path to paid tier; add health checks.                       | ENG   | Open   |
  | 5   | Embeddings provider                                 | Rate limits, cost changes, or API version changes could break embedding pipeline.     | M                  | M              | Abstract provider; store embeddings with model/version metadata; allow hot-swapping providers.                       | ENG   | Open   |
  | 6   | Hosting platform / cloud infrastructure             | Low-cost PaaS may throttle CPU/RAM, causing slowdowns or timeouts.                    | M                  | M              | Right-size instances; set conservative timeouts; queue work; document scaling path.                                  | ENG   | Open   |
  | 7   | Single-builder constraint                           | One engineer doing everything increases schedule and bus-factor risk.                 | M                  | H              | High documentation discipline; tight milestones; ruthless scope control; schedule buffer.                            | PM    | Open   |
  | 8   | No PDF storage (design constraint)                  | Debugging/training difficult without retaining PDFs.                                  | M                  | M              | Capture rich metadata + selective debug artefacts; permit ephemeral scratch storage (non-durable) only.              | ENG   | Open   |
  | 9   | Token-style extraction logging (no billing)         | Early logging schema may not align with future billing/usage analytics.               | M                  | M              | Keep schema generic (operation type, docID, timestamps); avoid embedding pricing semantics; document extension path. | PM    | Open   |
  | 10  | Dual-path RAG schema (`document_rows`, `documents`) | Schema may limit future AML/credit/DCF modules if too rigid.                          | M                  | H              | Use flexible metadata fields; map against likely future use cases; follow Marconi’s patterns precisely.              | ENG   | Open   |
  | 11  | Client-side integration capacity                    | Client engineering teams may struggle to integrate APIs during pilot.                 | M                  | M              | Provide clear API docs, Postman collection; allow portal-based fallback for manual usage.                            | PM    | Open   |
  | 12  | Retention & deletion jobs                           | Misconfigured jobs might delete structured data too early or fail to delete on time.  | M                  | H              | Implement idempotent scheduled jobs; add alerts; test in staging with sample data; observe logs.                     | ENG   | Open   |
  | 13  | In-memory queue                                     | Queue state may be lost or jobs may stall after process restarts.                     | M                  | H              | Persist queue metadata and reconcile stale jobs on startup.                                                          | ENG   | Open   |
  | 14  | Dual-path RAG ingestion                             | Structured rows and semantic chunks may fall out of sync if one ingestion path fails. | M                  | M              | Enforce atomic ingestion and validate consistency during write.                                                      | ENG   | Open   |

- **5.3. Product Management Team:** 📐

  - ❓ Q: Can you confirm the **exact retention policy** you want for structured outputs – is the 10-day window fixed for all pilot organisations, or should it be configurable per client within a bounded range (e.g. 7–30 days)?
  - ✅ A: The 10-day window is fixed for all pilot organisations.
  - ❓ Q: For **bank statement and accounts schemas**, do you expect us to match an existing internal schema, or should we define a canonical schema that downstream teams will map into?
  - ✅ A: We should define a canonical schema that downstream teams will map into.
  - ❓ Q: What are your expectations around **authentication and access control** for the pilot (e.g. single API key per organisation, per-user accounts for the portal, SSO), and how many organisations/users do you anticipate?
  - ✅ A: Duplicate the lightweight authentication model used in the reference implementation—namely a single organisation-level API key, a minimal portal login, and organisation-scoped Row-Level Security—without introducing SSO, per-user roles, or broader account-management features.
  - ❓ Q: What is your preferred **error-reporting and support workflow** during the pilot (e.g. shared Slack channel, ticketing tool, email) and what response times do you expect for blocking issues?
  - ✅ A: Single shared Slack channel for real-time issue reporting, supported by fallback email for anything requiring attachments or longer explanations.
  - ❓ Q: For pilot success metrics, how will your team **measure baseline manual processing time** and verify the 50% time-reduction target — should this be instrumented within the tool, or measured externally?
  - ✅ A: That is out of scope, it will be handled externally.
  - ❓ Q: Should the pilot portal include any **quality-review workflow** (e.g. marking fields as correct/incorrect), or is this explicitly out of scope for this phase?
  - ✅ A: Explicitly out of scope for this phase.

- **5.4. Engineering Team:** 🏗️

  - ❓ Q: Which **PDF and table extraction libraries** (and OCR engine, if any) will we standardise on for the MVP, and how will we encapsulate them behind an internal interface so they can be swapped later with minimal impact?
  - ✅ A: A custom Module01-style extraction engine using `pypdf` for PDF parsing, `pdfplumber` and `camelot` for table detection and extraction, optional `pytesseract` OCR for scanned pages, and `pandas`/`python-dateutil`/`rapidfuzz` for normalisation, all wrapped behind a single `extract_tables` interface returning table JSON, metadata, and a quality score.
  - ❓ Q: What is the **target hosting environment** for the pilot (e.g. Supabase functions, containerised app on a low-cost PaaS, or client infrastructure), and how does that choice influence our logging, monitoring, and deployment strategy?
  - ✅ A: A containerised FastAPI service backed by a single Supabase project with structured JSON logs, simple health checks, basic metrics, and the same deployment and monitoring approach as Marconi’s system
  - ❓ Q: Which **embedding provider and vector storage mechanism** will we use initially (e.g. OpenAI embeddings + Postgres vector extension vs self-hosted model), and how will we abstract this to avoid lock-in?
  - ✅ A: An OpenAI small embedding model with Postgres vector storage behind a minimal embedding abstraction that supports future model or dimensional changes.
  - ❓ Q: How will we implement **multi-organisation isolation** (tenant ID vs user ID), and do we need explicit support for multiple organisations sharing a single technical integration but separate data partitions?
  - ✅ A: Organisation-level tenancy with API keys directly mapped to `organisation_id`, RLS-enforced isolation, and a single-organisation integration model with schema flexibility for future routing.
  - ❓ Q: What are the concrete **SLA/SLO targets** we will commit to for the pilot (latency, throughput, uptime), given the single-builder constraint and limited infrastructure budget?
  - ✅ A: An extraction pipeline targeting five-minute completion for typical filings with a ten-minute hard timeout, immediate ingestion responses, and clear status transitions for client polling.
  - ❓ Q: How will we structure **token-style extraction logging** (operation records) so it can later support billing/usage analytics without forcing a rework of the logging schema?
  - ✅ A: Extraction operation records aligned with Marconi’s transaction pattern capturing timings, virtual token counts, and outcomes to form a durable basis for usage analytics and later billing.
  - ❓ Q: What is our **testing strategy** for extraction accuracy — e.g. golden datasets with expected outputs, differential tests against human-labelled data, and regression suites as we add new document types?
  - ✅ A: A golden dataset of labelled PDFs with end-to-end comparison tests and accuracy regressions enforcing expected financial outputs as new document types are added.
  - ❓ Q: How will we design **retention and deletion jobs** (e.g. cron, managed scheduled tasks) to be observable, idempotent, and easy to test in non-production environments?
  - ✅ A: A scheduled retention job expiring structured outputs after ten days, never storing PDFs, using idempotent deletion logic with summarised logs and shorter non-production windows.
  - ❓ Q: Do we want any **feature flags** or configuration toggles (e.g. enable/disable semantic storage, optional OCR) to simplify experimentation during the pilot?
  - ✅ A: Environment-driven feature flags controlling semantic storage, OCR readiness, and per-organisation overrides, read only at pipeline boundaries for predictable behaviour.

- **5.5. Explicit Assumptions & Known Dependencies**
  - ❓ Q: What assumptions or dependencies are we making that could affect delivery, scope, or performance?
  - ✅ A:
    1. **Pilot document supply:** We assume pilot organisations will provide at least **30 real, varied PDFs** (mix of accounts and bank statements) early enough in the project to support extraction tuning and QA.
    2. **Third-party services:** We assume continued access to chosen third-party services (Supabase, hosting provider, embedding API if used) under current free or low-cost usage limits.
    3. **Future feature alignment:** We assume future modules (AML rules, credit spreading, projections) will reuse the same dual-path RAG architecture and normalised schemas, so we must avoid bespoke, one-off schemas in the MVP.
    4. **Client integration capability:** We assume client engineering teams can integrate with a straightforward API using standard patterns (HTTPS, JSON, API keys) without requiring custom SDKs in this phase.
    5. **Data residency:** We assume UK/EU hosting is sufficient and there is no strict requirement for data to remain within a specific country or on client-premises infrastructure for the pilot.
    6. **Change control:** We assume any material changes to scope or NFRs (e.g., stricter latency SLOs, additional document types) will be managed through an explicit change-control process and reflected in the PRD.

_Definition of Done for Section 5: every row is either “Closed” or migrated into the PRD / Technical Architecture Document._

---

## 6. Guidance for Product Management Team 📐

_Task: Based on this project blueprint, develop the detailed **PRD**. Your focus is translating the agreed scope (Section 3) into precise, actionable requirements for the Engineering team._

- 🎯 **Problem Statement & Goals**: Define the core problem this product or feature solves and translate Sec 1 objectives into specific, measurable goals, and non-goals, in alignment with the success metrics.
- 👥 **Target Users & Personas**: Describe primary user types and scenarios (derived from Sec 1.4 and Sec 3) to anchor user stories in real workflows and motivations.
- 📋 **Detailed Feature Specification**: Create detailed user stories/functional specs for _each_ item in Sec 3.1. Define clear, testable acceptance criteria suitable for QA and client sign-off using Sec 3.2, including the key data that must exist at the functional level. Document any integration requirements, including APIs, authentication, rate limits, and expected error-handling behaviours.
- 🔁 **User Flows & UI/UX**: Document the detailed user flows (referencing Sec 3.3 if populated) and UI requirements (referencing client assets if provided). Specify error handling logic and UX.
- 🧪 **Validation Notes**: For each user story, include a short description of how the feature will be evaluated in practice — what “success” looks like, what QA must explicitly test, and what must be observable in logs/metrics to confirm the system is working as expected.
- 🔁 **User Flows & UI/UX:** Document the detailed user flows (referencing Sec 3.3 if populated) and UI requirements (referencing client assets if provided). Specify error handling logic and UX.
- 🚧 **Scope Boundaries**: Clearly delineate boundaries based on Sec 4.1.
- 🧩 **Assumptions & Dependencies**: Summarise any functional or business assumptions and relevant dependencies from Sec 2.3 and Sec 5 that must be captured in the PRD.
- 🔒 **NFRs**: Incorporate relevant NFRs from Sec 2.2 and Sec 5.1 into feature specifications and acceptance criteria where applicable. Ensure any non-standard NFRs are clearly specified.
- 📊 **Success Metrics & Analytics**: Specify how success will be measured (analytics events, KPIs, dashboards). Link each metric to the quantified targets in Section 1.3 and include validation notes. Include any non-analytics success criteria (functional, UX, or quality-based) that define what ‘good’ looks like from a user and business perspective.

---

## 7. Guidance for Engineering Team 🏗️

_Task: Based on the detailed **PRD** from the PM team, create the **Technical Architecture Document**. Reference this project blueprint for context. Focus on the technical requirements for a production-ready, standalone application, including major design decisions, system behaviours, and environment considerations._

- 🔍 **Detailed Feasibility Assessment:** Assess technical feasibility and implications of client constraints and specified features. Flag any gaps or trade-offs requiring client input before build.
- 🧱 **Architecture & Technology Stack:** Propose a suitable architecture and justified technology stack for a standalone application meeting all requirements. State the architectural pattern being used and present the high-level repository structure that implements it. Describe the main internal components and their responsibilities, external system integrations, data flows, API boundaries, and data models. Cite key external design docs, articles, or templates that materially influence the architecture, tech stack and tool design decisions.
- 🔗 **Interface Contracts**: Document any interface contracts required for the system to function, including externally visible endpoints or operations, request/response structures, authentication requirements, and error-handling behaviours.
- 🔒 **NFRs:** Detail _how_ the architecture and implementation plan will address the specified NFRs and state which security responsibilities the system architecture will handle and which are out of scope.
- ⚠️ **Dependency-Risk:** Detail _how_ the architecture and implementation plan will mitigate dependency-risks.
- 👁️ **Observability & Operations**: Outline suitable logging, tracing, and operational alerting required to support reliability, debugging, and production monitoring post-handover.
- 🧪 **Testing & QA Strategy:** Define the testing strategy (unit, component, E2E, etc.) to ensure features meet acceptance criteria, NFRs are met, dependency-risk mitigations are effective, and the application meets delivery success metrics. Specify tools, environments, and automation scope.
- 🛠️ **Implementation & Delivery:** Outline CI/CD pipelines, deployment environments, configuration surfaces (e.g., environment variables, configuration files, settings classes, feature flags), secrets management approach, and code quality controls. Specify client handover artifacts required for production-ready delivery, including the intended runtime topology (e.g. env vars, config files, container volumes, ports), deployment model, storage requirements, and any host-level or environment considerations necessary for correct operation.

---

## 8. Success Metrics for Project Delivery 📊

\*How _we_ measure the successful completion of _this_ project delivery\*.

- **8.1. Core Delivery Metrics:**
  - [ ] ✅ All features listed in Section 3.1 are implemented and demonstrably working per acceptance criteria defined in the PRD.
  - [ ] 🧪 Software passes internal QA against defined acceptance criteria.
  - [ ] 🔒 Meets NFRs outlined in Sections 2 and 5 (to the extent specified or standard practice).
  - [ ] 🛰️ Dependency-Risk Register closed (all mitigations implemented & tested).
  - [ ] 🚚 Software delivered/deployed to agreed environment suitable for handover.

## 9. Next Steps & Owners 🧾

_Immediate actions to move this project forward._

- **9.1. Action Items:**
  - [x] 📋 Agency lead compiles Blueprint.
  - [x] 🧐 PM/Eng review Blueprint and compile questions.
  - [x] 📨 Client responds to Agency questions.
  - [ ] 📝 PM drafts PRD.
  - [ ] ✅ Client approves PRD.
  - [ ] 📘 Eng drafts Technical Architecture Document.

---

## 10. How to Use

1.  🖊️ **Complete sections 1-4** based on initial understanding of client needs and the agreed scope.
2.  👀 **PMs and Engineers review** this blueprint thoroughly and compile client and internal questions (in Sec 5).
3.  🏗️ **PMs draft the detailed PRD**, incorporating clarifications needed and client responses (Guidance in Sec 6).
4.  🧑‍💻 **Engineers review the PRD**, draft Technical Architecture Document (Guidance in Sec 7).
5.  📌 **Define and track Next Steps** (Sec 9).
