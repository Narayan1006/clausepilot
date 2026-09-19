# 05 — System Architecture

## Overview

ClausePilot is a full-stack monorepo with a React frontend and a FastAPI backend. The AI pipeline uses Groq for LLM inference, sentence-transformers for embeddings, and ChromaDB for vector retrieval.

## Architecture Diagram

```mermaid
graph TB
    subgraph "Frontend (React + Vite)"
        LP[Landing Page]
        UP[Upload Page]
        AP[Analysis Page]
        EP[Evidence Page]
        CP[Compare Page]
        QP[Questions Page]
    end

    subgraph "Backend (FastAPI)"
        direction TB
        subgraph "API Layer"
            DR[Documents Router]
            AR[Analysis Router]
            CR[Chat Router]
            CMR[Comparison Router]
        end

        subgraph "Service Layer"
            DS[DocumentService]
            ES[ExtractionService]
            CK[ChunkingService]
            EM[EmbeddingService]
            RT[RetrievalService]
            LLM[LLMService]
            EV[EvidenceService]
            AN[AnalysisService]
            CO[ComparisonService]
            CF[ConflictService]
        end

        subgraph "Data Layer"
            SL[(SQLite DB)]
            UP2[Upload Dir]
            VD[(ChromaDB)]
        end
    end

    subgraph "External Services"
        GQ[Groq API]
        ST[sentence-transformers]
    end

    LP --> UP
    UP --> DR
    AP --> AR
    EP --> CR
    CP --> CMR

    DR --> DS
    DS --> ES
    DS --> SL
    DS --> UP2

    CR --> RT
    RT --> EM
    RT --> VD
    CR --> LLM
    LLM --> GQ
    EM --> ST

    AR --> AN
    AN --> RT
    AN --> LLM
    CMR --> CO
    CO --> CF
```

## Component Responsibilities

| Component | Responsibility |
|---|---|
| `DocumentService` | Upload orchestration, persistence |
| `ExtractionService` | PyMuPDF — PDF text + page extraction |
| `ChunkingService` | Overlapping text chunk creation |
| `EmbeddingService` | sentence-transformers dense vectors |
| `RetrievalService` | ChromaDB semantic search |
| `LLMService` | Groq API structured JSON output |
| `EvidenceService` | Citation validation against stored pages |
| `AnalysisService` | Attention map, obligations, risks |
| `ComparisonService` | Semantic document alignment + diff |
| `ConflictService` | Clause conflict classification |

## Deployment Architecture

```mermaid
graph LR
    Browser -->|HTTP| Nginx
    Nginx -->|/api| FastAPI
    Nginx -->|/| React
    FastAPI --> SQLite
    FastAPI --> ChromaDB
    FastAPI -->|HTTPS| Groq
```
