export interface ExtractedPage {
  page_number: number;
  text: string;
  char_count: number;
}

export interface DocumentUploadResponse {
  document_id: string;
  original_filename: string;
  file_size_bytes: number;
  page_count: number;
  upload_timestamp: string;
  processing_status: string;
  message: string;
  extracted_pages?: ExtractedPage[];
}

export interface Citation {
  document_id: string;
  page_number: number;
  clause_number?: string;
  quote: string;
}

export interface LegalAnswer {
  answer: string | null;
  status: 'GROUNDED' | 'INFERRED' | 'NOT_FOUND' | 'CONFLICT';
  confidence: 'HIGH' | 'MEDIUM' | 'LOW';
  citations: Citation[];
  reasoning: string;
  missing_information: string[];
  suggested_questions: string[];
}

export interface AttentionItem {
  category: string;
  level: 'HIGH' | 'MEDIUM' | 'LOW' | 'MISSING' | 'CONFLICT';
  summary: string;
  clause_ids: string[];
}

export interface AnalysisResponse {
  document_id: string;
  decision_context: string;
  processing_status: string;
  attention_items: AttentionItem[];
  obligations: string[];
  risks: string[];
  missing_information: string[];
  possible_conflicts: string[];
  message: string;
}

export interface ChecklistItem {
  item: string;
  priority: 'HIGH' | 'MEDIUM' | 'LOW';
  clause_reference?: string;
}

export interface ChecklistResponse {
  document_id: string;
  decision_context: string;
  items: ChecklistItem[];
}

export interface SuggestedQuestionsResponse {
  document_id: string;
  decision_context: string;
  questions_for_counterparty: string[];
  questions_for_legal_professional: string[];
  checklist: ChecklistItem[];
}

export interface ComparisonSection {
  topic: string;
  document_a_summary: string | null;
  document_b_summary: string | null;
  difference_type: 'ADDED' | 'REMOVED' | 'CHANGED' | 'SAME';
  citations_a: Citation[];
  citations_b: Citation[];
}

export interface ComparisonResponse {
  document_id_a: string;
  document_id_b: string;
  sections: ComparisonSection[];
  overall_summary: string;
  message: string;
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  phase: string;
  capabilities: {
    document_upload: boolean;
    pdf_extraction: boolean;
    rag_pipeline: boolean;
    llm_analysis: boolean;
    document_comparison: boolean;
  };
}
const isBrowser = typeof window !== 'undefined';
const isVercelOrRemote = isBrowser && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1';

// On Vercel, requests to /health and /api/* are reverse-proxied by vercel.json rewrites directly to Render,
// guaranteeing zero CORS errors. On local dev, use VITE_API_URL or fallback to http://localhost:8000.
const API_BASE_URL = isVercelOrRemote 
  ? '' 
  : (import.meta.env.VITE_API_URL || 'http://localhost:8000');

export async function checkHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE_URL}/health`);
  if (!res.ok) {
    throw new Error(`Health check failed with status ${res.status}`);
  }
  return res.json();
}

export async function uploadDocument(file: File): Promise<DocumentUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE_URL}/api/documents/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Upload failed with status ${res.status}`);
  }

  const uploadResult: DocumentUploadResponse = await res.json();

  const pages: ExtractedPage[] = [];
  for (let i = 1; i <= uploadResult.page_count; i++) {
    try {
      const pageRes = await fetch(`${API_BASE_URL}/api/documents/${uploadResult.document_id}/pages/${i}`);
      if (pageRes.ok) {
        const pageData = await pageRes.json();
        pages.push({
          page_number: pageData.page_number,
          text: pageData.text,
          char_count: pageData.character_count || pageData.text.length,
        });
      }
    } catch {
      // Continue fetching
    }
  }

  uploadResult.extracted_pages = pages;
  return uploadResult;
}

export interface IndexResponse {
  document_id: string;
  chunks_indexed: number;
  message: string;
}

export async function indexDocument(documentId: string): Promise<IndexResponse> {
  const res = await fetch(`${API_BASE_URL}/api/documents/${documentId}/index`, {
    method: 'POST',
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Indexing failed with status ${res.status}`);
  }
  return res.json();
}

export async function askQuestion(
  documentId: string,
  question: string,
  decisionContext?: string
): Promise<LegalAnswer> {
  const res = await fetch(`${API_BASE_URL}/api/documents/${documentId}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, decision_context: decisionContext }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Query failed with status ${res.status}`);
  }
  return res.json();
}

export async function analyzeDocument(
  documentId: string,
  decisionContext?: string
): Promise<AnalysisResponse> {
  const res = await fetch(`${API_BASE_URL}/api/analysis/${documentId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ decision_context: decisionContext || 'General Document Review' }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Analysis failed with status ${res.status}`);
  }
  return res.json();
}

export async function getChecklist(
  documentId: string,
  decisionContext?: string
): Promise<ChecklistResponse> {
  const params = new URLSearchParams({ decision_context: decisionContext || 'General Contract Review' });
  const res = await fetch(`${API_BASE_URL}/api/analysis/${documentId}/checklist?${params.toString()}`);
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Checklist failed with status ${res.status}`);
  }
  return res.json();
}

export async function getSuggestedQuestions(
  documentId: string,
  decisionContext?: string
): Promise<SuggestedQuestionsResponse> {
  const params = new URLSearchParams({ decision_context: decisionContext || 'General Contract Review' });
  const res = await fetch(`${API_BASE_URL}/api/analysis/${documentId}/suggested-questions?${params.toString()}`);
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Question generation failed with status ${res.status}`);
  }
  return res.json();
}

export async function compareDocuments(
  documentIdA: string,
  documentIdB: string,
  focus?: string
): Promise<ComparisonResponse> {
  const res = await fetch(`${API_BASE_URL}/api/comparison`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      document_id_a: documentIdA,
      document_id_b: documentIdB,
      focus: focus || undefined,
    }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Comparison failed with status ${res.status}`);
  }
  return res.json();
}
