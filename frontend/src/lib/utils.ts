import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatNumber(num: number): string {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toString();
}

export function formatPercentage(num: number): string {
  return `${num.toFixed(1)}%`;
}

export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function formatDateTime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function getSeverityColor(severity: string): string {
  switch (severity?.toLowerCase()) {
    case 'critical':
      return 'text-danger-600 bg-danger-50 border-danger-200';
    case 'high':
      return 'text-danger-600 bg-danger-50 border-danger-200';
    case 'medium':
      return 'text-warning-600 bg-warning-50 border-warning-200';
    case 'low':
      return 'text-success-600 bg-success-50 border-success-200';
    default:
      return 'text-secondary-600 bg-secondary-50 border-secondary-200';
  }
}

export function getStatusColor(status: string): string {
  switch (status?.toLowerCase()) {
    case 'active':
    case 'accepted':
    case 'closed':
    case 'remediated':
    case 'verified':
      return 'text-success-600 bg-success-50';
    case 'open':
    case 'investigating':
    case 'proposed':
    case 'submitted':
      return 'text-warning-600 bg-warning-50';
    case 'rejected':
    case 'failed':
    case 'expired':
    case 'ineffective':
      return 'text-danger-600 bg-danger-50';
    case 'draft':
    case 'archived':
    case 'inactive':
    case 'deprecated':
    case 'superseded':
      return 'text-secondary-600 bg-secondary-100';
    case 'needs_review':
    case 'partially_effective':
      return 'text-primary-600 bg-primary-50';
    default:
      return 'text-secondary-600 bg-secondary-50';
  }
}

export function getRiskColor(risk: string): string {
  switch (risk?.toLowerCase()) {
    case 'critical':
      return 'text-danger-600 bg-danger-50 border-danger-200';
    case 'high':
      return 'text-danger-600 bg-danger-50 border-danger-200';
    case 'medium':
      return 'text-warning-600 bg-warning-50 border-warning-200';
    case 'low':
      return 'text-success-600 bg-success-50 border-success-200';
    default:
      return 'text-secondary-600 bg-secondary-50 border-secondary-200';
  }
}

export function truncate(str: string, length: number): string {
  if (str.length <= length) return str;
  return str.slice(0, length) + '...';
}

export function calculateDaysBetween(start: string, end: string = new Date().toISOString()): number {
  const startDate = new Date(start);
  const endDate = new Date(end);
  const diffTime = Math.abs(endDate.getTime() - startDate.getTime());
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
}

export function isOverdue(dateString: string): boolean {
  const date = new Date(dateString);
  return date < new Date();
}

export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;
  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}