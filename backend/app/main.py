"""
CONTROLLENS FastAPI Application
Main entry point with all API routes.
"""
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional, Dict
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.db.base import get_db, init_db, engine
from app.schemas import (
    # Regulations
    RegulationCreate, RegulationUpdate, RegulationResponse,
    RegulatorySectionCreate, RegulatorySectionResponse,
    # Obligations
    ObligationCreate, ObligationUpdate, ObligationResponse,
    # Policies
    PolicyCreate, PolicyUpdate, PolicyResponse,
    # Processes
    ProcessCreate, ProcessUpdate, ProcessResponse,
    # Controls
    ControlCreate, ControlUpdate, ControlResponse,
    ControlOwnerCreate, ControlOwnerResponse,
    # Evidence
    EvidenceCreate, EvidenceUpdate, EvidenceResponse,
    # Transactions
    TransactionCreate, TransactionResponse,
    # Exceptions
    ExceptionCreate, ExceptionUpdate, ExceptionResponse,
    # Risk Assessments
    RiskAssessmentCreate, RiskAssessmentResponse,
    # Mapping Reviews
    MappingReviewCreate, MappingReviewUpdate, MappingReviewResponse,
    # Audit
    AuditEventResponse,
    # Analytics
    DashboardSummary, ObligationCoverageResponse,
    ControlEffectivenessResponse, TraceabilityChainResponse,
    UnresolvedGapsResponse,
    # Investigation
    InvestigationRequest, InvestigationResponse,
    # Documents
    DocumentCreate, DocumentResponse, DocumentChunkResponse,
    # Retrieval
    RetrievalRequest, RetrievalResponse, RetrievalResultResponse,
    # Health
    HealthResponse
)
from app.services.analytics import AnalyticsEngine, calculate_control_effectiveness, build_traceability_chain
from app.services.retrieval import HybridRetriever, retrieve_evidence_for_control
from app.services.document_pipeline import DocumentIngestionPipeline, ingest_sample_documents
from app.agents.agents import get_agent, list_agents
from app.agents.tools import AgentTools
from app.db.base import (
    Regulation, RegulatorySection, Obligation, Policy, Process,
    Control, ControlOwner, Evidence, Transaction, Exception as Exc,
    RiskAssessment, MappingReview, AuditEvent, Document, DocumentChunk
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("Starting CONTROLLENS...")
    init_db()
    print("Database initialized")
    yield
    # Shutdown
    print("Shutting down CONTROLLENS...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Regulatory & Control Intelligence Platform",
    openapi_url=settings.OPENAPI_URL,
    docs_url=settings.DOCS_URL,
    redoc_url=settings.REDOC_URL,
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================
# HEALTH CHECK
# =====================================================

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    
    return HealthResponse(
        status="ok" if db_status == "healthy" else "degraded",
        version=settings.APP_VERSION,
        database=db_status,
        timestamp=datetime.utcnow()
    )


# =====================================================
# REGULATION ENDPOINTS
# =====================================================

@app.post("/api/v1/regulations", response_model=RegulationResponse, status_code=status.HTTP_201_CREATED, tags=["Regulations"])
async def create_regulation(regulation: RegulationCreate, db: Session = Depends(get_db)):
    """Create a new regulation."""
    db_reg = Regulation(**regulation.model_dump())
    db.add(db_reg)
    db.commit()
    db.refresh(db_reg)
    return db_reg


@app.get("/api/v1/regulations", response_model=List[RegulationResponse], tags=["Regulations"])
async def list_regulations(
    status: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List regulations with optional filters."""
    query = db.query(Regulation)
    
    if status:
        query = query.filter(Regulation.status == status)
    if jurisdiction:
        query = query.filter(Regulation.jurisdiction.ilike(f"%{jurisdiction}%"))
    
    return query.order_by(Regulation.title).offset(offset).limit(limit).all()


@app.get("/api/v1/regulations/{regulation_id}", response_model=RegulationResponse, tags=["Regulations"])
async def get_regulation(regulation_id: str, db: Session = Depends(get_db)):
    """Get a regulation by ID."""
    reg = db.query(Regulation).filter(Regulation.id == regulation_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="Regulation not found")
    return reg


@app.patch("/api/v1/regulations/{regulation_id}", response_model=RegulationResponse, tags=["Regulations"])
async def update_regulation(regulation_id: str, regulation: RegulationUpdate, db: Session = Depends(get_db)):
    """Update a regulation."""
    reg = db.query(Regulation).filter(Regulation.id == regulation_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="Regulation not found")
    
    for field, value in regulation.model_dump(exclude_unset=True).items():
        setattr(reg, field, value)
    
    db.commit()
    db.refresh(reg)
    return reg


@app.get("/api/v1/regulations/{regulation_id}/sections", response_model=List[RegulatorySectionResponse], tags=["Regulations"])
async def get_regulation_sections(regulation_id: str, db: Session = Depends(get_db)):
    """Get all sections for a regulation."""
    reg = db.query(Regulation).filter(Regulation.id == regulation_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="Regulation not found")
    
    return db.query(RegulatorySection).filter(
        RegulatorySection.regulation_id == regulation_id
    ).order_by(RegulatorySection.section_number).all()


# =====================================================
# OBLIGATION ENDPOINTS
# =====================================================

@app.post("/api/v1/obligations", response_model=ObligationResponse, status_code=status.HTTP_201_CREATED, tags=["Obligations"])
async def create_obligation(obligation: ObligationCreate, db: Session = Depends(get_db)):
    """Create a new obligation."""
    db_obl = Obligation(**obligation.model_dump())
    db.add(db_obl)
    db.commit()
    db.refresh(db_obl)
    return db_obl


@app.get("/api/v1/obligations", response_model=List[ObligationResponse], tags=["Obligations"])
async def list_obligations(
    regulation_id: Optional[str] = None,
    category: Optional[str] = None,
    risk_level: Optional[str] = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List obligations with optional filters."""
    query = db.query(Obligation).filter(Obligation.status == 'active')
    
    if regulation_id:
        query = query.filter(Obligation.regulation_id == regulation_id)
    if category:
        query = query.filter(Obligation.category == category)
    if risk_level:
        query = query.filter(Obligation.risk_level == risk_level)
    
    return query.offset(offset).limit(limit).all()


@app.get("/api/v1/obligations/{obligation_id}", response_model=ObligationResponse, tags=["Obligations"])
async def get_obligation(obligation_id: str, db: Session = Depends(get_db)):
    """Get an obligation by ID."""
    obl = db.query(Obligation).filter(Obligation.id == obligation_id).first()
    if not obl:
        raise HTTPException(status_code=404, detail="Obligation not found")
    return obl


@app.get("/api/v1/obligations/{obligation_id}/coverage", tags=["Obligations"])
async def get_obligation_coverage(obligation_id: str, db: Session = Depends(get_db)):
    """Get coverage analysis for an obligation."""
    analytics = AnalyticsEngine(db)
    coverage = analytics.get_obligation_coverage()
    
    for obl in coverage["obligations"]:
        if obl["obligation_id"] == obligation_id:
            return obl
    
    raise HTTPException(status_code=404, detail="Obligation not found")


# =====================================================
# POLICY ENDPOINTS
# =====================================================

@app.post("/api/v1/policies", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED, tags=["Policies"])
async def create_policy(policy: PolicyCreate, db: Session = Depends(get_db)):
    """Create a new policy."""
    db_pol = Policy(**policy.model_dump())
    db.add(db_pol)
    db.commit()
    db.refresh(db_pol)
    return db_pol


@app.get("/api/v1/policies", response_model=List[PolicyResponse], tags=["Policies"])
async def list_policies(
    policy_type: Optional[str] = None,
    department: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List policies with optional filters."""
    query = db.query(Policy)
    
    if policy_type:
        query = query.filter(Policy.policy_type == policy_type)
    if department:
        query = query.filter(Policy.owner_department == department)
    if status:
        query = query.filter(Policy.status == status)
    
    return query.order_by(Policy.title).offset(offset).limit(limit).all()


@app.get("/api/v1/policies/{policy_id}", response_model=PolicyResponse, tags=["Policies"])
async def get_policy(policy_id: str, db: Session = Depends(get_db)):
    """Get a policy by ID."""
    pol = db.query(Policy).filter(Policy.id == policy_id).first()
    if not pol:
        raise HTTPException(status_code=404, detail="Policy not found")
    return pol


# =====================================================
# PROCESS ENDPOINTS
# =====================================================

@app.post("/api/v1/processes", response_model=ProcessResponse, status_code=status.HTTP_201_CREATED, tags=["Processes"])
async def create_process(process: ProcessCreate, db: Session = Depends(get_db)):
    """Create a new process."""
    db_proc = Process(**process.model_dump())
    db.add(db_proc)
    db.commit()
    db.refresh(db_proc)
    return db_proc


@app.get("/api/v1/processes", response_model=List[ProcessResponse], tags=["Processes"])
async def list_processes(
    department: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List processes with optional filters."""
    query = db.query(Process)
    
    if department:
        query = query.filter(Process.department == department)
    if status:
        query = query.filter(Process.status == status)
    
    return query.order_by(Process.name).offset(offset).limit(limit).all()


@app.get("/api/v1/processes/{process_id}", response_model=ProcessResponse, tags=["Processes"])
async def get_process(process_id: str, db: Session = Depends(get_db)):
    """Get a process by ID."""
    proc = db.query(Process).filter(Process.id == process_id).first()
    if not proc:
        raise HTTPException(status_code=404, detail="Process not found")
    return proc


# =====================================================
# CONTROL ENDPOINTS
# =====================================================

@app.post("/api/v1/controls", response_model=ControlResponse, status_code=status.HTTP_201_CREATED, tags=["Controls"])
async def create_control(control: ControlCreate, db: Session = Depends(get_db)):
    """Create a new control."""
    db_ctl = Control(**control.model_dump())
    db.add(db_ctl)
    db.commit()
    db.refresh(db_ctl)
    return db_ctl


@app.get("/api/v1/controls", response_model=List[ControlResponse], tags=["Controls"])
async def list_controls(
    process_id: Optional[str] = None,
    policy_id: Optional[str] = None,
    control_type: Optional[str] = None,
    status: Optional[str] = "active",
    limit: int = Query(50, le=100),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List controls with optional filters."""
    query = db.query(Control)
    
    if process_id:
        query = query.filter(Control.process_id == process_id)
    if policy_id:
        query = query.filter(Control.policy_id == policy_id)
    if control_type:
        query = query.filter(Control.control_type == control_type)
    if status:
        query = query.filter(Control.status == status)
    
    return query.order_by(Control.name).offset(offset).limit(limit).all()


@app.get("/api/v1/controls/{control_id}", response_model=ControlResponse, tags=["Controls"])
async def get_control(control_id: str, db: Session = Depends(get_db)):
    """Get a control by ID with owners."""
    ctl = db.query(Control).filter(Control.id == control_id).first()
    if not ctl:
        raise HTTPException(status_code=404, detail="Control not found")
    
    # Load owners
    owners = db.query(ControlOwner).filter(ControlOwner.control_id == control_id).all()
    ctl.owners = owners
    return ctl


@app.get("/api/v1/controls/{control_id}/effectiveness", response_model=ControlEffectivenessResponse, tags=["Controls"])
async def get_control_effectiveness(control_id: str, db: Session = Depends(get_db)):
    """Get detailed control effectiveness analysis."""
    result = calculate_control_effectiveness(db, control_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# =====================================================
# EVIDENCE ENDPOINTS
# =====================================================

@app.post("/api/v1/evidence", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED, tags=["Evidence"])
async def create_evidence(evidence: EvidenceCreate, db: Session = Depends(get_db)):
    """Create new evidence record."""
    db_ev = Evidence(**evidence.model_dump())
    db.add(db_ev)
    db.commit()
    db.refresh(db_ev)
    return db_ev


@app.get("/api/v1/evidence", response_model=List[EvidenceResponse], tags=["Evidence"])
async def list_evidence(
    control_id: Optional[str] = None,
    evidence_type: Optional[str] = None,
    status: Optional[str] = "verified",
    limit: int = Query(50, le=100),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List evidence with optional filters."""
    query = db.query(Evidence)
    
    if control_id:
        query = query.filter(Evidence.control_id == control_id)
    if evidence_type:
        query = query.filter(Evidence.evidence_type == evidence_type)
    if status:
        query = query.filter(Evidence.status == status)
    
    return query.order_by(Evidence.collected_at.desc()).offset(offset).limit(limit).all()


@app.get("/api/v1/evidence/{evidence_id}", response_model=EvidenceResponse, tags=["Evidence"])
async def get_evidence(evidence_id: str, db: Session = Depends(get_db)):
    """Get evidence by ID."""
    ev = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return ev


# =====================================================
# TRANSACTION ENDPOINTS
# =====================================================

@app.post("/api/v1/transactions", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED, tags=["Transactions"])
async def create_transaction(transaction: TransactionCreate, db: Session = Depends(get_db)):
    """Create a new transaction."""
    db_txn = Transaction(**transaction.model_dump())
    db.add(db_txn)
    db.commit()
    db.refresh(db_txn)
    return db_txn


@app.get("/api/v1/transactions", response_model=List[TransactionResponse], tags=["Transactions"])
async def list_transactions(
    process_id: Optional[str] = None,
    control_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    min_risk: Optional[float] = None,
    max_risk: Optional[float] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List transactions with filters."""
    query = db.query(Transaction)
    
    if process_id:
        query = query.filter(Transaction.process_id == process_id)
    if control_id:
        query = query.filter(Transaction.control_id == control_id)
    if start_date:
        query = query.filter(Transaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(Transaction.transaction_date <= end_date)
    if min_risk is not None:
        query = query.filter(Transaction.risk_score >= min_risk)
    if max_risk is not None:
        query = query.filter(Transaction.risk_score <= max_risk)
    
    return query.order_by(Transaction.transaction_date.desc()).offset(offset).limit(limit).all()


# =====================================================
# EXCEPTION ENDPOINTS
# =====================================================

@app.post("/api/v1/exceptions", response_model=ExceptionResponse, status_code=status.HTTP_201_CREATED, tags=["Exceptions"])
async def create_exception(exc: ExceptionCreate, db: Session = Depends(get_db)):
    """Create a new exception."""
    db_exc = Exc(**exc.model_dump())
    db.add(db_exc)
    db.commit()
    db.refresh(db_exc)
    return db_exc


@app.get("/api/v1/exceptions", response_model=List[ExceptionResponse], tags=["Exceptions"])
async def list_exceptions(
    control_id: Optional[str] = None,
    process_id: Optional[str] = None,
    obligation_id: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    days: int = Query(90, le=365),
    limit: int = Query(50, le=100),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List exceptions with filters."""
    from datetime import date, timedelta
    cutoff = date.today() - timedelta(days=days)
    
    query = db.query(Exc).filter(Exc.detected_date >= cutoff)
    
    if control_id:
        query = query.filter(Exc.control_id == control_id)
    if process_id:
        query = query.filter(Exc.process_id == process_id)
    if obligation_id:
        query = query.filter(Exc.obligation_id == obligation_id)
    if severity:
        query = query.filter(Exc.severity == severity)
    if status:
        query = query.filter(Exc.status == status)
    
    return query.order_by(Exc.detected_date.desc()).offset(offset).limit(limit).all()


@app.get("/api/v1/exceptions/{exception_id}", response_model=ExceptionResponse, tags=["Exceptions"])
async def get_exception(exception_id: str, db: Session = Depends(get_db)):
    """Get exception by ID."""
    exc = db.query(Exc).filter(Exc.id == exception_id).first()
    if not exc:
        raise HTTPException(status_code=404, detail="Exception not found")
    return exc


@app.patch("/api/v1/exceptions/{exception_id}", response_model=ExceptionResponse, tags=["Exceptions"])
async def update_exception(exception_id: str, exc: ExceptionUpdate, db: Session = Depends(get_db)):
    """Update an exception."""
    db_exc = db.query(Exc).filter(Exc.id == exception_id).first()
    if not db_exc:
        raise HTTPException(status_code=404, detail="Exception not found")
    
    for field, value in exc.model_dump(exclude_unset=True).items():
        setattr(db_exc, field, value)
    
    db.commit()
    db.refresh(db_exc)
    return db_exc


# =====================================================
# RISK ASSESSMENT ENDPOINTS
# =====================================================

@app.post("/api/v1/risk-assessments", response_model=RiskAssessmentResponse, status_code=status.HTTP_201_CREATED, tags=["Risk Assessments"])
async def create_risk_assessment(ra: RiskAssessmentCreate, db: Session = Depends(get_db)):
    """Create a new risk assessment."""
    db_ra = RiskAssessment(**ra.model_dump())
    db.add(db_ra)
    db.commit()
    db.refresh(db_ra)
    return db_ra


@app.get("/api/v1/risk-assessments", response_model=List[RiskAssessmentResponse], tags=["Risk Assessments"])
async def list_risk_assessments(
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List risk assessments with filters."""
    query = db.query(RiskAssessment)
    
    if entity_type:
        query = query.filter(RiskAssessment.entity_type == entity_type)
    if entity_id:
        query = query.filter(RiskAssessment.entity_id == entity_id)
    
    return query.order_by(RiskAssessment.risk_score.desc()).offset(offset).limit(limit).all()


# =====================================================
# MAPPING REVIEW ENDPOINTS (Human-in-the-loop)
# =====================================================

@app.post("/api/v1/mapping-reviews", response_model=MappingReviewResponse, status_code=status.HTTP_201_CREATED, tags=["Mapping Reviews"])
async def create_mapping_review(review: MappingReviewCreate, db: Session = Depends(get_db)):
    """Create a new mapping review (proposed mapping)."""
    db_review = MappingReview(**review.model_dump())
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review


@app.get("/api/v1/mapping-reviews", response_model=List[MappingReviewResponse], tags=["Mapping Reviews"])
async def list_mapping_reviews(
    source_type: Optional[str] = None,
    source_id: Optional[str] = None,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List mapping reviews with filters."""
    query = db.query(MappingReview)
    
    if source_type:
        query = query.filter(MappingReview.source_entity_type == source_type)
    if source_id:
        query = query.filter(MappingReview.source_entity_id == source_id)
    if target_type:
        query = query.filter(MappingReview.target_entity_type == target_type)
    if target_id:
        query = query.filter(MappingReview.target_entity_id == target_id)
    if status:
        query = query.filter(MappingReview.status == status)
    
    return query.order_by(MappingReview.created_at.desc()).offset(offset).limit(limit).all()


@app.patch("/api/v1/mapping-reviews/{review_id}", response_model=MappingReviewResponse, tags=["Mapping Reviews"])
async def update_mapping_review(
    review_id: str,
    review: MappingReviewUpdate,
    user_id: str = Query(..., description="User making the decision"),
    user_role: str = Query(..., description="User role"),
    db: Session = Depends(get_db)
):
    """Update mapping review status (human decision)."""
    db_review = db.query(MappingReview).filter(MappingReview.id == review_id).first()
    if not db_review:
        raise HTTPException(status_code=404, detail="Mapping review not found")
    
    old_status = db_review.status
    
    for field, value in review.model_dump(exclude_unset=True).items():
        setattr(db_review, field, value)
    
    # Set review metadata
    if review.review_decision:
        db_review.reviewed_by = user_id
        db_review.reviewed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_review)
    
    # Log audit event
    audit = AuditEvent(
        event_type="mapping_review_update",
        entity_type="mapping_review",
        entity_id=review_id,
        user_id=user_id,
        user_role=user_role,
        action=f"status_change: {old_status} -> {db_review.status}",
        old_values={"status": old_status},
        new_values={"status": db_review.status, "decision": review.review_decision}
    )
    db.add(audit)
    db.commit()
    
    return db_review


# =====================================================
# AUDIT ENDPOINTS
# =====================================================

@app.get("/api/v1/audit", response_model=List[AuditEventResponse], tags=["Audit"])
async def get_audit_trail(
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    user_id: Optional[str] = None,
    days: int = Query(30, le=365),
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get audit trail with filters."""
    from datetime import date, timedelta
    cutoff = date.today() - timedelta(days=days)
    
    query = db.query(AuditEvent).filter(AuditEvent.timestamp >= cutoff)
    
    if entity_type:
        query = query.filter(AuditEvent.entity_type == entity_type)
    if entity_id:
        query = query.filter(AuditEvent.entity_id == entity_id)
    if user_id:
        query = query.filter(AuditEvent.user_id == user_id)
    
    return query.order_by(AuditEvent.timestamp.desc()).offset(offset).limit(limit).all()


# =====================================================
# ANALYTICS ENDPOINTS
# =====================================================

@app.get("/api/v1/analytics/dashboard", response_model=DashboardSummary, tags=["Analytics"])
async def get_dashboard(db: Session = Depends(get_db)):
    """Get dashboard summary metrics."""
    analytics = AnalyticsEngine(db)
    return analytics.get_dashboard_summary()


@app.get("/api/v1/analytics/obligation-coverage", response_model=ObligationCoverageResponse, tags=["Analytics"])
async def get_obligation_coverage(
    regulation_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get obligation coverage analysis."""
    analytics = AnalyticsEngine(db)
    return analytics.get_obligation_coverage(regulation_id)


@app.get("/api/v1/analytics/control-coverage", tags=["Analytics"])
async def get_control_coverage(db: Session = Depends(get_db)):
    """Get control coverage metrics."""
    analytics = AnalyticsEngine(db)
    return analytics.get_control_coverage()


@app.get("/api/v1/analytics/evidence-completeness", tags=["Analytics"])
async def get_evidence_completeness(
    control_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get evidence completeness metrics."""
    analytics = AnalyticsEngine(db)
    return analytics.get_evidence_completeness(control_id)


@app.get("/api/v1/analytics/evidence-freshness", tags=["Analytics"])
async def get_evidence_freshness(
    control_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get evidence freshness metrics."""
    analytics = AnalyticsEngine(db)
    return analytics.get_evidence_freshness(control_id)


@app.get("/api/v1/analytics/risk-exposure", tags=["Analytics"])
async def get_risk_exposure(db: Session = Depends(get_db)):
    """Get organizational risk exposure."""
    analytics = AnalyticsEngine(db)
    return analytics.get_risk_exposure()


@app.get("/api/v1/analytics/gaps", response_model=UnresolvedGapsResponse, tags=["Analytics"])
async def get_unresolved_gaps(db: Session = Depends(get_db)):
    """Get all unresolved gaps."""
    analytics = AnalyticsEngine(db)
    return analytics.get_unresolved_gaps()


@app.get("/api/v1/analytics/trends", tags=["Analytics"])
async def get_trends(days: int = Query(90, le=365), db: Session = Depends(get_db)):
    """Get trend metrics."""
    analytics = AnalyticsEngine(db)
    return analytics.get_trend_metrics(days)


# =====================================================
# TRACEABILITY ENDPOINTS
# =====================================================

@app.get("/api/v1/traceability/{obligation_id}", response_model=TraceabilityChainResponse, tags=["Traceability"])
async def get_traceability_chain(obligation_id: str, db: Session = Depends(get_db)):
    """Get full traceability chain for an obligation."""
    chain = build_traceability_chain(db, obligation_id)
    if "error" in chain:
        raise HTTPException(status_code=404, detail=chain["error"])
    return chain


# =====================================================
# INVESTIGATION / AGENT ENDPOINTS
# =====================================================

@app.post("/api/v1/investigate", response_model=InvestigationResponse, tags=["Investigation"])
async def investigate(request: InvestigationRequest, db: Session = Depends(get_db)):
    """AI-powered investigation with evidence attribution."""
    tools = AgentTools(db)
    retriever = HybridRetriever(db)
    
    # Determine which tools to use based on question
    question = request.question.lower()
    evidence = []
    tools_used = []
    
    # Simple keyword routing
    if "control" in question and "evidence" in question:
        # Extract control ID if present
        import re
        control_match = re.search(r'(CTL_[A-Z0-9_]+)', question, re.IGNORECASE)
        if control_match:
            control_id = control_match.group(1)
            tools_used.append("search_evidence")
            results = retrieve_evidence_for_control(db, control_id, request.question)
            evidence = [r.to_dict() for r in results]
    
    elif "obligation" in question and ("coverage" in question or "control" in question):
        obl_match = re.search(r'(OBL_[A-Z0-9_]+)', question, re.IGNORECASE)
        if obl_match:
            obl_id = obl_match.group(1)
            tools_used.append("get_obligation_coverage")
            coverage = tools.analytics.get_obligation_coverage()
            for obl in coverage["obligations"]:
                if obl["obligation_id"] == obl_id:
                    evidence.append(obl)
                    break
    
    elif "exception" in question:
        tools_used.append("analyze_exceptions")
        exc_analysis = tools.analyze_exceptions(days=30)
        evidence.append(exc_analysis)
    
    elif "trace" in question or "traceability" in question:
        obl_match = re.search(r'(OBL_[A-Z0-9_]+)', question, re.IGNORECASE)
        if obl_match:
            obl_id = obl_match.group(1)
            tools_used.append("build_traceability_chain")
            chain = build_traceability_chain(db, obl_id)
            evidence.append(chain)
    
    # If no specific tool matched, do general retrieval
    if not evidence:
        tools_used.append("hybrid_retrieval")
        results = retriever.retrieve(request.question, limit=10)
        evidence = [r.to_dict() for r in results]
    
    # Generate answer (in production, use LLM)
    answer = _generate_answer(request.question, evidence)
    insufficient = len(evidence) == 0
    
    return InvestigationResponse(
        question=request.question,
        answer=answer,
        evidence=evidence,
        tools_used=tools_used,
        confidence=0.8 if not insufficient else 0.0,
        insufficient_evidence=insufficient
    )


def _generate_answer(question: str, evidence: List[Dict]) -> str:
    """Generate answer from evidence (placeholder for LLM)."""
    if not evidence:
        return "Insufficient evidence to answer this question. No relevant data found in the system."
    
    # Simple template-based answer
    if len(evidence) == 1 and isinstance(evidence[0], dict):
        if "evidence" in evidence[0]:
            ev = evidence[0]["evidence"]
            return f"Found {len(ev)} evidence items. " + "; ".join([e.get("title", "") for e in ev[:3]])
        elif "controls" in evidence[0]:
            controls = evidence[0]["controls"]
            return f"Traceability chain shows {len(controls)} controls linked."
    
    return f"Found {len(evidence)} relevant results. " + str(evidence[0])[:200]


# =====================================================
# DOCUMENT ENDPOINTS
# =====================================================

@app.post("/api/v1/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED, tags=["Documents"])
async def create_document(document: DocumentCreate, db: Session = Depends(get_db)):
    """Create document record (ingestion happens separately)."""
    db_doc = Document(**document.model_dump())
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    return db_doc


@app.get("/api/v1/documents", response_model=List[DocumentResponse], tags=["Documents"])
async def list_documents(
    document_type: Optional[str] = None,
    source: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List documents."""
    query = db.query(Document)
    
    if document_type:
        query = query.filter(Document.document_type == document_type)
    if source:
        query = query.filter(Document.source == source)
    if status:
        query = query.filter(Document.ingestion_status == status)
    
    return query.order_by(Document.created_at.desc()).offset(offset).limit(limit).all()


@app.get("/api/v1/documents/{document_id}", response_model=DocumentResponse, tags=["Documents"])
async def get_document(document_id: str, db: Session = Depends(get_db)):
    """Get document by ID."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@app.get("/api/v1/documents/{document_id}/chunks", response_model=List[DocumentChunkResponse], tags=["Documents"])
async def get_document_chunks(document_id: str, db: Session = Depends(get_db)):
    """Get chunks for a document."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return db.query(DocumentChunk).filter(
        DocumentChunk.document_id == document_id
    ).order_by(DocumentChunk.chunk_index).all()


@app.post("/api/v1/documents/ingest", tags=["Documents"])
async def ingest_document(
    file_path: str,
    title: str,
    source: str,
    document_type: str,
    publication_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Ingest a document through the pipeline."""
    import os
    if not os.path.exists(file_path):
        raise HTTPException(status_code=400, detail="File not found")
    
    pipeline = DocumentIngestionPipeline(db)
    document = pipeline.ingest(file_path, title, source, document_type, publication_date)
    return {"document_id": document.id, "status": document.ingestion_status, "chunks": document.chunk_count}


# =====================================================
# RETRIEVAL ENDPOINTS
# =====================================================

@app.post("/api/v1/retrieval/search", response_model=RetrievalResponse, tags=["Retrieval"])
async def search(request: RetrievalRequest, db: Session = Depends(get_db)):
    """Hybrid search across all sources."""
    retriever = HybridRetriever(db)
    results = retriever.retrieve(
        request.query,
        filters=request.filters,
        limit=request.limit,
        source_types=request.source_types
    )
    
    return RetrievalResponse(
        query=request.query,
        results=[r.to_dict() for r in results],
        total=len(results)
    )


# =====================================================
# AGENT ENDPOINTS
# =====================================================

@app.get("/api/v1/agents", tags=["Agents"])
async def list_available_agents():
    """List available agents."""
    return {"agents": list_agents()}


@app.post("/api/v1/agents/{agent_name}/run", tags=["Agents"])
async def run_agent(
    agent_name: str,
    action: str,
    parameters: Dict,
    db: Session = Depends(get_db)
):
    """Run a specific agent action."""
    agent = get_agent(agent_name, db)
    
    # Map actions to methods
    action_map = {
        "document_intelligence": {
            "analyze_document": agent.analyze_document,
            "extract_obligations": agent.extract_obligations
        },
        "obligation_mapping": {
            "map_obligation_to_policy": agent.map_obligation_to_policy,
            "map_policy_to_process": agent.map_policy_to_process,
            "map_process_to_control": agent.map_process_to_control
        },
        "evidence": {
            "get_evidence_for_control": agent.get_evidence_for_control,
            "identify_evidence_gaps": agent.identify_evidence_gaps,
            "verify_evidence_claim": agent.verify_evidence_claim
        },
        "monitoring": {
            "check_control_health": agent.check_control_health,
            "monitor_exceptions": agent.monitor_exceptions,
            "detect_transaction_anomalies": agent.detect_transaction_anomalies,
            "get_risk_trends": agent.get_risk_trends
        },
        "gap_analysis": {
            "find_unresolved_gaps": agent.find_unresolved_gaps,
            "analyze_obligation_gaps": agent.analyze_obligation_gaps,
            "analyze_control_gaps": agent.analyze_control_gaps
        },
        "report": {
            "generate_dashboard_report": agent.generate_dashboard_report,
            "generate_obligation_coverage_report": agent.generate_obligation_coverage_report,
            "generate_control_effectiveness_report": agent.generate_control_effectiveness_report,
            "generate_exception_report": agent.generate_exception_report,
            "generate_traceability_report": agent.generate_traceability_report
        }
    }
    
    agent_actions = action_map.get(agent_name, {})
    method = agent_actions.get(action)
    
    if not method:
        raise HTTPException(status_code=400, detail=f"Unknown action: {action} for agent: {agent_name}")
    
    try:
        result = method(**parameters)
        return {"agent": agent_name, "action": action, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# DATA GENERATION (Admin)
# =====================================================

@app.post("/api/v1/admin/generate-data", tags=["Admin"])
async def generate_synthetic_data(db: Session = Depends(get_db)):
    """Generate synthetic data for testing."""
    # Import and run generation
    from scripts.generate_data import main as generate_main
    import sys
    import io
    from contextlib import redirect_stdout
    
    # Capture output
    f = io.StringIO()
    with redirect_stdout(f):
        try:
            generate_main()
        except SystemExit:
            pass
    
    output = f.getvalue()
    return {"status": "completed", "output": output[-2000:]}  # Last 2000 chars


@app.post("/api/v1/admin/ingest-samples", tags=["Admin"])
async def ingest_sample_docs(db: Session = Depends(get_db)):
    """Ingest sample documents."""
    documents = ingest_sample_documents(db)
    return {"ingested": len(documents), "documents": [{"id": d.id, "title": d.title} for d in documents]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)