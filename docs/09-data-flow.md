# 09 — Data Flow Diagram

## Level 0 — Context Diagram

```mermaid
graph LR
    U((User)) -->|PDF + Question| CP[ClausePilot]
    CP -->|Grounded Answer + Citations| U
    CP -->|Queries| GQ((Groq API))
    GQ -->|Structured Response| CP
```

## Level 1 — Main Data Flows

```mermaid
flowchart TD
    subgraph "Inputs"
        PDF[PDF Upload]
        Q[User Question]
        DC[Decision Context]
    end

    subgraph "Processing"
        VAL[Validate & Store]
        EXT[Extract Text per Page]
        CHK[Chunk Text]
        EMB[Generate Embeddings]
        IDX[Index in ChromaDB]
        RET[Retrieve Relevant Chunks]
        LLM[LLM via Groq]
        EV[Validate Evidence]
    end

    subgraph "Storage"
        SL[(SQLite: documents, pages)]
        VD[(ChromaDB: vectors)]
        FS[File System: UUID.pdf]
    end

    subgraph "Outputs"
        ANS[LegalAnswer + Status]
        CIT[Citations + Quotes]
        ATM[Attention Map]
        CHE[Checklist]
        SQ[Suggested Questions]
    end

    PDF --> VAL
    VAL --> FS
    VAL --> EXT
    EXT --> SL
    EXT --> CHK
    CHK --> EMB
    EMB --> IDX
    IDX --> VD

    Q --> RET
    DC --> RET
    RET --> VD
    RET --> LLM
    LLM --> EV
    EV --> ANS
    ANS --> CIT
    ANS --> ATM
    ANS --> CHE
    ANS --> SQ
```

## Data States

| State | Description |
|---|---|
| `uploaded` | File received, not yet extracted |
| `extracted` | Text extracted successfully |
| `extracted_no_text` | Scanned PDF — no text layer |
| `indexed` | Chunks embedded and indexed in vector store |
| `error` | Processing failed (message stored) |

## Evidence Grounding States

| Status | Meaning |
|---|---|
| `GROUNDED` | Document directly supports the answer |
| `INFERRED` | Reasonable interpretation from document |
| `NOT_FOUND` | Information absent from document |
| `CONFLICT` | Two sections appear inconsistent |
