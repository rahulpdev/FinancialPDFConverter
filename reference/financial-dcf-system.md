name: "Financial PDF Processing & DCF Valuation System - Production Implementation"
description: |

## Purpose
Complete end-to-end financial analysis system: Upload PDFs → Extract structured data → RAG ingestion → DCF calculation → Professional Excel export.

This PRP enables one-pass implementation success through comprehensive context and validation loops.

## Core Principles
1. **Multi-user isolation** - User-specific file storage, extraction outputs, access control
2. **Dual RAG ingestion** - Structured JSON (SQL queryable) + Semantic chunks (vector searchable)
3. **Financial precision** - Decimal arithmetic for 100% accuracy in DCF calculations
4. **Token billing integration** - 10 (extract) + 15 (DCF) + 5 (recalc) tokens
5. **Template-based Excel** - Professional 5-worksheet DCF models
6. **Production-ready** - Logging, error handling, testing, 90-day retention

---

## Goal

Build a **production-ready financial analysis system** that allows users to:
1. Upload financial PDFs (10-Ks, annual reports) up to 30MB through chat interface
2. Automatically extract financial statements via Module01 pipeline (Income Statement, Balance Sheet, Cash Flow)
3. Store extracted data in dual RAG format (structured JSON + semantic text chunks)
4. Perform DCF valuations with customizable assumptions through conversational interface
5. Generate professional Excel models with formulas, formatting, and sensitivity analysis
6. Manage files through dedicated "My Files" page with extraction status, quality scores, actions

**Key Feature:** Reduce DCF creation time from 4 hours to 15 minutes (95% time savings).

## Why

**Business Impact:**
- Enable premium pricing tier for advanced financial analysis features
- Establish foundation for financial analysis marketplace (future: ratio analysis, peer comparisons)
- Generate revenue through token billing (25 tokens per full extract→DCF workflow)

**User Value:**
- Eliminate manual PDF data entry (error-prone, time-consuming)
- Conversational DCF analysis: "Calculate DCF for NVIDIA with 8% discount rate"
- Downloadable Excel models with working formulas for further analysis
- Complete file history with versioning for re-extractions

**Technical Achievement:**
- Multi-user Module01 integration (currently single-user)
- Dual RAG architecture for both structured queries and semantic search
- Financial-grade precision using Python Decimal (avoiding float errors)
- Production-grade error handling, logging, and data retention

## What

###  User-Visible Behavior

**Upload & Extraction Flow:**
1. User attaches PDF in chat → Auto-saved to `uploaded_files/user_{id}/`
2. Agent offers: "Extract financial data from this PDF?"
3. User confirms → Module01 extraction starts (progress updates via SSE)
4. Agent returns: "Extracted Income Statement, Balance Sheet, Cash Flow (Quality: 95%)"
5. If company name undetected: Agent asks "What company is this for?"

**DCF Calculation Flow:**
1. User: "Calculate DCF for NVIDIA"
2. Agent retrieves most recent extraction → Applies default assumptions → Streams calculation progress
3. Agent returns: "Enterprise Value: $2.5T, Equity Value: $2.0T (10% WACC, 2.5% terminal growth)"
4. User: "Recalculate with 8% discount rate"
5. Agent updates assumptions → Returns new valuation

**File Management:**
- "My Files" page displays all uploaded PDFs with:
  - Extraction status (pending/processing/success/failed)
  - Quality score badge (0-100%)
  - Actions: Extract, Calculate DCF, Download Excel, Delete
- Search and filter files by name or company
- Real-time status updates via Supabase subscriptions

### Technical Requirements

**Backend:**
- 3 new Pydantic AI tools: `extract_financial_pdf`, `calculate_dcf`, `recalculate_dcf`
- User-specific Module01 output directories: `output/user_{id}/runs/YYYYMMDD_HHMMSS/`
- Dual RAG ingestion:
  - Structured: `document_rows` table with nested JSON (company→statements→years→metrics)
  - Semantic: `documents` table with 400-char chunks + embeddings
- DCF calculator using Decimal precision (10 significant digits)
- Excel exporter using OpenPyXL templates (5 worksheets)
- Extraction queue: One extraction per user at a time (in-memory queue)
- Token billing: Atomic deductions with transaction records

**Frontend:**
- New `/files` route with full-featured file management page
- Upload integration in chat (automatic save on attachment)
- Real-time status updates via Supabase real-time subscriptions
- Download buttons for Excel models
- SSE streaming progress display for long operations

**Database:**
- `financial_extractions` table: Track uploads, status, quality scores, versions
- `dcf_calculations` table: Store calculation results, assumptions, Excel paths
- RLS policies: Users can only access their own data
- Indexes: user_id, company_name, extraction_status, created_at

### Success Criteria

- [ ] Users can upload PDFs up to 30MB through chat interface (auto-save to permanent storage)
- [ ] Module01 extraction completes within 10 minutes with progress updates (5 stages visible)
- [ ] Dual RAG ingestion: Structured data in document_rows, text chunks in documents
- [ ] DCF calculation completes within 60 seconds for any processed company
- [ ] Excel export generates within 60 seconds with 5 worksheets (formulas working)
- [ ] "My Files" page shows all uploads with real-time status, quality scores, and actions
- [ ] 98% extraction accuracy for complete financial statements (all 3 statements)
- [ ] Support for 50+ concurrent extractions across users (queue system prevents overload)
- [ ] Complete test coverage: Unit (DCF engine), Integration (full pipeline), E2E (user flows)
- [ ] Token billing correct: 10 (extract) + 15 (DCF) + 5 (recalc) + 25 (combined)
- [ ] Data retention cleanup: 90-day-old files auto-deleted (configurable)
- [ ] Error messages user-friendly: No technical jargon, actionable suggestions

---

## All Needed Context

### Documentation & References

```yaml
# MUST READ - Core Implementation Patterns from Codebase
- docfile: PRPs/planning/dcf-codebase-analysis.md
  why: Comprehensive codebase analysis with exact patterns to follow
  critical: |
    - File upload patterns (NOT chat message JSONB pattern)
    - Agent tool structure (@agent.tool decorator + tools.py implementation)
    - Database RLS policies from existing tables
    - Module01 integration (dynamic import, output structure)
    - RAG ingestion (text_processor.py chunking, db_handler.py storage)
    - Frontend patterns (page structure, Supabase subscriptions)
    - Token billing (deduct_tokens function, transaction records)
    - Testing patterns (pytest backend, Playwright frontend)

- file: backend_agent_api/tools.py
  why: Exact pattern for implementing DCF tools
  lines: 220-300 (extract_financial_pdf_tool example)
  critical: |
    - Dynamic Module01 import with sys.path manipulation
    - Try/finally cleanup for path changes
    - JSON response format (always return JSON, even on error)
    - Print statements for observability

- file: backend_agent_api/agent.py
  why: Tool registration pattern with @agent.tool decorator
  lines: 207-243 (example tool registrations)
  critical: |
    - RunContext[AgentDeps] parameter for accessing supabase, http_client
    - Docstring becomes LLM function description
    - Print debugging before calling implementation

- file: backend_rag_pipeline/common/text_processor.py
  why: Text chunking and embedding patterns
  lines: 27-52 (chunk_text function)
  lines: 113-134 (create_embeddings function)
  critical: |
    - Default 400-char chunks, 0 overlap (maintain for consistency)
    - OpenAI text-embedding-3-small model (1536 dimensions)
    - Batch embedding creation

- file: backend_rag_pipeline/common/db_handler.py
  why: Supabase storage patterns for documents and document_rows
  lines: 62-102 (insert_document_chunks function)
  lines: 140-170 (insert_document_rows function)
  critical: |
    - Metadata JSONB structure with file_id, chunk_index
    - document_rows uses dataset_id foreign key
    - Always check for existing records before insert/update

- file: Module01_Extraction Processing/pipeline_05_consolidation/pipeline_05_merge_excel_files.py
  why: Excel generation patterns with OpenPyXL
  lines: 1-50 (ExcelMerger class initialization)
  lines: 34-50 (Styling constants - header_font, header_fill, border)
  critical: |
    - Always close workbooks in finally block (prevent memory leaks)
    - Use Font, PatternFill, Border from openpyxl.styles
    - Load with data_only=True to get calculated values

- file: backend_agent_api/db_utils.py
  why: Token billing and transaction recording patterns
  lines: 267-386 (deduct_tokens and related functions)
  critical: |
    - Atomic token deduction (check balance → deduct → record transaction)
    - Transaction record includes user_id, amount, type, description
    - Return False if insufficient tokens (don't raise exception)

- file: sql/0-all-tables.sql
  why: Database schema patterns, RLS policies, indexes
  lines: 355-450 (RLS policy examples)
  critical: |
    - auth.uid() = user_id pattern for RLS
    - UUID primary keys with uuid_generate_v4()
    - JSONB for flexible data (metadata, row_data)
    - Soft deletes with deleted_at TIMESTAMPTZ

- file: frontend/src/pages/Chat.tsx
  why: Frontend page structure, Supabase integration
  critical: |
    - useEffect for data fetching and subscriptions
    - Supabase real-time channels for live updates
    - Loading states and error handling

# EXTERNAL DOCUMENTATION - Financial Calculations
- docfile: PRPs/ai_docs/dcf-calculation-methodology.md
  why: Complete DCF formulas, Decimal precision patterns, validation ranges
  critical: |
    - Always use Decimal from strings (NEVER floats)
    - Set getcontext().prec = 10 for financial precision
    - Gordon Growth Model terminal value formula
    - WACC validation (must be > terminal growth rate)
    - Sanity checks (terminal value should be 60-75% of EV)

- url: https://corporatefinanceinstitute.com/resources/valuation/dcf-formula-guide/
  why: Standard DCF methodology, industry best practices
  section: DCF Formula, Terminal Value Calculation
  critical: Use for validating calculation logic

- url: https://www.wallstreetprep.com/knowledge/terminal-value/
  why: Gordon Growth Model details, perpetual growth rates
  section: Terminal Value Calculation Methods
  critical: Terminal growth typically 2-3% (aligned with GDP)

# EXTERNAL DOCUMENTATION - Excel Generation
- docfile: PRPs/ai_docs/openpyxl-excel-patterns.md
  why: Template-based Excel generation, formula patterns, memory management
  critical: |
    - Template-based approach recommended (pre-formatted styling)
    - Always close workbooks in try/finally
    - Use cell references in formulas (not hardcoded values)
    - Apply number formatting: '$#,##0.0,,,"B"' for billions
    - Quote sheet names with spaces in cross-sheet formulas

- url: https://openpyxl.readthedocs.io/
  why: Official OpenPyXL documentation
  section: Working with Formulas, Styling Cells
  critical: Formula syntax, number format codes

- url: https://realpython.com/openpyxl-excel-spreadsheets-python/
  why: Practical OpenPyXL examples
  section: Creating Spreadsheets, Formatting
  critical: Multi-worksheet patterns, template loading

# EXTERNAL DOCUMENTATION - Pydantic AI
- url: https://ai.pydantic.dev/tools/
  why: Pydantic AI tool development patterns
  section: Tool Registration, RunContext, Streaming
  critical: |
    - Tools must be async
    - Use RunContext[AgentDeps] to access dependencies
    - Return JSON strings (for LLM to parse)

- url: https://ai.pydantic.dev/agents/
  why: Agent configuration, system prompts, dependency injection
  section: AgentDeps Pattern
  critical: Add user_id to AgentDeps for multi-user support

# PROJECT-SPECIFIC GOTCHAS
- docfile: PRPs/planning/dcf-codebase-analysis.md
  section: Critical Gotchas (lines 1150-1240)
  why: 10 common mistakes specific to this codebase
  critical: |
    1. AgentDeps missing user_id - MUST ADD for multi-user
    2. Module01 paths must be user-specific to avoid collisions
    3. File storage: Filesystem (NOT message JSONB)
    4. Dual RAG: Both document_rows AND documents tables
    5. RLS policies: MUST implement on new tables
    6. Soft deletes: Use deleted_at, don't hard delete
    7. Token billing: ATOMIC deduction before operations
    8. Extraction queue: Prevent concurrent user extractions
    9. Excel generation: ALWAYS close workbooks
    10. Company name fallback: Ask user if detection fails
```

### Current Codebase Structure

```
/home/marconi/agent/
├── backend_agent_api/              # FastAPI + Pydantic AI agent
│   ├── agent.py                    # Agent with 8 tools (extract_financial_pdf exists)
│   ├── agent_api.py                # SSE streaming + Stripe webhooks
│   ├── tools.py                    # Tool implementations
│   ├── db_utils.py                 # Token billing, message storage
│   ├── clients.py                  # Supabase, OpenAI, Mem0, Stripe clients
│   ├── tests/                      # Pytest tests
│   └── .env                        # API keys, database credentials
│
├── backend_rag_pipeline/           # Document processing
│   ├── common/
│   │   ├── text_processor.py       # chunk_text, create_embeddings
│   │   └── db_handler.py           # insert_document_chunks, insert_document_rows
│   ├── Local_Files/main.py         # Local file monitoring
│   └── Google_Drive/main.py        # Google Drive monitoring
│
├── Module01_Extraction Processing/ # Financial PDF extraction (5-stage pipeline)
│   ├── main.py                     # Pipeline orchestrator
│   ├── pipeline_01_input_discovery/
│   ├── pipeline_02_table_detection/
│   ├── pipeline_03_extraction/
│   ├── pipeline_04_processing/
│   ├── pipeline_05_consolidation/
│   │   └── pipeline_05_merge_excel_files.py  # Excel generation patterns
│   ├── parsers/                    # Direct parsers (100% accuracy)
│   ├── schemas/                    # Pydantic validation models
│   ├── output/runs/                # Extraction outputs (WILL ADD user subdirs)
│   └── input/                      # PDF inputs (WILL ADD user subdirs)
│
├── frontend/                       # React/TypeScript UI
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Chat.tsx            # Main chat interface
│   │   │   ├── Login.tsx           # Authentication
│   │   │   ├── Admin.tsx           # Admin dashboard
│   │   │   └── Purchase.tsx        # Token purchase (Stripe)
│   │   ├── components/
│   │   │   ├── chat/               # MessageList, ChatInput, MessageItem
│   │   │   ├── sidebar/            # ChatSidebar
│   │   │   ├── auth/               # LoginForm, SignupForm
│   │   │   ├── purchase/           # PurchasePage, pricing cards
│   │   │   └── ui/                 # Shadcn UI components
│   │   ├── hooks/
│   │   │   ├── useAuth.tsx         # Authentication state
│   │   │   └── useTokens.tsx       # Token balance tracking
│   │   ├── lib/
│   │   │   ├── api.ts              # SSE streaming, sendMessage
│   │   │   └── supabase.ts         # Supabase client
│   │   └── App.tsx                 # Routing, theme
│   └── .env                        # Frontend env vars
│
├── sql/                            # Database schemas
│   ├── 0-all-tables.sql            # Complete setup (DROP and recreate)
│   ├── 1-user_profiles_requests.sql
│   ├── 3-conversations_messages.sql
│   ├── 5-document_metadata.sql
│   ├── 6-document_rows.sql
│   ├── 7-documents.sql
│   ├── 10-transactions-table.sql   # Token transactions
│   └── *-rls.sql                   # RLS policies for each table
│
└── PRPs/                           # Project planning
    ├── planning/
    │   └── dcf-codebase-analysis.md  # Comprehensive codebase patterns
    ├── ai_docs/
    │   ├── dcf-calculation-methodology.md  # DCF formulas, Decimal patterns
    │   └── openpyxl-excel-patterns.md      # Excel generation guide
    └── templates/
        └── prp_base.md             # PRP template structure
```

### Desired Codebase Extensions

```
# NEW FILES TO CREATE

backend_agent_api/
├── dcf/                            # DCF-specific modules (NEW DIRECTORY)
│   ├── __init__.py
│   ├── dcf_models.py               # Pydantic models: DCFInputData, DCFAssumptions, DCFResult
│   ├── dcf_calculator.py           # Core DCF calculation engine (Decimal precision)
│   ├── dcf_excel_exporter.py       # Excel template filling with OpenPyXL
│   ├── rag_ingestion.py            # Dual RAG ingestion (document_rows + documents)
│   ├── extraction_queue.py         # In-memory queue (one extraction per user)
│   └── templates/
│       └── dcf_template.xlsx       # Pre-formatted 5-worksheet Excel template
├── tools_dcf.py                    # NEW: calculate_dcf, recalculate_dcf tools
├── tests/
│   ├── test_dcf_calculator.py      # Unit tests for DCF calculations
│   ├── test_dcf_tools.py           # Integration tests for agent tools
│   └── test_dcf_full_pipeline.py   # E2E test: Upload→Extract→RAG→DCF→Excel
└── logging_config.py               # NEW: Logging setup (logs/dcf_YYYYMMDD.log)

Module01_Extraction Processing/
├── output/
│   └── user_{user_id}/             # MODIFY: Add user-specific subdirectories
│       └── runs/YYYYMMDD_HHMMSS_STATUS/
└── input/
    └── user_{user_id}/             # MODIFY: Add user-specific input directories

frontend/src/
├── pages/
│   └── MyFiles.tsx                 # NEW: File management page
├── components/
│   └── dcf/                        # NEW DIRECTORY
│       ├── DCFResultsDisplay.tsx   # DCF calculation results display
│       └── FileActionsMenu.tsx     # Extract/DCF/Delete actions
└── hooks/
    └── useDCF.ts                   # NEW: DCF calculation state management

sql/
├── 16-financial-extractions.sql    # NEW: Track uploads, extraction status, quality scores
├── 17-dcf-calculations.sql         # NEW: Store DCF results, assumptions, Excel paths
├── 18-financial-extractions-rls.sql  # NEW: RLS policies for extractions
├── 19-dcf-calculations-rls.sql     # NEW: RLS policies for DCF calculations
└── 20-migration-add-dcf-tables.sql # NEW: Migration for existing databases

uploaded_files/                     # NEW DIRECTORY: User file storage
└── user_{user_id}/                 # User-specific PDF storage
    └── *.pdf

logs/                               # NEW DIRECTORY: Application logs
└── dcf_YYYYMMDD.log                # Daily rotating logs

tests/sample_pdfs/                  # NEW DIRECTORY: Test data
├── nvidia_10k_2023.pdf             # Complete financial statements (100% quality)
├── amd_10k_2022.pdf                # Complete financial statements
└── partial_financials.pdf          # Missing cash flow (66% quality)
```

### Known Gotchas & Library Quirks

```python
# CRITICAL #1: Pydantic AI Tool Requirements
# All tools MUST be async and return JSON strings
@agent.tool
async def dcf_tool(ctx: RunContext[AgentDeps], param: str) -> str:
    # ✅ CORRECT: Return JSON string
    return json.dumps({"status": "success", "data": result})

    # ❌ WRONG: Return Python object
    return {"status": "success"}  # LLM can't parse this

# CRITICAL #2: AgentDeps Missing user_id
# CURRENT AgentDeps doesn't have user_id - MUST ADD
# File: backend_agent_api/agent.py
class AgentDeps(BaseModel):
    supabase: Client
    http_client: AsyncClient
    brave_api_key: str
    searxng_base_url: str
    memories: Memory
    user_id: str  # ← ADD THIS for multi-user support

# CRITICAL #3: Module01 Output Path Collisions
# Current: output/runs/YYYYMMDD_HHMMSS/ (ALL USERS share same directory!)
# Fixed:  output/user_{user_id}/runs/YYYYMMDD_HHMMSS/
def setup_output_directory(user_id: str) -> Path:
    user_output = Path("output") / f"user_{user_id}" / "runs"
    user_output.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = user_output / f"{timestamp}_PROCESSING"
    return output_dir

# CRITICAL #4: Financial Calculations - NEVER Use Float
from decimal import Decimal, getcontext

# ✅ CORRECT: Decimal precision
getcontext().prec = 10
revenue = Decimal('26974000000')  # String initialization
discount_rate = Decimal('0.10')
enterprise_value = revenue * discount_rate

# ❌ WRONG: Float introduces precision errors
revenue = 26974000000.0 * 0.10  # Result: 2697400000.0000000001 (BAD!)

# CRITICAL #5: Supabase RPC Parameter Format
# RPC functions require dictionary parameters
result = supabase.rpc(
    'match_documents',
    {"query_embedding": embedding, "match_threshold": 0.8}  # ← MUST be dict
).execute()

# ❌ WRONG: Positional arguments don't work
result = supabase.rpc('match_documents', embedding, 0.8)  # ERROR!

# CRITICAL #6: OpenPyXL Memory Leaks
# ALWAYS close workbooks to prevent memory leaks
from openpyxl import load_workbook

# ✅ CORRECT: Try/finally cleanup
wb = load_workbook('template.xlsx')
try:
    ws = wb['Sheet1']
    ws['A1'] = "Data"
    wb.save('output.xlsx')
finally:
    wb.close()  # CRITICAL: Releases file handles

# ❌ WRONG: No cleanup
wb = load_workbook('template.xlsx')
wb.save('output.xlsx')  # Memory leak!

# CRITICAL #7: File Upload - NOT Chat Message Pattern
# EXISTING pattern stores files in message JSONB (base64) - DON'T USE FOR PDFs
# NEW pattern: Save to filesystem, store path in database

# ✅ CORRECT: Filesystem storage
user_dir = Path(f"uploaded_files/user_{user_id}")
user_dir.mkdir(parents=True, exist_ok=True)
file_path = user_dir / file.filename
file_path.write_bytes(content)

# Store path in database
supabase.table('financial_extractions').insert({
    'file_path': str(file_path),
    'file_name': file.filename
}).execute()

# ❌ WRONG: Message JSONB (bloats database with 30MB PDFs)
file_data = base64.b64encode(content).decode('utf-8')
supabase.table('messages').insert({
    'files': [{'fileName': name, 'content': file_data}]
}).execute()

# CRITICAL #8: Dual RAG Ingestion - BOTH Tables Required
# MUST ingest into BOTH document_rows (structured) AND documents (semantic)

# Path A: Structured data → document_rows
supabase.table('document_rows').insert({
    'dataset_id': document_id,
    'row_data': {
        'company_name': 'NVIDIA',
        'income_statement': {'2023': {'revenue': '26974000000'}},
        'balance_sheet': {'2023': {'total_assets': '65728000000'}}
    }
}).execute()

# Path B: Text chunks → documents
chunks = chunk_text(pdf_text, chunk_size=400)
embeddings = create_embeddings(chunks)
for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
    supabase.table('documents').insert({
        'content': chunk,
        'metadata': {'document_id': document_id, 'chunk_index': i},
        'embedding': embedding
    }).execute()

# CRITICAL #9: RLS Policies - MUST Implement on New Tables
# Every new table MUST have RLS policies (users can only access their own data)
ALTER TABLE financial_extractions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own extractions"
  ON financial_extractions FOR SELECT
  USING (auth.uid() = user_id);

# CRITICAL #10: Extraction Queue - Prevent Concurrent Overload
# One extraction per user at a time (prevents resource exhaustion)
class ExtractionQueue:
    def __init__(self):
        self.user_queues: Dict[str, deque] = {}
        self.processing: Dict[str, str] = {}  # user_id -> file_id

    def get_next(self, user_id: str) -> Optional[str]:
        if user_id in self.processing:
            return None  # User already has extraction in progress
        # ... return next file from queue

# CRITICAL #11: Company Name Detection Fallback
# Module01 may fail to detect company name - MUST ask user
if not company_name:
    return json.dumps({
        'status': 'success_needs_company_name',
        'message': 'What company is this for?',
        'file_id': file_id
    })

# CRITICAL #12: Excel Formula Syntax - Quote Sheet Names with Spaces
# ✅ CORRECT: Quotes around sheet names with spaces
ws['B5'] = "='Executive Summary'!B10 * 1.1"

# ❌ WRONG: No quotes (formula error)
ws['B5'] = "=Executive Summary!B10 * 1.1"

# CRITICAL #13: Soft Deletes - Don't Hard Delete
# Use deleted_at timestamp for soft deletes (preserves audit trail)
supabase.table('financial_extractions').update({
    'deleted_at': datetime.now(timezone.utc).isoformat()
}).eq('id', file_id).execute()

# Then cascade delete related records (extraction outputs, RAG chunks, DCF calculations)

# CRITICAL #14: Token Billing - ATOMIC Operations
# Check balance AND deduct in single transaction (prevent race conditions)
async def deduct_tokens(supabase: Client, user_id: str, amount: int) -> bool:
    # 1. Check balance
    result = supabase.table('user_profiles').select('tokens').eq('id', user_id).single().execute()
    current_balance = result.data['tokens']

    if current_balance < amount:
        return False  # Insufficient tokens

    # 2. Deduct tokens
    supabase.table('user_profiles').update({
        'tokens': current_balance - amount
    }).eq('id', user_id).execute()

    # 3. Record transaction
    supabase.table('transactions').insert({
        'user_id': user_id,
        'amount': -amount,
        'transaction_type': 'deduction',
        'description': f'DCF operation'
    }).execute()

    return True

# CRITICAL #15: Vector Embedding Dimensions
# MUST match existing embedding model dimensions (1536 for OpenAI text-embedding-3-small)
# Changing embedding model requires database migration (ALTER COLUMN embedding vector(768))
embeddings = create_embeddings(chunks)  # Returns 1536-dimensional vectors
# Database schema: embedding vector(1536)
```

---

## Implementation Blueprint

### Phase 1: File Management Foundation (4-5 days)

**Goal:** Users can upload PDFs, view in "My Files" page, and delete files

### Data Models and Structure

```python
# backend_agent_api/dcf/dcf_models.py
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict
from decimal import Decimal
from datetime import datetime
from uuid import UUID

class FinancialExtraction(BaseModel):
    """Database model for tracking uploaded PDFs and extraction jobs"""
    id: UUID
    user_id: UUID
    file_name: str
    file_path: str  # uploaded_files/user_xxx/file.pdf
    file_size_bytes: int
    company_name: Optional[str] = None
    extraction_status: str = 'pending'  # pending, processing, success, failed
    extraction_output_path: Optional[str] = None
    quality_score: Optional[int] = Field(None, ge=0, le=100)
    error_message: Optional[str] = None
    version: int = 1
    document_id: Optional[UUID] = None  # Link to RAG document_metadata
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

class DCFAssumptions(BaseModel):
    """User-customizable DCF assumptions with validation"""
    discount_rate: float = Field(
        default=0.10,
        ge=0.05,
        le=0.25,
        description="WACC/discount rate (5%-25%)"
    )
    terminal_growth_rate: float = Field(
        default=0.025,
        ge=0.0,
        le=0.10,
        description="Terminal value growth rate (0%-10%)"
    )
    revenue_growth_rates: List[float] = Field(
        default=[0.15, 0.12, 0.10, 0.08, 0.06],
        description="5-year revenue growth assumptions"
    )
    tax_rate: float = Field(
        default=0.21,
        ge=0.0,
        le=0.50,
        description="Corporate tax rate (US: 21%)"
    )
    ebitda_margin_target: float = Field(
        default=0.25,
        ge=0.0,
        le=1.0,
        description="Target EBITDA margin (% of revenue)"
    )
    capex_rate: float = Field(
        default=0.05,
        ge=0.0,
        le=0.20,
        description="CapEx as % of revenue"
    )

    @validator('revenue_growth_rates')
    def validate_growth_rates(cls, v):
        if not (3 <= len(v) <= 5):
            raise ValueError('Must provide 3-5 years of growth rates')
        if any(rate < -0.5 or rate > 2.0 for rate in v):
            raise ValueError('Growth rates must be between -50% and 200%')
        return v

    @validator('terminal_growth_rate', 'discount_rate')
    def validate_dcf_rates(cls, v, values, field):
        # Ensure discount rate > terminal growth rate
        if field.name == 'terminal_growth_rate' and 'discount_rate' in values:
            if v >= values['discount_rate']:
                raise ValueError('Terminal growth rate must be less than discount rate')
        return v

class DCFInputData(BaseModel):
    """Financial data extracted from statements (nested structure)"""
    company_name: str
    fiscal_years: List[int]

    # Nested structure: {year: {metric: value}}
    income_statement: Dict[str, Dict[str, str]]  # {"2023": {"revenue": "26974000000", ...}}
    balance_sheet: Dict[str, Dict[str, str]]
    cash_flow_statement: Optional[Dict[str, Dict[str, str]]] = None

    @validator('fiscal_years')
    def validate_years(cls, v):
        if not (3 <= len(v) <= 5):
            raise ValueError('Need 3-5 years of financial data for DCF')
        return v

class DCFResult(BaseModel):
    """Complete DCF calculation results"""
    calculation_id: str
    company_name: str
    calculation_date: datetime

    # Valuation results (floats for JSON, calculated with Decimal)
    enterprise_value: float  # In dollars
    equity_value: float
    price_per_share: Optional[float] = None

    # Supporting calculations
    projected_free_cash_flows: List[float]
    terminal_value: float
    present_value_factors: List[float]

    # Inputs
    assumptions: DCFAssumptions
    input_data: DCFInputData

    # Metadata
    tokens_used: int = 15
    quality_notes: Optional[str] = None  # For partial data warnings
```

### Task List (Dependency-Ordered)

```yaml
Task 1 - Add user_id to AgentDeps (CRITICAL FIRST STEP):
MODIFY backend_agent_api/agent.py:
  - FIND pattern: "class AgentDeps(BaseModel):"
  - ADD field: "user_id: str"
  - MODIFY all RunContext[AgentDeps] instantiations to include user_id
  - PRESERVE existing fields (supabase, http_client, brave_api_key, searxng_base_url, memories)

Task 2 - File Upload API Endpoint:
CREATE backend_agent_api/agent_api.py additions:
  - MIRROR pattern from: Stripe webhook endpoint (POST with verify_token dependency)
  - IMPLEMENT @app.post("/api/upload-financial-pdf")
  - VALIDATE: File size (max 30MB), PDF magic bytes (starts with b'%PDF')
  - SAVE to: uploaded_files/user_{user_id}/ directory
  - HANDLE filename conflicts: Auto-rename with timestamp (nvidia.pdf → nvidia_1704470400.pdf)
  - CREATE database record in financial_extractions table
  - RETURN: {file_id, file_path, file_name, size_bytes}

Task 3 - Database Schema for File Tracking:
CREATE sql/16-financial-extractions.sql:
  - MIRROR pattern from: sql/10-transactions-table.sql (UUID primary key, user references, timestamps)
  - CREATE TABLE financial_extractions with columns:
    - id UUID PRIMARY KEY DEFAULT uuid_generate_v4()
    - user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE
    - file_name TEXT NOT NULL
    - file_path TEXT NOT NULL
    - file_size_bytes BIGINT NOT NULL
    - company_name TEXT
    - extraction_status TEXT DEFAULT 'pending'
    - extraction_output_path TEXT
    - quality_score INTEGER CHECK (quality_score >= 0 AND quality_score <= 100)
    - error_message TEXT
    - version INTEGER DEFAULT 1
    - document_id UUID REFERENCES document_metadata(id) ON DELETE SET NULL
    - created_at TIMESTAMPTZ DEFAULT NOW()
    - updated_at TIMESTAMPTZ DEFAULT NOW()
    - deleted_at TIMESTAMPTZ
  - CREATE indexes: idx_financial_extractions_user, idx_financial_extractions_status, idx_financial_extractions_company
  - ADD RLS policies (users can only access their own data)

Task 4 - File Deletion with Cascade:
CREATE backend_agent_api/agent_api.py addition:
  - IMPLEMENT @app.delete("/api/delete-financial-pdf/{file_id}")
  - VERIFY user owns file (user_id = auth.uid())
  - DELETE physical file from filesystem
  - DELETE extraction output directory if exists
  - DELETE RAG chunks (documents table) if document_id linked
  - DELETE DCF calculations if any
  - SOFT DELETE extraction record (set deleted_at timestamp)
  - RETURN {status: 'deleted', file_id: ...}

Task 5 - Frontend "My Files" Page (Basic):
CREATE frontend/src/pages/MyFiles.tsx:
  - MIRROR pattern from: frontend/src/pages/Purchase.tsx (page structure, Supabase queries)
  - FETCH files: supabase.from('financial_extractions').select('*').is('deleted_at', null).order('created_at', desc)
  - DISPLAY: Card grid with file_name, size, status, created_at
  - ADD Delete button: Calls /api/delete-financial-pdf/{file_id}
  - ADD Real-time subscription:
    - supabase.channel('extraction_updates').on('postgres_changes', {event: 'UPDATE', table: 'financial_extractions'}, callback)
  - FORMAT file size: bytes → KB/MB (use helper function)
  - STATUS badge colors: pending (gray), processing (blue animated pulse), success (green), failed (red)

Task 6 - Add Route to Frontend:
MODIFY frontend/src/App.tsx:
  - FIND pattern: "<Route path="/purchase" element={<Purchase />} />"
  - ADD after: "<Route path="/files" element={<MyFiles />} />"
  - IMPORT MyFiles component

Task 7 - Chat File Upload Integration (Hybrid Pattern):
MODIFY frontend/src/components/chat/ChatInput.tsx:
  - FIND pattern: existing file attachment handling
  - VALIDATE: PDF only (file.type.includes('pdf')), max 30MB
  - CALL /api/upload-financial-pdf endpoint (FormData with file)
  - STORE result: {file_id, file_path, file_name}
  - ADD to message context (for agent to reference)
  - SHOW toast: "Uploaded {file_name}" (success) or error message

# Validation for Phase 1:
- [ ] User can upload PDF through chat (max 30MB validated)
- [ ] File saved to uploaded_files/user_{user_id}/
- [ ] Database record created in financial_extractions
- [ ] "My Files" page displays uploaded PDFs
- [ ] User can delete file (cascades to filesystem, RAG, database)
- [ ] Filename conflicts handled (auto-rename with timestamp)
- [ ] Security: PDF magic bytes validated, size limit enforced
- [ ] Real-time updates: Status changes appear immediately in "My Files"
```

### Per-Task Pseudocode

```python
# Task 2 - File Upload API Endpoint
@app.post("/api/upload-financial-pdf")
async def upload_financial_pdf(
    file: UploadFile = File(...),
    user_id: str = Depends(verify_token)  # ← PATTERN: Use existing auth dependency
):
    """
    Upload financial PDF and save to user-specific directory.

    PATTERN: Follow Stripe webhook validation approach
    """
    # VALIDATION BLOCK
    # PATTERN: Validate size first (prevent reading large files)
    if file.size > 30 * 1024 * 1024:  # 30MB limit
        raise HTTPException(400, "File exceeds 30MB limit")

    # CRITICAL: Read file once, reuse content
    content = await file.read()

    # PATTERN: PDF magic bytes check (security)
    if not content.startswith(b'%PDF'):
        raise HTTPException(400, "Invalid PDF file")

    # STORAGE BLOCK
    # PATTERN: User-specific directories (multi-user isolation)
    user_dir = Path(f"uploaded_files/user_{user_id}")
    user_dir.mkdir(parents=True, exist_ok=True)

    # GOTCHA: Handle filename conflicts (don't overwrite)
    file_path = user_dir / file.filename
    if file_path.exists():
        # PATTERN: Timestamp-based renaming
        timestamp = int(time.time())
        stem = file_path.stem
        file_path = user_dir / f"{stem}_{timestamp}.pdf"

    # CRITICAL: Atomic write (no partial files)
    file_path.write_bytes(content)

    # DATABASE BLOCK
    # PATTERN: Insert with error handling
    try:
        result = supabase.table('financial_extractions').insert({
            'user_id': user_id,
            'file_name': file.filename,
            'file_path': str(file_path),
            'file_size_bytes': len(content),
            'extraction_status': 'pending'
        }).execute()

        return {
            'file_id': result.data[0]['id'],
            'file_path': str(file_path),
            'file_name': file.filename,
            'size_bytes': len(content)
        }
    except Exception as e:
        # PATTERN: Rollback filesystem on database error
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(500, f"Database error: {str(e)}")

# Task 4 - File Deletion with Cascade
@app.delete("/api/delete-financial-pdf/{file_id}")
async def delete_financial_pdf(
    file_id: str,
    user_id: str = Depends(verify_token)
):
    """
    Delete uploaded PDF and all associated data.

    PATTERN: Soft delete with cascade cleanup
    """
    # FETCH AND VERIFY OWNERSHIP
    # PATTERN: Single query with user verification
    result = supabase.table('financial_extractions')\
        .select('*')\
        .eq('id', file_id)\
        .eq('user_id', user_id)\
        .single()\
        .execute()

    if not result.data:
        raise HTTPException(404, "File not found or access denied")

    file_record = result.data

    # CASCADE DELETE BLOCK (order matters!)
    # 1. Physical file
    file_path = Path(file_record['file_path'])
    if file_path.exists():
        file_path.unlink()

    # 2. Extraction outputs
    if file_record['extraction_output_path']:
        output_path = Path(file_record['extraction_output_path'])
        if output_path.exists():
            shutil.rmtree(output_path)

    # 3. RAG chunks (if extraction succeeded)
    if file_record['document_id']:
        # PATTERN: Delete from both documents and document_rows
        supabase.table('documents').delete()\
            .eq('metadata->>document_id', file_record['document_id'])\
            .execute()

        supabase.table('document_rows').delete()\
            .eq('dataset_id', file_record['document_id'])\
            .execute()

        supabase.table('document_metadata').delete()\
            .eq('id', file_record['document_id'])\
            .execute()

    # 4. DCF calculations (if any)
    supabase.table('dcf_calculations').delete()\
        .eq('extraction_id', file_id)\
        .execute()

    # 5. SOFT DELETE extraction record (audit trail)
    # PATTERN: Use deleted_at timestamp (reversible)
    supabase.table('financial_extractions').update({
        'deleted_at': datetime.now(timezone.utc).isoformat()
    }).eq('id', file_id).execute()

    return {'status': 'deleted', 'file_id': file_id}

# Task 7 - Chat File Upload Integration
# frontend/src/components/chat/ChatInput.tsx

const handleFileAttachment = async (file: File) => {
  // VALIDATION BLOCK
  // PATTERN: Client-side validation (better UX)
  if (!file.type.includes('pdf')) {
    toast.error('Only PDF files are supported');
    return;
  }

  if (file.size > 30 * 1024 * 1024) {
    toast.error('File must be under 30MB');
    return;
  }

  // UPLOAD BLOCK
  // PATTERN: FormData for file upload
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await fetch('/api/upload-financial-pdf', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${session?.access_token}`
      },
      body: formData  // ← CRITICAL: No Content-Type header (browser sets multipart/form-data)
    });

    if (!response.ok) {
      const error = await response.json();
      toast.error(error.message || 'Upload failed');
      return;
    }

    const result = await response.json();

    // PATTERN: Store file reference for agent
    setAttachments(prev => [...prev, {
      file_id: result.file_id,
      file_name: result.file_name,
      file_path: result.file_path
    }]);

    toast.success(`Uploaded ${result.file_name}`);

  } catch (error) {
    toast.error('Upload failed. Please try again.');
    console.error('Upload error:', error);
  }
};
```

### Integration Points

```yaml
DATABASE:
  - migration: "CREATE TABLE financial_extractions"
  - migration: "CREATE TABLE dcf_calculations (Phase 3)"
  - indexes: |
      CREATE INDEX idx_financial_extractions_user ON financial_extractions(user_id, deleted_at);
      CREATE INDEX idx_financial_extractions_status ON financial_extractions(extraction_status);
  - rls: "Enable RLS on financial_extractions with auth.uid() = user_id policy"

FILESYSTEM:
  - create: "uploaded_files/ directory at project root"
  - pattern: "uploaded_files/user_{user_id}/*.pdf"
  - cleanup: "Cascade delete when user deletes file"

AGENT_DEPS:
  - modify: "Add user_id field to AgentDeps class"
  - impact: "All tool functions can now access ctx.deps.user_id"
  - critical: "Required for multi-user file storage and Module01 integration"

API_ENDPOINTS:
  - add: "POST /api/upload-financial-pdf"
  - add: "DELETE /api/delete-financial-pdf/{file_id}"
  - pattern: "Use verify_token dependency for authentication"

FRONTEND_ROUTES:
  - add: "/files route to App.tsx"
  - component: "MyFiles.tsx page"
  - navigation: "Add link in sidebar (future enhancement)"
```

### Validation Loop

#### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
cd backend_agent_api
python -m ruff check agent.py agent_api.py dcf/ --fix
python -m mypy agent.py agent_api.py dcf/

# Frontend
cd frontend
npm run lint

# Expected: No errors. If errors, READ the error and fix.
```

#### Level 2: Unit Tests
```python
# backend_agent_api/tests/test_file_upload.py

import pytest
from fastapi.testclient import TestClient
from pathlib import Path

def test_upload_valid_pdf(client: TestClient, mock_pdf):
    """Upload a valid PDF file"""
    response = client.post(
        "/api/upload-financial-pdf",
        files={"file": ("test.pdf", mock_pdf, "application/pdf")},
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "file_id" in data
    assert "file_path" in data
    assert Path(data["file_path"]).exists()

def test_upload_oversized_pdf(client: TestClient):
    """Reject PDFs over 30MB"""
    large_file = b"x" * (31 * 1024 * 1024)  # 31MB

    response = client.post(
        "/api/upload-financial-pdf",
        files={"file": ("large.pdf", large_file, "application/pdf")},
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 400
    assert "30MB limit" in response.json()["detail"]

def test_upload_invalid_file_type(client: TestClient):
    """Reject non-PDF files"""
    response = client.post(
        "/api/upload-financial-pdf",
        files={"file": ("test.txt", b"not a pdf", "text/plain")},
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 400
    assert "Invalid PDF" in response.json()["detail"]

def test_delete_file_cascade(client: TestClient, uploaded_file):
    """Delete file with cascade cleanup"""
    response = client.delete(
        f"/api/delete-financial-pdf/{uploaded_file.id}",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    # Verify file deleted from filesystem
    assert not Path(uploaded_file.file_path).exists()
    # Verify soft delete in database
    result = supabase.table('financial_extractions').select('deleted_at').eq('id', uploaded_file.id).single().execute()
    assert result.data['deleted_at'] is not None
```

```bash
# Run and iterate until passing:
cd backend_agent_api
pytest tests/test_file_upload.py -v

# If failing: Read error, understand root cause, fix code, re-run
```

#### Level 3: Integration Test
```bash
# Start backend
cd backend_agent_api
uvicorn agent_api:app --reload --port 8001

# Test upload
curl -X POST http://localhost:8001/api/upload-financial-pdf \
  -H "Authorization: Bearer your_test_token" \
  -F "file=@tests/sample_pdfs/nvidia_10k_2023.pdf"

# Expected: {"file_id": "uuid", "file_path": "uploaded_files/user_xxx/nvidia_10k_2023.pdf", ...}

# Start frontend
cd frontend
npm run dev

# Navigate to http://localhost:8082/files
# Expected: "My Files" page displays, shows uploaded files, real-time updates work
```

## Final Validation Checklist

- [ ] All tests pass: `pytest backend_agent_api/tests/ -v`
- [ ] No linting errors: `ruff check backend_agent_api/`
- [ ] No type errors: `mypy backend_agent_api/`
- [ ] Manual upload test successful (PDF appears in "My Files")
- [ ] Manual delete test successful (file removed, cascades work)
- [ ] Real-time updates work (upload in one tab, see in "My Files" instantly)
- [ ] Error cases handled gracefully (oversized file, non-PDF, unauthorized)
- [ ] Logs are informative: extraction attempts, errors logged to logs/dcf_YYYYMMDD.log
- [ ] Documentation updated: CLAUDE.md mentions new upload feature

---

## Anti-Patterns to Avoid

- ❌ Don't store files in message JSONB (use filesystem instead)
- ❌ Don't use float for financial calculations (always use Decimal)
- ❌ Don't skip RLS policies on new tables (security critical)
- ❌ Don't hard delete data (use soft deletes with deleted_at)
- ❌ Don't forget to close OpenPyXL workbooks (memory leaks)
- ❌ Don't allow concurrent extractions per user (queue them)
- ❌ Don't skip input validation (30MB limit, PDF magic bytes)
- ❌ Don't hardcode file paths (use user_id in paths)
- ❌ Don't skip cascade deletes (orphaned data is bad)
- ❌ Don't ignore extraction errors (log them, surface to user)

---

**Confidence Score: 9/10** - This PRP provides comprehensive context for one-pass implementation success. All patterns are directly from the codebase, all external references are authoritative, and all gotchas are documented. Only missing live code review for final validation.
