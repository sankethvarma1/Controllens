'use client';

import { useState } from 'react';
import { Send, Loader2, Search, FileText, Shield, AlertTriangle, Link as LinkIcon, ExternalLink, Copy, Check } from 'lucide-react';
import { api, InvestigationResponse, RetrievalResultResponse } from '@/lib/api';
import { cn, formatDate, getStatusColor, getSeverityColor } from '@/lib/utils';

const SAMPLE_QUESTIONS = [
  "What evidence supports control CTL_001?",
  "Which obligations have no controls mapped?",
  "Why was exception EXC_2024_001 flagged?",
  "Show me the traceability chain for obligation OBL_REG_GDPR_SEC_001_01",
  "What controls are overdue for testing?",
  "Which evidence items have expired?",
  "What are the open exceptions for the payment processing process?",
  "Show me obligations with high risk and no evidence",
];

export default function InvestigatePage() {
  const [question, setQuestion] = useState('');
  const [response, setResponse] = useState<InvestigationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<Array<{question: string, response: InvestigationResponse, timestamp: Date}>>([]);
  const [showHistory, setShowHistory] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || loading) return;

    setLoading(true);
    try {
      const result = await api.investigate(question);
      const investigationResponse = result.data;
      setResponse(investigationResponse);
      setHistory(prev => [{ question, response: investigationResponse, timestamp: new Date() }, ...prev.slice(0, 9)]);
    } catch (err) {
      console.error(err);
      setResponse({
        question,
        answer: 'An error occurred while investigating. Please try again.',
        evidence: [],
        tools_used: [],
        confidence: 0,
        insufficient_evidence: true,
      });
    } finally {
      setLoading(false);
    }
  };

  const copyAnswer = () => {
    if (response) {
      navigator.clipboard.writeText(response.answer);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">Investigation</h1>
          <p className="text-secondary-500 mt-1">Ask questions about your control framework with evidence-based answers</p>
          <p className="text-xs text-secondary-400 mt-1">Template-based summaries over retrieved evidence — no live LLM call in this build.</p>
        </div>
        <button
          onClick={() => setShowHistory(!showHistory)}
          className="btn-outline"
        >
          {showHistory ? 'Hide' : 'Show'} History
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Question Input & Answer */}
        <div className="lg:col-span-2 space-y-6">
          {/* Question Form */}
          <div className="card p-6">
            <form onSubmit={handleSubmit}>
              <label className="block text-sm font-medium text-secondary-700 mb-2">
                Ask a question
              </label>
              <div className="flex gap-2">
                <textarea
                  value={question}
                  onChange={e => setQuestion(e.target.value)}
                  placeholder="e.g., What evidence supports control CTL_001?"
                  rows={3}
                  className="input flex-1 resize-none"
                  disabled={loading}
                />
                <button
                  type="submit"
                  disabled={loading || !question.trim()}
                  className="btn-primary self-end px-6"
                >
                  {loading ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <Send className="w-5 h-5" />
                  )}
                </button>
              </div>
            </form>

            {/* Sample Questions */}
            <div className="mt-4">
              <p className="text-sm text-secondary-500 mb-2">Sample questions:</p>
              <div className="flex flex-wrap gap-2">
                {SAMPLE_QUESTIONS.map((q, i) => (
                  <button
                    key={i}
                    onClick={() => setQuestion(q)}
                    className="px-3 py-1.5 text-xs text-secondary-600 bg-secondary-100 rounded hover:bg-secondary-200 transition-colors truncate max-w-[200px]"
                    title={q}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Answer */}
          {response && (
            <div className="card">
              <div className="p-4 border-b border-secondary-200 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-secondary-900">Answer</h2>
                <div className="flex items-center gap-2">
                  <span className={cn('badge', response.insufficient_evidence ? 'badge-warning' : 'badge-success')}>
                    {response.insufficient_evidence ? 'Insufficient Evidence' : 'Evidence Supported'}
                  </span>
                  <span className="text-sm text-secondary-500">
                    Confidence: {(response.confidence * 100).toFixed(0)}%
                  </span>
                  <button onClick={copyAnswer} className="p-2 hover:bg-secondary-100 rounded" title="Copy">
                    <Copy className="w-4 h-4" />
                  </button>
                </div>
              </div>
              <div className="p-4 prose prose-sm max-w-none">
                <p className="whitespace-pre-wrap">{response.answer}</p>
                {response.insufficient_evidence && (
                  <div className="mt-4 p-3 bg-warning-50 border border-warning-200 rounded-lg">
                    <p className="text-sm text-warning-800">
                      ⚠️ This answer is based on limited or no evidence. Please verify independently.
                    </p>
                  </div>
                )}
              </div>

              {/* Tools Used */}
              {response.tools_used.length > 0 && (
                <div className="p-4 border-t border-secondary-200 bg-secondary-50">
                  <h3 className="font-medium text-secondary-900 mb-2">Tools Used</h3>
                  <div className="flex flex-wrap gap-2">
                    {response.tools_used.map((tool: string, i: number) => (
                      <span key={i} className="px-2 py-1 bg-white rounded text-sm text-secondary-600 border border-secondary-200">
                        {tool}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Evidence */}
          {response && response.evidence.length > 0 && (
            <div className="card">
              <div className="p-4 border-b border-secondary-200">
                <h2 className="text-lg font-semibold text-secondary-900">Supporting Evidence ({response.evidence.length})</h2>
              </div>
              <div className="divide-y divide-secondary-200">
                {response.evidence.map((ev: RetrievalResultResponse, i: number) => (
                  <div key={ev.id} className="p-4 hover:bg-secondary-50">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className={cn('badge', 
                            ev.source_type === 'evidence' ? 'badge-success' :
                            ev.source_type === 'regulatory_section' ? 'badge-primary' :
                            'badge-neutral'
                          )}>
                            {ev.source_type.replace(/_/g, ' ')}
                          </span>
                          <span className="text-sm text-secondary-500">Score: {ev.score.toFixed(2)}</span>
                        </div>
                        <p className="font-medium text-secondary-900 mb-1">
                          {ev.document_title || ev.section_title || ev.metadata?.control_name || ev.source_id}
                        </p>
                        <p className="text-sm text-secondary-600 line-clamp-2">{ev.content}</p>
                        <div className="mt-2 flex flex-wrap gap-2 text-xs text-secondary-500">
                          {ev.control_id && <span className="flex items-center gap-1"><Shield className="w-3 h-3" />{ev.control_id}</span>}
                          {ev.evidence_type && <span className="flex items-center gap-1"><FileText className="w-3 h-3" />{ev.evidence_type}</span>}
                          {ev.regulation_id && <span className="flex items-center gap-1"><LinkIcon className="w-3 h-3" />{ev.regulation_id}</span>}
                          {ev.page_number && <span><FileText className="w-3 h-3" />Page {ev.page_number}</span>}
                        </div>
                      </div>
                      <div className="flex items-center gap-1">
                        <button className="p-1.5 hover:bg-secondary-100 rounded" title="View Source">
                          <ExternalLink className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {response && response.evidence.length === 0 && !response.insufficient_evidence && (
            <div className="card p-8 text-center">
              <Search className="w-12 h-12 text-secondary-300 mx-auto mb-3" />
              <p className="text-secondary-500">No specific evidence found for this question</p>
            </div>
          )}
        </div>

        {/* History & Context */}
        <div className="space-y-6">
          {/* Context Panel */}
          <div className="card p-4">
            <h3 className="font-semibold text-secondary-900 mb-3">Investigation Context</h3>
            <div className="space-y-3 text-sm">
              <div>
                <p className="text-secondary-500">Tools Available</p>
                <div className="flex flex-wrap gap-1 mt-1">
                  {['search_regulation', 'get_obligation', 'get_policy', 'get_control', 'search_evidence', 'query_transactions', 'analyze_exceptions', 'calculate_control_effectiveness', 'build_traceability_chain'].map(t => (
                    <span key={t} className="px-2 py-0.5 bg-secondary-100 rounded text-xs text-secondary-600">{t}</span>
                  ))}
                </div>
              </div>
              <div>
                <p className="text-secondary-500">Data Sources</p>
                <div className="flex flex-wrap gap-1 mt-1">
                  {['Regulations', 'Obligations', 'Policies', 'Processes', 'Controls', 'Evidence', 'Transactions', 'Exceptions', 'Risk Assessments'].map(s => (
                    <span key={s} className="px-2 py-0.5 bg-secondary-100 rounded text-xs text-secondary-600">{s}</span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* History */}
          {showHistory && history.length > 0 && (
            <div className="card">
              <div className="p-4 border-b border-secondary-200">
                <h3 className="font-semibold text-secondary-900">Recent Questions</h3>
              </div>
              <div className="divide-y divide-secondary-200">
                {history.map((item, i) => (
                  <button
                    key={i}
                    onClick={() => {
                      setQuestion(item.question);
                      setResponse(item.response);
                    }}
                    className="w-full p-4 text-left hover:bg-secondary-50 transition-colors"
                  >
                    <p className="font-medium text-secondary-900 mb-1">{item.question}</p>
                    <p className="text-xs text-secondary-500">{item.timestamp.toLocaleTimeString()}</p>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}