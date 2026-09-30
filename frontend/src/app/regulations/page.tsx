'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Search, Filter, ChevronDown, FileText, ExternalLink } from 'lucide-react';
import { api, Regulation } from '@/lib/api';
import { cn, formatDate, getStatusColor } from '@/lib/utils';

export default function RegulationsPage() {
  const [regulations, setRegulations] = useState<Regulation[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [sortBy, setSortBy] = useState<'title' | 'jurisdiction' | 'effective_date'>('title');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await api.getRegulations({ limit: 100 });
        setRegulations(response.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const filtered = regulations
    .filter(r => 
      r.title.toLowerCase().includes(search.toLowerCase()) ||
      r.short_name?.toLowerCase().includes(search.toLowerCase()) ||
      r.jurisdiction?.toLowerCase().includes(search.toLowerCase())
    )
    .filter(r => !statusFilter || r.status === statusFilter)
    .sort((a, b) => {
      if (sortBy === 'title') return a.title.localeCompare(b.title);
      if (sortBy === 'jurisdiction') return (a.jurisdiction || '').localeCompare(b.jurisdiction || '');
      return new Date(b.effective_date || 0).getTime() - new Date(a.effective_date || 0).getTime();
    });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">Regulations</h1>
          <p className="text-secondary-500 mt-1">Manage regulatory frameworks and their sections</p>
        </div>
        <button className="btn-primary opacity-50 cursor-not-allowed" disabled title="Regulation creation is not part of this demo">
          Add Regulation
        </button>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-secondary-400" />
            <input
              type="text"
              placeholder="Search regulations..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="input pl-10"
            />
          </div>
          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            className="input w-auto"
          >
            <option value="">All Statuses</option>
            <option value="active">Active</option>
            <option value="superseded">Superseded</option>
            <option value="draft">Draft</option>
          </select>
          <select
            value={sortBy}
            onChange={e => setSortBy(e.target.value as any)}
            className="input w-auto"
          >
            <option value="title">Sort by Title</option>
            <option value="jurisdiction">Sort by Jurisdiction</option>
            <option value="effective_date">Sort by Effective Date</option>
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
                  <th>Regulation</th>
                  <th>Jurisdiction</th>
                  <th>Regulator</th>
                  <th>Effective Date</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(reg => (
                  <tr key={reg.id}>
                    <td>
                      <span className="font-medium text-secondary-900" title={reg.id}>
                        {reg.title}
                      </span>
                      {reg.short_name && <p className="text-sm text-secondary-500">{reg.short_name}</p>}
                    </td>
                    <td className="text-secondary-600">{reg.jurisdiction || '-'}</td>
                    <td className="text-secondary-600">{reg.regulator || '-'}</td>
                    <td className="text-secondary-600">{reg.effective_date ? formatDate(reg.effective_date) : '-'}</td>
                    <td>
                      <span className={cn('badge', getStatusColor(reg.status))}>
                        {reg.status}
                      </span>
                    </td>

                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {filtered.length === 0 && !loading && (
          <div className="p-8 text-center text-secondary-500">No regulations found</div>
        )}
      </div>
    </div>
  );
}