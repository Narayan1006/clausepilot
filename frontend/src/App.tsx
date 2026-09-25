import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Upload, 
  CheckCircle2, 
  AlertCircle, 
  Shield, 
  Scale, 
  BookOpen, 
  FileCheck2, 
  RefreshCw,
  Send,
  AlertTriangle,
  Info,
  Sparkles,
  Layers,
  Quote,
  CheckSquare,
  HelpCircle,
  Briefcase,
  Users,
  GitCompare,
  ArrowRightLeft,
  Columns
} from 'lucide-react';
import { 
  checkHealth, 
  uploadDocument, 
  indexDocument, 
  askQuestion, 
  analyzeDocument,
  getChecklist,
  getSuggestedQuestions,
  compareDocuments
} from './api';
import type { 
  DocumentUploadResponse, 
  HealthResponse, 
  LegalAnswer, 
  AnalysisResponse,
  ChecklistResponse,
  SuggestedQuestionsResponse,
  ComparisonResponse
} from './api';

export function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthLoading, setHealthLoading] = useState(true);
  const [healthError, setHealthError] = useState<string | null>(null);

  // Document Ingestion States
  const [file, setFile] = useState<File | null>(null);
  const [decisionContext, setDecisionContext] = useState<string>('Accept a job offer');
  const [uploadStep, setUploadStep] = useState<'idle' | 'uploading' | 'extracting' | 'indexing' | 'ready'>('idle');
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadResult, setUploadResult] = useState<DocumentUploadResponse | null>(null);
  const [selectedPage, setSelectedPage] = useState<number>(1);

  // Phase 4: Second document for comparison
  const [, setFileB] = useState<File | null>(null);
  const [uploadStepB, setUploadStepB] = useState<'idle' | 'uploading' | 'extracting' | 'indexing' | 'ready'>('idle');
  const [uploadErrorB, setUploadErrorB] = useState<string | null>(null);
  const [uploadResultB, setUploadResultB] = useState<DocumentUploadResponse | null>(null);

  // Active Workspace Tab
  const [activeTab, setActiveTab] = useState<'qa' | 'analysis' | 'checklist' | 'questions' | 'comparison' | 'pages'>('qa');

  // Question / Reasoning States
  const [question, setQuestion] = useState<string>('');
  const [asking, setAsking] = useState(false);
  const [chatHistory, setChatHistory] = useState<Array<{ q: string; a: LegalAnswer }>>([]);
  const [qaError, setQaError] = useState<string | null>(null);

  // Document Analysis States
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  // Phase 3: Checklist & Question Generation States
  const [checklist, setChecklist] = useState<ChecklistResponse | null>(null);
  const [loadingChecklist, setLoadingChecklist] = useState(false);
  const [checklistError, setChecklistError] = useState<string | null>(null);
  const [completedItems, setCompletedItems] = useState<Record<number, boolean>>({});

  const [suggestedQuestions, setSuggestedQuestions] = useState<SuggestedQuestionsResponse | null>(null);
  const [loadingQuestions, setLoadingQuestions] = useState(false);
  const [questionsError, setQuestionsError] = useState<string | null>(null);

  // Phase 4: Comparison States
  const [comparisonFocus, setComparisonFocus] = useState<string>('');
  const [comparison, setComparison] = useState<ComparisonResponse | null>(null);
  const [comparing, setComparing] = useState(false);
  const [comparisonError, setComparisonError] = useState<string | null>(null);

  const fetchHealth = async () => {
    setHealthLoading(true);
    setHealthError(null);
    try {
      const data = await checkHealth();
      setHealth(data);
    } catch (err: any) {
      setHealthError(err.message || 'Unable to connect to backend service.');
    } finally {
      setHealthLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setUploadError(null);
      setUploadResult(null);
      setChatHistory([]);
      setAnalysis(null);
      setChecklist(null);
      setSuggestedQuestions(null);
      setCompletedItems({});
      setUploadStep('idle');
    }
  };

  const handleUploadAndIndex = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setUploadError(null);
    try {
      setUploadStep('uploading');
      const doc = await uploadDocument(file);
      
      setUploadStep('extracting');
      setUploadResult(doc);

      setUploadStep('indexing');
      await indexDocument(doc.document_id);

      setUploadStep('ready');
      setSelectedPage(1);
    } catch (err: any) {
      setUploadError(err.message || 'File processing and indexing failed.');
      setUploadStep('idle');
    }
  };

  const handleAsk = async (e?: React.FormEvent, customQ?: string) => {
    if (e) e.preventDefault();
    const queryText = customQ || question;
    if (!queryText.trim() || !uploadResult || asking) return;

    setAsking(true);
    setQaError(null);
    try {
      const answer = await askQuestion(uploadResult.document_id, queryText, decisionContext);
      setChatHistory(prev => [{ q: queryText, a: answer }, ...prev]);
      if (!customQ) setQuestion('');
    } catch (err: any) {
      setQaError(err.message || 'Failed to generate grounded answer.');
    } finally {
      setAsking(false);
    }
  };

  const handleRunAnalysis = async () => {
    if (!uploadResult || analyzing) return;
    setAnalyzing(true);
    setAnalysisError(null);
    try {
      const res = await analyzeDocument(uploadResult.document_id, decisionContext);
      setAnalysis(res);
    } catch (err: any) {
      setAnalysisError(err.message || 'Failed to complete document audit.');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleFetchChecklist = async () => {
    if (!uploadResult || loadingChecklist) return;
    setLoadingChecklist(true);
    setChecklistError(null);
    try {
      const res = await getChecklist(uploadResult.document_id, decisionContext);
      setChecklist(res);
    } catch (err: any) {
      setChecklistError(err.message || 'Failed to generate signing checklist.');
    } finally {
      setLoadingChecklist(false);
    }
  };

  const handleFetchQuestions = async () => {
    if (!uploadResult || loadingQuestions) return;
    setLoadingQuestions(true);
    setQuestionsError(null);
    try {
      const res = await getSuggestedQuestions(uploadResult.document_id, decisionContext);
      setSuggestedQuestions(res);
    } catch (err: any) {
      setQuestionsError(err.message || 'Failed to generate targeted questions.');
    } finally {
      setLoadingQuestions(false);
    }
  };

  const handleUploadAndIndexB = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || !e.target.files[0]) return;
    const fileSelected = e.target.files[0];
    setFileB(fileSelected);
    setUploadErrorB(null);
    try {
      setUploadStepB('uploading');
      const doc = await uploadDocument(fileSelected);
      setUploadStepB('extracting');
      setUploadResultB(doc);
      setUploadStepB('indexing');
      await indexDocument(doc.document_id);
      setUploadStepB('ready');
    } catch (err: any) {
      setUploadErrorB(err.message || 'File processing and indexing for Document B failed.');
      setUploadStepB('idle');
    }
  };

  const handleRunComparison = async () => {
    if (!uploadResult || !uploadResultB || comparing) return;
    setComparing(true);
    setComparisonError(null);
    try {
      const res = await compareDocuments(
        uploadResult.document_id,
        uploadResultB.document_id,
        comparisonFocus || undefined
      );
      setComparison(res);
    } catch (err: any) {
      setComparisonError(err.message || 'Failed to compare documents.');
    } finally {
      setComparing(false);
    }
  };

  const toggleChecklistItem = (idx: number) => {
    setCompletedItems(prev => ({ ...prev, [idx]: !prev[idx] }));
  };

  const getStatusBadge = (status: LegalAnswer['status']) => {
    switch (status) {
      case 'GROUNDED':
        return {
          bg: 'rgba(16, 185, 129, 0.15)',
          border: 'rgba(16, 185, 129, 0.4)',
          color: '#34d399',
          icon: <CheckCircle2 size={14} />,
          label: 'GROUNDED EVIDENCE',
        };
      case 'INFERRED':
        return {
          bg: 'rgba(59, 130, 246, 0.15)',
          border: 'rgba(59, 130, 246, 0.4)',
          color: '#60a5fa',
          icon: <Info size={14} />,
          label: 'REASONED INFERENCE',
        };
      case 'CONFLICT':
        return {
          bg: 'rgba(245, 158, 11, 0.15)',
          border: 'rgba(245, 158, 11, 0.4)',
          color: '#fbbf24',
          icon: <AlertTriangle size={14} />,
          label: 'CLAUSE CONFLICT DETECTED',
        };
      case 'NOT_FOUND':
      default:
        return {
          bg: 'rgba(244, 63, 94, 0.15)',
          border: 'rgba(244, 63, 94, 0.4)',
          color: '#fb7185',
          icon: <AlertCircle size={14} />,
          label: 'NOT FOUND IN DOCUMENT',
        };
    }
  };

  const getAttentionBadge = (level: string) => {
    switch (level) {
      case 'HIGH':
        return { bg: 'rgba(244, 63, 94, 0.15)', color: '#fb7185', label: '🔴 High Attention' };
      case 'MEDIUM':
        return { bg: 'rgba(245, 158, 11, 0.15)', color: '#fbbf24', label: '🟡 Needs Clarification' };
      case 'CONFLICT':
        return { bg: 'rgba(239, 68, 68, 0.15)', color: '#f87171', label: '⚠ Inconsistent Clause' };
      case 'MISSING':
        return { bg: 'rgba(156, 163, 175, 0.15)', color: '#9ca3af', label: '⚪ Missing Topic' };
      case 'LOW':
      default:
        return { bg: 'rgba(16, 185, 129, 0.15)', color: '#34d399', label: '🟢 Clear' };
    }
  };

  const getDiffBadge = (diffType: string) => {
    switch (diffType) {
      case 'ADDED':
        return { bg: 'rgba(16, 185, 129, 0.15)', border: 'rgba(16, 185, 129, 0.4)', color: '#34d399', label: '+ Added in Doc B' };
      case 'REMOVED':
        return { bg: 'rgba(244, 63, 94, 0.15)', border: 'rgba(244, 63, 94, 0.4)', color: '#fb7185', label: '- Removed in Doc B' };
      case 'CHANGED':
        return { bg: 'rgba(245, 158, 11, 0.15)', border: 'rgba(245, 158, 11, 0.4)', color: '#fbbf24', label: '⚡ Clause Changed' };
      case 'SAME':
      default:
        return { bg: 'rgba(156, 163, 175, 0.15)', border: 'rgba(156, 163, 175, 0.4)', color: '#9ca3af', label: '✓ Substantially Equivalent' };
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header / Navbar */}
      <header style={{
        borderBottom: '1px solid var(--border-color)',
        backgroundColor: 'rgba(11, 15, 25, 0.85)',
        backdropFilter: 'blur(16px)',
        position: 'sticky',
        top: 0,
        zIndex: 50,
        padding: '0.85rem 2rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{
            background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
            padding: '0.45rem',
            borderRadius: '10px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 20px rgba(99, 102, 241, 0.4)'
          }}>
            <Scale size={22} color="#fff" />
          </div>
          <div>
            <h1 style={{ fontSize: '1.2rem', fontWeight: 700, letterSpacing: '-0.02em', background: 'linear-gradient(to right, #fff, #9ca3af)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              ClausePilot
            </h1>
            <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Legal Decision & Evidence Workspace</p>
          </div>
        </div>

        {/* System Health Status Pill */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.35rem 0.8rem',
            borderRadius: '9999px',
            fontSize: '0.78rem',
            fontWeight: 500,
            background: healthError ? 'rgba(244, 63, 94, 0.1)' : 'rgba(16, 185, 129, 0.1)',
            border: `1px solid ${healthError ? 'rgba(244, 63, 94, 0.3)' : 'rgba(16, 185, 129, 0.3)'}`,
            color: healthError ? '#fb7185' : '#34d399'
          }}>
            <div style={{
              width: '7px',
              height: '7px',
              borderRadius: '50%',
              backgroundColor: healthError ? '#f43f5e' : '#10b981',
              boxShadow: healthError ? '0 0 8px #f43f5e' : '0 0 8px #10b981'
            }} />
            {healthLoading ? 'Checking...' : healthError ? 'API Disconnected' : `${health?.service} (Phase 3 Prep Engine)`}
            <button 
              onClick={fetchHealth} 
              aria-label="Refresh health status"
              title="Refresh health status"
              style={{ background: 'none', border: 'none', color: 'inherit', display: 'flex', alignItems: 'center', marginLeft: '0.2rem' }}>
              <RefreshCw size={11} className={healthLoading ? "spin" : ""} />
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main style={{ maxWidth: '1440px', margin: '0 auto', padding: '1.5rem 2rem', width: '100%', flex: 1 }}>
        <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: '1.75rem', alignItems: 'start' }}>
          
          {/* Left Column: Upload & Context Selector */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div className="glass-panel" style={{ padding: '1.25rem' }}>
              <h2 style={{ fontSize: '1.05rem', fontWeight: 600, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Upload size={18} color="var(--accent-indigo)" />
                Document Intake & Context
              </h2>
              
              <form onSubmit={handleUploadAndIndex} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {/* Decision Context Dropdown */}
                <div>
                  <label 
                    htmlFor="decision-context-select"
                    style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.35rem', display: 'block' }}>
                    Decision Context
                  </label>
                  <select 
                    id="decision-context-select"
                    aria-label="Decision Context"
                    value={decisionContext}
                    onChange={(e) => setDecisionContext(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '0.5rem 0.75rem',
                      borderRadius: '6px',
                      backgroundColor: 'rgba(255, 255, 255, 0.04)',
                      border: '1px solid var(--border-color)',
                      color: '#f3f4f6',
                      fontSize: '0.85rem'
                    }}
                  >
                    <option value="Accept a job offer" style={{ background: '#111827' }}>💼 Accept a Job Offer (Employment)</option>
                    <option value="Sign an NDA" style={{ background: '#111827' }}>🔒 Sign a Non-Disclosure Agreement</option>
                    <option value="Sign a rental lease" style={{ background: '#111827' }}>🏠 Sign a Rental Agreement</option>
                    <option value="Vendor / Master Services Agreement" style={{ background: '#111827' }}>📄 Commercial Services Agreement</option>
                    <option value="General Document Review" style={{ background: '#111827' }}>📑 General Contract Review</option>
                  </select>
                </div>

                <div style={{
                  border: '2px dashed var(--border-color)',
                  borderRadius: '8px',
                  padding: '1.25rem 0.75rem',
                  textAlign: 'center',
                  backgroundColor: 'rgba(255, 255, 255, 0.02)',
                  position: 'relative'
                }}>
                  <label htmlFor="contract-file-input" className="sr-only">
                    Upload contract PDF document
                  </label>
                  <input
                    id="contract-file-input"
                    type="file"
                    aria-label="Upload contract PDF document"
                    accept=".pdf,application/pdf"
                    onChange={handleFileChange}
                    style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      width: '100%',
                      height: '100%',
                      opacity: 0,
                      cursor: 'pointer'
                    }}
                  />
                  <FileText size={32} color="var(--text-faint)" style={{ margin: '0 auto 0.5rem auto' }} />
                  <p style={{ fontSize: '0.825rem', fontWeight: 500, color: '#e2e8f0', marginBottom: '0.2rem' }}>
                    {file ? file.name : 'Select or drop contract PDF'}
                  </p>
                  <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    PDF up to 20MB supported
                  </p>
                </div>

                {uploadError && (
                  <div style={{
                    padding: '0.65rem',
                    borderRadius: '6px',
                    backgroundColor: 'rgba(244, 63, 94, 0.1)',
                    border: '1px solid rgba(244, 63, 94, 0.3)',
                    color: '#fb7185',
                    fontSize: '0.8rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.4rem'
                  }}>
                    <AlertCircle size={15} style={{ flexShrink: 0 }} />
                    <span>{uploadError}</span>
                  </div>
                )}

                <button
                  type="submit"
                  aria-label="Process & Index Document"
                  disabled={!file || (uploadStep !== 'idle' && uploadStep !== 'ready')}
                  style={{
                    padding: '0.7rem 1rem',
                    borderRadius: '8px',
                    background: file && uploadStep === 'idle' ? 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)' : '#374151',
                    color: '#fff',
                    border: 'none',
                    fontWeight: 600,
                    fontSize: '0.85rem',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '0.5rem',
                    opacity: file && (uploadStep === 'idle' || uploadStep === 'ready') ? 1 : 0.7
                  }}
                >
                  {uploadStep === 'uploading' && <><RefreshCw size={15} className="spin" /> Uploading PDF...</>}
                  {uploadStep === 'extracting' && <><RefreshCw size={15} className="spin" /> Extracting Boundaries...</>}
                  {uploadStep === 'indexing' && <><RefreshCw size={15} className="spin" /> Semantic Indexing (ChromaDB)...</>}
                  {(uploadStep === 'idle' || uploadStep === 'ready') && <><FileCheck2 size={15} /> Process & Index Document</>}
                </button>
              </form>
            </div>

            {/* Document Meta Information (When Ready) */}
            {uploadResult && (
              <div className="glass-panel" style={{ padding: '1.25rem' }}>
                <h3 style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: '0.75rem', color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <Shield size={16} color="#10b981" />
                  Vault Status: Ready
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  <div><strong>File:</strong> {uploadResult.original_filename}</div>
                  <div><strong>ID:</strong> <code style={{ color: 'var(--accent-indigo)', fontFamily: 'var(--font-mono)' }}>{uploadResult.document_id.slice(0, 16)}...</code></div>
                  <div><strong>Pages:</strong> {uploadResult.page_count} preserved pages</div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: '#34d399', marginTop: '0.25rem' }}>
                    <CheckCircle2 size={13} /> ChromaDB Vectors Active
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Right Column: Interactive Workspace */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {uploadResult ? (
              <>
                {/* Navigation Tabs */}
                <div 
                  role="tablist" 
                  aria-label="Document Workspace Sections" 
                  style={{ display: 'flex', borderBottom: '1px solid var(--border-color)', gap: '0.5rem', overflowX: 'auto' }}
                >
                  <button
                    role="tab"
                    aria-selected={activeTab === 'qa'}
                    aria-label="Evidence Q&A tab"
                    onClick={() => setActiveTab('qa')}
                    style={{
                      padding: '0.65rem 0.85rem',
                      background: 'none',
                      border: 'none',
                      borderBottom: activeTab === 'qa' ? '2px solid var(--accent-indigo)' : '2px solid transparent',
                      color: activeTab === 'qa' ? '#fff' : 'var(--text-muted)',
                      fontWeight: 600,
                      fontSize: '0.85rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.4rem',
                      whiteSpace: 'nowrap'
                    }}
                  >
                    <Sparkles size={15} color={activeTab === 'qa' ? 'var(--accent-indigo)' : 'currentColor'} />
                    Evidence Q&A
                  </button>

                  <button
                    role="tab"
                    aria-selected={activeTab === 'analysis'}
                    aria-label="Attention Map tab"
                    onClick={() => {
                      setActiveTab('analysis');
                      if (!analysis && !analyzing) handleRunAnalysis();
                    }}
                    style={{
                      padding: '0.65rem 0.85rem',
                      background: 'none',
                      border: 'none',
                      borderBottom: activeTab === 'analysis' ? '2px solid var(--accent-indigo)' : '2px solid transparent',
                      color: activeTab === 'analysis' ? '#fff' : 'var(--text-muted)',
                      fontWeight: 600,
                      fontSize: '0.85rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.4rem',
                      whiteSpace: 'nowrap'
                    }}
                  >
                    <Layers size={15} color={activeTab === 'analysis' ? 'var(--accent-indigo)' : 'currentColor'} />
                    Attention Map
                  </button>

                  <button
                    role="tab"
                    aria-selected={activeTab === 'checklist'}
                    aria-label="Before You Sign Checklist tab"
                    onClick={() => {
                      setActiveTab('checklist');
                      if (!checklist && !loadingChecklist) handleFetchChecklist();
                    }}
                    style={{
                      padding: '0.65rem 0.85rem',
                      background: 'none',
                      border: 'none',
                      borderBottom: activeTab === 'checklist' ? '2px solid var(--accent-indigo)' : '2px solid transparent',
                      color: activeTab === 'checklist' ? '#fff' : 'var(--text-muted)',
                      fontWeight: 600,
                      fontSize: '0.85rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.4rem',
                      whiteSpace: 'nowrap'
                    }}
                  >
                    <CheckSquare size={15} color={activeTab === 'checklist' ? 'var(--accent-indigo)' : 'currentColor'} />
                    Before You Sign
                  </button>

                  <button
                    role="tab"
                    aria-selected={activeTab === 'questions'}
                    aria-label="What To Ask Next tab"
                    onClick={() => {
                      setActiveTab('questions');
                      if (!suggestedQuestions && !loadingQuestions) handleFetchQuestions();
                    }}
                    style={{
                      padding: '0.65rem 0.85rem',
                      background: 'none',
                      border: 'none',
                      borderBottom: activeTab === 'questions' ? '2px solid var(--accent-indigo)' : '2px solid transparent',
                      color: activeTab === 'questions' ? '#fff' : 'var(--text-muted)',
                      fontWeight: 600,
                      fontSize: '0.85rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.4rem',
                      whiteSpace: 'nowrap'
                    }}
                  >
                    <HelpCircle size={15} color={activeTab === 'questions' ? 'var(--accent-indigo)' : 'currentColor'} />
                    What To Ask Next
                  </button>

                  <button
                    role="tab"
                    aria-selected={activeTab === 'comparison'}
                    aria-label="Compare Contracts tab"
                    onClick={() => setActiveTab('comparison')}
                    style={{
                      padding: '0.65rem 0.85rem',
                      background: 'none',
                      border: 'none',
                      borderBottom: activeTab === 'comparison' ? '2px solid var(--accent-indigo)' : '2px solid transparent',
                      color: activeTab === 'comparison' ? '#fff' : 'var(--text-muted)',
                      fontWeight: 600,
                      fontSize: '0.85rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.4rem',
                      whiteSpace: 'nowrap'
                    }}
                  >
                    <ArrowRightLeft size={15} color={activeTab === 'comparison' ? 'var(--accent-indigo)' : 'currentColor'} />
                    Compare Contracts
                  </button>

                  <button
                    role="tab"
                    aria-selected={activeTab === 'pages'}
                    aria-label="Pages tab"
                    onClick={() => setActiveTab('pages')}
                    style={{
                      padding: '0.65rem 0.85rem',
                      background: 'none',
                      border: 'none',
                      borderBottom: activeTab === 'pages' ? '2px solid var(--accent-indigo)' : '2px solid transparent',
                      color: activeTab === 'pages' ? '#fff' : 'var(--text-muted)',
                      fontWeight: 600,
                      fontSize: '0.85rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.4rem',
                      whiteSpace: 'nowrap'
                    }}
                  >
                    <BookOpen size={15} color={activeTab === 'pages' ? 'var(--accent-indigo)' : 'currentColor'} />
                    Pages ({uploadResult.page_count})
                  </button>
                </div>

                {/* TAB 1: Evidence Q&A (RAG) */}
                {activeTab === 'qa' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                    {/* Prompt Box */}
                    <form onSubmit={handleAsk} className="glass-panel" style={{ padding: '1rem', display: 'flex', gap: '0.75rem' }}>
                      <label htmlFor="qa-question-input" className="sr-only">
                        Ask a question about the contract
                      </label>
                      <input
                        id="qa-question-input"
                        aria-label="Ask a question about the contract"
                        type="text"
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        placeholder="Ask a question (e.g. 'What is my notice period?', 'Can I work remotely?')..."
                        style={{
                          flex: 1,
                          padding: '0.75rem 1rem',
                          borderRadius: '8px',
                          backgroundColor: 'rgba(255, 255, 255, 0.04)',
                          border: '1px solid var(--border-color)',
                          color: '#fff',
                          fontSize: '0.875rem',
                          outline: 'none'
                        }}
                      />
                      <button
                        type="submit"
                        aria-label="Submit question to ClausePilot"
                        disabled={!question.trim() || asking}
                        style={{
                          padding: '0.75rem 1.25rem',
                          borderRadius: '8px',
                          background: question.trim() && !asking ? 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)' : '#374151',
                          color: '#fff',
                          border: 'none',
                          fontWeight: 600,
                          fontSize: '0.85rem',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.4rem',
                          opacity: question.trim() && !asking ? 1 : 0.6
                        }}
                      >
                        {asking ? <RefreshCw size={16} className="spin" /> : <Send size={16} />}
                        Ask
                      </button>
                    </form>

                    {/* Quick Suggestion Chips */}
                    <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-faint)', alignSelf: 'center' }}>Suggested:</span>
                      {[
                        'What is my notice period?',
                        'Can I work remotely or must I work at the office?',
                        'What happens to my stock options after resignation?',
                        'Is there a non-compete clause?',
                      ].map((sq, idx) => (
                        <button
                          key={idx}
                          aria-label={`Ask suggested question: ${sq}`}
                          onClick={() => handleAsk(undefined, sq)}
                          style={{
                            padding: '0.3rem 0.65rem',
                            borderRadius: '9999px',
                            backgroundColor: 'rgba(255, 255, 255, 0.04)',
                            border: '1px solid var(--border-color)',
                            color: 'var(--text-muted)',
                            fontSize: '0.75rem',
                            textAlign: 'left'
                          }}
                        >
                          {sq}
                        </button>
                      ))}
                    </div>

                    {qaError && (
                      <div style={{
                        padding: '0.75rem 1rem',
                        borderRadius: '8px',
                        backgroundColor: 'rgba(244, 63, 94, 0.1)',
                        border: '1px solid rgba(244, 63, 94, 0.3)',
                        color: '#fb7185',
                        fontSize: '0.85rem'
                      }}>
                        {qaError}
                      </div>
                    )}

                    {/* Chat & Answer Feed */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                      {chatHistory.map((item, index) => {
                        const badge = getStatusBadge(item.a.status);
                        return (
                          <div key={index} className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem' }}>
                              <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#f3f4f6' }}>
                                Q: {item.q}
                              </h3>
                              <div style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.35rem',
                                padding: '0.3rem 0.65rem',
                                borderRadius: '6px',
                                backgroundColor: badge.bg,
                                border: `1px solid ${badge.border}`,
                                color: badge.color,
                                fontSize: '0.75rem',
                                fontWeight: 600
                              }}>
                                {badge.icon}
                                {badge.label}
                              </div>
                            </div>

                            {item.a.answer ? (
                              <div style={{ fontSize: '0.925rem', lineHeight: '1.6', color: '#e2e8f0' }}>
                                {item.a.answer}
                              </div>
                            ) : (
                              <div style={{ fontSize: '0.875rem', color: '#9ca3af', fontStyle: 'italic' }}>
                                The document does not contain sufficient terms or explicit clauses to answer this question.
                              </div>
                            )}

                            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', backgroundColor: 'rgba(0,0,0,0.2)', padding: '0.75rem', borderRadius: '6px' }}>
                              <strong>Reasoning:</strong> {item.a.reasoning}
                            </div>

                            {item.a.citations && item.a.citations.length > 0 && (
                              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.25rem' }}>
                                <div style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--accent-indigo)', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                                  <Quote size={13} />
                                  VERIFIED CITATIONS ({item.a.citations.length}):
                                </div>
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '0.75rem' }}>
                                  {item.a.citations.map((cit, cIdx) => (
                                    <div key={cIdx} style={{
                                      padding: '0.75rem',
                                      borderRadius: '6px',
                                      backgroundColor: 'rgba(99, 102, 241, 0.06)',
                                      border: '1px solid rgba(99, 102, 241, 0.2)',
                                      fontSize: '0.78rem',
                                      display: 'flex',
                                      flexDirection: 'column',
                                      gap: '0.35rem'
                                    }}>
                                      <div style={{ display: 'flex', justifyContent: 'space-between', color: '#a5b4fc', fontWeight: 600 }}>
                                        <span>Page {cit.page_number} {cit.clause_number ? `· Clause ${cit.clause_number}` : ''}</span>
                                        <button 
                                          aria-label={`View page ${cit.page_number} citations`}
                                          onClick={() => {
                                            setSelectedPage(cit.page_number);
                                            setActiveTab('pages');
                                          }}
                                          style={{ background: 'none', border: 'none', color: 'var(--accent-indigo)', fontSize: '0.75rem', textDecoration: 'underline' }}>
                                          View Page
                                        </button>
                                      </div>
                                      <p style={{ color: '#cbd5e1', fontStyle: 'italic', fontFamily: 'var(--font-mono)', lineHeight: '1.4' }}>
                                        "{cit.quote}"
                                      </p>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {item.a.missing_information && item.a.missing_information.length > 0 && (
                              <div style={{ fontSize: '0.78rem', color: '#fb7185' }}>
                                <strong>Missing Information:</strong> {item.a.missing_information.join('; ')}
                              </div>
                            )}
                            {item.a.suggested_questions && item.a.suggested_questions.length > 0 && (
                              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                                <strong>Suggested Questions for HR/Counsel:</strong>
                                <ul style={{ marginLeft: '1.25rem', marginTop: '0.25rem' }}>
                                  {item.a.suggested_questions.map((sq, sIdx) => (
                                    <li key={sIdx}>{sq}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* TAB 2: Attention Map & Audit */}
                {activeTab === 'analysis' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                    {analysisError && (
                      <div style={{
                        padding: '0.75rem 1rem',
                        borderRadius: '8px',
                        backgroundColor: 'rgba(244, 63, 94, 0.1)',
                        border: '1px solid rgba(244, 63, 94, 0.3)',
                        color: '#fb7185',
                        fontSize: '0.85rem'
                      }}>
                        {analysisError}
                      </div>
                    )}
                    {analyzing ? (
                      <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center' }}>
                        <RefreshCw size={28} className="spin" style={{ margin: '0 auto 1rem auto', color: 'var(--accent-indigo)' }} />
                        <p style={{ color: '#e2e8f0', fontWeight: 500 }}>Generating First-Pass Contract Audit...</p>
                      </div>
                    ) : analysis ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                        <div className="glass-panel" style={{ padding: '1.5rem' }}>
                          <h3 style={{ fontSize: '1.05rem', fontWeight: 600, marginBottom: '1rem', color: '#f3f4f6' }}>
                            Contract Attention Map
                          </h3>
                          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1rem' }}>
                            {analysis.attention_items.map((item, idx) => {
                              const badge = getAttentionBadge(item.level);
                              return (
                                <div key={idx} style={{
                                  padding: '1rem',
                                  borderRadius: '8px',
                                  backgroundColor: 'rgba(255, 255, 255, 0.02)',
                                  border: '1px solid var(--border-color)',
                                  display: 'flex',
                                  flexDirection: 'column',
                                  gap: '0.5rem'
                                }}>
                                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <span style={{ fontWeight: 600, fontSize: '0.85rem', color: '#f3f4f6' }}>{item.category}</span>
                                    <span style={{ fontSize: '0.72rem', padding: '0.2rem 0.5rem', borderRadius: '4px', backgroundColor: badge.bg, color: badge.color, fontWeight: 600 }}>
                                      {badge.label}
                                    </span>
                                  </div>
                                  <p style={{ fontSize: '0.8rem', color: '#cbd5e1', lineHeight: '1.5' }}>
                                    {item.summary}
                                  </p>
                                </div>
                              );
                            })}
                          </div>
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem' }}>
                          <div className="glass-panel" style={{ padding: '1.25rem' }}>
                            <h4 style={{ fontSize: '0.9rem', fontWeight: 600, color: '#60a5fa', marginBottom: '0.75rem' }}>
                              Key Obligations
                            </h4>
                            <ul style={{ fontSize: '0.8rem', color: '#cbd5e1', lineHeight: '1.6', marginLeft: '1.2rem' }}>
                              {analysis.obligations.map((ob, idx) => (
                                <li key={idx}>{ob}</li>
                              ))}
                            </ul>
                          </div>

                          <div className="glass-panel" style={{ padding: '1.25rem' }}>
                            <h4 style={{ fontSize: '0.9rem', fontWeight: 600, color: '#fbbf24', marginBottom: '0.75rem' }}>
                              Areas Requiring Clarification
                            </h4>
                            <ul style={{ fontSize: '0.8rem', color: '#cbd5e1', lineHeight: '1.6', marginLeft: '1.2rem' }}>
                              {analysis.risks.map((rk, idx) => (
                                <li key={idx}>{rk}</li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center' }}>
                        <button
                          onClick={handleRunAnalysis}
                          aria-label="Run First-Pass Audit"
                          style={{
                            padding: '0.75rem 1.5rem',
                            borderRadius: '8px',
                            background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
                            color: '#fff',
                            border: 'none',
                            fontWeight: 600,
                            fontSize: '0.875rem'
                          }}
                        >
                          Run First-Pass Audit
                        </button>
                      </div>
                    )}
                  </div>
                )}

                {/* TAB 3: Before You Sign Checklist (Phase 3) */}
                {activeTab === 'checklist' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                    {checklistError && (
                      <div style={{
                        padding: '0.75rem 1rem',
                        borderRadius: '8px',
                        backgroundColor: 'rgba(244, 63, 94, 0.1)',
                        border: '1px solid rgba(244, 63, 94, 0.3)',
                        color: '#fb7185',
                        fontSize: '0.85rem'
                      }}>
                        {checklistError}
                      </div>
                    )}
                    {loadingChecklist ? (
                      <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center' }}>
                        <RefreshCw size={28} className="spin" style={{ margin: '0 auto 1rem auto', color: 'var(--accent-indigo)' }} />
                        <p style={{ color: '#e2e8f0', fontWeight: 500 }}>Synthesizing Actionable Signing Checklist...</p>
                      </div>
                    ) : checklist ? (
                      <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem' }}>
                          <div>
                            <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: '#f3f4f6' }}>
                              Before You Sign: Action Checklist
                            </h3>
                            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                              Prioritized verification tasks tailored for: <em>{decisionContext}</em>
                            </p>
                          </div>
                          <button
                            onClick={handleFetchChecklist}
                            aria-label="Regenerate signing checklist"
                            style={{ background: 'none', border: '1px solid var(--border-color)', padding: '0.35rem 0.75rem', borderRadius: '6px', color: 'var(--text-muted)', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}
                          >
                            <RefreshCw size={12} /> Regenerate
                          </button>
                        </div>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                          {checklist.items.map((item, idx) => {
                            const isDone = Boolean(completedItems[idx]);
                            const isHigh = item.priority === 'HIGH';
                            return (
                              <div
                                key={idx}
                                onClick={() => toggleChecklistItem(idx)}
                                style={{
                                  padding: '1rem',
                                  borderRadius: '8px',
                                  backgroundColor: isDone ? 'rgba(16, 185, 129, 0.05)' : 'rgba(255, 255, 255, 0.02)',
                                  border: `1px solid ${isDone ? 'rgba(16, 185, 129, 0.3)' : 'var(--border-color)'}`,
                                  display: 'flex',
                                  alignItems: 'flex-start',
                                  gap: '0.85rem',
                                  cursor: 'pointer',
                                  transition: 'all 0.15s'
                                }}
                              >
                                <input
                                  type="checkbox"
                                  aria-label={`Mark as completed: ${item.item}`}
                                  checked={isDone}
                                  onChange={() => {}} // Handled by div click
                                  style={{ marginTop: '0.2rem', accentColor: '#10b981', cursor: 'pointer' }}
                                />
                                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                    <span style={{
                                      fontSize: '0.875rem',
                                      fontWeight: 500,
                                      color: isDone ? 'var(--text-muted)' : '#f3f4f6',
                                      textDecoration: isDone ? 'line-through' : 'none'
                                    }}>
                                      {item.item}
                                    </span>
                                    <span style={{
                                      fontSize: '0.68rem',
                                      padding: '0.15rem 0.4rem',
                                      borderRadius: '4px',
                                      backgroundColor: isHigh ? 'rgba(244, 63, 94, 0.15)' : 'rgba(99, 102, 241, 0.15)',
                                      color: isHigh ? '#fb7185' : '#a5b4fc',
                                      fontWeight: 600
                                    }}>
                                      {item.priority}
                                    </span>
                                  </div>
                                  {item.clause_reference && (
                                    <span style={{ fontSize: '0.75rem', color: 'var(--accent-indigo)' }}>
                                      Reference: {item.clause_reference}
                                    </span>
                                  )}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    ) : (
                      <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center' }}>
                        <button
                          onClick={handleFetchChecklist}
                          aria-label="Generate Signing Checklist"
                          style={{
                            padding: '0.75rem 1.5rem',
                            borderRadius: '8px',
                            background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
                            color: '#fff',
                            border: 'none',
                            fontWeight: 600,
                            fontSize: '0.875rem'
                          }}
                        >
                          Generate Signing Checklist
                        </button>
                      </div>
                    )}
                  </div>
                )}

                {/* TAB 4: What To Ask Next (Phase 3) */}
                {activeTab === 'questions' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                    {questionsError && (
                      <div style={{
                        padding: '0.75rem 1rem',
                        borderRadius: '8px',
                        backgroundColor: 'rgba(244, 63, 94, 0.1)',
                        border: '1px solid rgba(244, 63, 94, 0.3)',
                        color: '#fb7185',
                        fontSize: '0.85rem'
                      }}>
                        {questionsError}
                      </div>
                    )}
                    {loadingQuestions ? (
                      <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center' }}>
                        <RefreshCw size={28} className="spin" style={{ margin: '0 auto 1rem auto', color: 'var(--accent-indigo)' }} />
                        <p style={{ color: '#e2e8f0', fontWeight: 500 }}>Generating Targeted Negotiation & Legal Questions...</p>
                      </div>
                    ) : suggestedQuestions ? (
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem' }}>
                        {/* Questions for HR / Counterparty */}
                        <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem' }}>
                            <Briefcase size={18} color="#60a5fa" />
                            <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#f3f4f6' }}>
                              Questions for HR / Counterparty
                            </h3>
                          </div>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                            {suggestedQuestions.questions_for_counterparty.map((q, idx) => (
                              <div key={idx} style={{
                                padding: '0.85rem',
                                borderRadius: '6px',
                                backgroundColor: 'rgba(59, 130, 246, 0.05)',
                                border: '1px solid rgba(59, 130, 246, 0.2)',
                                fontSize: '0.825rem',
                                color: '#e2e8f0',
                                lineHeight: '1.5'
                              }}>
                                <p>{q}</p>
                                <button
                                  aria-label={`Ask in workspace: ${q}`}
                                  onClick={() => {
                                    setQuestion(q);
                                    setActiveTab('qa');
                                  }}
                                  style={{
                                    marginTop: '0.5rem',
                                    background: 'none',
                                    border: 'none',
                                    color: 'var(--accent-indigo)',
                                    fontSize: '0.75rem',
                                    fontWeight: 600,
                                    cursor: 'pointer',
                                    padding: 0
                                  }}
                                >
                                  Ask this in workspace →
                                </button>
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Questions for Legal Counsel */}
                        <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem' }}>
                            <Users size={18} color="#a855f7" />
                            <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#f3f4f6' }}>
                              Questions for Legal Professional
                            </h3>
                          </div>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                            {suggestedQuestions.questions_for_legal_professional.map((q, idx) => (
                              <div key={idx} style={{
                                padding: '0.85rem',
                                borderRadius: '6px',
                                backgroundColor: 'rgba(168, 85, 247, 0.05)',
                                border: '1px solid rgba(168, 85, 247, 0.2)',
                                fontSize: '0.825rem',
                                color: '#e2e8f0',
                                lineHeight: '1.5'
                              }}>
                                <p>{q}</p>
                                <button
                                  aria-label={`Ask in workspace: ${q}`}
                                  onClick={() => {
                                    setQuestion(q);
                                    setActiveTab('qa');
                                  }}
                                  style={{
                                    marginTop: '0.5rem',
                                    background: 'none',
                                    border: 'none',
                                    color: 'var(--accent-purple)',
                                    fontSize: '0.75rem',
                                    fontWeight: 600,
                                    cursor: 'pointer',
                                    padding: 0
                                  }}
                                >
                                  Ask this in workspace →
                                </button>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center' }}>
                        <button
                          onClick={handleFetchQuestions}
                          aria-label="Generate Targeted Questions"
                          style={{
                            padding: '0.75rem 1.5rem',
                            borderRadius: '8px',
                            background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
                            color: '#fff',
                            border: 'none',
                            fontWeight: 600,
                            fontSize: '0.875rem'
                          }}
                        >
                          Generate Targeted Questions
                        </button>
                      </div>
                    )}
                  </div>
                )}

                {/* TAB 5: Comparison View (Phase 4) */}
                {activeTab === 'comparison' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                    {/* Comparison Control Panel */}
                    <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
                          <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: '#f3f4f6', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <GitCompare size={20} color="var(--accent-indigo)" />
                            Multi-Contract Difference & Conflict Engine
                          </h3>
                          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                            Compare baseline contract against a modified version, counter-offer, or competitor terms.
                          </p>
                        </div>

                        <button
                          onClick={handleRunComparison}
                          aria-label="Run Semantic Diff and Conflict Engine"
                          disabled={!uploadResultB || comparing}
                          style={{
                            padding: '0.65rem 1.25rem',
                            borderRadius: '8px',
                            background: uploadResultB && !comparing ? 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)' : '#374151',
                            color: '#fff',
                            border: 'none',
                            fontWeight: 600,
                            fontSize: '0.85rem',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            opacity: uploadResultB && !comparing ? 1 : 0.6
                          }}
                        >
                          {comparing ? <><RefreshCw size={15} className="spin" /> Comparing Clauses...</> : <><ArrowRightLeft size={15} /> Run Semantic Diff</>}
                        </button>
                      </div>

                      {/* Document Selector Grid */}
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                        {/* Doc A */}
                        <div style={{
                          padding: '1rem',
                          borderRadius: '8px',
                          backgroundColor: 'rgba(255, 255, 255, 0.02)',
                          border: '1px solid var(--border-color)',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '0.35rem'
                        }}>
                          <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--accent-indigo)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                            Document A (Baseline)
                          </span>
                          <span style={{ fontSize: '0.875rem', fontWeight: 600, color: '#e2e8f0' }}>
                            {uploadResult.original_filename}
                          </span>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                            {uploadResult.page_count} pages • ID: {uploadResult.document_id.slice(0, 8)}...
                          </span>
                        </div>

                        {/* Doc B Upload */}
                        <div style={{
                          padding: '1rem',
                          borderRadius: '8px',
                          backgroundColor: uploadResultB ? 'rgba(255, 255, 255, 0.02)' : 'rgba(99, 102, 241, 0.04)',
                          border: uploadResultB ? '1px solid var(--border-color)' : '2px dashed var(--accent-indigo)',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '0.35rem',
                          position: 'relative'
                        }}>
                          <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#a855f7', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                            Document B (Modified / Comparison Target)
                          </span>
                          {uploadResultB ? (
                            <>
                              <span style={{ fontSize: '0.875rem', fontWeight: 600, color: '#e2e8f0' }}>
                                {uploadResultB.original_filename}
                              </span>
                              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                {uploadResultB.page_count} pages • Indexed in ChromaDB
                              </span>
                            </>
                          ) : (
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.2rem' }}>
                              <label htmlFor="doc-b-file-input" className="sr-only">
                                Upload second PDF for comparison
                              </label>
                              <input
                                id="doc-b-file-input"
                                type="file"
                                aria-label="Upload second PDF for comparison"
                                accept=".pdf,application/pdf"
                                onChange={handleUploadAndIndexB}
                                style={{
                                  position: 'absolute',
                                  top: 0,
                                  left: 0,
                                  width: '100%',
                                  height: '100%',
                                  opacity: 0,
                                  cursor: 'pointer'
                                }}
                              />
                              <Upload size={16} color="var(--accent-purple)" />
                              <span style={{ fontSize: '0.825rem', color: '#cbd5e1' }}>
                                {uploadStepB === 'uploading' || uploadStepB === 'extracting' || uploadStepB === 'indexing'
                                  ? 'Processing Doc B...'
                                  : 'Click to upload second PDF for comparison'}
                              </span>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Optional Focus Input */}
                      <div>
                        <label 
                          htmlFor="comparison-focus-input"
                          style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.3rem', display: 'block' }}>
                          Comparison Focus (Optional)
                        </label>
                        <input
                          id="comparison-focus-input"
                          aria-label="Comparison Focus"
                          type="text"
                          value={comparisonFocus}
                          onChange={(e) => setComparisonFocus(e.target.value)}
                          placeholder="e.g. Focus on Notice period, Non-compete scope, and IP ownership..."
                          style={{
                            width: '100%',
                            padding: '0.5rem 0.75rem',
                            borderRadius: '6px',
                            backgroundColor: 'rgba(255, 255, 255, 0.04)',
                            border: '1px solid var(--border-color)',
                            color: '#fff',
                            fontSize: '0.825rem',
                            outline: 'none'
                          }}
                        />
                      </div>

                      {uploadErrorB && (
                        <div style={{
                          padding: '0.75rem',
                          borderRadius: '6px',
                          backgroundColor: 'rgba(244, 63, 94, 0.1)',
                          border: '1px solid rgba(244, 63, 94, 0.3)',
                          color: '#fb7185',
                          fontSize: '0.825rem',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.5rem'
                        }}>
                          <AlertCircle size={16} />
                          <span>{uploadErrorB}</span>
                        </div>
                      )}

                      {comparisonError && (
                        <div style={{
                          padding: '0.75rem',
                          borderRadius: '6px',
                          backgroundColor: 'rgba(244, 63, 94, 0.1)',
                          border: '1px solid rgba(244, 63, 94, 0.3)',
                          color: '#fb7185',
                          fontSize: '0.825rem',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.5rem'
                        }}>
                          <AlertCircle size={16} />
                          <span>{comparisonError}</span>
                        </div>
                      )}
                    </div>

                    {/* Comparison Results */}
                    {comparison && (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                        {/* Summary Box */}
                        <div className="glass-panel" style={{ padding: '1.25rem' }}>
                          <h4 style={{ fontSize: '0.9rem', fontWeight: 600, color: '#f3f4f6', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                            <Columns size={16} color="var(--accent-indigo)" />
                            Executive Comparison Summary
                          </h4>
                          <p style={{ fontSize: '0.85rem', lineHeight: '1.6', color: '#cbd5e1' }}>
                            {comparison.overall_summary}
                          </p>
                        </div>

                        {/* Section Diff Cards */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                          {comparison.sections.map((sec, idx) => {
                            const badge = getDiffBadge(sec.difference_type);
                            return (
                              <div key={idx} className="glass-panel" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                  <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: '#f3f4f6' }}>
                                    {sec.topic}
                                  </h4>
                                  <span style={{
                                    padding: '0.2rem 0.6rem',
                                    borderRadius: '9999px',
                                    fontSize: '0.72rem',
                                    fontWeight: 600,
                                    backgroundColor: badge.bg,
                                    border: `1px solid ${badge.border}`,
                                    color: badge.color
                                  }}>
                                    {badge.label}
                                  </span>
                                </div>

                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                                  {/* Side A */}
                                  <div style={{
                                    backgroundColor: 'rgba(255, 255, 255, 0.02)',
                                    borderRadius: '6px',
                                    padding: '0.85rem',
                                    border: '1px solid var(--border-color)',
                                    display: 'flex',
                                    flexDirection: 'column',
                                    gap: '0.5rem'
                                  }}>
                                    <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>
                                      Doc A (Baseline):
                                    </div>
                                    <p style={{ fontSize: '0.825rem', color: '#cbd5e1', lineHeight: '1.5' }}>
                                      {sec.document_a_summary || 'Not mentioned in Document A.'}
                                    </p>
                                    {sec.citations_a.length > 0 && (
                                      <div style={{ marginTop: '0.25rem', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                                        {sec.citations_a.map((cit, cIdx) => (
                                          <div key={cIdx} style={{
                                            fontSize: '0.72rem',
                                            padding: '0.35rem 0.5rem',
                                            borderRadius: '4px',
                                            backgroundColor: 'rgba(99, 102, 241, 0.08)',
                                            borderLeft: '2px solid var(--accent-indigo)',
                                            color: '#cbd5e1',
                                            fontStyle: 'italic',
                                            display: 'flex',
                                            justifyContent: 'space-between',
                                            alignItems: 'center'
                                          }}>
                                            <span>"{cit.quote}" (p. {cit.page_number})</span>
                                            <button
                                              aria-label={`View page ${cit.page_number} citations for Document A`}
                                              onClick={() => {
                                                setSelectedPage(cit.page_number);
                                                setActiveTab('pages');
                                              }}
                                              style={{
                                                background: 'none',
                                                border: 'none',
                                                color: 'var(--accent-indigo)',
                                                fontSize: '0.68rem',
                                                fontWeight: 600,
                                                cursor: 'pointer',
                                                marginLeft: '0.4rem',
                                                whiteSpace: 'nowrap'
                                              }}
                                            >
                                              View Page →
                                            </button>
                                          </div>
                                        ))}
                                      </div>
                                    )}
                                  </div>

                                  {/* Side B */}
                                  <div style={{
                                    backgroundColor: 'rgba(255, 255, 255, 0.02)',
                                    borderRadius: '6px',
                                    padding: '0.85rem',
                                    border: '1px solid var(--border-color)',
                                    display: 'flex',
                                    flexDirection: 'column',
                                    gap: '0.5rem'
                                  }}>
                                    <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>
                                      Doc B (Modified):
                                    </div>
                                    <p style={{ fontSize: '0.825rem', color: '#cbd5e1', lineHeight: '1.5' }}>
                                      {sec.document_b_summary || 'Not mentioned in Document B.'}
                                    </p>
                                    {sec.citations_b.length > 0 && (
                                      <div style={{ marginTop: '0.25rem', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                                        {sec.citations_b.map((cit, cIdx) => (
                                          <div key={cIdx} style={{
                                            fontSize: '0.72rem',
                                            padding: '0.35rem 0.5rem',
                                            borderRadius: '4px',
                                            backgroundColor: 'rgba(168, 85, 247, 0.08)',
                                            borderLeft: '2px solid #a855f7',
                                            color: '#cbd5e1',
                                            fontStyle: 'italic',
                                            display: 'flex',
                                            justifyContent: 'space-between',
                                            alignItems: 'center'
                                          }}>
                                            <span>"{cit.quote}" (p. {cit.page_number})</span>
                                            {uploadResultB?.extracted_pages && (
                                              <button
                                                aria-label={`View page ${cit.page_number} citations for Document B`}
                                                onClick={() => {
                                                  setSelectedPage(cit.page_number);
                                                  setActiveTab('pages');
                                                }}
                                                style={{
                                                  background: 'none',
                                                  border: 'none',
                                                  color: '#c084fc',
                                                  fontSize: '0.68rem',
                                                  fontWeight: 600,
                                                  cursor: 'pointer',
                                                  marginLeft: '0.4rem',
                                                  whiteSpace: 'nowrap'
                                                }}
                                              >
                                                View Page →
                                              </button>
                                            )}
                                          </div>
                                        ))}
                                      </div>
                                    )}
                                  </div>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* TAB 6: Document Page Viewer */}
                {activeTab === 'pages' && (
                  <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    <div style={{ display: 'flex', gap: '0.5rem', overflowX: 'auto', paddingBottom: '0.5rem' }}>
                      {uploadResult.extracted_pages?.map((p) => (
                        <button
                          key={p.page_number}
                          aria-label={`View contract page ${p.page_number}`}
                          onClick={() => setSelectedPage(p.page_number)}
                          style={{
                            padding: '0.4rem 0.85rem',
                            borderRadius: '6px',
                            fontSize: '0.8rem',
                            fontWeight: 500,
                            border: selectedPage === p.page_number ? '1px solid var(--accent-indigo)' : '1px solid var(--border-color)',
                            backgroundColor: selectedPage === p.page_number ? 'rgba(99, 102, 241, 0.25)' : 'rgba(255, 255, 255, 0.03)',
                            color: selectedPage === p.page_number ? '#fff' : 'var(--text-muted)',
                            whiteSpace: 'nowrap'
                          }}
                        >
                          Page {p.page_number}
                        </button>
                      ))}
                    </div>

                    <div style={{
                      backgroundColor: 'rgba(11, 15, 25, 0.6)',
                      border: '1px solid var(--border-color)',
                      borderRadius: '8px',
                      padding: '1.25rem',
                      minHeight: '400px',
                      maxHeight: '600px',
                      overflowY: 'auto'
                    }}>
                      <pre style={{
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word',
                        fontSize: '0.85rem',
                        lineHeight: '1.6',
                        fontFamily: 'var(--font-mono)',
                        color: '#d1d5db'
                      }}>
                        {uploadResult.extracted_pages?.find(p => p.page_number === selectedPage)?.text || '[No text on page]'}
                      </pre>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="glass-panel" style={{
                padding: '4rem 2rem',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                textAlign: 'center',
                gap: '1rem',
                minHeight: '450px'
              }}>
                <div style={{
                  width: '64px',
                  height: '64px',
                  borderRadius: '50%',
                  backgroundColor: 'rgba(255, 255, 255, 0.03)',
                  border: '1px solid var(--border-color)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <BookOpen size={30} color="var(--text-faint)" />
                </div>
                <div>
                  <h2 style={{ fontSize: '1.15rem', fontWeight: 600, color: '#f3f4f6', marginBottom: '0.35rem' }}>
                    Workspace Awaiting Contract Intake
                  </h2>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', maxWidth: '420px', lineHeight: '1.5' }}>
                    Upload an employment agreement, vendor NDA, or rental lease to index into ChromaDB and begin grounded legal Q&A.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer style={{
        borderTop: '1px solid var(--border-color)',
        padding: '1rem 2rem',
        fontSize: '0.78rem',
        color: 'var(--text-faint)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        backgroundColor: 'rgba(11, 15, 25, 0.6)'
      }}>
        <div>ClausePilot © 2026 Prompt Wars. Built for verifiable legal assistance.</div>
        <div>Legal Disclaimer: Provides analysis & navigational assistance only. Not professional legal advice.</div>
      </footer>
    </div>
  );
}

export default App;
