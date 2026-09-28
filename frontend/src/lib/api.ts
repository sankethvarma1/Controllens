import axios, { AxiosInstance, AxiosError } from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000,
    });

    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        console.error('API Error:', error.response?.data || error.message);
        return Promise.reject(error);
      }
    );
  }

  // Health
  async health() {
    return this.client.get('/health');
  }

  // Dashboard
  async getDashboard() {
    return this.client.get('/analytics/dashboard');
  }

  // Regulations
  async getRegulations(params?: { status?: string; jurisdiction?: string; limit?: number; offset?: number }) {
    return this.client.get('/regulations', { params });
  }

  async getRegulation(id: string) {
    return this.client.get(`/regulations/${id}`);
  }

  async getRegulationSections(regulationId: string) {
    return this.client.get(`/regulations/${regulationId}/sections`);
  }

  // Obligations
  async getObligations(params?: { regulation_id?: string; category?: string; risk_level?: string; limit?: number; offset?: number }) {
    return this.client.get('/obligations', { params });
  }

  async getObligation(id: string) {
    return this.client.get(`/obligations/${id}`);
  }

  async getObligationCoverage(obligationId: string) {
    return this.client.get(`/obligations/${obligationId}/coverage`);
  }

  async getAllObligationCoverage(regulationId?: string) {
    return this.client.get('/analytics/obligation-coverage', { params: { regulation_id: regulationId } });
  }

  // Policies
  async getPolicies(params?: { policy_type?: string; department?: string; status?: string; limit?: number; offset?: number }) {
    return this.client.get('/policies', { params });
  }

  async getPolicy(id: string) {
    return this.client.get(`/policies/${id}`);
  }

  // Processes
  async getProcesses(params?: { department?: string; status?: string; limit?: number; offset?: number }) {
    return this.client.get('/processes', { params });
  }

  async getProcess(id: string) {
    return this.client.get(`/processes/${id}`);
  }

  // Controls
  async getControls(params?: { process_id?: string; policy_id?: string; control_type?: string; status?: string; limit?: number; offset?: number }) {
    return this.client.get('/controls', { params });
  }

  async getControl(id: string) {
    return this.client.get(`/controls/${id}`);
  }

  async getControlEffectiveness(controlId: string) {
    return this.client.get(`/controls/${controlId}/effectiveness`);
  }

  // Evidence
  async getEvidence(params?: { control_id?: string; evidence_type?: string; status?: string; limit?: number; offset?: number }) {
    return this.client.get('/evidence', { params });
  }

  async getEvidenceById(id: string) {
    return this.client.get(`/evidence/${id}`);
  }

  // Transactions
  async getTransactions(params?: { 
    process_id?: string; 
    control_id?: string; 
    start_date?: string; 
    end_date?: string; 
    min_risk?: number; 
    max_risk?: number; 
    limit?: number; 
    offset?: number 
  }) {
    return this.client.get('/transactions', { params });
  }

  // Exceptions
  async getExceptions(params?: {
    control_id?: string;
    process_id?: string;
    obligation_id?: string;
    severity?: string;
    status?: string;
    days?: number;
    limit?: number;
    offset?: number;
  }) {
    return this.client.get('/exceptions', { params });
  }

  async getException(id: string) {
    return this.client.get(`/exceptions/${id}`);
  }

  async updateException(id: string, data: any) {
    return this.client.patch(`/exceptions/${id}`, data);
  }

  // Analytics
  async getControlCoverage() {
    return this.client.get('/analytics/control-coverage');
  }

  async getEvidenceCompleteness(controlId?: string) {
    return this.client.get('/analytics/evidence-completeness', { params: { control_id: controlId } });
  }

  async getEvidenceFreshness(controlId?: string) {
    return this.client.get('/analytics/evidence-freshness', { params: { control_id: controlId } });
  }

  async getRiskExposure() {
    return this.client.get('/analytics/risk-exposure');
  }

  async getUnresolvedGaps() {
    return this.client.get('/analytics/gaps');
  }

  async getTrends(days: number = 90) {
    return this.client.get('/analytics/trends', { params: { days } });
  }

  // Traceability
  async getTraceabilityChain(obligationId: string) {
    return this.client.get(`/traceability/${obligationId}`);
  }

  // Investigation
  async investigate(question: string, context?: any) {
    return this.client.post('/investigate', { question, context });
  }

  // Documents
  async getDocuments(params?: { document_type?: string; source?: string; status?: string; limit?: number; offset?: number }) {
    return this.client.get('/documents', { params });
  }

  async getDocumentChunks(documentId: string) {
    return this.client.get(`/documents/${documentId}/chunks`);
  }

  // Retrieval
  async search(query: string, filters?: any, limit?: number, sourceTypes?: string[]) {
    return this.client.post('/retrieval/search', { query, filters, limit, source_types: sourceTypes });
  }

  // Agents
  async listAgents() {
    return this.client.get('/agents');
  }

  async runAgent(agentName: string, action: string, parameters: any) {
    return this.client.post(`/agents/${agentName}/run`, { action, parameters });
  }

  // Mapping Reviews
  async getMappingReviews(params?: { source_type?: string; source_id?: string; target_type?: string; target_id?: string; status?: string; limit?: number; offset?: number }) {
    return this.client.get('/mapping-reviews', { params });
  }

  async updateMappingReview(reviewId: string, data: any, userId: string, userRole: string) {
    return this.client.patch(`/mapping-reviews/${reviewId}`, data, { params: { user_id: userId, user_role: userRole } });
  }

  // Audit
  async getAuditTrail(params?: { entity_type?: string; entity_id?: string; user_id?: string; days?: number; limit?: number; offset?: number }) {
    return this.client.get('/audit', { params });
  }
}

export const api = new ApiClient();

// Types
export interface DashboardSummary {
  total_obligations: number;
  mapped_obligations: number;
  coverage_percentage: number;
  control_gaps: number;
  evidence_gaps: number;
  open_exceptions: number;
  risk_exposure: number;
  unresolved_gaps: number;
  critical_gaps: number;
  high_gaps: number;
}

export interface ObligationCoverage {
  total_obligations: number;
  covered_obligations: number;
  coverage_percentage: number;
  status_breakdown: Record<string, number>;
  obligations: ObligationCoverageItem[];
}

export interface ObligationCoverageItem {
  obligation_id: string;
  regulation_id: string;
  obligation_text: string;
  risk_level: string;
  category: string;
  policy_count: number;
  process_count: number;
  control_count: number;
  verified_evidence_count: number;
  coverage_status: string;
  risk_weight: number;
}

export interface ControlEffectiveness {
  control_id: string;
  control_name: string;
  composite_score: number;
  rating: string;
  components: Record<string, number>;
  details: Record<string, any>;
}

export interface TraceabilityChain {
  regulation: any;
  obligation: any;
  policies: any[];
  processes: any[];
  controls: any[];
  evidence: any[];
  exceptions: any[];
}

export interface UnresolvedGaps {
  total_gaps: number;
  by_type: Record<string, number>;
  by_severity: Record<string, number>;
  gaps: Gap[];
}

export interface Gap {
  gap_type: string;
  entity_id: string;
  entity_name: string;
  severity: string;
  description: string;
  [key: string]: any;
}

export interface EvidenceItem {
  id: string;
  control_id: string;
  evidence_type: string;
  title: string;
  description: string | null;
  file_path: string | null;
  status: string;
  collected_at: string;
  period_start: string | null;
  period_end: string | null;
  expiry_date: string | null;
  source_system: string | null;
  verified_by: string | null;
  verified_at: string | null;
}

export interface ExceptionItem {
  id: string;
  exception_number: string;
  title: string;
  description: string | null;
  exception_type: string;
  severity: string;
  status: string;
  detected_date: string;
  detected_by: string | null;
  control_id: string | null;
  process_id: string | null;
  obligation_id: string | null;
  root_cause: string | null;
  remediation_plan: string | null;
  remediation_deadline: string | null;
  actual_resolution_date: string | null;
  assigned_to: string | null;
}

export interface TransactionItem {
  id: string;
  transaction_id: string;
  transaction_date: string;
  transaction_type: string;
  amount: number | null;
  currency: string;
  account_id: string | null;
  counterparty: string | null;
  status: string;
  risk_score: number | null;
  flags: string[];
  process_id: string | null;
  control_id: string | null;
}

export interface Regulation {
  id: string;
  title: string;
  short_name: string | null;
  jurisdiction: string | null;
  regulator: string | null;
  publication_date: string | null;
  effective_date: string | null;
  status: string;
  description: string | null;
  source_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface Policy {
  id: string;
  title: string;
  description: string | null;
  policy_type: string | null;
  owner_department: string | null;
  owner_role: string | null;
  version: string | null;
  status: string;
  effective_date: string | null;
  review_date: string | null;
  document_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface Process {
  id: string;
  name: string;
  description: string | null;
  department: string | null;
  process_owner: string | null;
  risk_rating: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Control {
  id: string;
  name: string;
  description: string | null;
  control_type: string;
  control_category: string | null;
  frequency: string | null;
  automation_level: string | null;
  status: string;
  design_effectiveness: string | null;
  operating_effectiveness: string | null;
  last_tested_date: string | null;
  next_test_date: string | null;
  process_id: string | null;
  policy_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface Obligation {
  id: string;
  regulation_id: string;
  section_id: string | null;
  obligation_text: string;
  obligation_type: string | null;
  category: string | null;
  risk_level: string;
  status: string;
  effective_date: string | null;
  created_at: string;
  updated_at: string;
}

export interface InvestigationResponse {
  question: string;
  answer: string;
  evidence: any[];
  tools_used: string[];
  confidence: number;
  insufficient_evidence: boolean;
}

export interface RetrievalResultResponse {
  id: string;
  content: string;
  score: number;
  source_type: string;
  source_id: string;
  metadata: Record<string, any>;
  document_id: string | null;
  document_title: string | null;
  section_title: string | null;
  section_number: string | null;
  page_number: number | null;
  control_id: string | null;
  evidence_type: string | null;
  regulation_id: string | null;
}

export interface MappingReviewResponse {
  id: string;
  mapping_type: string;
  source_entity_type: string;
  source_entity_id: string;
  target_entity_type: string;
  target_entity_id: string;
  confidence_score: number | null;
  ai_reasoning: string | null;
  status: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
  review_decision: string | null;
  review_comments: string | null;
  created_at: string;
  updated_at: string;
}

export interface AuditEventResponse {
  id: string;
  event_type: string;
  entity_type: string | null;
  entity_id: string | null;
  user_id: string | null;
  user_role: string | null;
  action: string | null;
  timestamp: string;
  old_values: any;
  new_values: any;
  ip_address: string | null;
  user_agent: string | null;
}