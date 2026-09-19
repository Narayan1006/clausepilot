# 03 — Functional Requirements

## FR-01: Document Upload
- Accept PDF file uploads (up to 20 MB)
- Validate file type (MIME + extension)
- Generate UUID-based server filename (never expose user filename as filesystem path)
- Return document ID, page count, and processing status

## FR-02: PDF Text Extraction
- Extract text from PDF using PyMuPDF
- Preserve page boundaries (every chunk/page knows its page number)
- Handle: encrypted PDFs, empty PDFs, scanned PDFs (no text layer), invalid PDFs
- 1-indexed page numbers throughout the system

## FR-03: Document Storage
- Persist document metadata in SQLite
- Persist per-page extracted text
- Support document deletion (cascade all associated data)

## FR-04: Health Endpoint
- `/health` must work without any external service
- Must not require Groq API key, ChromaDB, or embeddings

## FR-05: Chunking (Phase 2)
- Chunk pages into overlapping text segments
- Every chunk preserves: document_id, page_number, chunk_index, text

## FR-06: Embedding & Retrieval (Phase 2)
- Generate vector embeddings per chunk
- Store in ChromaDB
- Retrieve top-K semantically relevant chunks per query

## FR-07: Structured Legal Answers (Phase 2)
- Every LLM answer must return a LegalAnswer schema:
  - answer, status (GROUNDED/INFERRED/NOT_FOUND/CONFLICT), confidence
  - citations (document_id, page_number, clause_number, exact quote)
  - reasoning, missing_information, suggested_questions

## FR-08: Attention Map (Phase 3)
- Categorize clauses by attention level: HIGH / MEDIUM / LOW / MISSING / CONFLICT
- Categories: compensation, notice, termination, IP, non-compete, etc.

## FR-09: Decision Context (Phase 3)
- Accept user decision context ("I'm deciding whether to accept a job offer")
- Use context to prioritize relevant categories in analysis

## FR-10: Question Generation (Phase 3)
- Generate questions for HR / counterparty
- Generate questions for a legal professional
- Ground questions in identified uncertainties

## FR-11: Before You Sign Checklist (Phase 3)
- Generate prioritized action checklist
- Each item linked to source evidence where possible

## FR-12: Document Comparison (Phase 4)
- Accept two documents
- Semantic alignment + clause-level diff
- Display: added, removed, changed, with citations from both documents

## FR-13: Conflict Detection (Phase 4)
- Find semantically related but potentially inconsistent clauses
- Classify: NO_CONFLICT / POSSIBLE_CONFLICT / CLEAR_CONFLICT
- Never present as legal conclusion — use "possible inconsistency"

## FR-14: Security
- No API keys in frontend
- File type + size validation
- UUID-based server filenames
- Prompt injection defense in all LLM calls
- CORS configurable via environment
- Input validation on all endpoints
