"""
Deterministic Agent Tools for CONTROLLENS
Each tool performs a specific database operation or calculation.
LLM reasons over tool results - never invents facts.
"""
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from app.db.base import (
    Regulation, RegulatorySection, Obligation, Policy, Process,
    Control, ControlOwner, Evidence, Transaction, Exception as Exc,
    RiskAssessment, MappingReview, AuditEvent
)
from app.services.analytics import (
    AnalyticsEngine, calculate_control_effectiveness, build_traceability_chain
)
from app.services.retrieval import HybridRetriever, retrieve_evidence_for_control


class AgentTools:
    """Collection of deterministic tools for agents."""
    
    def __init__(self, db: Session):
        self.db = db
        self.analytics = AnalyticsEngine(db)
        self.retriever = HybridRetriever(db)
    
    # =====================================================
    # REGULATION TOOLS
    # =====================================================
    
    def search_regulation(self, query: str, jurisdiction: str = None, 
                          regulator: str = None, limit: int = 10) -> List[Dict]:
        """Search regulations by text, jurisdiction, or regulator."""
        q = self.db.query(Regulation).filter(Regulation.status == 'active')
        
        if jurisdiction:
            q = q.filter(Regulation.jurisdiction.ilike(f"%{jurisdiction}%"))
        if regulator:
            q = q.filter(Regulation.regulator.ilike(f"%{regulator}%"))
        if query:
            q = q.filter(
                or_(
                    Regulation.title.ilike(f"%{query}%"),
                    Regulation.description.ilike(f"%{query}%"),
                    Regulation.short_name.ilike(f"%{query}%")
                )
            )
        
        results = q.limit(limit).all()
        return [
            {
                "id": r.id,
                "title": r.title,
                "short_name": r.short_name,
                "jurisdiction": r.jurisdiction,
                "regulator": r.regulator,
                "publication_date": r.publication_date.isoformat() if r.publication_date else None,
                "effective_date": r.effective_date.isoformat() if r.effective_date else None,
                "status": r.status
            }
            for r in results
        ]
    
    def get_regulation_sections(self, regulation_id: str) -> List[Dict]:
        """Get all sections for a regulation."""
        sections = self.db.query(RegulatorySection).filter(
            RegulatorySection.regulation_id == regulation_id
        ).order_by(RegulatorySection.section_number).all()
        
        return [
            {
                "id": s.id,
                "section_number": s.section_number,
                "title": s.title,
                "section_type": s.section_type,
                "page_start": s.page_start,
                "page_end": s.page_end,
                "content_preview": s.content[:500] if s.content else None
            }
            for s in sections
        ]
    
    # =====================================================
    # OBLIGATION TOOLS
    # =====================================================
    
    def get_obligation(self, obligation_id: str) -> Optional[Dict]:
        """Get obligation with full details."""
        obl = self.db.query(Obligation).filter(Obligation.id == obligation_id).first()
        if not obl:
            return None
        
        regulation = self.db.query(Regulation).filter(Regulation.id == obl.regulation_id).first()
        section = self.db.query(RegulatorySection).filter(RegulatorySection.id == obl.section_id).first()
        
        return {
            "id": obl.id,
            "regulation_id": obl.regulation_id,
            "regulation_title": regulation.title if regulation else None,
            "section_id": obl.section_id,
            "section_title": section.title if section else None,
            "obligation_text": obl.obligation_text,
            "obligation_type": obl.obligation_type,
            "category": obl.category,
            "risk_level": obl.risk_level,
            "status": obl.status,
            "effective_date": obl.effective_date.isoformat() if obl.effective_date else None
        }
    
    def search_obligations(self, regulation_id: str = None, category: str = None,
                           risk_level: str = None, limit: int = 20) -> List[Dict]:
        """Search obligations with filters."""
        q = self.db.query(Obligation).filter(Obligation.status == 'active')
        
        if regulation_id:
            q = q.filter(Obligation.regulation_id == regulation_id)
        if category:
            q = q.filter(Obligation.category == category)
        if risk_level:
            q = q.filter(Obligation.risk_level == risk_level)
        
        results = q.limit(limit).all()
        return [
            {
                "id": o.id,
                "regulation_id": o.regulation_id,
                "obligation_text": o.obligation_text[:200],
                "category": o.category,
                "risk_level": o.risk_level
            }
            for o in results
        ]
    
    def get_obligation_coverage(self, obligation_id: str) -> Dict:
        """Get coverage analysis for a specific obligation."""
        return self.analytics.get_obligation_coverage()[obligation_id] if obligation_id else self.analytics.get_obligation_coverage()
    
    def get_weak_obligations(self, min_controls: int = 1, min_evidence: int = 1) -> List[Dict]:
        """Find obligations with weak control/evidence coverage."""
        coverage = self.analytics.get_obligation_coverage()
        weak = []
        for obl in coverage["obligations"]:
            if obl["control_count"] < min_controls or obl["verified_evidence_count"] < min_evidence:
                weak.append(obl)
        return weak
    
    # =====================================================
    # POLICY TOOLS
    # =====================================================
    
    def get_policy(self, policy_id: str) -> Optional[Dict]:
        """Get policy with full details."""
        pol = self.db.query(Policy).filter(Policy.id == policy_id).first()
        if not pol:
            return None
        
        return {
            "id": pol.id,
            "title": pol.title,
            "description": pol.description,
            "policy_type": pol.policy_type,
            "owner_department": pol.owner_department,
            "owner_role": pol.owner_role,
            "version": pol.version,
            "status": pol.status,
            "effective_date": pol.effective_date.isoformat() if pol.effective_date else None,
            "review_date": pol.review_date.isoformat() if pol.review_date else None
        }
    
    def search_policies(self, policy_type: str = None, department: str = None,
                        status: str = None, limit: int = 20) -> List[Dict]:
        """Search policies with filters."""
        q = self.db.query(Policy)
        
        if policy_type:
            q = q.filter(Policy.policy_type == policy_type)
        if department:
            q = q.filter(Policy.owner_department == department)
        if status:
            q = q.filter(Policy.status == status)
        
        results = q.limit(limit).all()
        return [
            {
                "id": p.id,
                "title": p.title,
                "policy_type": p.policy_type,
                "owner_department": p.owner_department,
                "version": p.version,
                "status": p.status
            }
            for p in results
        ]
    
    # =====================================================
    # PROCESS TOOLS
    # =====================================================
    
    def get_process(self, process_id: str) -> Optional[Dict]:
        """Get process with full details."""
        proc = self.db.query(Process).filter(Process.id == process_id).first()
        if not proc:
            return None
        
        controls = self.db.query(Control).filter(
            Control.process_id == process_id,
            Control.status == 'active'
        ).all()
        
        return {
            "id": proc.id,
            "name": proc.name,
            "description": proc.description,
            "department": proc.department,
            "process_owner": proc.process_owner,
            "risk_rating": proc.risk_rating,
            "status": proc.status,
            "control_count": len(controls),
            "controls": [{"id": c.id, "name": c.name} for c in controls]
        }
    
    # =====================================================
    # CONTROL TOOLS
    # =====================================================
    
    def get_control(self, control_id: str) -> Optional[Dict]:
        """Get control with full details."""
        ctl = self.db.query(Control).filter(Control.id == control_id).first()
        if not ctl:
            return None
        
        process = self.db.query(Process).filter(Process.id == ctl.process_id).first()
        policy = self.db.query(Policy).filter(Policy.id == ctl.policy_id).first() if ctl.policy_id else None
        owners = self.db.query(ControlOwner).filter(ControlOwner.control_id == control_id).all()
        
        return {
            "id": ctl.id,
            "name": ctl.name,
            "description": ctl.description,
            "control_type": ctl.control_type,
            "control_category": ctl.control_category,
            "frequency": ctl.frequency,
            "automation_level": ctl.automation_level,
            "status": ctl.status,
            "design_effectiveness": ctl.design_effectiveness,
            "operating_effectiveness": ctl.operating_effectiveness,
            "last_tested_date": ctl.last_tested_date.isoformat() if ctl.last_tested_date else None,
            "next_test_date": ctl.next_test_date.isoformat() if ctl.next_test_date else None,
            "process": {"id": process.id, "name": process.name} if process else None,
            "policy": {"id": policy.id, "title": policy.title} if policy else None,
            "owners": [
                {
                    "name": o.person_name,
                    "email": o.person_email,
                    "type": o.owner_type,
                    "department": o.department
                }
                for o in owners
            ]
        }
    
    def search_controls(self, process_id: str = None, policy_id: str = None,
                        control_type: str = None, status: str = "active",
                        limit: int = 20) -> List[Dict]:
        """Search controls with filters."""
        q = self.db.query(Control)
        
        if process_id:
            q = q.filter(Control.process_id == process_id)
        if policy_id:
            q = q.filter(Control.policy_id == policy_id)
        if control_type:
            q = q.filter(Control.control_type == control_type)
        if status:
            q = q.filter(Control.status == status)
        
        results = q.limit(limit).all()
        return [
            {
                "id": c.id,
                "name": c.name,
                "control_type": c.control_type,
                "control_category": c.control_category,
                "frequency": c.frequency,
                "automation_level": c.automation_level,
                "status": c.status,
                "design_effectiveness": c.design_effectiveness,
                "operating_effectiveness": c.operating_effectiveness,
                "next_test_date": c.next_test_date.isoformat() if c.next_test_date else None
            }
            for c in results
        ]
    
    def get_control_effectiveness(self, control_id: str) -> Dict:
        """Calculate detailed control effectiveness."""
        return calculate_control_effectiveness(self.db, control_id)
    
    def get_overdue_controls(self) -> List[Dict]:
        """Get controls with overdue testing."""
        today = date.today()
        controls = self.db.query(Control).filter(
            Control.status == 'active',
            Control.next_test_date < today
        ).order_by(Control.next_test_date).all()
        
        return [
            {
                "id": c.id,
                "name": c.name,
                "next_test_date": c.next_test_date.isoformat(),
                "days_overdue": (today - c.next_test_date).days,
                "frequency": c.frequency
            }
            for c in controls
        ]
    
    # =====================================================
    # EVIDENCE TOOLS
    # =====================================================
    
    def search_evidence(self, control_id: str = None, evidence_type: str = None,
                        status: str = "verified", limit: int = 20) -> List[Dict]:
        """Search evidence records."""
        q = self.db.query(Evidence)
        
        if control_id:
            q = q.filter(Evidence.control_id == control_id)
        if evidence_type:
            q = q.filter(Evidence.evidence_type == evidence_type)
        if status:
            q = q.filter(Evidence.status == status)
        
        results = q.order_by(Evidence.collected_at.desc()).limit(limit).all()
        
        return [
            {
                "id": e.id,
                "control_id": e.control_id,
                "evidence_type": e.evidence_type,
                "title": e.title,
                "description": e.description,
                "status": e.status,
                "collected_at": e.collected_at.isoformat() if e.collected_at else None,
                "period_start": e.period_start.isoformat() if e.period_start else None,
                "period_end": e.period_end.isoformat() if e.period_end else None,
                "expiry_date": e.expiry_date.isoformat() if e.expiry_date else None,
                "source_system": e.source_system,
                "verified_by": e.verified_by,
                "verified_at": e.verified_at.isoformat() if e.verified_at else None
            }
            for e in results
        ]
    
    def get_evidence_completeness(self, control_id: str = None) -> Dict:
        """Get evidence completeness metrics."""
        return self.analytics.get_evidence_completeness(control_id)
    
    def get_stale_evidence(self, days: int = 90) -> List[Dict]:
        """Get evidence older than specified days."""
        cutoff = date.today() - timedelta(days=days)
        evidence = self.db.query(Evidence).filter(
            Evidence.status == 'verified',
            Evidence.collected_at < cutoff
        ).order_by(Evidence.collected_at).all()
        
        return [
            {
                "id": e.id,
                "control_id": e.control_id,
                "title": e.title,
                "collected_at": e.collected_at.isoformat(),
                "days_old": (date.today() - e.collected_at.date()).days,
                "expiry_date": e.expiry_date.isoformat() if e.expiry_date else None
            }
            for e in evidence
        ]
    
    # =====================================================
    # TRANSACTION TOOLS
    # =====================================================
    
    def query_transactions(self, process_id: str = None, control_id: str = None,
                           start_date: date = None, end_date: date = None,
                           min_risk_score: float = None, max_risk_score: float = None,
                           flags: List[str] = None, limit: int = 50) -> List[Dict]:
        """Query transactions with filters."""
        q = self.db.query(Transaction)
        
        if process_id:
            q = q.filter(Transaction.process_id == process_id)
        if control_id:
            q = q.filter(Transaction.control_id == control_id)
        if start_date:
            q = q.filter(Transaction.transaction_date >= start_date)
        if end_date:
            q = q.filter(Transaction.transaction_date <= end_date)
        if min_risk_score is not None:
            q = q.filter(Transaction.risk_score >= min_risk_score)
        if max_risk_score is not None:
            q = q.filter(Transaction.risk_score <= max_risk_score)
        if flags:
            q = q.filter(Transaction.flags.op('&&')(flags))
        
        results = q.order_by(Transaction.transaction_date.desc()).limit(limit).all()
        
        return [
            {
                "id": t.id,
                "transaction_id": t.transaction_id,
                "transaction_date": t.transaction_date.isoformat(),
                "transaction_type": t.transaction_type,
                "amount": float(t.amount) if t.amount else None,
                "currency": t.currency,
                "account_id": t.account_id,
                "counterparty": t.counterparty,
                "status": t.status,
                "risk_score": float(t.risk_score) if t.risk_score else None,
                "flags": t.flags,
                "process_id": t.process_id,
                "control_id": t.control_id
            }
            for t in results
        ]
    
    def get_high_risk_transactions(self, threshold: float = 70.0, days: int = 30) -> List[Dict]:
        """Get high-risk transactions in recent period."""
        cutoff = date.today() - timedelta(days=days)
        return self.query_transactions(
            start_date=cutoff,
            min_risk_score=threshold,
            limit=100
        )
    
    # =====================================================
    # EXCEPTION TOOLS
    # =====================================================
    
    def analyze_exceptions(self, control_id: str = None, process_id: str = None,
                           obligation_id: str = None, severity: str = None,
                           status: str = None, days: int = 90) -> Dict:
        """Analyze exceptions with filters."""
        cutoff = date.today() - timedelta(days=days)
        
        q = self.db.query(Exc).filter(Exc.detected_date >= cutoff)
        
        if control_id:
            q = q.filter(Exc.control_id == control_id)
        if process_id:
            q = q.filter(Exc.process_id == process_id)
        if obligation_id:
            q = q.filter(Exc.obligation_id == obligation_id)
        if severity:
            q = q.filter(Exc.severity == severity)
        if status:
            q = q.filter(Exc.status == status)
        
        exceptions = q.all()
        
        return {
            "total": len(exceptions),
            "by_severity": {
                "critical": len([e for e in exceptions if e.severity == "critical"]),
                "high": len([e for e in exceptions if e.severity == "high"]),
                "medium": len([e for e in exceptions if e.severity == "medium"]),
                "low": len([e for e in exceptions if e.severity == "low"])
            },
            "by_status": {
                "open": len([e for e in exceptions if e.status == "open"]),
                "investigating": len([e for e in exceptions if e.status == "investigating"]),
                "remediated": len([e for e in exceptions if e.status == "remediated"]),
                "closed": len([e for e in exceptions if e.status == "closed"]),
                "accepted_risk": len([e for e in exceptions if e.status == "accepted_risk"])
            },
            "by_type": {},
            "recent": [
                {
                    "id": e.id,
                    "number": e.exception_number,
                    "title": e.title,
                    "severity": e.severity,
                    "status": e.status,
                    "detected_date": e.detected_date.isoformat(),
                    "control_id": e.control_id,
                    "process_id": e.process_id
                }
                for e in sorted(exceptions, key=lambda x: x.detected_date, reverse=True)[:20]
            ]
        }
    
    def get_open_exceptions(self) -> List[Dict]:
        """Get all open exceptions."""
        return self.analyze_exceptions(status="open")["recent"]
    
    # =====================================================
    # TRACEABILITY TOOLS
    # =====================================================
    
    def build_traceability_chain(self, obligation_id: str) -> Dict:
        """Build full traceability chain from regulation to exception."""
        return build_traceability_chain(self.db, obligation_id)
    
    def get_mapping_reviews(self, source_type: str = None, source_id: str = None,
                            target_type: str = None, target_id: str = None,
                            status: str = None) -> List[Dict]:
        """Get mapping reviews with filters."""
        q = self.db.query(MappingReview)
        
        if source_type:
            q = q.filter(MappingReview.source_entity_type == source_type)
        if source_id:
            q = q.filter(MappingReview.source_entity_id == source_id)
        if target_type:
            q = q.filter(MappingReview.target_entity_type == target_type)
        if target_id:
            q = q.filter(MappingReview.target_entity_id == target_id)
        if status:
            q = q.filter(MappingReview.status == status)
        
        results = q.order_by(MappingReview.created_at.desc()).all()
        
        return [
            {
                "id": m.id,
                "mapping_type": m.mapping_type,
                "source_entity_type": m.source_entity_type,
                "source_entity_id": m.source_entity_id,
                "target_entity_type": m.target_entity_type,
                "target_entity_id": m.target_entity_id,
                "confidence_score": float(m.confidence_score) if m.confidence_score else None,
                "ai_reasoning": m.ai_reasoning,
                "status": m.status,
                "reviewed_by": m.reviewed_by,
                "reviewed_at": m.reviewed_at.isoformat() if m.reviewed_at else None,
                "review_decision": m.review_decision,
                "review_comments": m.review_comments
            }
            for m in results
        ]
    
    def get_proposed_mappings(self) -> List[Dict]:
        """Get all proposed mappings awaiting human review."""
        return self.get_mapping_reviews(status="proposed")
    
    # =====================================================
    # RISK TOOLS
    # =====================================================
    
    def get_risk_assessment(self, entity_type: str, entity_id: str) -> Optional[Dict]:
        """Get risk assessment for an entity."""
        ra = self.db.query(RiskAssessment).filter(
            RiskAssessment.entity_type == entity_type,
            RiskAssessment.entity_id == entity_id
        ).first()
        
        if not ra:
            return None
        
        return {
            "id": ra.id,
            "entity_type": ra.entity_type,
            "entity_id": ra.entity_id,
            "risk_category": ra.risk_category,
            "inherent_risk": ra.inherent_risk,
            "residual_risk": ra.residual_risk,
            "likelihood": ra.likelihood,
            "impact": ra.impact,
            "risk_score": float(ra.risk_score) if ra.risk_score else None,
            "mitigation_status": ra.mitigation_status,
            "assessed_by": ra.assessed_by,
            "assessed_date": ra.assessed_date.isoformat() if ra.assessed_date else None,
            "next_review_date": ra.next_review_date.isoformat() if ra.next_review_date else None
        }
    
    def get_high_risk_entities(self, entity_type: str = None) -> List[Dict]:
        """Get entities with high residual risk."""
        q = self.db.query(RiskAssessment).filter(
            RiskAssessment.residual_risk.in_(["high", "critical"])
        )
        
        if entity_type:
            q = q.filter(RiskAssessment.entity_type == entity_type)
        
        results = q.order_by(RiskAssessment.risk_score.desc()).limit(20).all()
        
        return [
            {
                "entity_type": r.entity_type,
                "entity_id": r.entity_id,
                "risk_category": r.risk_category,
                "residual_risk": r.residual_risk,
                "risk_score": float(r.risk_score) if r.risk_score else None,
                "mitigation_status": r.mitigation_status
            }
            for r in results
        ]
    
    # =====================================================
    # AUDIT TOOLS
    # =====================================================
    
    def get_audit_trail(self, entity_type: str = None, entity_id: str = None,
                        user_id: str = None, days: int = 30) -> List[Dict]:
        """Get audit trail with filters."""
        cutoff = date.today() - timedelta(days=days)
        
        q = self.db.query(AuditEvent).filter(AuditEvent.created_at >= cutoff)
        
        if entity_type:
            q = q.filter(AuditEvent.entity_type == entity_type)
        if entity_id:
            q = q.filter(AuditEvent.entity_id == entity_id)
        if user_id:
            q = q.filter(AuditEvent.user_id == user_id)
        
        results = q.order_by(AuditEvent.created_at.desc()).limit(100).all()
        
        return [
            {
                "id": a.id,
                "event_type": a.event_type,
                "entity_type": a.entity_type,
                "entity_id": a.entity_id,
                "user_id": a.user_id,
                "user_role": a.user_role,
                "action": a.action,
                "timestamp": a.timestamp.isoformat(),
                "old_values": a.old_values,
                "new_values": a.new_values
            }
            for a in results
        ]


# Convenience function for agent use
def get_agent_tools(db: Session) -> AgentTools:
    """Get agent tools instance."""
    return AgentTools(db)