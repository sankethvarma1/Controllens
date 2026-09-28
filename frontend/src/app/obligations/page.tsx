'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Search, Filter, Target, AlertTriangle, ExternalLink } from 'lucide-react';
import { api, Obligation, ObligationCoverageItem } from '@/lib/api';
import { cn, getSeverityColor, getRiskColor, truncate } from '@/lib/utils';

export default function ObligationsPage() {
  const [obligations, setObligations] = useState<Obligation[]>([]);
  const [coverageData, setCoverageData] = useState<ObligationCoverageItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [regulationFilter, setRegulationFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [riskFilter, setRiskFilter] = useState('');
  const [showCoverage, setShowCoverage] = useState(false);
  const [regulations, setRegulations] = useState<Array<{id: string, title: string, short_name: string}>>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [oblResponse, covResponse, regResponse] = await Promise.all([
          api.getObligations({ limit: 200 }),
          api.getAllObligationCoverage(),
          api.getRegulations({ limit: 50 })
        ]);
        setObligations(oblResponse.data);
        setCoverageData(covResponse.data.obligations || []);
        setRegulations(regResponse.data.map((r: any) => ({ id: r.id, title: r.title, short_name: r.short_name })));
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const getCoverageStatus = (obligationId: string) => {
    const cov = coverageData.find(c => c.obligation_id === obligationId);
    return cov?.coverage_status || 'unknown';
  };

  const getCoverageBadge = (status: string) => {
    switch (status) {
      case 'covered': return 'badge-success';
      case 'partial_evidence': return 'badge-warning';
      case 'no_evidence': return 'badge-danger';
      case 'no_controls': return 'badge-danger';
      default: return 'badge-neutral';
    }
  };

  const filtered = obligations
    .filter(o => 
      o.obligation_text.toLowerCase().includes(search.toLowerCase()) ||
      o.category?.toLowerCase().includes(search.toLowerCase())
    )
    .filter(o => !regulationFilter || o.regulation_id === regulationFilter)
    .filter(o => !categoryFilter || o.category === categoryFilter)
    .filter(o => !riskFilter || o.risk_level === riskFilter);

  const categories = [...new Set(obligations.map(o => o.category).filter(Boolean))] as string[];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">Obligations</h1>
          <p className="text-secondary-500 mt-1">Track regulatory obligations and their control coverage</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowCoverage(!showCoverage)}
            className={cn('btn', showCoverage ? 'btn-primary' : 'btn-outline')}
          >
            {showCoverage ? 'Hide Coverage' : 'Show Coverage'}
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-secondary-400" />
            <input
              type="text"
              placeholder="Search obligations..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="input pl-10"
            />
          </div>
          <select
            value={regulationFilter}
            onChange={e => setRegulationFilter(e.target.value)}
            className="input w-auto min-w-[200px]"
          >
            <option value="">All Regulations</option>
            {regulations.map(r => (
              <option key={r.id} value={r.id}>{r.short_name || r.title}</option>
            ))}
          </select>
          <select
            value={categoryFilter}
            onChange={e => setCategoryFilter(e.target.value)}
            className="input w-auto min-w-[180px]"
          >
            <option value="">All Categories</option>
            {categories.map(c => (
              <option key={c} value={c}>{c.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</option>
            ))}
          </select>
          <select
            value={riskFilter}
            onChange={e => setRiskFilter(e.target.value)}
            className="input w-auto"
          >
            <option value="">All Risk Levels</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
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
                  <th className="w-8"></th>
                  <th>Obligation</th>
                  <th>Regulation</th>
                  <th>Category</th>
                  <th>Risk</th>
                  {showCoverage && (
                    <>
                      <th>Policies</th>
                      <th>Controls</th>
                      <th>Verified Evidence</th>
                      <th>Coverage</th>
                    </>
                  )}
                  <th className="w-24">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(obl => {
                  const coverage = coverageData.find(c => c.obligation_id === obl.id);
                  const status = getCoverageStatus(obl.id);
                  return (
                    <tr key={obl.id}>
                      <td>
                        <span className={cn('badge', getRiskColor(obl.risk_level))}>
                          {obl.risk_level}
                        </span>
                      </td>
                      <td>
                        <Link href={`/obligations/${obl.id}`} className="font-medium text-secondary-900 hover:text-primary-600 max-w-xs truncate block">
                          {truncate(obl.obligation_text, 100)}
                        </Link>
                      </td>
                      <td className="text-secondary-600">
                        {regulations.find(r => r.id === obl.regulation_id)?.short_name || obl.regulation_id}
                      </td>
                      <td className="text-secondary-600 capitalize">{obl.category?.replace(/_/g, ' ')}</td>
                      <td>
                        <span className={cn('badge', getRiskColor(obl.risk_level))}>
                          {obl.risk_level}
                        </span>
                      </td>
                      {showCoverage && (
                        <>
                          <td className="text-secondary-600">{coverage?.policy_count || 0}</td>
                          <td className="text-secondary-600">{coverage?.control_count || 0}</td>
                          <td className="text-secondary-600">{coverage?.verified_evidence_count || 0}</td>
                          <td>
                            <span className={cn('badge', getCoverageBadge(status))}>
                              {status.replace(/_/g, ' ')}
                            </span>
                          </td>
                        </>
                      )}
                      <td>
                        <Link href={`/obligations/${obl.id}`} className="p-1.5 hover:bg-secondary-100 rounded" title="View Details">
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
          <div className="p-8 text-center text-secondary-500">No obligations found</div>
        )}
      </div>
    </div>
  );
}