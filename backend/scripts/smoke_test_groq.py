import os
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from app.core.config import get_settings
from app.services.chunking_service import ChunkingService
from app.services.extraction_service import extract_pdf
from app.services.rag_pipeline import RagPipeline


def smoke_test():
    settings = get_settings()
    print("=== ClausePilot Phase 2 Smoke Test ===")
    print(f"Embedding model: {settings.embedding_model}")
    print(f"Groq model: {settings.groq_model}")
    print(f"GROQ_API_KEY configured: {bool(settings.groq_api_key)}")

    sample_pdf = backend_dir.parent / "sample-documents" / "employment-contract-a.pdf"
    if not sample_pdf.exists():
        print(f"Error: Sample document not found at {sample_pdf}")
        return

    from app.services.document_service import DocumentService
    from app.utils.db import init_db

    init_db()
    doc_service = DocumentService(max_upload_size_bytes=20 * 1024 * 1024)

    print(f"\n1. Uploading & Extracting sample PDF: {sample_pdf.name}")
    upload_res = doc_service.upload_document(
        file_content=sample_pdf.read_bytes(),
        original_filename=sample_pdf.name,
        content_type="application/pdf",
    )
    doc_id = upload_res.document_id
    print(f"   Document registered: ID={doc_id}, Pages={upload_res.page_count}")

    rag = RagPipeline()

    print("\n2. Indexing into ChromaDB...")
    pages = [doc_service.get_page(doc_id, p) for p in range(1, upload_res.page_count + 1)]
    from app.services.extraction_service import DocumentPage
    doc_pages = [DocumentPage(page_number=p.page_number, text=p.text) for p in pages if p]
    indexed_count = rag.index_document(doc_id, doc_pages)
    print(f"   Indexed {indexed_count} chunks.")

    print("\n3. Testing Grounded Question: 'What is my notice period?'")
    ans1 = rag.answer_question(doc_id, "What is my notice period?", decision_context="Job Offer")
    print(f"   Status: {ans1.status}")
    print(f"   Confidence: {ans1.confidence}")
    print(f"   Answer: {ans1.answer}")
    print(f"   Citations: {len(ans1.citations)}")
    for cit in ans1.citations:
        print(f"     - Page {cit.page_number} (Clause {cit.clause_number}): \"{cit.quote[:60]}...\"")

    print("\n4. Testing Absent/Not-Found Question: 'What happens to my stock options after resignation?'")
    ans2 = rag.answer_question(doc_id, "What happens to my stock options after resignation?", decision_context="Job Offer")
    print(f"   Status: {ans2.status}")
    print(f"   Answer: {ans2.answer}")
    print(f"   Missing Information: {ans2.missing_information}")
    print(f"   Suggested Questions: {ans2.suggested_questions}")

    print("\n5. Testing Inconsistent/Conflict Question: 'Can I work remotely or must I be at HQ?'")
    ans3 = rag.answer_question(doc_id, "Can I work remotely or must I work at the office?", decision_context="Job Offer")
    print(f"   Status: {ans3.status}")
    print(f"   Answer: {ans3.answer}")
    print(f"   Citations: {len(ans3.citations)}")

    print("\n=== Smoke test completed successfully ===")


if __name__ == "__main__":
    smoke_test()
