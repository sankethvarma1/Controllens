'use client';

import { useEffect, useState } from 'react';
import { Search, Filter, CheckCircle, XCircle, Clock, AlertCircle, ExternalLink, MoreVertical, ChevronDown, ChevronRight } from 'lucide-react';
import { api, MappingReviewResponse } from '@/lib/api';
import { cn, formatDate, getStatusColor } from '@/lib/utils';

const MAPPING_TYPES = [
  { value: 'obligation_to_policy', label: 'Obligation → Policy' },
  { value: 'policy_to_process', label: 'Policy → Process' },
  { value: 'process_to_control', label: 'Process → Control' },
  { value: 'control_to_evidence', label: 'Control → Evidence' },
];

export default function ReviewPage() {
  const [reviews, setReviews] = useState<MappingReviewResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('proposed');
  const [typeFilter, setTypeFilter] = useState('');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await api.getMappingReviews({ limit: 200 });
        setReviews(response.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const filtered = reviews
    .filter(r => 
      r.ai_reasoning?.toLowerCase().includes(search.toLowerCase()) ||
      r.source_entity_id.toLowerCase().includes(search.toLowerCase()) ||
      r.target_entity_id.toLowerCase().includes(search.toLowerCase())
    )
    .filter(r => !statusFilter || r.status === statusFilter)
    .filter(r => !typeFilter || r.mapping_type === typeFilter);

  const proposedCount = reviews.filter(r => r.status === 'proposed').length;
  const needsReviewCount = reviews.filter(r => r.status === 'needs_review').length;
  const acceptedCount = reviews.filter(r => r.status === 'accepted').length;
  const rejectedCount = reviews.filter(r => r.status === 'rejected').length;

  const handleDecision = async (reviewId: string, decision: 'accept' | 'reject' | 'needs_more_info', comments: string) => {
    try {
      await api.updateMappingReview(reviewId, {
        status: decision === 'accept' ? 'accepted' : decision === 'reject' ? 'rejected' : 'needs_review',
        review_decision: decision,
        review_comments: comments,
      }, 'current_user', 'compliance_manager');
      
      setReviews(prev => prev.map(r => 
        r.id === reviewId 
          ? { ...r, status: decision === 'accept' ? 'accepted' : decision === 'reject' ? 'rejected' : 'needs_review', review_decision: decision, review_comments: comments, reviewed_by: 'current_user', reviewed_at: new Date().toISOString() }
          : r
      ));
      setExpandedId(null);
    } catch (err) {
      console.error(err);
      alert('Failed to submit decision');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">Mapping Review</h1>
          <p className="text-secondary-500 mt-1">Review and approve AI-proposed mappings</p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card p-4 border-l-4 border-warning-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-secondary-500">Proposed</p>
              <p className="text-2xl font-bold text-warning-600">{proposedCount}</p>
            </div>
            <Clock className="w-8 h-8 text-warning-500" />
          </div>
        </div>
        <div className="card p-4 border-l-4 border-primary-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-secondary-500">Needs Review</p>
              <p className="text-2xl font-bold text-primary-600">{needsReviewCount}</p>
            </div>
            <AlertCircle className="w-8 h-8 text-primary-500" />
          </div>
        </div>
        <div className="card p-4 border-l-4 border-success-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-secondary-500">Accepted</p>
              <p className="text-2xl font-bold text-success-600">{acceptedCount}</p>
            </div>
            <CheckCircle className="w-8 h-8 text-success-500" />
          </div>
        </div>
        <div className="card p-4 border-l-4 border-danger-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-secondary-500">Rejected</p>
              <p className="text-2xl font-bold text-danger-600">{rejectedCount}</p>
            </div>
            <XCircle className="w-8 h-8 text-danger-500" />
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-secondary-400" />
            <input
              type="text"
              placeholder="Search mappings..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="input pl-10"
            />
          </div>
          <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="input w-auto">
            <option value="proposed">Proposed</option>
            <option value="needs_review">Needs Review</option>
            <option value="accepted">Accepted</option>
            <option value="rejected">Rejected</option>
            <option value="">All</option>
          </select>
          <select value={typeFilter} onChange={e => setTypeFilter(e.target.value)} className="input w-auto min-w-[200px]">
            <option value="">All Types</option>
            {MAPPING_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
          </select>
        </div>
      </div>

      {/* Reviews List */}
      <div className="card">
        {loading ? (
          <div className="p-8 text-center">
            <div className="animate-pulse flex justify-center">
              <div className="w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full" />
            </div>
          </div>
        ) : (
          <div className="divide-y divide-secondary-200">
            {filtered.map(review => (
              <div key={review.id} className="p-4 hover:bg-secondary-50 transition-colors">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2">
                      <span className={cn('badge', getStatusColor(review.status))}>
                        {review.status.replace(/_/g, ' ')}
                      </span>
                      <span className="text-sm text-secondary-500 capitalize">{review.mapping_type.replace(/_/g, ' ')}</span>
                      <span className="text-sm text-secondary-500">
                        Confidence: {review.confidence_score ? (review.confidence_score * 100).toFixed(0) + '%' : 'N/A'}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-secondary-600 mb-2">
                      <span className="font-medium">{review.source_entity_type}</span>
                      <ChevronRight className="w-4 h-4" />
                      <span className="font-medium">{review.target_entity_type}</span>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-secondary-500">
                      <span>{review.source_entity_id} → {review.target_entity_id}</span>
                      {review.reviewed_by && <span>Reviewed by {review.reviewed_by} on {review.reviewed_at ? formatDate(review.reviewed_at) : ''}</span>}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setExpandedId(expandedId === review.id ? null : review.id)}
                      className="p-2 hover:bg-secondary-100 rounded"
                    >
                      <ChevronDown className={cn('w-4 h-4', expandedId === review.id && 'rotate-180')} />
                    </button>
                  </div>
                </div>

                {/* Expanded Details */}
                {expandedId === review.id && (
                  <div className="mt-4 pt-4 border-t border-secondary-200 animate-slide-up">
                    <div className="mb-4">
                      <h4 className="font-medium text-secondary-900 mb-2">AI Reasoning</h4>
                      <p className="text-sm text-secondary-600 bg-secondary-50 p-3 rounded">{review.ai_reasoning || 'No reasoning provided'}</p>
                    </div>
                    
                    {review.status === 'proposed' || review.status === 'needs_review' ? (
                      <div className="space-y-3">
                        <h4 className="font-medium text-secondary-900 mb-2">Your Decision</h4>
                        <textarea
                          placeholder="Add comments (required for reject/needs more info)..."
                          className="input mb-2"
                          rows={3}
                          data-review-id={review.id}
                        />
                        <div className="flex gap-2">
                          <button
                            onClick={() => {
                              const textarea = document.querySelector(`textarea[data-review-id="${review.id}"]`) as HTMLTextAreaElement;
                              handleDecision(review.id, 'accept', textarea?.value || '');
                            }}
                            className="btn-success"
                          >
                            <CheckCircle className="w-4 h-4 mr-1" />
                            Accept
                          </button>
                          <button
                            onClick={() => {
                              const textarea = document.querySelector(`textarea[data-review-id="${review.id}"]`) as HTMLTextAreaElement;
                              if (!textarea?.value.trim()) {
                                alert('Please add comments for rejection');
                                return;
                              }
                              handleDecision(review.id, 'reject', textarea.value);
                            }}
                            className="btn-danger"
                          >
                            <XCircle className="w-4 h-4 mr-1" />
                            Reject
                          </button>
                          <button
                            onClick={() => {
                              const textarea = document.querySelector(`textarea[data-review-id="${review.id}"]`) as HTMLTextAreaElement;
                              if (!textarea?.value.trim()) {
                                alert('Please add comments');
                                return;
                              }
                              handleDecision(review.id, 'needs_more_info', textarea.value);
                            }}
                            className="btn-warning"
                          >
                            <AlertCircle className="w-4 h-4 mr-1" />
                            Needs More Info
                          </button>
                        </div>
                      </div>
                    ) : review.review_comments ? (
                      <div>
                        <h4 className="font-medium text-secondary-900 mb-2">Review Comments</h4>
                        <p className="text-sm text-secondary-600 bg-secondary-50 p-3 rounded">{review.review_comments}</p>
                      </div>
                    ) : null}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
        {filtered.length === 0 && !loading && (
          <div className="p-8 text-center text-secondary-500">No mappings found</div>
        )}
      </div>
    </div>
  );
}