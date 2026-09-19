# ClausePilot ⚖️
**Legal Decision & Evidence Workspace**

> *Understand the contract → Verify the evidence → Decide what matters → Compare alternatives.*

---

## 1. Problem
Legal documents (such as employment offers, NDAs, master service agreements, and leases) are notoriously difficult for non-lawyers to understand, compare, and safely navigate. Traditional AI chatbots frequently hallucinate legal conclusions, invent nonexistent clauses, silently resolve contradictory terms, or offer unauthorized legal advice.

## 2. Solution: ClausePilot
ClausePilot is an **evidence-first legal document understanding and decision-support workspace**. Rather than acting as an ungrounded chat assistant, ClausePilot enforces strict architectural boundaries:
* **Evidence Grounding**: Every factual answer is tied to exact, verbatim document quotes with preserved page numbers.
* **Deterministic Verification**: Citations are validated outside the LLM. If a quote is not found in the source text, the status is automatically downgraded from `GROUNDED` to `INFERRED`.
* **Explicit Handling of Unknowns**: When information is absent, the system explicitly returns `NOT_FOUND`, itemizes missing terms, and suggests follow-up questions for HR or counsel rather than guessing.
* **Inconsistency & Conflict Detection**: Conflicting provisions are flagged as `CONFLICT` rather than resolved by the model.
* **Multi-Contract Difference Engine**: Side-by-side comparison identifies differences across contracts categorized as `ADDED`, `REMOVED`, `CHANGED`, or `SAME` with supporting evidence from both sides.
* **Preparation & Action Tooling**: Generates actionable *Before You Sign* checklists and tailored questions for counterparty negotiation or legal counsel.

---

## 3. Core Architecture & Workflow

```text
Uploaded PDF
     ↓
Fast Page Extraction (PyMuPDF with preserved 1-indexed page boundaries)
     ↓
Deterministic Sanitization & SQLite Metadata Store
     ↓
Sentence-Aware Overlapping Chunking
     ↓
ChromaDB Vector Store (Isolated Collections)
     ↓
Semantic Retrieval & Threshold Filtering
     ↓
Groq Structured LLM Reasoning (openai/gpt-oss-120b)
     ↓
Deterministic Outside-the-LLM Evidence Validation
     ↓
Interactive Multi-Tab Workspace
```

---

## 4. Key Differentiators

| Feature | Standard "Chat with PDF" | ClausePilot |
|---|---|---|
| **Grounding** | Probabilistic text generation | Strict schema output (`GROUNDED`, `INFERRED`, `NOT_FOUND`, `CONFLICT`) |
| **Citation Verifiability** | Often hallucinations or missing | Deterministically validated against source page chunks |
| **Missing Information** | Frequently hallucinates terms | Returns `NOT_FOUND` + itemized missing data |
| **Comparison** | Blind text prompt | Retrieval-aware, bounded semantic diff with dual-document citations |
| **Actionability** | Generic summaries | Decision-context checklists & tailored negotiation questions |
| **Legal Safety** | Risks unauthorized legal advice | Decision-support & navigational assistance disclaimer enforced |

---

## 5. Technology Stack

* **Backend**: Python 3.11+, FastAPI, Uvicorn, Pydantic v2
* **Storage & Vectors**: SQLite (metadata & pages), ChromaDB (embeddings)
* **Embeddings & AI**: `sentence-transformers` (`all-MiniLM-L6-v2`) with pure-Python fallback, Groq API (`openai/gpt-oss-120b`)
* **Extraction**: PyMuPDF (`fitz`)
* **Synthetic Data Generation**: ReportLab
* **Frontend**: React 18, TypeScript, Vite, TailwindCSS / Glassmorphism Design System, Lucide Icons

---

## 6. Quickstart Guide

### Prerequisites
* Python 3.11+
* Node.js 18+ and npm
* Groq API Key (`GROQ_API_KEY`)

### Backend Setup
```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Unix/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 7. Demo Walkthrough Flow

1. **Intake & Context Selection**:
   - Upload `sample-documents/employment-contract-a.pdf`.
   - Select Decision Context: *"Accept a job offer"*.
   - Click **Process & Index Document**.
2. **Attention Map & Audit**:
   - Review categorized items: Notice Period, Working Location, Non-Compete, Moonlighting, Compensation.
3. **Evidence Q&A**:
   - Ask: *"What is my notice period?"* → Returns `GROUNDED` answer with exact quote and page reference.
   - Click **View Page →** to jump directly to Page 3 in the document viewer.
4. **Safety & NOT_FOUND Verification**:
   - Ask: *"What happens to my stock options after resignation?"* → Returns `NOT_FOUND`, itemizes missing terms, and suggests targeted follow-up questions.
5. **Before You Sign & Preparation**:
   - Switch to **Before You Sign** tab to inspect actionable items.
   - Switch to **What To Ask Next** tab for counterparty vs. legal professional questions.
6. **Multi-Contract Comparison Engine**:
   - Switch to **Compare Contracts** tab.
   - Upload `sample-documents/employment-contract-b.pdf` as Document B.
   - Click **Run Semantic Diff**.
   - Observe side-by-side section comparisons (`CHANGED` Notice Period: 60d vs 30d, Non-Compete: 12mo vs None, Moonlighting: Allowed vs Approval Required, Compensation: $145k vs $155k) with clickable citations.

---

## 8. Security & Privacy Guarantees

* **Untrusted Document Delimiters**: Document text is wrapped in `<document_evidence>` and `<document_a>` / `<document_b>` tags and treated strictly as data. Instructions within uploaded files cannot override system prompts.
* **UUID Filesystem Isolation**: Files are stored under server-generated UUIDs; user filenames never touch filesystem paths.
* **Zero Secrets in Git**: `GROQ_API_KEY` is loaded strictly server-side and never exposed to the client or logs.
* **Deterministic Guardrails**: Validations for MIME types, file sizes, path traversal, and JSON output schemas.

---

## 9. Verification & Test Suite

Run the full backend test suite:
```bash
cd backend
.venv\Scripts\pytest -v
```
**Results: 79 passed tests** covering security, extraction, RAG pipelines, citation verification, prompt injection defense, and bounded multi-contract comparison.
