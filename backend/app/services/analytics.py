"""
Analytics Module for CONTROLLENS
Deterministic calculations for control effectiveness, coverage, risk exposure, etc.
All calculations use SQL/Python - no LLM involvement.
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any
from sqlalchemy import text, func, and_, or_
from sqlalchemy.orm import Session

from app.db.base import (
    Regulation, Obligation, Policy, Process, Control,
    Evidence, Transaction, Exception as Exc,
    RiskAssessment, MappingReview, DocumentChunk
)


class AnalyticsEngine:
    """Deterministic analytics calculations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    # =====================================================
    # CONTROL EXECUTION METRICS
    # =====================================================
    
    def get_control_execution_rate(self, control_id: Optional[str] = None,
                                    days: int = 90) -> Dict[str, Any]:
        """Calculate control execution rate over specified period."""
        cutoff = date.today() - timedelta(days=days)
        
        query = self.db.query(
            Control.id,
            Control.name,
            Control.frequency,
            Control.next_test_date,
            func.count(Evidence.id).label('evidence_count'),
            func.count(Evidence.id).filter(Evidence.status == 'verified').label('verified_count'),
            func.max(Evidence.collected_at).label('latest_evidence')
        ).outerjoin(Evidence, and_(
            Evidence.control_id == Control.id,
            Evidence.collected_at >= cutoff
        )).filter(Control.status == 'active')
        
        if control_id:
            query = query.filter(Control.id == control_id)
        
        results = query.group_by(Control.id, Control.name, Control.frequency, Control.next_test_date).all()
        
        execution_rates = []
        for row in results:
            expected_executions = self._calculate_expected_executions(row.frequency, days)
            actual_executions = row.verified_count or 0
            rate = (actual_executions / expected_executions * 100) if expected_executions > 0 else 0
            
            execution_rates.append({
                "control_id": row.id,
                "control_name": row.name,
                "frequency": row.frequency,
                "expected_executions": expected_executions,
                "actual_executions": actual_executions,
                "execution_rate_pct": round(rate, 2),
                "next_test_date": row.next_test_date.isoformat() if row.next_test_date else None,
                "is_overdue": row.next_test_date and row.next_test_date < date.today(),
                "latest_evidence_date": row.latest_evidence.isoformat() if row.latest_evidence else None
            })
        
        overall_rate = sum(r["execution_rate_pct"] for r in execution_rates) / len(execution_rates) if execution_rates else 0
        
        return {
            "period_days": days,
            "overall_execution_rate_pct": round(overall_rate, 2),
            "controls": execution_rates
        }
    
    def _calculate_expected_executions(self, frequency: str, days: int) -> int:
        """Calculate expected number of executions based on frequency."""
        freq_map = {
            "daily": days,
            "weekly": max(1, days // 7),
            "monthly": max(1, days // 30),
            "quarterly": max(1, days // 90),
            "annually": max(1, days // 365),
            "ad_hoc": 1,
            "continuous": days,
            "per_change": max(1, days // 30),
            "per_project": max(1, days // 90)
        }
        return freq_map.get(frequency, 1)
    
    # =====================================================
    # EXCEPTION METRICS
    # =====================================================
    
    def get_exception_rate(self, days: int = 90,
                            group_by: str = "month") -> Dict[str, Any]:
        """Calculate exception rate and trends."""
        cutoff = date.today() - timedelta(days=days)
        
        exceptions = self.db.query(Exc).filter(Exc.detected_date >= cutoff).all()
        
        total = len(exceptions)
        by_severity = {}
        by_type = {}
        by_status = {}
        by_month = {}
        
        for exc in exceptions:
            # By severity
            by_severity[exc.severity] = by_severity.get(exc.severity, 0) + 1
            # By type
            by_type[exc.exception_type] = by_type.get(exc.exception_type, 0) + 1
            # By status
            by_status[exc.status] = by_status.get(exc.status, 0) + 1
            # By month
            month_key = exc.detected_date.strftime("%Y-%m")
            by_month[month_key] = by_month.get(month_key, 0) + 1
        
        # Resolution time for closed exceptions
        resolved = [e for e in exceptions if e.actual_resolution_date]
        avg_resolution_days = 0
        if resolved:
            total_days = sum((e.actual_resolution_date - e.detected_date).days for e in resolved)
            avg_resolution_days = round(total_days / len(resolved), 1)
        
        open_exceptions = by_status.get("open", 0) + by_status.get("investigating", 0)
        
        return {
            "period_days": days,
            "total_exceptions": total,
            "open_exceptions": open_exceptions,
            "closed_exceptions": by_status.get("closed", 0) + by_status.get("remediated", 0),
            "by_severity": by_severity,
            "by_type": by_type,
            "by_status": by_status,
            "by_month": dict(sorted(by_month.items())),
            "avg_resolution_days": avg_resolution_days,
            "exception_rate_per_month": round(total / max(1, days / 30), 2)
        }
    
    def get_recent_exception_spikes(self, threshold: float = 2.0) -> List[Dict]:
        """Detect months with exception count spikes."""
        monthly = self.get_exception_rate(days=365, group_by="month")["by_month"]
        if len(monthly) < 2:
            return []
        
        values = list(monthly.values())
        avg = sum(values) / len(values)
        std = (sum((v - avg) ** 2 for v in values) / len(values)) ** 0.5
        
        spikes = []
        for month, count in monthly.items():
            if count > avg + threshold * std:
                spikes.append({
                    "month": month,
                    "count": count,
                    "avg": round(avg, 1),
                    "std_dev": round(std, 1),
                    "z_score": round((count - avg) / std, 2) if std > 0 else 0
                })
        return spikes
    
    # =====================================================
    # EVIDENCE METRICS
    # =====================================================
    
    def get_evidence_completeness(self, control_id: Optional[str] = None) -> Dict[str, Any]:
        """Calculate evidence completeness per control."""
        query = self.db.query(
            Control.id,
            Control.name,
            func.count(Evidence.id).label('total_evidence'),
            func.count(Evidence.id).filter(Evidence.status == 'verified').label('verified_evidence'),
            func.count(Evidence.id).filter(Evidence.status == 'submitted').label('pending_evidence'),
            func.count(Evidence.id).filter(Evidence.status == 'rejected').label('rejected_evidence'),
            func.count(Evidence.id).filter(Evidence.status == 'expired').label('expired_evidence'),
            func.max(Evidence.expiry_date).label('latest_expiry'),
            func.min(Evidence.expiry_date).label('earliest_expiry')
        ).outerjoin(Evidence, Evidence.control_id == Control.id).filter(
            Control.status == 'active'
        )
        
        if control_id:
            query = query.filter(Control.id == control_id)
        
        results = query.group_by(Control.id, Control.name).all()
        
        completeness = []
        for row in results:
            total = row.total_evidence or 0
            verified = row.verified_evidence or 0
            completeness_pct = (verified / total * 100) if total > 0 else 0
            
            # Determine status
            if total == 0:
                status = "no_evidence"
            elif verified == 0:
                status = "unverified"
            elif row.expired_evidence and row.expired_evidence > 0:
                status = "has_expired"
            elif completeness_pct >= 80:
                status = "complete"
            elif completeness_pct >= 50:
                status = "partial"
            else:
                status = "incomplete"
            
            completeness.append({
                "control_id": row.id,
                "control_name": row.name,
                "total_evidence": total,
                "verified_evidence": verified,
                "pending_evidence": row.pending_evidence or 0,
                "rejected_evidence": row.rejected_evidence or 0,
                "expired_evidence": row.expired_evidence or 0,
                "completeness_pct": round(completeness_pct, 2),
                "status": status,
                "earliest_expiry": row.earliest_expiry.isoformat() if row.earliest_expiry else None,
                "latest_expiry": row.latest_expiry.isoformat() if row.latest_expiry else None
            })
        
        avg_completeness = sum(c["completeness_pct"] for c in completeness) / len(completeness) if completeness else 0
        
        return {
            "overall_completeness_pct": round(avg_completeness, 2),
            "controls": completeness
        }
    
    def get_evidence_freshness(self, control_id: Optional[str] = None) -> Dict[str, Any]:
        """Calculate evidence freshness."""
        query = self.db.query(
            Control.id,
            Control.name,
            func.max(Evidence.collected_at).label('latest_collected'),
            func.min(Evidence.expiry_date).label('earliest_expiry'),
            func.count(Evidence.id).filter(Evidence.expiry_date < date.today()).label('expired_count'),
            func.count(Evidence.id).label('total_evidence')
        ).outerjoin(Evidence, Evidence.control_id == Control.id).filter(
            Control.status == 'active'
        )
        
        if control_id:
            query = query.filter(Control.id == control_id)
        
        results = query.group_by(Control.id, Control.name).all()
        
        freshness = []
        for row in results:
            latest = row.latest_collected
            total = row.total_evidence or 0
            
            if latest is None:
                status = "no_evidence"
                days_old = None
            else:
                days_old = (date.today() - latest.date()).days
                if days_old > 90:
                    status = "stale"
                elif days_old > 30:
                    status = "aging"
                else:
                    status = "fresh"
            
            freshness.append({
                "control_id": row.id,
                "control_name": row.name,
                "total_evidence": total,
                "latest_evidence_date": latest.isoformat() if latest else None,
                "days_since_latest": days_old,
                "earliest_expiry": row.earliest_expiry.isoformat() if row.earliest_expiry else None,
                "expired_count": row.expired_count or 0,
                "freshness_status": status
            })
        
        status_counts = {}
        for f in freshness:
            status_counts[f["freshness_status"]] = status_counts.get(f["freshness_status"], 0) + 1
        
        return {
            "summary": status_counts,
            "controls": freshness
        }
    
    # =====================================================
    # OBLIGATION COVERAGE
    # =====================================================
    
    def get_obligation_coverage(self, regulation_id: Optional[str] = None) -> Dict[str, Any]:
        """Calculate obligation coverage through policy -> process -> control -> evidence chain."""
        query = self.db.query(Obligation)
        if regulation_id:
            query = query.filter(Obligation.regulation_id == regulation_id)
        
        obligations = query.all()
        
        coverage = []
        for obl in obligations:
            # Trace: Obligation -> Policy -> Process -> Control -> Evidence
            policies = self._get_linked_policies(obl.id)
            policy_count = len(policies)
            
            processes = []
            for p in policies:
                processes.extend(self._get_linked_processes(p.id))
            process_count = len(set(p.id for p in processes))
            
            controls = []
            for pr in processes:
                controls.extend(self._get_active_controls(pr.id))
            control_count = len(controls)
            
            verified_evidence = 0
            for c in controls:
                verified_evidence += self.db.query(func.count(Evidence.id)).filter(
                    Evidence.control_id == c.id,
                    Evidence.status == 'verified'
                ).scalar() or 0
            
            # Coverage determination
            if control_count == 0:
                coverage_status = "no_controls"
            elif verified_evidence == 0:
                coverage_status = "no_evidence"
            elif verified_evidence < control_count:
                coverage_status = "partial_evidence"
            else:
                coverage_status = "covered"
            
            # Risk-adjusted coverage
            risk_weight = {"low": 1, "medium": 2, "high": 3, "critical": 4}.get(obl.risk_level, 2)
            
            coverage.append({
                "obligation_id": obl.id,
                "regulation_id": obl.regulation_id,
                "obligation_text": obl.obligation_text[:200] + "..." if len(obl.obligation_text) > 200 else obl.obligation_text,
                "risk_level": obl.risk_level,
                "category": obl.category,
                "policy_count": policy_count,
                "process_count": process_count,
                "control_count": control_count,
                "verified_evidence_count": verified_evidence,
                "coverage_status": coverage_status,
                "risk_weight": risk_weight
            })
        
        # Summary
        status_counts = {}
        for c in coverage:
            status_counts[c["coverage_status"]] = status_counts.get(c["coverage_status"], 0) + 1
        
        covered = status_counts.get("covered", 0)
        total = len(coverage)
        coverage_pct = (covered / total * 100) if total > 0 else 0
        
        return {
            "total_obligations": total,
            "covered_obligations": covered,
            "coverage_percentage": round(coverage_pct, 2),
            "status_breakdown": status_counts,
            "obligations": coverage
        }
    
    def _get_linked_policies(self, obligation_id: str) -> List[Policy]:
        """Get policies linked to obligation via accepted mappings."""
        return self.db.query(Policy).join(
            MappingReview,
            and_(
                MappingReview.target_entity_type == 'policy',
                MappingReview.target_entity_id == Policy.id,
                MappingReview.source_entity_type == 'obligation',
                MappingReview.source_entity_id == obligation_id,
                MappingReview.status == 'accepted',
                MappingReview.mapping_type == 'obligation_to_policy'
            )
        ).all()

    def _get_linked_processes(self, policy_id: str) -> List[Process]:
        """Get processes linked to policy via accepted mappings."""
        return self.db.query(Process).join(
            MappingReview,
            and_(
                MappingReview.target_entity_type == 'process',
                MappingReview.target_entity_id == Process.id,
                MappingReview.source_entity_type == 'policy',
                MappingReview.source_entity_id == policy_id,
                MappingReview.status == 'accepted',
                MappingReview.mapping_type == 'policy_to_process'
            )
        ).all()
    
    def _get_active_controls(self, process_id: str) -> List[Control]:
        """Get active controls for a process."""
        return self.db.query(Control).filter(
            Control.process_id == process_id,
            Control.status == 'active'
        ).all()
    
    def get_control_coverage(self) -> Dict[str, Any]:
        """Calculate control coverage metrics."""
        controls = self.db.query(Control).filter(Control.status == 'active').all()
        
        with_evidence = 0
        with_verified_evidence = 0
        without_evidence = 0
        with_exceptions = 0
        
        for c in controls:
            ev_count = self.db.query(func.count(Evidence.id)).filter(
                Evidence.control_id == c.id
            ).scalar() or 0
            
            verified_count = self.db.query(func.count(Evidence.id)).filter(
                Evidence.control_id == c.id,
                Evidence.status == 'verified'
            ).scalar() or 0
            
            exc_count = self.db.query(func.count(Exc.id)).filter(
                Exc.control_id == c.id,
                Exc.status.in_(['open', 'investigating'])
            ).scalar() or 0
            
            if ev_count == 0:
                without_evidence += 1
            else:
                with_evidence += 1
                if verified_count > 0:
                    with_verified_evidence += 1
            
            if exc_count > 0:
                with_exceptions += 1
        
        total = len(controls)
        return {
            "total_controls": total,
            "controls_with_evidence": with_evidence,
            "controls_with_verified_evidence": with_verified_evidence,
            "controls_without_evidence": without_evidence,
            "controls_with_open_exceptions": with_exceptions,
            "evidence_coverage_pct": round(with_evidence / total * 100, 2) if total > 0 else 0,
            "verified_evidence_coverage_pct": round(with_verified_evidence / total * 100, 2) if total > 0 else 0
        }
    
    # =====================================================
    # RISK EXPOSURE
    # =====================================================
    
    def get_risk_exposure(self) -> Dict[str, Any]:
        """Calculate organizational risk exposure."""
        assessments = self.db.query(RiskAssessment).all()
        
        risk_levels = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        
        total_inherent = 0
        total_residual = 0
        by_category = {}
        by_entity = {}
        high_residual = 0
        
        for ra in assessments:
            inherent_score = risk_levels.get(ra.inherent_risk, 2)
            residual_score = risk_levels.get(ra.residual_risk, 2)
            
            total_inherent += inherent_score
            total_residual += residual_score
            
            if ra.residual_risk in ["high", "critical"]:
                high_residual += 1
            
            cat = ra.risk_category or "uncategorized"
            if cat not in by_category:
                by_category[cat] = {"inherent": 0, "residual": 0, "count": 0}
            by_category[cat]["inherent"] += inherent_score
            by_category[cat]["residual"] += residual_score
            by_category[cat]["count"] += 1
            
            entity_key = f"{ra.entity_type}:{ra.entity_id}"
            if entity_key not in by_entity:
                by_entity[entity_key] = {"inherent": 0, "residual": 0, "count": 0}
            by_entity[entity_key]["inherent"] += inherent_score
            by_entity[entity_key]["residual"] += residual_score
            by_entity[entity_key]["count"] += 1
        
        count = len(assessments)
        avg_inherent = total_inherent / count if count > 0 else 0
        avg_residual = total_residual / count if count > 0 else 0
        risk_reduction = ((avg_inherent - avg_residual) / avg_inherent * 100) if avg_inherent > 0 else 0
        
        return {
            "total_assessments": count,
            "avg_inherent_risk": round(avg_inherent, 2),
            "avg_residual_risk": round(avg_residual, 2),
            "risk_reduction_pct": round(risk_reduction, 2),
            "high_residual_count": high_residual,
            "by_category": {k: {**v, "avg_inherent": round(v["inherent"]/v["count"], 2), "avg_residual": round(v["residual"]/v["count"], 2)} for k, v in by_category.items()},
            "top_risk_entities": sorted(
                [{"entity": k, **v, "avg_residual": round(v["residual"]/v["count"], 2)} for k, v in by_entity.items()],
                key=lambda x: x["avg_residual"], reverse=True
            )[:10]
        }
    
    # =====================================================
    # GAP ANALYSIS
    # =====================================================
    
    def get_unresolved_gaps(self) -> Dict[str, Any]:
        """Identify unresolved gaps in the control framework."""
        gaps = []
        
        # 1. Obligations without controls
        coverage = self.get_obligation_coverage()
        for obl in coverage["obligations"]:
            if obl["coverage_status"] in ["no_controls", "no_evidence"]:
                gaps.append({
                    "gap_type": "obligation_coverage",
                    "entity_id": obl["obligation_id"],
                    "entity_name": obl["obligation_text"][:100],
                    "severity": "high" if obl["risk_level"] in ["high", "critical"] else "medium",
                    "description": f"Obligation has {obl['coverage_status'].replace('_', ' ')}",
                    "risk_level": obl["risk_level"]
                })
        
        # 2. Controls without evidence
        control_cov = self.get_control_coverage()
        for c in self.db.query(Control).filter(Control.status == 'active').all():
            ev_count = self.db.query(func.count(Evidence.id)).filter(Evidence.control_id == c.id).scalar() or 0
            if ev_count == 0:
                gaps.append({
                    "gap_type": "missing_evidence",
                    "entity_id": c.id,
                    "entity_name": c.name,
                    "severity": "high" if c.operating_effectiveness == "ineffective" else "medium",
                    "description": "Control has no supporting evidence",
                    "control_type": c.control_type
                })
        
        # 3. Stale evidence
        freshness = self.get_evidence_freshness()
        for c in freshness["controls"]:
            if c["freshness_status"] in ["stale", "no_evidence"]:
                gaps.append({
                    "gap_type": "stale_evidence",
                    "entity_id": c["control_id"],
                    "entity_name": c["control_name"],
                    "severity": "high" if c["freshness_status"] == "no_evidence" else "medium",
                    "description": f"Evidence is {c['freshness_status']}",
                    "days_old": c["days_since_latest"]
                })
        
        # 4. Overdue controls
        overdue = self.db.query(Control).filter(
            Control.status == 'active',
            Control.next_test_date < date.today()
        ).all()
        for c in overdue:
            days_overdue = (date.today() - c.next_test_date).days
            gaps.append({
                "gap_type": "overdue_testing",
                "entity_id": c.id,
                "entity_name": c.name,
                "severity": "high" if days_overdue > 90 else "medium",
                "description": f"Control testing overdue by {days_overdue} days",
                "days_overdue": days_overdue
            })
        
        # 5. Open exceptions
        open_exc = self.db.query(Exc).filter(
            Exc.status.in_(['open', 'investigating'])
        ).all()
        for e in open_exc:
            days_open = (date.today() - e.detected_date).days
            gaps.append({
                "gap_type": "open_exception",
                "entity_id": e.id,
                "entity_name": e.title,
                "severity": e.severity,
                "description": f"Exception open for {days_open} days",
                "days_open": days_open
            })
        
        # Summary
        by_type = {}
        by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for g in gaps:
            by_type[g["gap_type"]] = by_type.get(g["gap_type"], 0) + 1
            by_severity[g["severity"]] = by_severity.get(g["severity"], 0) + 1
        
        return {
            "total_gaps": len(gaps),
            "by_type": by_type,
            "by_severity": by_severity,
            "gaps": gaps
        }
    
    # =====================================================
    # TREND METRICS
    # =====================================================
    
    def get_trend_metrics(self, days: int = 90) -> Dict[str, Any]:
        """Calculate trend metrics over time."""
        cutoff = date.today() - timedelta(days=days)
        
        # Exception trend
        exc_trend = self.db.execute(text("""
            SELECT DATE_TRUNC('week', detected_date) as week,
                   COUNT(*) as count,
                   COUNT(*) FILTER (WHERE severity IN ('high', 'critical')) as high_severity
            FROM exceptions
            WHERE detected_date >= :cutoff
            GROUP BY DATE_TRUNC('week', detected_date)
            ORDER BY week
        """), {"cutoff": cutoff}).fetchall()
        
        # Evidence submission trend
        ev_trend = self.db.execute(text("""
            SELECT DATE_TRUNC('week', collected_at) as week,
                   COUNT(*) as submitted,
                   COUNT(*) FILTER (WHERE status = 'verified') as verified
            FROM evidence
            WHERE collected_at >= :cutoff
            GROUP BY DATE_TRUNC('week', collected_at)
            ORDER BY week
        """), {"cutoff": cutoff}).fetchall()
        
        # Control testing trend
        ctl_trend = self.db.execute(text("""
            SELECT DATE_TRUNC('week', last_tested_date) as week,
                   COUNT(*) as tested
            FROM controls
            WHERE last_tested_date >= :cutoff
            GROUP BY DATE_TRUNC('week', last_tested_date)
            ORDER BY week
        """), {"cutoff": cutoff}).fetchall()
        
        return {
            "period_days": days,
            "exception_trend": [
                {"week": r.week.isoformat(), "count": r.count, "high_severity": r.high_severity}
                for r in exc_trend
            ],
            "evidence_trend": [
                {"week": r.week.isoformat(), "submitted": r.submitted, "verified": r.verified}
                for r in ev_trend
            ],
            "control_testing_trend": [
                {"week": r.week.isoformat(), "tested": r.tested}
                for r in ctl_trend
            ]
        }
    
    # =====================================================
    # DASHBOARD SUMMARY
    # =====================================================
    
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get comprehensive dashboard metrics."""
        total_obligations = self.db.query(func.count(Obligation.id)).filter(Obligation.status == 'active').scalar()
        coverage = self.get_obligation_coverage()
        control_cov = self.get_control_coverage()
        exception_rate = self.get_exception_rate(days=30)
        evidence_comp = self.get_evidence_completeness()
        risk = self.get_risk_exposure()
        gaps = self.get_unresolved_gaps()
        
        return {
            "total_obligations": total_obligations,
            "mapped_obligations": sum(
                1 for obl in self.db.query(Obligation).filter(Obligation.status == 'active').all()
                if self._get_linked_policies(obl.id)
            ),
            "coverage_percentage": coverage["coverage_percentage"],
            "control_gaps": control_cov["controls_without_evidence"],
            "evidence_gaps": sum(1 for c in evidence_comp["controls"] if c["status"] in ["no_evidence", "unverified", "incomplete"]),
            "open_exceptions": exception_rate["open_exceptions"],
            "risk_exposure": risk["avg_residual_risk"],
            "unresolved_gaps": gaps["total_gaps"],
            "critical_gaps": gaps["by_severity"].get("critical", 0),
            "high_gaps": gaps["by_severity"].get("high", 0)
        }


def calculate_control_effectiveness(db: Session, control_id: str) -> Dict[str, Any]:
    """Calculate detailed control effectiveness score."""
    analytics = AnalyticsEngine(db)
    
    # Get control
    control = db.query(Control).filter(Control.id == control_id).first()
    if not control:
        return {"error": "Control not found"}
    
    # Evidence metrics
    evidence = analytics.get_evidence_completeness(control_id)
    freshness = analytics.get_evidence_freshness(control_id)
    
    # Exception metrics
    exceptions = db.query(Exc).filter(Exc.control_id == control_id).all()
    open_exceptions = [e for e in exceptions if e.status in ['open', 'investigating']]
    
    # Execution rate
    execution = analytics.get_control_execution_rate(control_id)
    
    # Calculate composite score
    design_score = {"effective": 100, "partially_effective": 60, "ineffective": 20}.get(control.design_effectiveness, 50)
    operating_score = {"effective": 100, "partially_effective": 60, "ineffective": 20}.get(control.operating_effectiveness, 50)
    evidence_score = evidence["controls"][0]["completeness_pct"] if evidence["controls"] else 0
    freshness_score = 100 if freshness["controls"][0]["freshness_status"] == "fresh" else (50 if freshness["controls"][0]["freshness_status"] == "aging" else 0)
    exception_penalty = min(len(open_exceptions) * 10, 50)
    execution_score = execution["controls"][0]["execution_rate_pct"] if execution["controls"] else 0
    
    composite = round((
        design_score * 0.2 +
        operating_score * 0.2 +
        evidence_score * 0.2 +
        freshness_score * 0.15 +
        execution_score * 0.15 +
        (100 - exception_penalty) * 0.1
    ), 2)
    
    rating = "effective" if composite >= 80 else ("partially_effective" if composite >= 60 else "ineffective")
    
    return {
        "control_id": control_id,
        "control_name": control.name,
        "composite_score": composite,
        "rating": rating,
        "components": {
            "design_effectiveness": design_score,
            "operating_effectiveness": operating_score,
            "evidence_completeness": evidence_score,
            "evidence_freshness": freshness_score,
            "execution_rate": execution_score,
            "exception_penalty": exception_penalty
        },
        "details": {
            "evidence": evidence["controls"][0] if evidence["controls"] else {},
            "freshness": freshness["controls"][0] if freshness["controls"] else {},
            "open_exceptions": len(open_exceptions),
            "execution": execution["controls"][0] if execution["controls"] else {}
        }
    }


def build_traceability_chain(db: Session, obligation_id: str) -> Dict[str, Any]:
    """Build full traceability chain from regulation to exception."""
    analytics = AnalyticsEngine(db)
    
    obligation = db.query(Obligation).filter(Obligation.id == obligation_id).first()
    if not obligation:
        return {"error": "Obligation not found"}
    
    regulation = db.query(Regulation).filter(Regulation.id == obligation.regulation_id).first()
    
    # Get linked policies
    policies = analytics._get_linked_policies(obligation_id)
    
    chain = {
        "regulation": {
            "id": regulation.id if regulation else None,
            "title": regulation.title if regulation else None,
            "short_name": regulation.short_name if regulation else None
        },
        "obligation": {
            "id": obligation.id,
            "text": obligation.obligation_text,
            "risk_level": obligation.risk_level,
            "category": obligation.category
        },
        "policies": [],
        "processes": [],
        "controls": [],
        "evidence": [],
        "exceptions": []
    }
    
    for policy in policies:
        p_data = {
            "id": policy.id,
            "title": policy.title,
            "status": policy.status,
            "owner": policy.owner_department
        }
        chain["policies"].append(p_data)
        
        # Get processes for this policy
        processes = analytics._get_linked_processes(policy.id)
        for process in processes:
            pr_data = {
                "id": process.id,
                "name": process.name,
                "department": process.department,
                "risk_rating": process.risk_rating
            }
            chain["processes"].append(pr_data)
            
            # Get controls for this process
            controls = analytics._get_active_controls(process.id)
            for control in controls:
                c_data = {
                    "id": control.id,
                    "name": control.name,
                    "type": control.control_type,
                    "frequency": control.frequency,
                    "design_effectiveness": control.design_effectiveness,
                    "operating_effectiveness": control.operating_effectiveness,
                    "process_id": process.id
                }
                chain["controls"].append(c_data)
                
                # Get evidence for this control
                evidence_list = db.query(Evidence).filter(Evidence.control_id == control.id).all()
                for ev in evidence_list:
                    e_data = {
                        "id": ev.id,
                        "type": ev.evidence_type,
                        "title": ev.title,
                        "status": ev.status,
                        "collected_at": ev.collected_at.isoformat() if ev.collected_at else None,
                        "expiry_date": ev.expiry_date.isoformat() if ev.expiry_date else None,
                        "control_id": control.id
                    }
                    chain["evidence"].append(e_data)
                
                # Get exceptions for this control
                exc_list = db.query(Exc).filter(Exc.control_id == control.id).all()
                for exc in exc_list:
                    ex_data = {
                        "id": exc.id,
                        "number": exc.exception_number,
                        "type": exc.exception_type,
                        "severity": exc.severity,
                        "status": exc.status,
                        "detected_date": exc.detected_date.isoformat() if exc.detected_date else None,
                        "control_id": control.id
                    }
                    chain["exceptions"].append(ex_data)
    
    return chain
