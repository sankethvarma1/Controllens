'use client';

import { useEffect, useState } from 'react';
import { Search, Filter, Clock, User, Database, Edit, Trash2, Eye, ExternalLink, ChevronDown, ChevronUp } from 'lucide-react';
import { api, AuditEventResponse } from '@/lib/api';
import { cn, formatDateTime, getStatusColor } from '@/lib/utils';

export default function AuditPage() {
  const [events, setEvents] = useState<AuditEventResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [entityTypeFilter, setEntityTypeFilter] = useState('');
  const [actionFilter, setActionFilter] = useState('');
  const [daysFilter, setDaysFilter] = useState(30);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await api.getAuditTrail({ days: daysFilter, limit: 500 });
        setEvents(response.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [daysFilter]);

  const filtered = events
    .filter(e => 
      e.action?.toLowerCase().includes(search.toLowerCase()) ||
      e.entity_type?.toLowerCase().includes(search.toLowerCase()) ||
      e.entity_id?.toLowerCase().includes(search.toLowerCase()) ||
      e.user_id?.toLowerCase().includes(search.toLowerCase())
    )
    .filter(e => !entityTypeFilter || e.entity_type === entityTypeFilter)
    .filter(e => !actionFilter || e.action === actionFilter);

  const entityTypes = [...new Set(events.map(e => e.entity_type).filter(Boolean))] as string[];
  const actions = [...new Set(events.map(e => e.action).filter(Boolean))] as string[];

  const getActionIcon = (action: string) => {
    if (action.includes('create')) return <Database className="w-4 h-4 text-success-600" />;
    if (action.includes('update') || action.includes('edit')) return <Edit className="w-4 h-4 text-primary-600" />;
    if (action.includes('delete')) return <Trash2 className="w-4 h-4 text-danger-600" />;
    if (action.includes('review') || action.includes('approve') || action.includes('reject')) return <Eye className="w-4 h-4 text-warning-600" />;
    return <Clock className="w-4 h-4 text-secondary-600" />;
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">Audit Trail</h1>
          <p className="text-secondary-500 mt-1">Track all system changes and user actions</p>
        </div>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-secondary-400" />
            <input
              type="text"
              placeholder="Search audit events..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="input pl-10"
            />
          </div>
          <select value={entityTypeFilter} onChange={e => setEntityTypeFilter(e.target.value)} className="input w-auto">
            <option value="">All Entity Types</option>
            {entityTypes.map(t => <option key={t} value={t}>{t.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</option>)}
          </select>
          <select value={actionFilter} onChange={e => setActionFilter(e.target.value)} className="input w-auto min-w-[180px]">
            <option value="">All Actions</option>
            {actions.map(a => <option key={a} value={a}>{a.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</option>)}
          </select>
          <select value={daysFilter} onChange={e => setDaysFilter(Number(e.target.value))} className="input w-auto">
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
            <option value={180}>Last 180 days</option>
            <option value={365}>Last year</option>
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
                  <th className="w-12"></th>
                  <th>Timestamp</th>
                  <th>User</th>
                  <th>Action</th>
                  <th>Entity</th>
                  <th>Entity ID</th>
                  <th className="w-32">Details</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(event => (
                  <tr key={event.id}>
                    <td>
                      <button
                        onClick={() => setExpandedId(expandedId === event.id ? null : event.id)}
                        className="p-1 hover:bg-secondary-100 rounded"
                      >
                        {expandedId === event.id ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                      </button>
                    </td>
                    <td className="text-secondary-600 whitespace-nowrap">{event.timestamp ? formatDateTime(event.timestamp) : '-'}</td>
                    <td>
                      <div className="flex items-center gap-2">
                        <User className="w-4 h-4 text-secondary-400" />
                        <span className="font-medium text-secondary-900">{event.user_id}</span>
                        {event.user_role && <span className="text-xs text-secondary-500">({event.user_role})</span>}
                      </div>
                    </td>
                    <td>
                      <div className="flex items-center gap-2">
                        {getActionIcon(event.action || '')}
                        <span className="capitalize text-secondary-700">{(event.action || '').replace(/_/g, ' ')}</span>
                      </div>
                    </td>
                    <td className="text-secondary-600 capitalize">{event.entity_type?.replace(/_/g, ' ')}</td>
                    <td className="font-mono text-sm text-secondary-600">{event.entity_id || '-'}</td>
                    <td>
                      <button
                        onClick={() => setExpandedId(expandedId === event.id ? null : event.id)}
                        className="p-1.5 hover:bg-secondary-100 rounded"
                        title="View Details"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {filtered.length === 0 && !loading && (
          <div className="p-8 text-center text-secondary-500">No audit events found</div>
        )}
      </div>

      {/* Expanded Details Modal */}
      {expandedId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={() => setExpandedId(null)}>
          <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[80vh] overflow-hidden" onClick={e => e.stopPropagation()}>
            <div className="p-4 border-b border-secondary-200 flex items-center justify-between">
              <h3 className="font-semibold text-secondary-900">Event Details</h3>
              <button onClick={() => setExpandedId(null)} className="p-1 hover:bg-secondary-100 rounded">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
              </button>
            </div>
            <div className="p-4 overflow-y-auto">
              {(() => {
                const event = events.find(e => e.id === expandedId);
                if (!event) return null;
                return (
                  <dl className="space-y-4 text-sm">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <dt className="text-secondary-500">Event ID</dt>
                        <dd className="font-mono text-secondary-900">{event.id}</dd>
                      </div>
                      <div>
                        <dt className="text-secondary-500">Timestamp</dt>
                        <dd className="font-mono text-secondary-900">{formatDateTime(event.timestamp)}</dd>
                      </div>
                      <div>
                        <dt className="text-secondary-500">User</dt>
                        <dd className="text-secondary-900">{event.user_id}</dd>
                      </div>
                      <div>
                        <dt className="text-secondary-500">Role</dt>
                        <dd className="text-secondary-900">{event.user_role || '-'}</dd>
                      </div>
                      <div>
                        <dt className="text-secondary-500">Action</dt>
                        <dd className="capitalize text-secondary-900">{event.action?.replace(/_/g, ' ')}</dd>
                      </div>
                      <div>
                        <dt className="text-secondary-500">Entity Type</dt>
                        <dd className="capitalize text-secondary-900">{event.entity_type?.replace(/_/g, ' ')}</dd>
                      </div>
                      <div>
                        <dt className="text-secondary-500">Entity ID</dt>
                        <dd className="font-mono text-secondary-900">{event.entity_id || '-'}</dd>
                      </div>
                      <div>
                        <dt className="text-secondary-500">IP Address</dt>
                        <dd className="font-mono text-secondary-900">{event.ip_address || '-'}</dd>
                      </div>
                    </div>
                    {event.old_values && (
                      <div>
                        <dt className="text-secondary-500">Old Values</dt>
                        <dd className="mt-1 p-3 bg-secondary-50 rounded font-mono text-xs overflow-x-auto">
                          {JSON.stringify(event.old_values, null, 2)}
                        </dd>
                      </div>
                    )}
                    {event.new_values && (
                      <div>
                        <dt className="text-secondary-500">New Values</dt>
                        <dd className="mt-1 p-3 bg-secondary-50 rounded font-mono text-xs overflow-x-auto">
                          {JSON.stringify(event.new_values, null, 2)}
                        </dd>
                      </div>
                    )}
                    {event.user_agent && (
                      <div>
                        <dt className="text-secondary-500">User Agent</dt>
                        <dd className="mt-1 p-3 bg-secondary-50 rounded font-mono text-xs overflow-x-auto truncate">
                          {event.user_agent}
                        </dd>
                      </div>
                    )}
                  </dl>
                );
              })()}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}