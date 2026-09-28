'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Search, FileCheck, AlertTriangle, Clock, CheckCircle, XCircle, ExternalLink, Download, Filter } from 'lucide-react';
import { api, EvidenceItem } from '@/lib/api';
import { cn, formatDate, getStatusColor, isOverdue } from '@/lib/utils';

export default function EvidencePage() {
  const [evidence, setEvidence] = useState<EvidenceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('verified');
  const [controls, setControls] = useState<Array<{id: string, name: string}>>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [evResponse, ctlResponse] = await Promise.all([
          api.getEvidence({ limit: 200 }),
          api.getControls({ limit: 200 })
        ]);
        setEvidence(evResponse.data);
        setControls(ctlResponse.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const types = [...new Set(evidence.map(e => e.evidence_type).filter(Boolean))] as string[];

  const filtered = evidence
    .filter(e => 
      e.title.toLowerCase().includes(search.toLowerCase()) ||
      e.description?.toLowerCase().includes(search.toLowerCase())
    )
    .filter(e => !typeFilter || e.evidence_type === typeFilter)
    .filter(e => !statusFilter || e.status === statusFilter);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">Evidence</h1>
          <p className="text-secondary-500 mt-1">Manage and verify control evidence</p>
        </div>
        <div className="flex gap-2">
          <button className="btn-outline">Import Evidence</button>
        </div>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card p-4">
          <p className="text-sm text-secondary-500">Total Evidence</p>
          <p className="text-2xl font-bold text-secondary-900">{evidence.length}</p>
        </div>
        <div className="card p-4">
          <p className="text-sm text-secondary-500">Verified</p>
          <p className="text-2xl font-bold text-success-600">
            {evidence.filter(e => e.status === 'verified').length}
          </p>
        </div>
        <div className="card p-4">
          <p className="text-sm text-secondary-500">Pending</p>
          <p className="text-2xl font-bold text-warning-600">
            {evidence.filter(e => e.status === 'submitted').length}
          </p>
        </div>
        <div className="card p-4">
          <p className="text-sm text-secondary-500">Expired</p>
          <p className="text-2xl font-bold text-danger-600">
            {evidence.filter(e => e.expiry_date && isOverdue(e.expiry_date)).length}
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-secondary-400" />
            <input
              type="text"
              placeholder="Search evidence..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="input pl-10"
            />
          </div>
          <select value={typeFilter} onChange={e => setTypeFilter(e.target.value)} className="input w-auto">
            <option value="">All Types</option>
            {types.map(t => <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
          </select>
          <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="input w-auto">
            <option value="verified">Verified</option>
            <option value="submitted">Submitted</option>
            <option value="rejected">Rejected</option>
            <option value="expired">Expired</option>
            <option value="">All</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="card">
        {loading ? (
          <div className="p-8 text-center">
            <div className="animate-pulse flex justify-center">
              <div className="w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full" />
            </div>
          </div>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Evidence</th>
                  <th>Type</th>
                  <th>Control</th>
                  <th>Collected</th>
                  <th>Period</th>
                  <th>Expiry</th>
                  <th>Source</th>
                  <th>Status</th>
                  <th className="w-24">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(ev => {
                  const expired = ev.expiry_date && isOverdue(ev.expiry_date);
                  return (
                    <tr key={ev.id}>
                      <td>
                        <Link href={`/evidence/${ev.id}`} className="font-medium text-secondary-900 hover:text-primary-600 max-w-xs truncate block">
                          {ev.title}
                        </Link>
                        {ev.description && <p className="text-sm text-secondary-500 truncate max-w-xs">{ev.description}</p>}
                      </td>
                      <td className="capitalize">{ev.evidence_type}</td>
                      <td className="text-secondary-600">
                        {controls.find(c => c.id === ev.control_id)?.name || ev.control_id}
                      </td>
                      <td className="text-secondary-600">{ev.collected_at ? formatDate(ev.collected_at) : '-'}</td>
                      <td className="text-secondary-600">
                        {ev.period_start && ev.period_end ? 
                          `${formatDate(ev.period_start)} - ${formatDate(ev.period_end)}` : '-'}
                      </td>
                      <td className={cn(expired ? 'text-danger-600 font-medium' : 'text-secondary-600')}>
                        {ev.expiry_date ? formatDate(ev.expiry_date) : '-'}
                        {expired && <span className="ml-1 text-xs text-danger-600">(Expired)</span>}
                      </td>
                      <td className="text-secondary-600">{ev.source_system || '-'}</td>
                      <td>
                        <span className={cn('badge', getStatusColor(ev.status))}>
                          {ev.status}
                        </span>
                      </td>
                      <td>
                        <div className="flex items-center gap-1">
                          <Link href={`/evidence/${ev.id}`} className="p-1.5 hover:bg-secondary-100 rounded" title="View">
                            <ExternalLink className="w-4 h-4" />
                          </Link>
                          {ev.file_path && (
                            <a href={ev.file_path} target="_blank" rel="noopener noreferrer" className="p-1.5 hover:bg-secondary-100 rounded" title="Download">
                              <Download className="w-4 h-4" />
                            </a>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
        {filtered.length === 0 && !loading && (
          <div className="p-8 text-center text-secondary-500">No evidence found</div>
        )}
      </div>
    </div>
  );
}