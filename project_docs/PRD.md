# Product Requirements Document: Financial PDFs Converter

**Project Name:** Financial PDFs Converter
**Version:** 1.0
**Date:** 2025-12-05
**Prepared By:** Product Management Team
**Status:** Draft for Client Approval

---

## 1. Problem Statement & Goals

### 1.1 Problem Statement

Financial services firms and fintechs currently rely on manual, error-prone processes to extract data from customer-provided financial PDFs (company accounts and bank statements). Operations analysts spend hours per document manually copying data into spreadsheets, introducing errors and creating bottlenecks in customer onboarding, credit renewals, and risk assessments. This manual toil scales linearly with document volume and lacks consistency across analysts.

### 1.2 Goals

**Primary Goal:**
Reduce manual financial data extraction time by ≥50% through an API-first extraction service that transforms financial PDFs into clean, structured datasets suitable for downstream business workflows.

**Specific Success Metrics** (from Blueprint Section 1.3):
1. Process ≥30 real-world financial PDFs with ≥99% field extraction accuracy vs human benchmark
2. Reduce average manual processing time per PDF by ≥50% for pilot users (measured via before/after baseline)
3. Onboard ≥2 organisations, each processing ≥5 PDFs through the system during pilot
4. Obtain ≥2 concrete commercial signals (pricing inquiries, production integration discussions)
5. Deliver architecture foundation robust enough to support future modules (AML, financial modelling, credit spreading) without re-architecture

### 1.3 Non-Goals (Explicitly Out of Scope)

- Full pricing, billing, and subscription management (Stripe integration, enterprise invoicing)
- Multi-tenant user management with granular roles beyond organisation-level isolation
- Alternative output formats (XLSX files)
- Advanced downstream analytics modules (AML rules engine, credit spreading, DCF/IPO modelling)
- EU-grade compliance artefacts (formal DPAs, DPIAs) beyond standard good practices
- Long-term archival storage of PDFs or structured data beyond 10-day retention window
- Native mobile applications or desktop clients
- Complex third-party platform integrations (core banking systems, CRMs)

---

## 2. Target Users & Personas

### 2.1 Primary User: Operations/Onboarding Analyst

**Profile:**
Works at fintech or financial services firm; receives customer financial PDFs as part of onboarding, periodic reviews, or credit renewals.

**Current Workflow Pain Points:**
- Manually opens each PDF, scans for relevant tables, re-keys data into Excel
- Time-consuming (4-6 hours per complex filing), error-prone (typos, misread numbers)
- Inconsistent data structuring across different analysts
- No automation capability with current ad-hoc tools

**Goals:**
- Upload PDFs via portal or receive extraction results via API
- Obtain structured datasets (JSON/CSV) with minimal manual correction needed
- Increase throughput to approve/decline customers faster
- Reduce error rate in financial data handling

**Success Criteria:**
- Can upload 30MB PDF and receive extraction results within 10 minutes
- Extracted data requires <5% manual correction (vs 100% manual entry today)
- Can view extraction quality score before using data

### 2.2 Secondary User: Risk/Credit/Compliance Analyst

**Profile:**
Relies on financial statement line items and transaction data for AML reviews, creditworthiness assessments, financial projections.

**Current Workflow Pain Points:**
- Receives inconsistent data formats from operations team
- Must validate and reconcile data before using in risk models
- Limited ability to query historical financial data across customers

**Goals:**
- Consume structured data for downstream rules, models, and analysis
- Review extraction quality and request schema adjustments if needed
- Rely on consistent, machine-usable data format

**Success Criteria:**
- Can programmatically query extracted data via API
- Data structure matches expected schema contracts
- Can identify extraction quality issues via quality scores

### 2.3 Secondary User: Internal Engineering/Data Team

**Profile:**
Integrates the extraction API into existing onboarding, risk, or analytics pipelines at client organisation.

**Current Workflow Pain Points:**
- No standardised financial data extraction service available
- Must build custom parsers for each new document format
- Integration points are brittle and require ongoing maintenance

**Goals:**
- Integrate well-defined, stable API into existing systems
- Minimal maintenance overhead for extraction logic
- Clear error handling and status visibility

**Success Criteria:**
- API documentation sufficient for integration without support calls
- Predictable response formats (consistent JSON schemas)
- Rate limits and error responses clearly documented

---

## 3. Detailed Feature Specifications

### 3.1 Feature: PDF Ingestion & Validation API

**User Story:**
As an engineering team member, I want to programmatically submit financial PDFs for extraction so that I can automate customer onboarding workflows.

**Functional Requirements:**
1. Accept PDF files up to 30MB via POST endpoint `/api/ingest-pdf`
2. Validate file type (PDF magic bytes: `%PDF` header)
3. Validate file size (reject >30MB with 400 error)
4. Require authentication (organisation-level API key in Authorization header)
5. Accept metadata: `document_type_hint` (enum: "company_accounts", "bank_statement"), `customer_id` (optional string), `environment` (enum: "sandbox", "production")
6. Assign unique `document_id` (UUID)
7. Store PDF to filesystem: `uploaded_files/organisation_{org_id}/{document_id}.pdf`
8. Create database record in `financial_extractions` table with status "pending"
9. Enqueue extraction job (async processing, not blocking)
10. Return synchronous response within 500ms (NFR #1)

**API Contract:**

Request:
```
POST /api/ingest-pdf
Authorization: Bearer {organisation_api_key}
Content-Type: multipart/form-data

file: [PDF binary]
document_type_hint: "company_accounts"
customer_id: "CUST-12345" (optional)
environment: "production" (default: "sandbox")
```

Response (Success 202):
```json
{
  "status": "accepted",
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "initial_status": "pending",
  "estimated_completion_minutes": 5,
  "warnings": []
}
```

Response (Error 400 - Oversized):
```json
{
  "error": "file_too_large",
  "message": "PDF exceeds 30MB limit. Please split document or contact support.",
  "max_size_mb": 30
}
```

Response (Error 400 - Invalid Type):
```json
{
  "error": "invalid_file_type",
  "message": "File is not a valid PDF. Please ensure file starts with PDF magic bytes.",
  "received_header": "504B0304" (example: ZIP file)
}
```

Response (Error 401 - Unauthorized):
```json
{
  "error": "unauthorized",
  "message": "Invalid or missing API key. Visit portal settings for your organisation API key."
}
```

**Edge Cases & Error Handling:**
- Non-PDF files: Return 400 with magic bytes validation error
- Encrypted/password-protected PDFs: Accept, defer error to extraction stage
- Network timeout during upload: Return 504, instruct client to retry
- Duplicate uploads (same filename): Allow, generate new document_id (versioning)
- Missing/invalid document_type_hint: Default to null, extraction attempts auto-detection

**Validation Notes:**
- QA must test 10MB, 20MB, 29MB, 31MB files (boundary testing)
- QA must test encrypted PDFs (extraction stage should log error, mark as failed)
- QA must verify filename collision handling (upload nvidia.pdf twice → both stored)
- Monitor logs for API response time P95 <500ms (NFR #1)

**Acceptance Criteria:**
- [ ] Endpoint accepts valid PDFs up to 30MB
- [ ] Rejects files >30MB with helpful error message
- [ ] Validates PDF magic bytes, rejects non-PDFs
- [ ] Returns document_id within 500ms (P95)
- [ ] Stores file to correct organisation-scoped directory
- [ ] Creates pending extraction record in database with timestamp
- [ ] API key authentication required (no anonymous uploads)
- [ ] Logs: `INFO: PDF ingested document_id={id} org_id={org} size_mb={size}`

---

### 3.2 Feature: PDF Ingestion via Web Portal

**User Story:**
As an operations analyst, I want to manually upload PDFs through a browser interface so that I can process documents without API integration.

**Functional Requirements:**
1. Provide file upload component on portal home page (drag-and-drop or click to browse)
2. Show file size validation before upload (30MB client-side check)
3. Require document type tagging: dropdown with "Company Accounts", "Bank Statement"
4. Show upload progress indicator (progress bar with %)
5. Display upload confirmation with document_id and processing status
6. Redirect to "Document History" page after successful upload
7. Handle upload failures gracefully (network errors, server errors)
8. Require user login (email/password authentication)
9. Scope all uploads to user's organisation_id (RLS enforced)

**UI Mockup Flow:**
```
[Upload Page]
┌─────────────────────────────────────┐
│ Upload Financial Document           │
│                                     │
│ ┌─────────────────────────────┐   │
│ │  Drag PDF here or click     │   │
│ │  to browse                  │   │
│ │  (Max 30MB)                 │   │
│ └─────────────────────────────┘   │
│                                     │
│ Document Type: [▼ Company Accounts]│
│                                     │
│ [Upload] [Cancel]                  │
└─────────────────────────────────────┘

[Upload Progress]
┌─────────────────────────────────────┐
│ Uploading nvidia_10k.pdf...         │
│ ████████████████░░░░ 75%           │
└─────────────────────────────────────┘

[Upload Success]
┌─────────────────────────────────────┐
│ ✓ Upload Successful                 │
│ Document ID: 550e8400-e29b...       │
│ Status: Processing                  │
│                                     │
│ [View Document History]             │
└─────────────────────────────────────┘
```

**Edge Cases & Error Handling:**
- User selects .docx file: Show error "Only PDF files supported" before upload starts
- User closes browser during upload: Upload continues server-side, status visible on return
- Upload fails mid-transfer: Show "Upload failed. Please try again." with retry button
- Server returns 500: Show "Processing error. Our team has been notified. Please retry in 5 minutes."

**Validation Notes:**
- QA must test browser upload with 10MB, 20MB, 29MB files
- QA must test unsupported file types (.xlsx, .docx, .txt)
- QA must test network disconnect during upload
- QA must verify correct organisation scoping (User A cannot see User B's uploads if different orgs)

**Acceptance Criteria:**
- [ ] File upload component accepts PDF drag-and-drop and file browser selection
- [ ] Client-side validation prevents >30MB uploads before transmission
- [ ] Document type dropdown populated with valid options
- [ ] Progress bar shows upload percentage
- [ ] Success confirmation displays document_id and links to history page
- [ ] Unsupported file types rejected with clear message
- [ ] Upload errors display user-friendly messages (no technical jargon)
- [ ] Uploads scoped to authenticated user's organisation

---

### 3.3 Feature: Web Portal Document History & Results Viewer

**User Story:**
As an operations analyst, I want to view all my organisation's uploaded documents and their extraction results so that I can monitor processing status and download structured data.

**Functional Requirements:**
1. Display paginated list of all extractions (25 per page, newest first)
2. Show columns: Document Name, Upload Date, Status, Quality Score, Actions
3. Status values with visual indicators:
   - Pending (grey icon, no score)
   - Processing (blue animated pulse, no score)
   - Success (green checkmark, quality score badge)
   - Failed (red X, error icon)
4. Quality score displayed as: "Quality: 95%" with colour coding (≥90% green, 70-89% amber, <70% red)
5. Actions dropdown per row: "View Data", "Download CSV", "Re-extract", "Delete"
6. "View Data" opens modal showing HTML table of extracted financial data
7. "Download CSV" triggers file download of normalised structured data
8. Real-time status updates via Supabase subscriptions (no page refresh needed)
9. Search/filter by company name or document name
10. Show empty state when no documents: "No documents yet. Upload your first financial PDF."

**UI Mockup:**
```
[Document History Page]
┌──────────────────────────────────────────────────────────────────┐
│ My Documents                                    [+ Upload New]    │
│                                                                   │
│ Search: [________________]  Filter: [All Statuses ▼]            │
│                                                                   │
│ ┌────────────────────────────────────────────────────────────┐  │
│ │ Document Name       │ Uploaded    │ Status  │ Quality │ ▼  │  │
│ ├────────────────────────────────────────────────────────────┤  │
│ │ nvidia_10k_2023.pdf │ 2 min ago   │ ✓ Success│ 95% 🟢│ ⋮  │  │
│ │ amd_accounts.pdf    │ 5 min ago   │ ⟲ Processing│ -  │ ⋮  │  │
│ │ bank_statement.pdf  │ 10 min ago  │ ✗ Failed │ -   │ ⋮  │  │
│ │ tesla_10q.pdf       │ 1 hour ago  │ ✓ Success│ 88% 🟡│ ⋮  │  │
│ └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│ Page 1 of 3                          [< Prev] [Next >]          │
└──────────────────────────────────────────────────────────────────┘

[Actions Dropdown on click ⋮]
┌──────────────────┐
│ View Data        │
│ Download CSV     │
│ Re-extract       │
│ ───────────────  │
│ Delete           │
└──────────────────┘

[View Data Modal]
┌──────────────────────────────────────────────────────────────────┐
│ Extracted Data: nvidia_10k_2023.pdf                        [✕]   │
│                                                                   │
│ Company: NVIDIA Corporation                                      │
│ Document Type: Company Accounts                                  │
│ Fiscal Year: 2023                                                │
│                                                                   │
│ Income Statement                                                 │
│ ┌──────────────────────────────────────────────────────────┐    │
│ │ Metric                    │ 2023         │ 2022          │    │
│ ├──────────────────────────────────────────────────────────┤    │
│ │ Revenue                   │ $26,974M     │ $26,914M      │    │
│ │ Cost of Revenue           │ $11,618M     │ $9,439M       │    │
│ │ Gross Profit              │ $15,356M     │ $17,475M      │    │
│ └──────────────────────────────────────────────────────────┘    │
│                                                                   │
│ [Download CSV] [Close]                                           │
└──────────────────────────────────────────────────────────────────┘
```

**Edge Cases & Error Handling:**
- Missing records due to retention policy: Show "Data expired (10-day retention)" in status
- Malformed stored data: Show "Data corrupted. Please re-extract." with re-extract button
- Access control violation: Never show other organisations' documents (RLS enforced)
- Real-time update failure: Fallback to 30-second polling if WebSocket disconnects

**Validation Notes:**
- QA must verify real-time updates: Upload in Tab A, verify appears in Tab B instantly
- QA must verify pagination works correctly with >25 documents
- QA must verify quality score colour coding (90%+ green, 70-89% amber, <70% red)
- QA must test "View Data" modal with various document types and year ranges
- QA must verify CSV download contains correct data matching displayed HTML table

**Acceptance Criteria:**
- [ ] Document list displays all organisation's extractions (RLS scoped)
- [ ] Status indicators accurate and visually distinct (pending/processing/success/failed)
- [ ] Quality scores displayed with colour coding
- [ ] "View Data" modal renders HTML table with financial data
- [ ] "Download CSV" delivers valid CSV file with normalised data
- [ ] Real-time updates work (status changes appear without page refresh)
- [ ] Search filters documents by name
- [ ] Pagination handles >25 documents correctly
- [ ] Empty state displays when no documents exist
- [ ] Delete action removes document and shows confirmation

---

### 3.4 Feature: Table Detection

**User Story:**
As a system, I must identify and isolate relevant table regions within financial PDFs before extraction to ensure accurate structured data output.

**Functional Requirements:**
1. Integrate LLMWhisperer Text Extraction Service as primary table detection engine
2. Process PDF page-by-page to identify table regions
3. Detect table types: Income Statement, Balance Sheet, Cash Flow Statement, Bank Transactions
4. Handle tables spanning multiple pages (merge adjacent regions)
5. Generate table coordinates and structure maps for extraction engine
6. Pass detected table regions to extraction engine (Module01 pipeline_03)
7. Log table detection metadata: page numbers, table types detected, confidence scores
8. Handle irregular table borders and partially corrupted pages gracefully
9. Trigger OCR for scanned images when native text extraction fails
10. Set extraction status to "processing" with stage indicator "Stage 2/5: Table Detection"

**Technical Approach:**
- LLMWhisperer API integration wrapped behind internal `ITableDetector` interface
- Fallback to `pdfplumber` table detection if LLMWhisperer fails or times out
- Store detection results in extraction output directory: `output/organisation_{org_id}/runs/{timestamp}_PROCESSING/02_table_detection/`
- Detection output format: JSON with table regions `{"page": 1, "bbox": [x1, y1, x2, y2], "type": "income_statement", "confidence": 0.92}`

**Edge Cases & Error Handling:**
- Tables spanning pages: Merge regions if bottom of page N matches top of page N+1
- No tables detected: Mark extraction as failed, log "No financial tables found in PDF"
- Irregular table borders: Use LLMWhisperer's ML-based detection (handles borderless tables)
- Partially corrupted pages: Skip corrupted pages, continue with valid pages, mark quality score accordingly
- Scanned images: Detect non-native text (low character confidence), trigger pytesseract OCR
- LLMWhisperer timeout: Log error, fallback to pdfplumber, continue extraction

**Validation Notes:**
- QA must test PDFs with tables spanning 2 pages (verify merge logic)
- QA must test PDFs with irregular borders (no grid lines)
- QA must test scanned PDFs (verify OCR triggers)
- Monitor LLMWhisperer API response times (log if >10 seconds)
- Verify fallback triggers correctly when LLMWhisperer returns 500 error

**Acceptance Criteria:**
- [ ] LLMWhisperer integrated as primary detection engine
- [ ] Detects Income Statement, Balance Sheet, Cash Flow Statement tables
- [ ] Handles multi-page tables (merges regions correctly)
- [ ] Triggers OCR for scanned pages (low native text confidence)
- [ ] Falls back to pdfplumber if LLMWhisperer fails
- [ ] Logs table detection results (page numbers, types, confidence)
- [ ] Updates extraction status to "processing - Stage 2/5"
- [ ] Detection completes within 2 minutes for ≤20 page PDFs (NFR #2)

---

### 3.5 Feature: Extraction Engine

**User Story:**
As a system, I must extract cell-level data from detected table regions and transform them into structured JSON with confidence scores.

**Functional Requirements:**
1. Receive table regions from detection stage (coordinates, type hints)
2. Extract cell-by-cell data using Module01 pipeline_03 (pdfplumber + camelot integration)
3. Preserve row/column structure from PDF layout
4. Generate per-field confidence scores (0.0-1.0 scale)
5. Store extraction payloads as JSON in output directory: `03_extraction/extracted_tables.json`
6. Create operation record in `transactions` table for extraction run (virtual token usage logging)
7. Handle merged cells, inconsistent headers, OCR uncertainty
8. Set extraction status to "processing" with stage indicator "Stage 3/5: Data Extraction"
9. Log timing metrics: extraction start time, end time, duration
10. Update database record with extraction output path

**Extraction Output Schema:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "extraction_timestamp": "2025-12-05T14:23:45Z",
  "tables": [
    {
      "table_type": "income_statement",
      "page_number": 3,
      "rows": [
        {
          "row_index": 0,
          "cells": [
            {"column": "Metric", "value": "Revenue", "confidence": 0.98},
            {"column": "2023", "value": "26974000000", "confidence": 0.95},
            {"column": "2022", "value": "26914000000", "confidence": 0.94}
          ]
        }
      ],
      "metadata": {
        "header_row_count": 1,
        "data_row_count": 15,
        "column_count": 3
      }
    }
  ],
  "ocr_pages": [3, 7],
  "extraction_quality_score": 95
}
```

**Edge Cases & Error Handling:**
- Inconsistent headers: Use fuzzy matching to normalize column names ("Total Rev" → "Revenue")
- Merged cells: Duplicate value across merged cell range
- OCR uncertainty: Mark cells with confidence <0.70 as "low_confidence"
- Partially unreadable tables: Extract readable portions, mark missing cells as null
- Extraction timeout (>10 minutes): Mark as failed, log partial results, allow re-extraction

**Validation Notes:**
- QA must verify confidence scores align with actual extraction accuracy
- QA must test PDFs with merged cells (verify value duplication logic)
- QA must test PDFs with inconsistent headers (verify fuzzy matching)
- Monitor extraction timing: 95% complete within 5 minutes for ≤20 pages (NFR #2)
- Verify operation records created in transactions table with correct timestamps

**Acceptance Criteria:**
- [ ] Extracts cell-level data from detected table regions
- [ ] Generates per-field confidence scores
- [ ] Preserves row/column structure from PDF
- [ ] Handles merged cells correctly (duplicates values)
- [ ] Normalizes inconsistent headers (fuzzy matching)
- [ ] Stores extraction JSON in output directory
- [ ] Creates operation record in transactions table
- [ ] Updates extraction status to "processing - Stage 3/5"
- [ ] Completes within 5 minutes for ≤20 page PDFs (P95, NFR #2)
- [ ] Logs extraction start/end timestamps for success metric analysis

---

### 3.6 Feature: Normalization & Schema Mapping

**User Story:**
As a system, I must transform extracted data into consistent canonical schemas per document family so downstream consumers receive predictable data structures.

**Functional Requirements:**
1. Receive extraction payloads from extraction engine
2. Map extracted fields to canonical schema per document type (company_accounts, bank_statement)
3. Canonical schemas defined by Product Management, provided to Engineering as Pydantic models
4. Normalize field names: "Turnover"/"Sales"/"Total Revenue" → "revenue"
5. Normalize date formats: "31/01/2023", "2023-01-31", "Jan 31, 2023" → ISO 8601 "2023-01-31"
6. Detect and store currency metadata (GBP, USD, EUR) without conversion
7. Handle unknown/custom line items: Store in "other_line_items" array with original label
8. Validate data types: amounts as strings (preserve precision), dates as ISO strings
9. Calculate overall quality score: (matched_fields / expected_fields) * 100
10. Store normalized JSON in output directory: `04_processing/normalized_data.json`

**Canonical Schema Structure (Company Accounts):**
```json
{
  "company_name": "NVIDIA Corporation",
  "document_type": "company_accounts",
  "fiscal_year_end": "2023-01-29",
  "currency": "USD",
  "income_statement": {
    "2023": {
      "revenue": "26974000000",
      "cost_of_revenue": "11618000000",
      "gross_profit": "15356000000",
      "operating_expenses": "3949000000",
      "operating_income": "11407000000",
      "net_income": "9752000000"
    },
    "2022": {...}
  },
  "balance_sheet": {
    "2023": {
      "total_assets": "65728000000",
      "current_assets": "41182000000",
      "total_liabilities": "30349000000",
      "current_liabilities": "14762000000",
      "total_equity": "35379000000"
    }
  },
  "cash_flow_statement": {
    "2023": {
      "operating_cash_flow": "11145000000",
      "investing_cash_flow": "-10279000000",
      "financing_cash_flow": "-2372000000",
      "net_cash_change": "-1506000000"
    }
  },
  "other_line_items": [
    {"label": "Unusual Tax Credits", "value": "123000000", "statement": "income"}
  ]
}
```

**Canonical Schema Structure (Bank Statement):**
```json
{
  "account_holder": "NVIDIA Corporation",
  "document_type": "bank_statement",
  "account_number": "****1234",
  "statement_period_start": "2023-01-01",
  "statement_period_end": "2023-01-31",
  "currency": "USD",
  "opening_balance": "5432100000",
  "closing_balance": "6123400000",
  "transactions": [
    {
      "date": "2023-01-05",
      "description": "Customer Payment - ABC Corp",
      "debit": null,
      "credit": "450000000",
      "balance": "5882100000"
    }
  ]
}
```

**Edge Cases & Error Handling:**
- Unknown line items: Store in "other_line_items" with original label, don't fail extraction
- Custom labels: Use fuzzy matching (rapidfuzz) with 80% threshold to map to canonical fields
- Mixed currencies in document: Store currency per line item if detected, flag in quality notes
- Missing column headers: Use column position heuristics (first column = metric name)
- Ambiguous dates: Prefer DD/MM/YYYY for UK documents, MM/DD/YYYY for US (based on document_type_hint)
- Date parsing failure: Store as original string, mark field with "date_parse_error" flag

**Validation Notes:**
- QA must test PDFs with non-standard terminology ("Turnover" vs "Revenue")
- QA must test various date formats (UK vs US conventions)
- QA must test mixed currency scenarios (multi-entity statements)
- QA must verify quality score calculation: 100% when all expected fields present, 66% when cash flow missing
- PM team must provide Pydantic schema definitions before Engineering implementation

**Acceptance Criteria:**
- [ ] Maps extracted fields to canonical schema per document type
- [ ] Normalizes field names (fuzzy matching with 80% threshold)
- [ ] Normalizes date formats to ISO 8601
- [ ] Detects and stores currency metadata
- [ ] Handles unknown line items (stores in "other_line_items")
- [ ] Validates data types (amounts as strings, dates as ISO strings)
- [ ] Calculates quality score: (matched_fields / expected_fields) * 100
- [ ] Stores normalized JSON in output directory
- [ ] Updates extraction status to "processing - Stage 4/5"
- [ ] Canonical schemas provided by PM, implemented as Pydantic models by Engineering

---

### 3.7 Feature: Structured Storage Integration (Dual-Path RAG)

**User Story:**
As a system, I must persist normalized data into dual-path RAG architecture to enable both exact SQL queries and semantic LLM retrieval.

**Functional Requirements:**
1. Receive normalized data from normalization stage
2. **Structured Path (document_rows):** Insert canonical normalized data as single JSONB record per extraction
3. **Semantic Path (documents):** Generate text chunks from normalized data, create embeddings, store with metadata
4. Link both paths via `document_id` foreign key
5. Use OpenAI text-embedding-3-small (1536 dimensions) for embeddings
6. Chunk normalized data into 400-character text segments (0 overlap, consistent with existing RAG)
7. Store chunk metadata: `{document_id, chunk_index, statement_type, fiscal_year}`
8. Create document_metadata record linking to extraction record
9. Update extraction record with `document_id` foreign key
10. Set extraction status to "success" with quality score on completion

**Structured Path Implementation:**
```sql
-- Insert into document_rows
INSERT INTO document_rows (dataset_id, row_data, created_at)
VALUES (
  '550e8400-e29b-41d4-a716-446655440000',
  '{"company_name": "NVIDIA", "income_statement": {...}}',
  NOW()
);
```

**Semantic Path Implementation:**
```python
# Generate text chunks from normalized data
text_representation = f"""
Company: {data['company_name']}
Fiscal Year: {data['fiscal_year_end']}

Income Statement 2023:
Revenue: {data['income_statement']['2023']['revenue']}
Gross Profit: {data['income_statement']['2023']['gross_profit']}
...
"""

chunks = chunk_text(text_representation, chunk_size=400, overlap=0)
embeddings = create_embeddings(chunks)  # OpenAI API call

# Store in documents table
for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
    INSERT INTO documents (content, metadata, embedding)
    VALUES (
        chunk,
        '{"document_id": "...", "chunk_index": i, "statement_type": "income"}',
        embedding  # vector(1536)
    )
```

**Edge Cases & Error Handling:**
- Embedding API failure: Retry 3 times with exponential backoff, mark extraction as "partial" if semantic path fails
- Chunking inconsistency: Validate chunk count matches expected range (10-50 chunks per document)
- Schema drift: Validate JSONB structure against Pydantic schema before insert
- Retention window: Schedule job deletes document_rows and documents records after 10 days (soft delete)
- Document_metadata already exists: Update existing record instead of creating duplicate

**Validation Notes:**
- QA must verify both document_rows and documents records created for each extraction
- QA must verify embeddings have correct dimensions (1536)
- QA must test semantic search retrieval (query "NVIDIA revenue" should return relevant chunks)
- QA must verify retention job correctly deletes 10-day-old records
- Monitor embedding API costs (log token usage per extraction)

**Acceptance Criteria:**
- [ ] Inserts normalized data into document_rows as single JSONB record
- [ ] Generates text chunks (400 chars, 0 overlap)
- [ ] Creates embeddings using OpenAI text-embedding-3-small
- [ ] Stores chunks with embeddings in documents table
- [ ] Links structured and semantic paths via document_id
- [ ] Creates document_metadata record
- [ ] Updates extraction status to "success" with quality score
- [ ] Handles embedding API failures gracefully (retries, marks as partial)
- [ ] Retention job deletes records after 10 days (configurable)

---

### 3.8 Feature: Result Delivery & Export

**User Story:**
As an API consumer, I want to retrieve extracted data in JSON format so I can integrate financial data into my systems.

As a portal user, I want to download extracted data as CSV so I can analyze it in Excel.

**Functional Requirements:**

**API Endpoint:**
1. Provide GET endpoint `/api/results/{document_id}`
2. Require authentication (organisation API key)
3. Verify organisation owns document (RLS check)
4. Return normalized JSON data from document_rows table
5. Include metadata: extraction timestamp, quality score, document type
6. Return 404 if document not found or expired (retention policy)
7. Return 202 if extraction still processing (with current status)
8. Return 500 if extraction failed (with error message)

**Portal CSV Export:**
1. Provide "Download CSV" button in document history page
2. Generate CSV from normalized JSON (flatten nested structure)
3. Include metadata header row: Company, Document Type, Fiscal Year, Quality Score
4. Separate CSV sheets for Income Statement, Balance Sheet, Cash Flow (ZIP archive)
5. Trigger browser download (Content-Disposition: attachment)
6. CSV format: UTF-8 encoding, comma delimiters, quoted strings

**API Contract:**

Request:
```
GET /api/results/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer {organisation_api_key}
```

Response (Success 200):
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "extraction_timestamp": "2025-12-05T14:30:22Z",
  "quality_score": 95,
  "document_type": "company_accounts",
  "data": {
    "company_name": "NVIDIA Corporation",
    "fiscal_year_end": "2023-01-29",
    "currency": "USD",
    "income_statement": {...},
    "balance_sheet": {...},
    "cash_flow_statement": {...}
  }
}
```

Response (Processing 202):
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "current_stage": "Stage 3/5: Data Extraction",
  "estimated_completion_seconds": 180
}
```

Response (Failed 500):
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failed",
  "error": "No financial tables detected in PDF",
  "support_message": "Please verify this is a financial statement document. Contact support if issue persists."
}
```

Response (Expired 404):
```json
{
  "error": "document_expired",
  "message": "Document data deleted due to 10-day retention policy. Please re-upload and re-extract if needed.",
  "document_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**CSV Export Format:**
```csv
Company,NVIDIA Corporation
Document Type,Company Accounts
Fiscal Year End,2023-01-29
Quality Score,95%
Currency,USD

Income Statement
Metric,2023,2022,2021
Revenue,26974000000,26914000000,16675000000
Cost of Revenue,11618000000,9439000000,6279000000
Gross Profit,15356000000,17475000000,10396000000
...
```

**Edge Cases & Error Handling:**
- Document still processing: Return 202 with current stage and estimated time
- Extraction failed: Return 500 with user-friendly error message
- Document expired: Return 404 with retention policy explanation
- Unauthorized access: Return 401 (organisation does not own document)
- Malformed document_id: Return 400 "Invalid document ID format"
- CSV generation timeout: Return 500 after 60 seconds, log error

**Validation Notes:**
- QA must verify API returns correct status codes (200/202/404/500)
- QA must verify CSV download works in Chrome, Firefox, Safari
- QA must verify CSV UTF-8 encoding (test with £, €, ¥ symbols)
- QA must verify unauthorised access blocked (User A cannot retrieve User B's documents if different orgs)
- Monitor API response times: P95 <1 second for result retrieval

**Acceptance Criteria:**
- [ ] API endpoint returns normalized JSON for valid document_id
- [ ] API returns 202 when extraction still processing
- [ ] API returns 404 when document expired (retention policy)
- [ ] API returns 500 when extraction failed (with error message)
- [ ] CSV export generates valid CSV from normalized JSON
- [ ] CSV includes metadata header (company, type, year, quality)
- [ ] CSV download triggers correctly (no browser errors)
- [ ] UTF-8 encoding preserved in CSV (currency symbols intact)
- [ ] RLS enforced (organisation-scoped access only)

---

### 3.9 Feature: Logging, Metadata Capture & QA Support

**User Story:**
As an engineering team member, I need rich extraction metadata and logs to debug issues, support QA validation, and ensure auditability.

**Functional Requirements:**
1. Capture PDF metadata: File hash (SHA-256), digital signatures, XMP metadata, creation date, modification date
2. Log OCR mismatch details: Pages requiring OCR, OCR confidence scores, fallback triggers
3. Detect embedded JavaScript in PDFs (security concern), log warning
4. Store metadata in `financial_extractions` table as JSONB column
5. Generate structured logs (JSON format) for each extraction stage
6. Log extraction timing: stage start/end timestamps, total duration
7. Provide internal QA API endpoint to retrieve full extraction diagnostics
8. Surface minimal quality flags in portal (e.g., "OCR used on 3 pages")
9. Implement daily rotating log files: `logs/extraction_YYYYMMDD.log`
10. Retain logs for 90 days (configurable)

**Metadata Capture Schema:**
```json
{
  "file_hash_sha256": "a3d5f8...",
  "file_size_bytes": 15728640,
  "pdf_version": "1.7",
  "page_count": 87,
  "creation_date": "2023-10-15T09:23:11Z",
  "modification_date": "2023-10-20T14:45:33Z",
  "digital_signature_present": false,
  "xmp_metadata": {
    "author": "NVIDIA Investor Relations",
    "subject": "Annual Report 2023"
  },
  "embedded_javascript": false,
  "ocr_pages": [12, 45, 67],
  "ocr_confidence_avg": 0.87,
  "extraction_timing": {
    "stage_1_input_discovery_ms": 234,
    "stage_2_table_detection_ms": 45123,
    "stage_3_extraction_ms": 123456,
    "stage_4_normalization_ms": 3421,
    "stage_5_rag_ingestion_ms": 8976,
    "total_duration_ms": 181210
  }
}
```

**Structured Logging Format:**
```json
{
  "timestamp": "2025-12-05T14:23:45.123Z",
  "level": "INFO",
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "organisation_id": "org_abc123",
  "stage": "table_detection",
  "message": "LLMWhisperer detected 3 tables",
  "metadata": {
    "table_types": ["income_statement", "balance_sheet", "cash_flow"],
    "confidence_scores": [0.95, 0.92, 0.88],
    "duration_ms": 45123
  }
}
```

**QA Support Features:**
1. Internal endpoint `/internal/diagnostics/{document_id}` (admin-only access)
2. Returns full extraction logs, intermediate outputs, metadata
3. Portal displays quality flags: "⚠ OCR used on 3 pages", "✓ All tables detected"
4. Error logs include LLM-friendly diagnostic details for troubleshooting
5. Logs stored in searchable format (structured JSON) for future analytics

**Edge Cases & Error Handling:**
- Missing PDF metadata: Log warning, continue extraction (non-blocking)
- Malformed XMP: Log error, store null for XMP fields
- Embedded JavaScript detected: Log security warning, flag for manual review
- Log file rotation failure: Fall back to console logging, alert engineering team
- Log storage saturation: Implement log compression after 7 days, delete after 90 days

**Validation Notes:**
- QA must verify SHA-256 hash matches re-calculated hash (data integrity)
- QA must verify OCR page numbers logged correctly
- QA must verify timing logs sum correctly (stage times ≈ total duration)
- QA must test diagnostics endpoint returns full extraction context
- Monitor log file sizes (alert if daily log >1GB, indicates excessive logging)

**Acceptance Criteria:**
- [ ] Captures PDF metadata (hash, signatures, XMP, dates)
- [ ] Logs OCR details (pages, confidence scores)
- [ ] Detects embedded JavaScript (logs security warning)
- [ ] Stores metadata in financial_extractions.metadata JSONB column
- [ ] Generates structured JSON logs for each stage
- [ ] Logs extraction timing (stage and total duration)
- [ ] Provides internal diagnostics API endpoint (admin-only)
- [ ] Portal displays quality flags (OCR usage indicator)
- [ ] Implements daily rotating log files (logs/extraction_YYYYMMDD.log)
- [ ] Retains logs for 90 days (configurable)

---

### 3.10 Feature: Pilot Administration & Usage Reporting

**User Story:**
As the project owner, I need visibility into pilot usage metrics to evaluate success criteria and commercial potential.

**Functional Requirements:**
1. Store extraction operation records in `transactions` table (reuse existing pattern)
2. Log virtual token usage: 10 tokens per successful extraction
3. Record per-extraction metrics: organisation_id, user_id (nullable), document_id, status, quality_score, duration_ms
4. Provide SQL query templates for common metrics (stored in `sql/reports/` directory)
5. Enable CSV export from Supabase dashboard for success metric reporting
6. Track success metrics defined in blueprint Section 1.3:
   - Metric 1: Count of extractions with quality_score ≥99%
   - Metric 2: Avg extraction duration (for time savings calculation)
   - Metric 3: Count of unique organisations with ≥5 successful extractions
   - Metric 4: Commercial signals tracked manually (out of system scope)
7. No custom reporting dashboard (use Supabase SQL editor + CSV exports)
8. Data retention: Operation logs retained beyond 10-day structured data retention

**Transaction Record Schema:**
```json
{
  "id": "uuid",
  "user_id": "user_uuid",
  "organisation_id": "org_uuid",
  "transaction_type": "extraction",
  "amount": -10,
  "description": "Financial PDF extraction - nvidia_10k_2023.pdf",
  "metadata": {
    "document_id": "550e8400-e29b-41d4-a716-446655440000",
    "extraction_status": "success",
    "quality_score": 95,
    "duration_ms": 181210,
    "document_type": "company_accounts"
  },
  "created_at": "2025-12-05T14:30:22Z"
}
```

**SQL Query Templates (for project owner):**

Success Metric 1:
```sql
-- Extractions with ≥99% accuracy
SELECT COUNT(*) as high_accuracy_count
FROM transactions
WHERE transaction_type = 'extraction'
  AND metadata->>'extraction_status' = 'success'
  AND CAST(metadata->>'quality_score' AS INTEGER) >= 99;
```

Success Metric 2:
```sql
-- Average extraction duration (for time savings calculation)
SELECT AVG(CAST(metadata->>'duration_ms' AS INTEGER)) / 1000.0 as avg_duration_seconds
FROM transactions
WHERE transaction_type = 'extraction'
  AND metadata->>'extraction_status' = 'success';
```

Success Metric 3:
```sql
-- Organisations with ≥5 successful extractions
SELECT organisation_id, COUNT(*) as extraction_count
FROM transactions
WHERE transaction_type = 'extraction'
  AND metadata->>'extraction_status' = 'success'
GROUP BY organisation_id
HAVING COUNT(*) >= 5;
```

**Edge Cases & Error Handling:**
- Partial data due to log rotation: Clearly indicate date ranges in report headers
- Inconsistent clocks: Use database timestamps (UTC) consistently
- Missing metadata fields: Handle null values gracefully in SQL queries
- CSV export limits: Supabase limits to 10,000 rows (document limitation in report instructions)

**Validation Notes:**
- QA must verify transaction records created for each extraction attempt
- QA must verify virtual token usage logged correctly (10 per extraction)
- QA must test SQL query templates return correct results
- Project owner must test CSV export from Supabase dashboard (ensure UTF-8 encoding)

**Acceptance Criteria:**
- [ ] Transaction records created for each extraction (success and failed)
- [ ] Virtual token usage logged (10 tokens per extraction)
- [ ] Metadata includes: document_id, status, quality_score, duration_ms
- [ ] SQL query templates provided in sql/reports/ directory
- [ ] CSV export tested from Supabase dashboard
- [ ] Success metric queries return accurate counts
- [ ] Operation logs retained beyond 10-day structured data retention
- [ ] Report documentation includes date range limitations and CSV export instructions

---

## 4. User Flows & Error Handling

### 4.1 API-Based Ingestion Flow

**Happy Path:**
1. Client sends POST `/api/ingest-pdf` with valid PDF and API key
2. System validates file (size, magic bytes, auth)
3. System returns 202 with document_id
4. System enqueues extraction job (async)
5. Extraction completes within 5 minutes
6. Client polls GET `/api/results/{document_id}` until 200 response
7. Client retrieves normalized JSON data

**Error Path - User Input:**
- Invalid file type → 400 "Invalid PDF file" with actionable guidance
- File too large → 400 "Exceeds 30MB limit. Please split document."
- Missing API key → 401 "Invalid or missing API key. Visit portal settings."
- Invalid document_id format → 400 "Document ID must be valid UUID"

**Error Path - System Failure:**
- Extraction timeout → Status "failed", error "Extraction exceeded 10 minute timeout"
- LLMWhisperer API down → Falls back to pdfplumber, marks extraction with "fallback_used" flag
- No tables detected → Status "failed", error "No financial tables found in PDF"
- Database unavailable → 503 "Service temporarily unavailable. Please retry in 5 minutes."

### 4.2 Portal Upload and Review Flow

**Happy Path:**
1. User logs into portal (email/password)
2. User drags PDF onto upload component
3. System validates file client-side (<30MB, PDF type)
4. Upload progress bar shows percentage
5. Upload completes, redirect to Document History page
6. User sees new document with "Processing" status (blue pulse icon)
7. Real-time update changes status to "Success" with quality score badge (green)
8. User clicks "View Data" → Modal displays HTML table
9. User clicks "Download CSV" → CSV file downloads to browser

**Error Path - User Input:**
- User selects .xlsx file → "Only PDF files supported" toast notification
- User uploads 35MB file → "File must be under 30MB" before upload starts
- User uploads corrupted PDF → Upload succeeds, extraction fails with "Unable to parse PDF"

**Error Path - System Failure:**
- Network disconnects during upload → "Upload failed. Please try again." with retry button
- Server returns 500 → "Processing error. Our team has been notified. Please retry in 5 minutes."
- Extraction fails → Status shows "Failed" (red X), hover shows error: "No financial tables detected"

### 4.3 Result Retrieval Flow

**Happy Path:**
1. User calls GET `/api/results/{document_id}` with API key
2. System verifies organisation owns document (RLS check passes)
3. System retrieves normalized data from document_rows
4. System returns 200 with JSON payload

**Error Path:**
- Document still processing → 202 "Status: processing, Stage 3/5"
- Document expired (>10 days) → 404 "Document data deleted due to retention policy"
- Unauthorized access → 401 "Invalid API key or access denied"
- Extraction failed → 500 with error message and support guidance

---

## 5. Non-Functional Requirements

### 5.1 Performance
- **NFR #1**: API ingestion P95 response time <500ms for requests up to 20MB
- **NFR #2**: 95% of extractions (≤20 pages) complete within 5 minutes end-to-end
- **NFR #3**: One active extraction per organisation_id via in-memory queue

### 5.2 Accuracy & Quality
- **NFR #4**: Achieve ≥99% field-level extraction accuracy on 30 pilot PDFs vs human benchmark

### 5.3 Data Retention & Storage
- **NFR #5**: Structured outputs retained max 10 days; PDFs stored only during processing; metadata retained permanently

### 5.4 Security
- **NFR #6**: All external access over HTTPS with TLS 1.2+; no unauthenticated endpoints
- **NFR #7**: Row-Level Security (RLS) enforced; soft deletes (deleted_at); no cross-org access
- **NFR #8**: All secrets in environment variables or managed secrets store; none in source control

### 5.5 Multi-User Isolation
- **NFR #9**: All data scoped by organisation_id; key tables include nullable user_id for future per-user access control

### 5.6 Structured Storage
- **NFR #10**: Dual-path RAG: normalised rows in document_rows; embeddings in documents; schema supports future modules

### 5.7 Numerical Precision
- **NFR #11**: All financial amounts use decimal/fixed-precision types (Python Decimal, PostgreSQL NUMERIC)

### 5.8 Reliability & Availability
- **NFR #12**: Target 99.0% uptime during UK business hours (08:00-18:00); planned maintenance outside these hours

### 5.9 Observability
- **NFR #13**: Structured logs for each pipeline stage with correlation IDs, timing, error codes
- **NFR #14**: Metrics for PDFs processed, stage timings, success/failure rates, retention deletions

### 5.10 Maintainability & Extensibility
- **NFR #15**: Clear modular boundaries; single engineer understands/extends each module within 1-2 days
- **NFR #16**: Adding new doc types requires changes only to extraction + schema mapping layers (not core ingestion/auth)

### 5.11 Schema Contracts
- **NFR #17**: All inputs/outputs validate against canonical Pydantic schemas per PDF document family

### 5.12 Deployment & Recovery
- **NFR #18**: Automated deployment with rollback capability within 30 minutes; DB backups with ≥7-day point-in-time recovery

### 5.13 Testing
- **NFR #19**: Maintain curated regression-test fixtures (sample PDFs + JSON outputs) stored outside production tables and retention policies

---

## 6. Assumptions & Dependencies

### 6.1 Assumptions
1. **Pilot document supply**: Pilot organisations will provide ≥30 real, varied PDFs early enough to support extraction tuning and QA
2. **Third-party services**: Continued access to Supabase, LLMWhisperer, hosting provider, OpenAI embeddings under current free/low-cost limits
3. **Future feature alignment**: Future modules (AML, credit, projections) will reuse dual-path RAG architecture and normalized schemas
4. **Client integration capability**: Client engineering teams can integrate straightforward API (HTTPS, JSON, API keys) without custom SDKs
5. **Data residency**: UK/EU hosting sufficient; no strict country-specific or on-premises requirement for pilot
6. **Change control**: Material scope/NFR changes managed through explicit change-control process, reflected in PRD updates

### 6.2 Dependencies
1. **LLMWhisperer API**: Primary table extraction service; fallback to pdfplumber if unavailable
2. **Supabase/PostgreSQL**: Database, RLS, real-time subscriptions; free-tier limits may require paid upgrade
3. **OpenAI Embeddings**: text-embedding-3-small for semantic RAG path; rate limits and cost changes monitored
4. **Module01 Pipeline**: Existing 5-stage extraction pipeline adapted for multi-user isolation
5. **Canonical Schemas**: PM team must provide Pydantic schema definitions before Engineering implementation
6. **Pilot User Access**: Pilot organisations must be onboarded with API keys and portal accounts before testing

---

## 7. Success Metrics & Analytics

### 7.1 Functional Success Criteria
- **Criterion 1**: Users can upload PDFs up to 30MB through both API and portal
- **Criterion 2**: Dual RAG ingestion (structured + semantic) completes successfully
- **Criterion 3**: API returns normalized JSON with ≥99% accuracy on pilot PDFs
- **Criterion 4**: Portal displays extraction status with real-time updates
- **Criterion 5**: CSV export delivers valid, UTF-8 encoded files

### 7.2 Performance Success Criteria
- **Criterion 6**: API ingestion response time P95 <500ms
- **Criterion 7**: Extraction pipeline completes within 5 minutes for ≤20 page PDFs (P95)
- **Criterion 8**: Portal loads Document History page within 2 seconds

### 7.3 Quality Success Criteria
- **Criterion 9**: Field-level extraction accuracy ≥99% on 30 pilot PDFs vs human benchmark
- **Criterion 10**: Quality score calculation accurate (100% when all fields present, 66% when cash flow missing)

### 7.4 Business Success Criteria (from Blueprint Section 1.3)
- **Metric 1**: Process ≥30 real-world PDFs with ≥99% accuracy
- **Metric 2**: Reduce average manual processing time per PDF by ≥50%
- **Metric 3**: Onboard ≥2 organisations, each processing ≥5 PDFs
- **Metric 4**: Obtain ≥2 concrete commercial signals (tracked manually, out of system scope)
- **Metric 5**: Architecture supports future modules without re-architecture

### 7.5 Instrumentation for Success Metrics
- **Timing logs**: Extraction start/end timestamps for time-reduction analysis (Success Metric 2)
- **Transaction records**: Operation logs track extraction counts, quality scores, organisations
- **SQL query templates**: Provided in sql/reports/ for project owner to run success metric queries

---

## 8. Validation Notes per Feature

### API Ingestion
- QA must test boundary file sizes: 10MB, 20MB, 29MB, 31MB
- QA must test encrypted PDFs (defer error to extraction stage)
- QA must verify filename collision handling (auto-rename with timestamp)
- Monitor API response time P95 <500ms

### Portal Upload
- QA must test unsupported file types (.xlsx, .docx, .txt)
- QA must test network disconnect during upload
- QA must verify organisation scoping (User A cannot see User B's uploads if different orgs)

### Document History
- QA must verify real-time updates (upload in Tab A, appears in Tab B instantly)
- QA must verify pagination with >25 documents
- QA must test quality score colour coding (≥90% green, 70-89% amber, <70% red)

### Table Detection
- QA must test PDFs with multi-page tables (verify merge logic)
- QA must test PDFs with irregular borders
- QA must test scanned PDFs (verify OCR triggers)

### Extraction Engine
- QA must verify confidence scores align with actual accuracy
- QA must test PDFs with merged cells
- Monitor extraction timing: 95% complete within 5 minutes for ≤20 pages

### Normalization
- QA must test PDFs with non-standard terminology ("Turnover" vs "Revenue")
- QA must test various date formats (UK vs US conventions)
- QA must verify quality score calculation accuracy

### Dual-Path RAG
- QA must verify both document_rows and documents records created
- QA must verify embeddings have correct dimensions (1536)
- QA must test semantic search retrieval

### Result Delivery
- QA must verify correct status codes (200/202/404/500)
- QA must verify CSV UTF-8 encoding (test with £, €, ¥ symbols)
- QA must verify unauthorised access blocked (RLS enforced)

---

## 9. Open Questions for Engineering Team

1. **Hosting Environment Confirmation**: Verify containerised FastAPI service backed by Supabase meets NFR #12 (99% uptime during UK business hours)
2. **LLMWhisperer Integration Pattern**: Confirm wrapping LLMWhisperer behind `ITableDetector` interface allows seamless fallback to pdfplumber
3. **In-Memory Queue Implementation**: Confirm queue state persistence/reconciliation strategy after process restarts (NFR #3, Dependency-Risk #13)
4. **Retention Job Scheduling**: Confirm idempotent scheduled job design for 10-day data deletion (Dependency-Risk #12)
5. **Dual-Path RAG Atomicity**: Confirm atomic ingestion strategy if one path fails (Dependency-Risk #14)
6. **Canonical Schema Evolution**: Confirm schema versioning strategy to support future document types without breaking changes

---

## 10. Next Steps

- [ ] **Client Approval**: Review and approve this PRD
- [ ] **PM Handover**: Conduct PRD walkthrough with Engineering team
- [ ] **Schema Definition**: PM team provides canonical Pydantic schemas for company_accounts and bank_statement document families
- [ ] **Engineering Review**: Engineering team drafts Technical Architecture Document per Blueprint Section 7
- [ ] **Pilot Organisation Onboarding**: PM team coordinates pilot org recruitment and sample PDF collection
- [ ] **Development Kickoff**: Engineering begins implementation once Technical Architecture Document approved

---

**Document Status**: Draft for Client Approval
**Next Review Date**: TBD
**Approval Required From**: Client Product Owner

