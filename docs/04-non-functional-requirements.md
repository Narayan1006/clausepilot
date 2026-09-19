# 04 — Non-Functional Requirements

## Performance
- Document upload + extraction: < 10 seconds for a 20-page PDF
- API response time: < 500ms for metadata endpoints
- LLM response time: < 30 seconds (Groq is fast; acceptable for legal analysis)
- Frontend initial load: < 3 seconds on modern hardware

## Reliability
- Backend must start without external AI services
- Extraction must handle corrupt/scanned PDFs without crashing
- LLM timeouts must be caught and reported clearly

## Security
- Groq API key never exposed to frontend
- User-supplied filenames never used as filesystem paths
- File type and MIME type validated on every upload
- Prompt injection defense on every LLM call
- Document content treated as untrusted input
- CORS origins configurable via environment variable
- No sensitive information in logs

## Scalability (Post-Hackathon)
- SQLite is suitable for MVP; swap for PostgreSQL via same interface
- ChromaDB persists to disk; can be swapped for Pinecone/Weaviate
- Services are stateless; can be containerized and scaled horizontally

## Maintainability
- Clean service boundaries — no business logic in route handlers
- Typed interfaces on all service stubs (Phase 2 slots in cleanly)
- Modular prompts — each task has its own prompt file
- All services and routes have unit or integration tests

## Accessibility
- WCAG 2.1 AA compliance target
- Keyboard navigation for all interactive elements
- Visible focus states
- Sufficient color contrast
- Status indicators not relying on color alone
- Screen-reader-friendly labels and buttons
- Reduced motion support

## Compliance
- No data persistence beyond user session (MVP)
- Legal disclaimer present on all AI output pages
- Clearly labeled as information, not legal advice
- Citations always present when AI makes a claim

## Deployment
- Works locally without any paid cloud service
- Docker Compose for local dev
- Backend: uvicorn (production-ready ASGI server)
- Frontend: Vite dev server (development); Nginx (production)
