"""
Pydantic schemas for CONTROLLENS API.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


# =====================================================
# ENUMS
# =====================================================

class RegulationStatus(str, Enum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    DRAFT = "draft"


class ObligationStatus(str, Enum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"


class PolicyStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    SUPERSEDED = "superseded"


class ProcessStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class ControlStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"


class ControlType(str, Enum):
    PREVENTIVE = "preventive"
    DETECTIVE = "detective"
    CORRECTIVE = "corrective"


class EvidenceStatus(str, Enum):
    SUBMITTED = "submitted"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ExceptionStatus(str, Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    REMEDIATED = "remediated"
    CLOSED = "closed"
    ACCEPTED_RISK = "accepted_risk"


class ExceptionSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MappingStatus(str, Enum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# =====================================================
# BASE SCHEMAS
# =====================================================

class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TimestampMixin(BaseModel):
    created_at: datetime
    updated_at: datetime


# =====================================================
# REGULATION SCHEMAS
# =====================================================

class RegulationBase(BaseSchema):
    title: str
    short_name: Optional[str] = None
    jurisdiction: Optional[str] = None
    regulator: Optional[str] = None
    publication_date: Optional[date] = None
    effective_date: Optional[date] = None
    status: RegulationStatus = RegulationStatus.ACTIVE
    description: Optional[str] = None
    source_url: Optional[str] = None


class RegulationCreate(RegulationBase):
    pass


class RegulationUpdate(BaseSchema):
    title: Optional[str] = None
    short_name: Optional[str] = None
    jurisdiction: Optional[str] = None
    regulator: Optional[str] = None
    publication_date: Optional[date] = None
    effective_date: Optional[date] = None
    status: Optional[RegulationStatus] = None
    description: Optional[str] = None
    source_url: Optional[str] = None


class RegulationResponse(RegulationBase, TimestampMixin):
    id: str


class RegulatorySectionBase(BaseSchema):
    regulation_id: str
    section_number: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    parent_section_id: Optional[str] = None
    section_type: Optional[str] = None
    page_start: Optional[int] = None
    page_end: Optional[int] = None


class RegulatorySectionCreate(RegulatorySectionBase):
    pass


class RegulatorySectionResponse(RegulatorySectionBase, TimestampMixin):
    id: str


# =====================================================
# OBLIGATION SCHEMAS
# =====================================================

class ObligationBase(BaseSchema):
    regulation_id: str
    section_id: Optional[str] = None
    obligation_text: str
    obligation_type: Optional[str] = None
    category: Optional[str] = None
    risk_level: RiskLevel = RiskLevel.MEDIUM
    status: ObligationStatus = ObligationStatus.ACTIVE
    effective_date: Optional[date] = None


class ObligationCreate(ObligationBase):
    pass


class ObligationUpdate(BaseSchema):
    section_id: Optional[str] = None
    obligation_text: Optional[str] = None
    obligation_type: Optional[str] = None
    category: Optional[str] = None
    risk_level: Optional[RiskLevel] = None
    status: Optional[ObligationStatus] = None
    effective_date: Optional[date] = None


class ObligationResponse(ObligationBase, TimestampMixin):
    id: str


# =====================================================
# POLICY SCHEMAS
# =====================================================

class PolicyBase(BaseSchema):
    title: str
    description: Optional[str] = None
    policy_type: Optional[str] = None
    owner_department: Optional[str] = None
    owner_role: Optional[str] = None
    version: Optional[str] = None
    status: PolicyStatus = PolicyStatus.ACTIVE
    effective_date: Optional[date] = None
    review_date: Optional[date] = None
    document_id: Optional[str] = None


class PolicyCreate(PolicyBase):
    pass


class PolicyUpdate(BaseSchema):
    title: Optional[str] = None
    description: Optional[str] = None
    policy_type: Optional[str] = None
    owner_department: Optional[str] = None
    owner_role: Optional[str] = None
    version: Optional[str] = None
    status: Optional[PolicyStatus] = None
    effective_date: Optional[date] = None
    review_date: Optional[date] = None
    document_id: Optional[str] = None


class PolicyResponse(PolicyBase, TimestampMixin):
    id: str


# =====================================================
# PROCESS SCHEMAS
# =====================================================

class ProcessBase(BaseSchema):
    name: str
    description: Optional[str] = None
    department: Optional[str] = None
    process_owner: Optional[str] = None
    risk_rating: RiskLevel = RiskLevel.MEDIUM
    status: ProcessStatus = ProcessStatus.ACTIVE


class ProcessCreate(ProcessBase):
    pass


class ProcessUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    department: Optional[str] = None
    process_owner: Optional[str] = None
    risk_rating: Optional[RiskLevel] = None
    status: Optional[ProcessStatus] = None


class ProcessResponse(ProcessBase, TimestampMixin):
    id: str


# =====================================================
# CONTROL SCHEMAS
# =====================================================

class ControlBase(BaseSchema):
    name: str
    description: Optional[str] = None
    control_type: ControlType
    control_category: Optional[str] = None
    frequency: Optional[str] = None
    automation_level: Optional[str] = None
    status: ControlStatus = ControlStatus.ACTIVE
    design_effectiveness: Optional[str] = None
    operating_effectiveness: Optional[str] = None
    last_tested_date: Optional[date] = None
    next_test_date: Optional[date] = None
    process_id: Optional[str] = None
    policy_id: Optional[str] = None


class ControlCreate(ControlBase):
    pass


class ControlUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    control_type: Optional[ControlType] = None
    control_category: Optional[str] = None
    frequency: Optional[str] = None
    automation_level: Optional[str] = None
    status: Optional[ControlStatus] = None
    design_effectiveness: Optional[str] = None
    operating_effectiveness: Optional[str] = None
    last_tested_date: Optional[date] = None
    next_test_date: Optional[date] = None
    process_id: Optional[str] = None
    policy_id: Optional[str] = None


class ControlOwnerBase(BaseSchema):
    control_id: str
    owner_type: str
    person_name: str
    person_email: str
    department: Optional[str] = None
    role: Optional[str] = None
    assigned_date: Optional[date] = None


class ControlOwnerCreate(ControlOwnerBase):
    pass


class ControlOwnerResponse(ControlOwnerBase, TimestampMixin):
    id: str


class ControlResponse(ControlBase, TimestampMixin):
    id: str
    owners: List[ControlOwnerResponse] = []


# =====================================================
# EVIDENCE SCHEMAS
# =====================================================

class EvidenceBase(BaseSchema):
    control_id: str
    evidence_type: str
    title: str
    description: Optional[str] = None
    file_path: Optional[str] = None
    file_hash: Optional[str] = None
    source_system: Optional[str] = None
    collected_by: Optional[str] = None
    collected_at: Optional[datetime] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    status: EvidenceStatus = EvidenceStatus.SUBMITTED
    verification_notes: Optional[str] = None
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    expiry_date: Optional[date] = None


class EvidenceCreate(EvidenceBase):
    pass


class EvidenceUpdate(BaseSchema):
    evidence_type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    file_path: Optional[str] = None
    status: Optional[EvidenceStatus] = None
    verification_notes: Optional[str] = None
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    expiry_date: Optional[date] = None


class EvidenceResponse(EvidenceBase, TimestampMixin):
    id: str


# =====================================================
# TRANSACTION SCHEMAS
# =====================================================

class TransactionBase(BaseSchema):
    transaction_id: str
    transaction_date: datetime
    transaction_type: Optional[str] = None
    amount: Optional[Decimal] = None
    currency: str = "USD"
    account_id: Optional[str] = None
    counterparty: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    risk_score: Optional[Decimal] = None
    flags: List[str] = []
    process_id: Optional[str] = None
    control_id: Optional[str] = None


class TransactionCreate(TransactionBase):
    pass


class TransactionResponse(TransactionBase, TimestampMixin):
    id: str


# =====================================================
# EXCEPTION SCHEMAS
# =====================================================

class ExceptionBase(BaseSchema):
    exception_number: str
    title: Optional[str] = None
    description: Optional[str] = None
    exception_type: str
    severity: ExceptionSeverity = ExceptionSeverity.MEDIUM
    status: ExceptionStatus = ExceptionStatus.OPEN
    detected_date: date
    detected_by: Optional[str] = None
    control_id: Optional[str] = None
    process_id: Optional[str] = None
    obligation_id: Optional[str] = None
    transaction_id: Optional[str] = None
    root_cause: Optional[str] = None
    remediation_plan: Optional[str] = None
    remediation_deadline: Optional[date] = None
    actual_resolution_date: Optional[date] = None
    assigned_to: Optional[str] = None


class ExceptionCreate(ExceptionBase):
    pass


class ExceptionUpdate(BaseSchema):
    title: Optional[str] = None
    description: Optional[str] = None
    exception_type: Optional[str] = None
    severity: Optional[ExceptionSeverity] = None
    status: Optional[ExceptionStatus] = None
    detected_by: Optional[str] = None
    control_id: Optional[str] = None
    process_id: Optional[str] = None
    obligation_id: Optional[str] = None
    root_cause: Optional[str] = None
    remediation_plan: Optional[str] = None
    remediation_deadline: Optional[date] = None
    actual_resolution_date: Optional[date] = None
    assigned_to: Optional[str] = None


class ExceptionResponse(ExceptionBase, TimestampMixin):
    id: str


# =====================================================
# RISK ASSESSMENT SCHEMAS
# =====================================================

class RiskAssessmentBase(BaseSchema):
    entity_type: str
    entity_id: str
    risk_category: Optional[str] = None
    inherent_risk: RiskLevel
    residual_risk: RiskLevel
    likelihood: Optional[str] = None
    impact: Optional[str] = None
    risk_score: Optional[Decimal] = None
    mitigation_status: Optional[str] = None
    assessed_by: Optional[str] = None
    assessed_date: Optional[date] = None
    next_review_date: Optional[date] = None
    notes: Optional[str] = None


class RiskAssessmentCreate(RiskAssessmentBase):
    pass


class RiskAssessmentResponse(RiskAssessmentBase, TimestampMixin):
    id: str


# =====================================================
# MAPPING REVIEW SCHEMAS
# =====================================================

class MappingReviewBase(BaseSchema):
    mapping_type: str
    source_entity_type: str
    source_entity_id: str
    target_entity_type: str
    target_entity_id: str
    confidence_score: Optional[Decimal] = None
    ai_reasoning: Optional[str] = None
    status: MappingStatus = MappingStatus.PROPOSED
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_decision: Optional[str] = None
    review_comments: Optional[str] = None


class MappingReviewCreate(MappingReviewBase):
    pass


class MappingReviewUpdate(BaseSchema):
    confidence_score: Optional[Decimal] = None
    ai_reasoning: Optional[str] = None
    status: Optional[MappingStatus] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_decision: Optional[str] = None
    review_comments: Optional[str] = None


class MappingReviewResponse(MappingReviewBase, TimestampMixin):
    id: str


# =====================================================
# AUDIT SCHEMAS
# =====================================================

class AuditEventResponse(BaseSchema):
    id: str
    event_type: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    user_id: Optional[str] = None
    user_role: Optional[str] = None
    action: Optional[str] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime


# =====================================================
# ANALYTICS SCHEMAS
# =====================================================

class DashboardSummary(BaseSchema):
    total_obligations: int
    mapped_obligations: int
    coverage_percentage: float
    control_gaps: int
    evidence_gaps: int
    open_exceptions: int
    risk_exposure: float
    unresolved_gaps: int
    critical_gaps: int
    high_gaps: int


class ObligationCoverageResponse(BaseSchema):
    total_obligations: int
    covered_obligations: int
    coverage_percentage: float
    status_breakdown: Dict[str, int]
    obligations: List[Dict[str, Any]]


class ControlEffectivenessResponse(BaseSchema):
    control_id: str
    control_name: str
    composite_score: float
    rating: str
    components: Dict[str, float]
    details: Dict[str, Any]


class TraceabilityChainResponse(BaseSchema):
    regulation: Dict[str, Any]
    obligation: Dict[str, Any]
    policies: List[Dict[str, Any]]
    processes: List[Dict[str, Any]]
    controls: List[Dict[str, Any]]
    evidence: List[Dict[str, Any]]
    exceptions: List[Dict[str, Any]]


class UnresolvedGapsResponse(BaseSchema):
    total_gaps: int
    by_type: Dict[str, int]
    by_severity: Dict[str, int]
    gaps: List[Dict[str, Any]]


# =====================================================
# AGENT/INVESTIGATION SCHEMAS
# =====================================================

class InvestigationRequest(BaseSchema):
    question: str
    context: Optional[Dict[str, Any]] = None


class InvestigationResponse(BaseSchema):
    question: str
    answer: str
    evidence: List[Dict[str, Any]]
    tools_used: List[str]
    confidence: float
    insufficient_evidence: bool


class AgentToolCall(BaseSchema):
    tool: str
    parameters: Dict[str, Any]
    result: Any


# =====================================================
# DOCUMENT SCHEMAS
# =====================================================

class DocumentBase(BaseSchema):
    title: str
    source: str
    document_type: str
    file_path: Optional[str] = None
    publication_date: Optional[date] = None


class DocumentCreate(DocumentBase):
    pass


class DocumentResponse(DocumentBase, TimestampMixin):
    id: str
    file_hash: str
    mime_type: Optional[str] = None
    page_count: Optional[int] = None
    ingestion_status: str
    ingestion_error: Optional[str] = None
    chunk_count: int


class DocumentChunkResponse(BaseSchema):
    id: str
    document_id: str
    chunk_index: int
    content: str
    section_title: Optional[str] = None
    section_number: Optional[str] = None
    page_number: Optional[int] = None
    token_count: Optional[int] = None
    metadata: Dict[str, Any]


# =====================================================
# RETRIEVAL SCHEMAS
# =====================================================

class RetrievalRequest(BaseSchema):
    query: str
    filters: Optional[Dict[str, Any]] = None
    limit: int = 10
    source_types: Optional[List[str]] = None


class RetrievalResultResponse(BaseSchema):
    id: str
    content: str
    score: float
    source_type: str
    source_id: str
    metadata: Dict[str, Any]
    document_id: Optional[str] = None
    document_title: Optional[str] = None
    section_title: Optional[str] = None
    section_number: Optional[str] = None
    page_number: Optional[int] = None
    control_id: Optional[str] = None
    evidence_type: Optional[str] = None
    regulation_id: Optional[str] = None


class RetrievalResponse(BaseSchema):
    query: str
    results: List[RetrievalResultResponse]
    total: int


# =====================================================
# HEALTH CHECK
# =====================================================

class HealthResponse(BaseSchema):
    status: str
    version: str
    database: str
    timestamp: datetime