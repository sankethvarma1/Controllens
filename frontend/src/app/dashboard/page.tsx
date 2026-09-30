'use client';

import { useEffect, useState } from 'react';
import {
  Target,
  Shield,
  FileCheck,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  AlertCircle,
  ExternalLink,
} from 'lucide-react';
import Link from 'next/link';
import { api, DashboardSummary } from '@/lib/api';
import { cn, formatNumber, formatPercentage, getSeverityColor, getStatusColor } from '@/lib/utils';

const METRIC_CARDS = [
  {
    key: 'total_obligations',
    label: 'Total Obligations',
    icon: Target,
    color: 'bg-blue-500',
    trend: null,
  },
  {
    key: 'mapped_obligations',
    label: 'Mapped Obligations',
    icon: Target,
    color: 'bg-green-500',
    trend: null,
  },
  {
    key: 'coverage_percentage',
    label: 'Coverage',
    icon: Target,
    color: 'bg-purple-500',
    format: 'percentage',
    trend: null,
  },
  {
    key: 'control_gaps',
    label: 'Control Gaps',
    icon: Shield,
    color: 'bg-orange-500',
    trend: 'down',
  },
  {
    key: 'evidence_gaps',
    label: 'Evidence Gaps',
    icon: FileCheck,
    color: 'bg-amber-500',
    trend: 'down',
  },
  {
    key: 'open_exceptions',
    label: 'Open Exceptions (30d)',
    icon: AlertTriangle,
    color: 'bg-red-500',
    trend: 'down',
  },
  {
    key: 'risk_exposure',
    label: 'Risk Exposure',
    icon: TrendingUp,
    color: 'bg-red-600',
    format: 'decimal',
    trend: 'down',
  },
  {
    key: 'unresolved_gaps',
    label: 'Unresolved Gaps',
    icon: AlertCircle,
    color: 'bg-red-500',
    trend: 'down',
  },
];

export default function DashboardPage() {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await api.getDashboard();
        setData(response.data);
      } catch (err) {
        setError('Failed to load dashboard data');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {METRIC_CARDS.map((_, i) => (
            <div key={i} className="card p-6 animate-pulse">
              <div className="h-4 bg-secondary-200 rounded w-3/4 mb-2" />
              <div className="h-8 bg-secondary-200 rounded w-1/2" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card p-8 text-center">
        <AlertCircle className="w-12 h-12 text-danger-500 mx-auto mb-4" />
        <h2 className="text-lg font-medium text-secondary-900 mb-2">Failed to load dashboard</h2>
        <p className="text-secondary-500 mb-4">{error}</p>
        <button onClick={() => window.location.reload()} className="btn-primary">Retry</button>
      </div>
    );
  }

  const getValue = (key: string) => {
    const value = data?.[key as keyof DashboardSummary] ?? 0;
    const card = METRIC_CARDS.find(c => c.key === key);
    if (card?.format === 'percentage') return formatPercentage(value);
    if (card?.format === 'decimal') return value.toFixed(2);
    return formatNumber(value);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">Dashboard</h1>
          <p className="text-secondary-500 mt-1">Overview of your regulatory control framework</p>
        </div>
        <div className="flex gap-2">
          <Link href="/obligations" className="btn-outline">View Obligations</Link>
          <Link href="/controls" className="btn-primary">View Controls</Link>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {METRIC_CARDS.map((card) => {
          const Icon = card.icon;
          const value = getValue(card.key);
          return (
            <div key={card.key} className="card p-6 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-medium text-secondary-500">{card.label}</p>
                  <p className="text-3xl font-bold text-secondary-900 mt-1">{value}</p>
                </div>
                <div className={cn('p-3 rounded-xl', card.color)}>
                  <Icon className="w-6 h-6 text-white" />
                </div>
              </div>
              {card.trend && (
                <div className="mt-4 flex items-center gap-2 text-sm">
                  {card.trend === 'down' ? (
                    <TrendingDown className="w-4 h-4 text-success-600" />
                  ) : (
                    <TrendingUp className="w-4 h-4 text-danger-600" />
                  )}
                  <span className={cn(card.trend === 'down' ? 'text-success-600' : 'text-danger-600')}>
                    {card.trend === 'down' ? 'Lower is better' : 'Higher is better'}
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Quick Actions & Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Critical Items */}
        <div className="lg:col-span-2 card">
          <div className="p-4 border-b border-secondary-200">
            <h2 className="text-lg font-semibold text-secondary-900">Critical Items Requiring Attention</h2>
          </div>
          <div className="p-4">
            {data && data.critical_gaps > 0 && (
              <div className="mb-4 p-3 bg-danger-50 border border-danger-200 rounded-lg">
                <div className="flex items-center gap-2">
                  <AlertCircle className="w-5 h-5 text-danger-600" />
                  <span className="font-medium text-danger-800">
                    {data.critical_gaps} critical gap{data.critical_gaps !== 1 ? 's' : ''} require immediate action
                  </span>
                </div>
              </div>
            )}
            {data && data.high_gaps > 0 && (
              <div className="mb-4 p-3 bg-warning-50 border border-warning-200 rounded-lg">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-warning-600" />
                  <span className="font-medium text-warning-800">
                    {data.high_gaps} high severity gap{data.high_gaps !== 1 ? 's' : ''} need attention
                  </span>
                </div>
              </div>
            )}
            {data && data.open_exceptions > 0 && (
              <div className="mb-4 p-3 bg-danger-50 border border-danger-200 rounded-lg">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-danger-600" />
                  <span className="font-medium text-danger-800">
                    {data.open_exceptions} open exception{data.open_exceptions !== 1 ? 's' : ''} requiring investigation
                  </span>
                </div>
              </div>
            )}
            {data && data.control_gaps > 0 && (
              <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                <div className="flex items-center gap-2">
                  <Shield className="w-5 h-5 text-amber-600" />
                  <span className="font-medium text-amber-800">
                    {data.control_gaps} control{data.control_gaps !== 1 ? 's' : ''} without evidence
                  </span>
                </div>
              </div>
            )}
            {data && data.evidence_gaps > 0 && (
              <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
                <div className="flex items-center gap-2">
                  <FileCheck className="w-5 h-5 text-amber-600" />
                  <span className="font-medium text-amber-800">
                    {data.evidence_gaps} control{data.evidence_gaps !== 1 ? 's' : ''} with incomplete evidence
                  </span>
                </div>
              </div>
            )}
            {!data || (data.critical_gaps === 0 && data.high_gaps === 0 && data.open_exceptions === 0 && data.control_gaps === 0 && data.evidence_gaps === 0) && (
              <div className="text-center py-8 text-secondary-500">
                <Target className="w-12 h-12 mx-auto text-secondary-300 mb-3" />
                <p className="font-medium">No critical issues detected</p>
                <p className="text-sm mt-1">All systems operating within normal parameters</p>
              </div>
            )}
          </div>
        </div>

        {/* Quick Links */}
        <div className="card">
          <div className="p-4 border-b border-secondary-200">
            <h2 className="text-lg font-semibold text-secondary-900">Quick Actions</h2>
          </div>
          <div className="p-4 space-y-2">
            <Link href="/obligations" className="flex items-center gap-3 p-3 rounded-lg hover:bg-secondary-50 transition-colors">
              <div className="p-2 bg-primary-100 rounded-lg">
                <Target className="w-5 h-5 text-primary-600" />
              </div>
              <div>
                <p className="font-medium text-secondary-900">Review Obligations</p>
                <p className="text-sm text-secondary-500">Check coverage & gaps</p>
              </div>
              <ExternalLink className="ml-auto w-4 h-4 text-secondary-400" />
            </Link>
            <Link href="/controls" className="flex items-center gap-3 p-3 rounded-lg hover:bg-secondary-50 transition-colors">
              <div className="p-2 bg-green-100 rounded-lg">
                <Shield className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <p className="font-medium text-secondary-900">Manage Controls</p>
                <p className="text-sm text-secondary-500">View effectiveness & testing</p>
              </div>
              <ExternalLink className="ml-auto w-4 h-4 text-secondary-400" />
            </Link>
            <Link href="/evidence" className="flex items-center gap-3 p-3 rounded-lg hover:bg-secondary-50 transition-colors">
              <div className="p-2 bg-blue-100 rounded-lg">
                <FileCheck className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p className="font-medium text-secondary-900">Evidence Repository</p>
                <p className="text-sm text-secondary-500">Collect & verify evidence</p>
              </div>
              <ExternalLink className="ml-auto w-4 h-4 text-secondary-400" />
            </Link>
            <Link href="/exceptions" className="flex items-center gap-3 p-3 rounded-lg hover:bg-secondary-50 transition-colors">
              <div className="p-2 bg-red-100 rounded-lg">
                <AlertTriangle className="w-5 h-5 text-red-600" />
              </div>
              <div>
                <p className="font-medium text-secondary-900">Track Exceptions</p>
                <p className="text-sm text-secondary-500">Monitor & remediate issues</p>
              </div>
              <ExternalLink className="ml-auto w-4 h-4 text-secondary-400" />
            </Link>
            <Link href="/traceability" className="flex items-center gap-3 p-3 rounded-lg hover:bg-secondary-50 transition-colors">
              <div className="p-2 bg-purple-100 rounded-lg">
                <TrendingUp className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <p className="font-medium text-secondary-900">Traceability View</p>
                <p className="text-sm text-secondary-500">Regulation → Control chain</p>
              </div>
              <ExternalLink className="ml-auto w-4 h-4 text-secondary-400" />
            </Link>
            <Link href="/review" className="flex items-center gap-3 p-3 rounded-lg hover:bg-secondary-50 transition-colors">
              <div className="p-2 bg-orange-100 rounded-lg">
                <AlertCircle className="w-5 h-5 text-orange-600" />
              </div>
              <div>
                <p className="font-medium text-secondary-900">Mapping Review</p>
                <p className="text-sm text-secondary-500">Approve proposed mappings</p>
              </div>
              <ExternalLink className="ml-auto w-4 h-4 text-secondary-400" />
            </Link>
          </div>
        </div>
      </div>

      {/* Coverage Summary */}
      <div className="card">
        <div className="p-4 border-b border-secondary-200">
          <h2 className="text-lg font-semibold text-secondary-900">Obligation Coverage Overview</h2>
        </div>
        <div className="p-4 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-primary-50 rounded-lg">
            <p className="text-3xl font-bold text-primary-600">{data?.coverage_percentage?.toFixed(1) || '0'}%</p>
            <p className="text-sm text-secondary-500">Overall Coverage</p>
          </div>
          <div className="text-center p-4 bg-success-50 rounded-lg">
            <p className="text-3xl font-bold text-success-600">{data?.mapped_obligations || 0}</p>
            <p className="text-sm text-secondary-500">Fully Covered</p>
          </div>
          <div className="text-center p-4 bg-warning-50 rounded-lg">
            <p className="text-3xl font-bold text-warning-600">
              {(data && data.total_obligations - data.mapped_obligations) || 0}
            </p>
            <p className="text-sm text-secondary-500">Gaps Remaining</p>
          </div>
          <div className="text-center p-4 bg-secondary-100 rounded-lg">
            <p className="text-3xl font-bold text-secondary-600">{data?.total_obligations || 0}</p>
            <p className="text-sm text-secondary-500">Total Obligations</p>
          </div>
        </div>
      </div>
    </div>
  );
}