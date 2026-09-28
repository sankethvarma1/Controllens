'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Search, Shield, AlertCircle, Clock, CheckCircle, XCircle, ExternalLink, TrendingUp } from 'lucide-react';
import { api, Control } from '@/lib/api';
import { cn, formatDate, getStatusColor, isOverdue } from '@/lib/utils';

export default function ControlsPage() {
  const [controls, setControls] = useState<Control[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('active');
  const [effectivenessFilter, setEffectivenessFilter] = useState('');
  const [processes, setProcesses] = useState<Array<{id: string, name: string}>>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [ctlResponse, procResponse] = await Promise.all([
          api.getControls({ limit: 200 }),
          api.getProcesses({ limit: 100 })
        ]);
        setControls(ctlResponse.data);
        setProcesses(procResponse.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const types = [...new Set(controls.map(c => c.control_type).filter(Boolean))] as string[];

  const filtered = controls
    .filter(c => 
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      c.description?.toLowerCase().includes(search.toLowerCase())
    )
    .filter(c => !typeFilter || c.control_type === typeFilter)
    .filter(c => !statusFilter || c.status === statusFilter)
    .filter(c => !effectivenessFilter || c.operating_effectiveness === effectivenessFilter);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">Controls</h1>
          <p className="text-secondary-500 mt-1">Manage and monitor control effectiveness</p>
        </div>
        <Link href="/controls/new" className="btn-primary">
          Add Control
        </Link>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-secondary-400" />
            <input
              type="text"
              placeholder="Search controls..."
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
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="deprecated">Deprecated</option>
            <option value="">All</option>
          </select>
          <select value={effectivenessFilter} onChange={e => setEffectivenessFilter(e.target.value)} className="input w-auto">
            <option value="">All Effectiveness</option>
            <option value="effective">Effective</option>
            <option value="partially_effective">Partially Effective</option>
            <option value="ineffective">Ineffective</option>
          </select>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card p-4">
          <p className="text-sm text-secondary-500">Total Active</p>
          <p className="text-2xl font-bold text-secondary-900">{controls.filter(c => c.status === 'active').length}</p>
        </div>
        <div className="card p-4">
          <p className="text-sm text-secondary-500">Overdue Testing</p>
          <p className="text-2xl font-bold text-danger-600">
            {controls.filter(c => c.status === 'active' && c.next_test_date && isOverdue(c.next_test_date)).length}
          </p>
        </div>
        <div className="card p-4">
          <p className="text-sm text-secondary-500">Ineffective</p>
          <p className="text-2xl font-bold text-danger-600">
            {controls.filter(c => c.operating_effectiveness === 'ineffective').length}
          </p>
        </div>
        <div className="card p-4">
          <p className="text-sm text-secondary-500">Partially Effective</p>
          <p className="text-2xl font-bold text-warning-600">
            {controls.filter(c => c.operating_effectiveness === 'partially_effective').length}
          </p>
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
                  <th>Control</th>
                  <th>Type</th>
                  <th>Process</th>
                  <th>Frequency</th>
                  <th>Automation</th>
                  <th>Design Eff.</th>
                  <th>Operating Eff.</th>
                  <th>Next Test</th>
                  <th>Status</th>
                  <th className="w-24">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(ctl => {
                  const overdue = ctl.next_test_date && isOverdue(ctl.next_test_date);
                  return (
                    <tr key={ctl.id}>
                      <td>
                        <Link href={`/controls/${ctl.id}`} className="font-medium text-secondary-900 hover:text-primary-600">
                          {ctl.name}
                        </Link>
                      </td>
                      <td className="capitalize">{ctl.control_type}</td>
                      <td className="text-secondary-600">
                        {processes.find(p => p.id === ctl.process_id)?.name || ctl.process_id || '-'}
                      </td>
                      <td className="text-secondary-600">{ctl.frequency || '-'}</td>
                      <td className="text-secondary-600 capitalize">{ctl.automation_level?.replace(/_/g, ' ')}</td>
                      <td>
                        <span className={cn('badge', 
                          ctl.design_effectiveness === 'effective' ? 'badge-success' :
                          ctl.design_effectiveness === 'partially_effective' ? 'badge-warning' :
                          ctl.design_effectiveness === 'ineffective' ? 'badge-danger' : 'badge-neutral'
                        )}>
                          {ctl.design_effectiveness?.replace(/_/g, ' ') || '-'}
                        </span>
                      </td>
                      <td>
                        <span className={cn('badge',
                          ctl.operating_effectiveness === 'effective' ? 'badge-success' :
                          ctl.operating_effectiveness === 'partially_effective' ? 'badge-warning' :
                          ctl.operating_effectiveness === 'ineffective' ? 'badge-danger' : 'badge-neutral'
                        )}>
                          {ctl.operating_effectiveness?.replace(/_/g, ' ') || '-'}
                        </span>
                      </td>
                      <td className={cn(overdue ? 'text-danger-600 font-medium' : 'text-secondary-600')}>
                        {ctl.next_test_date ? formatDate(ctl.next_test_date) : '-'}
                        {overdue && <span className="ml-1 text-xs text-danger-600">(Overdue)</span>}
                      </td>
                      <td>
                        <span className={cn('badge', getStatusColor(ctl.status))}>
                          {ctl.status}
                        </span>
                      </td>
                      <td>
                        <Link href={`/controls/${ctl.id}`} className="p-1.5 hover:bg-secondary-100 rounded" title="View Details">
                          <ExternalLink className="w-4 h-4" />
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
        {filtered.length === 0 && !loading && (
          <div className="p-8 text-center text-secondary-500">No controls found</div>
        )}
      </div>
    </div>
  );
}