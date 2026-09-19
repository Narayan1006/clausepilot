# 14 — API Contract

Full OpenAPI documentation is auto-generated at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Base URL

```
http://localhost:8000
```

## Endpoints

### System

#### GET /health
Returns service health. No external dependencies required.

**Response 200**:
```json
{
  "status": "ok",
  "service": "ClausePilot API",
  "version": "0.1.0",
  "phase": "Phase 1 — Foundation",
  "capabilities": {
    "document_upload": true,
    "pdf_extraction": true,
    "rag_pipeline": false,
    "llm_analysis": false,
    "document_comparison": false
  }
}
```

---

### Documents

#### POST /api/documents/upload
Upload and extract a PDF.

**Request**: `multipart/form-data`
- `file`: PDF file (max 20 MB)

**Response 201**:
```json
{
  "document_id": "uuid",
  "original_filename": "contract.pdf",
  "file_size_bytes": 52000,
  "page_count": 4,
  "upload_timestamp": "2025-03-01T10:00:00Z",
  "processing_status": "extracted",
  "message": "Document uploaded and extracted successfully. 4 pages processed."
}
```

**Errors**:
- `400` — Empty file
- `422` — Invalid file type, invalid MIME, validation error
- `500` — Unexpected server error

---

#### GET /api/documents/{document_id}
Get document metadata.

**Response 200**: `DocumentMetadataResponse`  
**Response 404**: Document not found

---

#### GET /api/documents/{document_id}/pages/{page_number}
Get extracted text for a specific page (1-indexed).

**Response 200**:
```json
{
  "document_id": "uuid",
  "page_number": 2,
  "text": "Clause 6. TERMINATION...",
  "character_count": 842
}
```

**Errors**:
- `404` — Document not found or page out of range
- `422` — page_number < 1

---

#### DELETE /api/documents/{document_id}
Delete document and all associated data.

**Response 200**:
```json
{
  "document_id": "uuid",
  "deleted": true,
  "message": "Document and all associated data deleted."
}
```

---

### Analysis (Phase 2)

- `POST /api/analysis/{document_id}` — Trigger first-pass document audit (Attention Map, Key Obligations, Clarification Areas, Missing Info)
- `GET /api/analysis/{document_id}/checklist` — HTTP 501 (Phase 3)
- `GET /api/analysis/{document_id}/suggested-questions` — HTTP 501 (Phase 3)

---

### Chat & Semantic Search (Phase 2)

- `POST /api/documents/{document_id}/index` — Index document in ChromaDB for semantic search
- `POST /api/documents/{document_id}/ask` — Ask a question (returns validated `LegalAnswer`)
- `POST /api/documents/{document_id}/evidence` — Get retrieved raw evidence chunks with relevance scores

---

### Comparison (Phase 4+)

- `POST /api/comparison` — Compare two documents

---

## LegalAnswer Schema

```typescript
type LegalAnswer = {
  answer: string | null;
  status: "GROUNDED" | "INFERRED" | "NOT_FOUND" | "CONFLICT";
  confidence: "HIGH" | "MEDIUM" | "LOW";
  citations: Citation[];
  reasoning: string;
  missing_information: string[];
  suggested_questions: string[];
};

type Citation = {
  document_id: string;
  page_number: number;
  clause_number?: string;
  quote: string;  // exact verbatim quote, never paraphrased
};
```

## Error Response Format

All errors return:
```json
{
  "detail": "Human-readable error message"
}
```

No stack traces, no internal paths, no schema information in error responses.
