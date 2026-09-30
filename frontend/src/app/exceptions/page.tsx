'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Search, AlertTriangle, AlertCircle, Clock, CheckCircle, XCircle, ExternalLink, Filter, MoreVertical } from 'lucide-react';
import { api, ExceptionItem } from '@/lib/api';
import { cn, formatDate, getSeverityColor, getStatusColor, calculateDaysBetween } from '@/lib/utils';

export default function ExceptionsPage() {
  const [exceptions, setExceptions] = useState<ExceptionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  // Default to "All time" so seeded historical records are visible;
  // narrower ranges can still be selected below.
  const [daysFilter, setDaysFilter] = useState(3650);
  const [controls, setControls] = useState<Array<{id: string, name: string}>>([]);
  const [processes, setProcesses] = useState<Array<{id: string, name: string}>>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [excResponse, ctlResponse, procResponse] = await Promise.all([
          api.getExceptions({ days: daysFilter, limit: 200 }),
          api.getControls({ limit: 200 }),
          api.getProcesses({ limit: 100 })
        ]);
        setExceptions(excResponse.data);
        setControls(ctlResponse.data);
        setProcesses(procResponse.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [daysFilter]);

  const types = [...new Set(exceptions.map(e => e.exception_type).filter(Boolean))] as string[];

  const filtered = exceptions
    .filter(e => 
      e.title?.toLowerCase().includes(search.toLowerCase()) ||
      e.description?.toLowerCase().includes(search.toLowerCase()) ||
      e.exception_number.toLowerCase().includes(search.toLowerCase())
    )
    .filter(e => !typeFilter || e.exception_type === typeFilter)
    .filter(e => !severityFilter || e.severity === severityFilter)
    .filter(e => !statusFilter || e.status === statusFilter);

  const openCount = exceptions.filter(e => e.status === 'open' || e.status === 'investigating').length;
  const criticalCount = exceptions.filter(e => e.severity === 'critical').length;
  const highCount = exceptions.filter(e => e.severity === 'high').length;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">Exceptions</h1>
          <p className="text-secondary-500 mt-1">Track and remediate control failures and policy violations</p>
        </div>
        <div className="flex gap-2">
          <button className="btn-primary opacity-50 cursor-not-allowed" disabled title="Exception logging is not part of this demo">Log Exception</button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="card p-4 border-l-4 border-danger-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-secondary-500">Open Exceptions</p>
              <p className="text-2xl font-bold text-secondary-900">{openCount}</p>
            </div>
            <AlertTriangle className="w-8 h-8 text-danger-500" />
          </div>
        </div>
        <div className="card p-4 border-l-4 border-danger-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-secondary-500">Critical</p>
              <p className="text-2xl font-bold text-danger-600">{criticalCount}</p>
            </div>
            <AlertCircle className="w-8 h-8 text-danger-500" />
          </div>
        </div>
        <div className="card p-4 border-l-4 border-warning-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-secondary-500">High</p>
              <p className="text-2xl font-bold text-warning-600">{highCount}</p>
            </div>
            <AlertCircle className="w-8 h-8 text-warning-500" />
          </div>
        </div>
        <div className="card p-4 border-l-4 border-primary-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-secondary-500">Total ({daysFilter >= 3650 ? 'all time' : `${daysFilter} days`})</p>
              <p className="text-2xl font-bold text-secondary-900">{exceptions.length}</p>
            </div>
            <Clock className="w-8 h-8 text-primary-500" />
          </div>
        </div>
        <div className="card p-4 border-l-4 border-success-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-secondary-500">Remediated</p>
              <p className="text-2xl font-bold text-success-600">
                {exceptions.filter(e => e.status === 'remediated' || e.status === 'closed').length}
              </p>
            </div>
            <CheckCircle className="w-8 h-8 text-success-500" />
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
              placeholder="Search exceptions..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="input pl-10"
            />
          </div>
          <select value={typeFilter} onChange={e => setTypeFilter(e.target.value)} className="input w-auto">
            <option value="">All Types</option>
            {types.map(t => <option key={t} value={t}>{t.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</option>)}
          </select>
          <select value={severityFilter} onChange={e => setSeverityFilter(e.target.value)} className="input w-auto">
            <option value="">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
          <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="input w-auto">
            <option value="">All Statuses</option>
            <option value="open">Open</option>
            <option value="investigating">Investigating</option>
            <option value="remediated">Remediated</option>
            <option value="closed">Closed</option>
            <option value="accepted_risk">Accepted Risk</option>
          </select>
          <select value={daysFilter} onChange={e => setDaysFilter(Number(e.target.value))} className="input w-auto">
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
            <option value={180}>Last 180 days</option>
            <option value={365}>Last year</option>
            <option value={3650}>All time</option>
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
                  <th>Exception</th>
                  <th>Type</th>
                  <th>Severity</th>
                  <th>Control</th>
                  <th>Process</th>
                  <th>Detected</th>
                  <th>Days Open</th>
                  <th>Assigned To</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(exc => {
                  const daysOpen = calculateDaysBetween(exc.detected_date, exc.actual_resolution_date || new Date().toISOString());
                  return (
                    <tr key={exc.id}>
                      <td>
                        <span className="font-medium text-secondary-900" title={exc.id}>
                          {exc.exception_number}
                        </span>
                        <p className="text-sm text-secondary-500 max-w-xs truncate">{exc.title || 'No title'}</p>
                      </td>
                      <td className="text-secondary-600 capitalize">{exc.exception_type.replace(/_/g, ' ')}</td>
                      <td>
                        <span className={cn('badge', getSeverityColor(exc.severity))}>
                          {exc.severity}
                        </span>
                      </td>
                      <td className="text-secondary-600">
                        {controls.find(c => c.id === exc.control_id)?.name || exc.control_id || '-'}
                      </td>
                      <td className="text-secondary-600">
                        {processes.find(p => p.id === exc.process_id)?.name || exc.process_id || '-'}
                      </td>
                      <td className="text-secondary-600">{formatDate(exc.detected_date)}</td>
                      <td className={cn(daysOpen > 30 ? 'text-danger-600 font-medium' : 'text-secondary-600')}>
                        {daysOpen} days
                      </td>
                      <td className="text-secondary-600">{exc.assigned_to || '-'}</td>
                      <td>
                        <span className={cn('badge', getStatusColor(exc.status))}>
                          {exc.status.replace(/_/g, ' ')}
                        </span>
                      </td>

                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
        {filtered.length === 0 && !loading && (
          <div className="p-8 text-center text-secondary-500">No exceptions found</div>
        )}
      </div>
    </div>
  );
}