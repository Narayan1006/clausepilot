# 12 — Testing

## Test Strategy

| Layer | What is tested |
|---|---|
| Unit — Security | Filename sanitization, UUID generation, type/size validation |
| Unit — Extraction | PDF text extraction, page numbering, error handling, normalization |
| Unit — Schemas | LegalAnswer schema validation, Citation, status enums |
| Integration — API | Upload pipeline, retrieval, deletion, stub endpoints |
| Security — Upload | Path traversal in filename, wrong MIME, oversized, empty file |

## Running Tests

```bash
cd backend
.venv/Scripts/activate   # Windows
# source .venv/bin/activate  # Unix/Mac

python -m pytest tests/ -v
```

## Test Files

| File | Coverage |
|---|---|
| `tests/test_security.py` | Security helpers |
| `tests/test_extraction.py` | ExtractionService |
| `tests/test_schemas.py` | Pydantic schema validation |
| `tests/test_documents_api.py` | Full upload/retrieval/deletion API |

## Phase 2+ Test Plan

### Unit Tests
- ChunkingService: chunk size, overlap, page number preservation
- EmbeddingService: embedding shape, determinism
- RetrievalService: top-K retrieval, empty result handling
- EvidenceService: citation validation, quote verification

### Integration Tests
- Upload → chunk → embed → index → retrieve pipeline
- Question → retrieve → Groq → LegalAnswer pipeline
- Comparison pipeline: two documents → diff

### Security Tests
- Prompt injection document upload
- Groq response with hallucinated page numbers
- Missing GROQ_API_KEY handling

## Test Fixtures

Synthetic PDFs are generated using `reportlab` with deterministic content.
Each fixture has known properties (page count, specific text) that tests can assert against.

No real legal documents are used in tests.
