'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Search, ChevronRight, Target, FileText, Shield, FileCheck, AlertTriangle, ExternalLink, Filter } from 'lucide-react';
import { api, TraceabilityChain, Obligation } from '@/lib/api';
import { cn, getRiskColor, getSeverityColor, getStatusColor, truncate } from '@/lib/utils';

const CHAIN_STEPS = [
  { key: 'regulation', label: 'Regulation', icon: FileText, color: 'bg-blue-500' },
  { key: 'obligation', label: 'Obligation', icon: Target, color: 'bg-purple-500' },
  { key: 'policies', label: 'Policies', icon: FileText, color: 'bg-indigo-500' },
  { key: 'processes', label: 'Processes', icon: Shield, color: 'bg-teal-500' },
  { key: 'controls', label: 'Controls', icon: Shield, color: 'bg-green-500' },
  { key: 'evidence', label: 'Evidence', icon: FileCheck, color: 'bg-emerald-500' },
  { key: 'exceptions', label: 'Exceptions', icon: AlertTriangle, color: 'bg-red-500' },
];

export default function TraceabilityPage() {
  const [obligations, setObligations] = useState<Obligation[]>([]);
  const [selectedObligation, setSelectedObligation] = useState<string>('');
  const [chain, setChain] = useState<TraceabilityChain | null>(null);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [regulationFilter, setRegulationFilter] = useState('');
  const [riskFilter, setRiskFilter] = useState('');

  useEffect(() => {
    const fetchObligations = async () => {
      try {
        const response = await api.getObligations({ limit: 200 });
        setObligations(response.data);
      } catch (err) {
        console.error(err);
      }
    };
    fetchObligations();
  }, []);

  useEffect(() => {
    if (selectedObligation) {
      const fetchChain = async () => {
        setLoading(true);
        try {
          const response = await api.getTraceabilityChain(selectedObligation);
          setChain(response.data);
        } catch (err) {
          console.error(err);
          setChain(null);
        } finally {
          setLoading(false);
        }
      };
      fetchChain();
    } else {
      setChain(null);
    }
  }, [selectedObligation]);

  const filteredObligations = obligations
    .filter(o => 
      o.obligation_text.toLowerCase().includes(search.toLowerCase()) ||
      o.category?.toLowerCase().includes(search.toLowerCase())
    )
    .filter(o => !regulationFilter || o.regulation_id === regulationFilter)
    .filter(o => !riskFilter || o.risk_level === riskFilter);

  const regulations = [...new Set(obligations.map(o => o.regulation_id).filter(Boolean))] as string[];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">Traceability</h1>
          <p className="text-secondary-500 mt-1">Trace the complete chain from regulation to exception</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Obligation Selector */}
        <div className="lg:col-span-1 card h-fit sticky top-24">
          <div className="p-4 border-b border-secondary-200">
            <h2 className="text-lg font-semibold text-secondary-900">Select Obligation</h2>
          </div>
          <div className="p-4 space-y-4">
            <div>
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
              className="input"
            >
              <option value="">All Regulations</option>
              {regulations.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
            <select
              value={riskFilter}
              onChange={e => setRiskFilter(e.target.value)}
              className="input"
            >
              <option value="">All Risk Levels</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
          <div className="p-4 border-t border-secondary-200 max-h-[60vh] overflow-y-auto">
            {filteredObligations.map(obl => (
              <button
                key={obl.id}
                onClick={() => setSelectedObligation(obl.id)}
                className={cn(
                  'w-full text-left p-3 rounded-lg transition-colors',
                  selectedObligation === obl.id
                    ? 'bg-primary-50 border border-primary-200'
                    : 'hover:bg-secondary-50'
                )}
              >
                <div className="flex items-start gap-2">
                  <span className={cn('badge', getRiskColor(obl.risk_level))}>
                    {obl.risk_level}
                  </span>
                  <p className="text-sm font-medium text-secondary-900 truncate flex-1">
                    {truncate(obl.obligation_text, 80)}
                  </p>
                </div>
                <p className="text-xs text-secondary-500 mt-1">{obl.regulation_id}</p>
              </button>
            ))}
            {filteredObligations.length === 0 && (
              <p className="text-center text-secondary-500 py-4">No obligations match filters</p>
            )}
          </div>
        </div>

        {/* Traceability Chain */}
        <div className="lg:col-span-3">
          {!selectedObligation ? (
            <div className="card p-12 text-center">
              <Target className="w-16 h-16 text-secondary-300 mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-secondary-900 mb-2">Select an Obligation</h2>
              <p className="text-secondary-500">Choose an obligation from the left panel to view its complete traceability chain</p>
            </div>
          ) : loading ? (
            <div className="card p-12 text-center">
              <div className="animate-pulse flex justify-center">
                <div className="w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full" />
              </div>
              <p className="text-secondary-500 mt-4">Loading traceability chain...</p>
            </div>
          ) : chain ? (
            <div className="space-y-4">
              {/* Chain Overview */}
              <div className="card p-4">
                <div className="flex flex-wrap items-center gap-2">
                  {CHAIN_STEPS.map((step, i) => (
                    <div key={step.key} className="flex items-center gap-2">
                      <div className={cn('p-2 rounded-lg', step.color)}>
                        <step.icon className="w-4 h-4 text-white" />
                      </div>
                      <span className="font-medium text-secondary-900">{step.label}</span>
                      {i < CHAIN_STEPS.length - 1 && (
                        <ChevronRight className="w-4 h-4 text-secondary-400" />
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Chain Details */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Regulation & Obligation */}
                <div className="card p-4">
                  <h3 className="font-semibold text-secondary-900 mb-3 flex items-center gap-2">
                    <div className="p-1.5 bg-blue-100 rounded">
                      <FileText className="w-4 h-4 text-blue-600" />
                    </div>
                    Regulation
                  </h3>
                  <div className="space-y-2 text-sm">
                    <p><span className="font-medium">Title:</span> {chain.regulation?.title || 'N/A'}</p>
                    <p><span className="font-medium">Short Name:</span> {chain.regulation?.short_name || 'N/A'}</p>
                    <p><span className="font-medium">Jurisdiction:</span> {chain.regulation?.jurisdiction || 'N/A'}</p>
                  </div>
                </div>

                <div className="card p-4">
                  <h3 className="font-semibold text-secondary-900 mb-3 flex items-center gap-2">
                    <div className="p-1.5 bg-purple-100 rounded">
                      <Target className="w-4 h-4 text-purple-600" />
                    </div>
                    Obligation
                  </h3>
                  <div className="space-y-2 text-sm">
                    <p className="text-secondary-600">{chain.obligation?.obligation_text || 'N/A'}</p>
                    <p><span className="font-medium">Risk:</span> 
                      <span className={cn('badge ml-2', getRiskColor(chain.obligation?.risk_level))}>
                        {chain.obligation?.risk_level}
                      </span>
                    </p>
                    <p><span className="font-medium">Category:</span> {chain.obligation?.category?.replace(/_/g, ' ')}</p>
                  </div>
                </div>

                {/* Policies */}
                <div className="card p-4 md:col-span-2">
                  <h3 className="font-semibold text-secondary-900 mb-3 flex items-center gap-2">
                    <div className="p-1.5 bg-indigo-100 rounded">
                      <FileText className="w-4 h-4 text-indigo-600" />
                    </div>
                    Policies ({chain.policies?.length || 0})
                  </h3>
                  <div className="space-y-2">
                    {chain.policies?.length ? (
                      chain.policies.map((p: any) => (
                        <div key={p.id} className="p-3 bg-secondary-50 rounded-lg">
                          <Link href={`/policies/${p.id}`} className="font-medium text-secondary-900 hover:text-primary-600">
                            {p.title}
                          </Link>
                          <p className="text-sm text-secondary-500">{p.owner_department} • {p.status}</p>
                        </div>
                      ))
                    ) : (
                      <p className="text-secondary-500 text-center py-4">No policies linked</p>
                    )}
                  </div>
                </div>

                {/* Processes */}
                <div className="card p-4 md:col-span-2">
                  <h3 className="font-semibold text-secondary-900 mb-3 flex items-center gap-2">
                    <div className="p-1.5 bg-teal-100 rounded">
                      <Shield className="w-4 h-4 text-teal-600" />
                    </div>
                    Processes ({chain.processes?.length || 0})
                  </h3>
                  <div className="space-y-2">
                    {chain.processes?.length ? (
                      chain.processes.map((p: any) => (
                        <div key={p.id} className="p-3 bg-secondary-50 rounded-lg">
                          <Link href={`/processes/${p.id}`} className="font-medium text-secondary-900 hover:text-primary-600">
                            {p.name}
                          </Link>
                          <p className="text-sm text-secondary-500">{p.department} • Risk: {p.risk_rating}</p>
                        </div>
                      ))
                    ) : (
                      <p className="text-secondary-500 text-center py-4">No processes linked</p>
                    )}
                  </div>
                </div>

                {/* Controls */}
                <div className="card p-4 md:col-span-2">
                  <h3 className="font-semibold text-secondary-900 mb-3 flex items-center gap-2">
                    <div className="p-1.5 bg-green-100 rounded">
                      <Shield className="w-4 h-4 text-green-600" />
                    </div>
                    Controls ({chain.controls?.length || 0})
                  </h3>
                  <div className="space-y-2 max-h-96 overflow-y-auto">
                    {chain.controls?.length ? (
                      chain.controls.map((c: any) => (
                        <div key={c.id} className="p-3 bg-secondary-50 rounded-lg border border-secondary-200">
                          <div className="flex items-start justify-between">
                            <div>
                              <Link href={`/controls/${c.id}`} className="font-medium text-secondary-900 hover:text-primary-600">
                                {c.name}
                              </Link>
                              <p className="text-sm text-secondary-500">{c.control_type} • {c.frequency}</p>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className={cn('badge', c.design_effectiveness === 'effective' ? 'badge-success' : c.design_effectiveness === 'partially_effective' ? 'badge-warning' : 'badge-danger')}>
                                Design: {c.design_effectiveness}
                              </span>
                              <span className={cn('badge', c.operating_effectiveness === 'effective' ? 'badge-success' : c.operating_effectiveness === 'partially_effective' ? 'badge-warning' : 'badge-danger')}>
                                Op: {c.operating_effectiveness}
                              </span>
                            </div>
                          </div>
                        </div>
                      ))
                    ) : (
                      <p className="text-secondary-500 text-center py-4">No controls linked</p>
                    )}
                  </div>
                </div>

                {/* Evidence */}
                <div className="card p-4 md:col-span-2">
                  <h3 className="font-semibold text-secondary-900 mb-3 flex items-center gap-2">
                    <div className="p-1.5 bg-emerald-100 rounded">
                      <FileCheck className="w-4 h-4 text-emerald-600" />
                    </div>
                    Evidence ({chain.evidence?.length || 0})
                  </h3>
                  <div className="space-y-2 max-h-96 overflow-y-auto">
                    {chain.evidence?.length ? (
                      chain.evidence.map((e: any) => (
                        <div key={e.id} className="p-3 bg-secondary-50 rounded-lg border border-secondary-200">
                          <div className="flex items-start justify-between">
                            <div>
                              <Link href={`/evidence/${e.id}`} className="font-medium text-secondary-900 hover:text-primary-600">
                                {e.title}
                              </Link>
                              <p className="text-sm text-secondary-500">{e.evidence_type} • Control: {e.control_id}</p>
                            </div>
                            <span className={cn('badge', getStatusColor(e.status))}>
                              {e.status}
                            </span>
                          </div>
                        </div>
                      ))
                    ) : (
                      <p className="text-secondary-500 text-center py-4">No evidence linked</p>
                    )}
                  </div>
                </div>

                {/* Exceptions */}
                <div className="card p-4 md:col-span-2">
                  <h3 className="font-semibold text-secondary-900 mb-3 flex items-center gap-2">
                    <div className="p-1.5 bg-red-100 rounded">
                      <AlertTriangle className="w-4 h-4 text-red-600" />
                    </div>
                    Exceptions ({chain.exceptions?.length || 0})
                  </h3>
                  <div className="space-y-2 max-h-96 overflow-y-auto">
                    {chain.exceptions?.length ? (
                      chain.exceptions.map((e: any) => (
                        <div key={e.id} className="p-3 bg-secondary-50 rounded-lg border border-secondary-200">
                          <div className="flex items-start justify-between">
                            <div>
                              <Link href={`/exceptions/${e.id}`} className="font-medium text-secondary-900 hover:text-primary-600">
                                {e.number}
                              </Link>
                              <p className="text-sm text-secondary-500">{e.type.replace(/_/g, ' ')} • Control: {e.control_id}</p>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className={cn('badge', getSeverityColor(e.severity))}>
                                {e.severity}
                              </span>
                              <span className={cn('badge', getStatusColor(e.status))}>
                                {e.status.replace(/_/g, ' ')}
                              </span>
                            </div>
                          </div>
                        </div>
                      ))
                    ) : (
                      <p className="text-secondary-500 text-center py-4">No exceptions linked</p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="card p-12 text-center">
              <AlertTriangle className="w-16 h-16 text-warning-500 mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-secondary-900 mb-2">No Traceability Data</h2>
              <p className="text-secondary-500">This obligation has no mapped policies, processes, or controls</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}