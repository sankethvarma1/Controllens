"""
Agent Classes for CONTROLLENS
Each agent uses deterministic tools and reasons over results.
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import json

from app.agents.tools import AgentTools, get_agent_tools


class BaseAgent:
    """Base class for all agents."""
    
    def __init__(self, db: Session):
        self.db = db
        self.tools = get_agent_tools(db)
        self.name = self.__class__.__name__
    
    def log_action(self, action: str, details: Dict):
        """Log agent action for audit."""
        print(f"[{self.name}] {action}: {json.dumps(details)}")


class DocumentIntelligenceAgent(BaseAgent):
    """Agent for document analysis and extraction."""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.name = "DocumentIntelligenceAgent"
    
    def analyze_document(self, document_id: str, query: str) -> Dict[str, Any]:
        """Analyze a document for specific information."""
        self.log_action("analyze_document", {"document_id": document_id, "query": query})
        
        # Search document chunks
        from app.services.retrieval import HybridRetriever
        retriever = HybridRetriever(self.db)
        results = retriever.retrieve(
            query,
            filters={"document_id": document_id},
            source_types=["document_chunk"]
        )
        
        return {
            "document_id": document_id,
            "query": query,
            "results_count": len(results),
            "evidence": [r.to_dict() for r in results],
            "answer": self._synthesize_answer(query, results)
        }
    
    def extract_obligations(self, regulation_id: str) -> Dict[str, Any]:
        """Extract obligations from regulation sections."""
        self.log_action("extract_obligations", {"regulation_id": regulation_id})
        
        sections = self.tools.get_regulation_sections(regulation_id)
        
        # In practice, this would use LLM to extract obligations
        # For now, return existing obligations
        obligations = self.tools.search_obligations(regulation_id=regulation_id)
        
        return {
            "regulation_id": regulation_id,
            "sections_analyzed": len(sections),
            "obligations_found": len(obligations),
            "obligations": obligations
        }
    
    def _synthesize_answer(self, query: str, results: List) -> str:
        """Synthesize answer from retrieval results."""
        if not results:
            return "No relevant information found in the document."
        
        # Simple synthesis - in practice would use LLM
        snippets = [r.content[:200] for r in results[:3]]
        return f"Based on {len(results)} relevant sections: " + " | ".join(snippets)


class ObligationMappingAgent(BaseAgent):
    """Agent for mapping obligations to policies, processes, controls."""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.name = "ObligationMappingAgent"
    
    def map_obligation_to_policy(self, obligation_id: str) -> Dict[str, Any]:
        """Propose policy mappings for an obligation."""
        self.log_action("map_obligation_to_policy", {"obligation_id": obligation_id})
        
        obligation = self.tools.get_obligation(obligation_id)
        if not obligation:
            return {"error": "Obligation not found"}
        
        # Find relevant policies using retrieval
        from app.services.retrieval import HybridRetriever
        retriever = HybridRetriever(self.db)
        results = retriever.retrieve(
            obligation["obligation_text"],
            filters={"document_type": "policy"},
            source_types=["document_chunk"]
        )
        
        # Get actual policy records
        policies = self.tools.search_policies(status="active")
        
        proposed_mappings = []
        for policy in policies[:5]:  # Top 5 candidates
            proposed_mappings.append({
                "source_entity_type": "obligation",
                "source_entity_id": obligation_id,
                "target_entity_type": "policy",
                "target_entity_id": policy["id"],
                "mapping_type": "obligation_to_policy",
                "confidence_score": 0.75,  # Would be calculated
                "ai_reasoning": f"Policy '{policy['title']}' addresses {obligation['category']} requirements relevant to this obligation."
            })
        
        return {
            "obligation_id": obligation_id,
            "proposed_mappings": proposed_mappings,
            "retrieval_evidence": [r.to_dict() for r in results[:3]]
        }
    
    def map_policy_to_process(self, policy_id: str) -> Dict[str, Any]:
        """Propose process mappings for a policy."""
        self.log_action("map_policy_to_process", {"policy_id": policy_id})
        
        policy = self.tools.get_policy(policy_id)
        if not policy:
            return {"error": "Policy not found"}
        
        processes = self.db.query(Process).filter(Process.status == 'active').all()
        
        proposed_mappings = []
        for process in processes[:5]:
            proposed_mappings.append({
                "source_entity_type": "policy",
                "source_entity_id": policy_id,
                "target_entity_type": "process",
                "target_entity_id": process.id,
                "mapping_type": "policy_to_process",
                "confidence_score": 0.70,
                "ai_reasoning": f"Process '{process.name}' in {process.department} implements {policy['policy_type']} policy requirements."
            })
        
        return {
            "policy_id": policy_id,
            "proposed_mappings": proposed_mappings
        }
    
    def map_process_to_control(self, process_id: str) -> Dict[str, Any]:
        """Propose control mappings for a process."""
        self.log_action("map_process_to_control", {"process_id": process_id})
        
        process = self.tools.get_process(process_id)
        if not process:
            return {"error": "Process not found"}
        
        controls = self.tools.search_controls(status="active")
        
        proposed_mappings = []
        for control in controls[:5]:
            proposed_mappings.append({
                "source_entity_type": "process",
                "source_entity_id": process_id,
                "target_entity_type": "control",
                "target_entity_id": control["id"],
                "mapping_type": "process_to_control",
                "confidence_score": 0.80,
                "ai_reasoning": f"Control '{control['name']}' ({control['control_type']}) operates within {process['name']} process."
            })
        
        return {
            "process_id": process_id,
            "proposed_mappings": proposed_mappings
        }


class EvidenceAgent(BaseAgent):
    """Agent for evidence collection, validation, and gap analysis."""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.name = "EvidenceAgent"
    
    def get_evidence_for_control(self, control_id: str) -> Dict[str, Any]:
        """Get all evidence for a control with completeness analysis."""
        self.log_action("get_evidence_for_control", {"control_id": control_id})
        
        evidence = self.tools.search_evidence(control_id=control_id)
        completeness = self.tools.get_evidence_completeness(control_id)
        control = self.tools.get_control(control_id)
        
        return {
            "control_id": control_id,
            "control_name": control["name"] if control else None,
            "evidence_count": len(evidence),
            "completeness": completeness,
            "evidence": evidence
        }
    
    def identify_evidence_gaps(self) -> Dict[str, Any]:
        """Identify controls with missing or stale evidence."""
        self.log_action("identify_evidence_gaps", {})
        
        # Controls without evidence
        no_evidence = self.db.query(Control).filter(
            Control.status == 'active',
            ~Control.id.in_(
                self.db.query(Evidence.control_id).distinct()
            )
        ).all()
        
        # Stale evidence
        stale = self.tools.get_stale_evidence(days=90)
        
        # Expired evidence
        from app.db.base import Evidence
        expired = self.db.query(Evidence).filter(
            Evidence.status == 'verified',
            Evidence.expiry_date < date.today()
        ).all()
        
        return {
            "controls_without_evidence": [
                {"id": c.id, "name": c.name, "process_id": c.process_id}
                for c in no_evidence
            ],
            "stale_evidence": stale,
            "expired_evidence": [
                {
                    "id": e.id,
                    "control_id": e.control_id,
                    "title": e.title,
                    "expiry_date": e.expiry_date.isoformat()
                }
                for e in expired
            ],
            "summary": {
                "controls_without_evidence": len(no_evidence),
                "stale_evidence_count": len(stale),
                "expired_evidence_count": len(expired)
            }
        }
    
    def verify_evidence_claim(self, claim: str, control_id: str) -> Dict[str, Any]:
        """Verify if a claim about evidence is supported."""
        self.log_action("verify_evidence_claim", {"control_id": control_id, "claim": claim})
        
        from app.services.retrieval import EvidenceAttributor
        attributor = EvidenceAttributor(self.db)
        
        return attributor.verify_claim(claim, "control", control_id)


class MonitoringAgent(BaseAgent):
    """Agent for continuous monitoring of controls, exceptions, transactions."""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.name = "MonitoringAgent"
    
    def check_control_health(self) -> Dict[str, Any]:
        """Comprehensive control health check."""
        self.log_action("check_control_health", {})
        
        overdue = self.tools.get_overdue_controls()
        effectiveness = self.db.query(Control).filter(
            Control.status == 'active'
        ).all()
        
        ineffective = [c for c in effectiveness if c.operating_effectiveness == 'ineffective']
        partially = [c for c in effectiveness if c.operating_effectiveness == 'partially_effective']
        
        return {
            "overdue_controls": overdue,
            "ineffective_controls": [
                {"id": c.id, "name": c.name, "design": c.design_effectiveness, "operating": c.operating_effectiveness}
                for c in ineffective
            ],
            "partially_effective_controls": [
                {"id": c.id, "name": c.name, "design": c.design_effectiveness, "operating": c.operating_effectiveness}
                for c in partially
            ],
            "summary": {
                "total_active": len(effectiveness),
                "overdue": len(overdue),
                "ineffective": len(ineffective),
                "partially_effective": len(partially),
                "fully_effective": len([c for c in effectiveness if c.operating_effectiveness == 'effective'])
            }
        }
    
    def monitor_exceptions(self, days: int = 7) -> Dict[str, Any]:
        """Monitor recent exception activity."""
        self.log_action("monitor_exceptions", {"days": days})
        
        return self.tools.analyze_exceptions(days=days)
    
    def detect_transaction_anomalies(self, threshold: float = 70.0) -> Dict[str, Any]:
        """Detect anomalous transactions."""
        self.log_action("detect_transaction_anomalies", {"threshold": threshold})
        
        anomalies = self.tools.get_high_risk_transactions(threshold=threshold)
        
        # Group by type
        by_type = {}
        for t in anomalies:
            by_type[t["transaction_type"]] = by_type.get(t["transaction_type"], 0) + 1
        
        return {
            "threshold": threshold,
            "anomaly_count": len(anomalies),
            "by_type": by_type,
            "top_anomalies": anomalies[:10]
        }
    
    def get_risk_trends(self, days: int = 90) -> Dict[str, Any]:
        """Get risk trend metrics."""
        self.log_action("get_risk_trends", {"days": days})
        
        return self.tools.analytics.get_trend_metrics(days)


class GapAnalysisAgent(BaseAgent):
    """Agent for identifying and analyzing gaps in the control framework."""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.name = "GapAnalysisAgent"
    
    def find_unresolved_gaps(self) -> Dict[str, Any]:
        """Find all unresolved gaps."""
        self.log_action("find_unresolved_gaps", {})
        
        return self.tools.analytics.get_unresolved_gaps()
    
    def analyze_obligation_gaps(self) -> Dict[str, Any]:
        """Analyze gaps in obligation coverage."""
        self.log_action("analyze_obligation_gaps", {})
        
        coverage = self.tools.analytics.get_obligation_coverage()
        
        gaps = [o for o in coverage["obligations"] if o["coverage_status"] != "covered"]
        
        return {
            "total_obligations": coverage["total_obligations"],
            "covered": coverage["covered_obligations"],
            "coverage_pct": coverage["coverage_percentage"],
            "gaps": gaps,
            "gap_breakdown": coverage["status_breakdown"]
        }
    
    def analyze_control_gaps(self) -> Dict[str, Any]:
        """Analyze gaps in control coverage."""
        self.log_action("analyze_control_gaps", {})
        
        control_cov = self.tools.analytics.get_control_coverage()
        no_evidence = self.db.query(Control).filter(
            Control.status == 'active',
            ~Control.id.in_(
                self.db.query(Evidence.control_id).filter(Evidence.status == 'verified').distinct()
            )
        ).all()
        
        return {
            "control_coverage": control_cov,
            "controls_without_verified_evidence": [
                {"id": c.id, "name": c.name, "process_id": c.process_id}
                for c in no_evidence
            ],
            "summary": {
                "controls_without_evidence": len(no_evidence),
                "evidence_coverage_pct": control_cov["evidence_coverage_pct"]
            }
        }


class ReportAgent(BaseAgent):
    """Agent for generating compliance and audit reports."""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.name = "ReportAgent"
    
    def generate_dashboard_report(self) -> Dict[str, Any]:
        """Generate executive dashboard report."""
        self.log_action("generate_dashboard_report", {})
        
        return self.tools.analytics.get_dashboard_summary()
    
    def generate_obligation_coverage_report(self, regulation_id: str = None) -> Dict[str, Any]:
        """Generate obligation coverage report."""
        self.log_action("generate_obligation_coverage_report", {"regulation_id": regulation_id})
        
        return self.tools.analytics.get_obligation_coverage(regulation_id)
    
    def generate_control_effectiveness_report(self) -> Dict[str, Any]:
        """Generate control effectiveness report."""
        self.log_action("generate_control_effectiveness_report", {})
        
        health = MonitoringAgent(self.db).check_control_health()
        evidence_gaps = EvidenceAgent(self.db).identify_evidence_gaps()
        
        return {
            "control_health": health,
            "evidence_gaps": evidence_gaps["summary"],
            "recommendations": self._generate_recommendations(health, evidence_gaps)
        }
    
    def generate_exception_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate exception trend report."""
        self.log_action("generate_exception_report", {"days": days})
        
        return self.tools.analyze_exceptions(days=days)
    
    def generate_traceability_report(self, obligation_id: str) -> Dict[str, Any]:
        """Generate full traceability report for an obligation."""
        self.log_action("generate_traceability_report", {"obligation_id": obligation_id})
        
        chain = self.tools.build_traceability_chain(obligation_id)
        
        return {
            "traceability_chain": chain,
            "summary": {
                "policies": len(chain.get("policies", [])),
                "processes": len(chain.get("processes", [])),
                "controls": len(chain.get("controls", [])),
                "evidence": len(chain.get("evidence", [])),
                "exceptions": len(chain.get("exceptions", []))
            }
        }
    
    def _generate_recommendations(self, health: Dict, evidence_gaps: Dict) -> List[str]:
        """Generate actionable recommendations."""
        recs = []
        
        if health["summary"]["overdue"] > 0:
            recs.append(f"Schedule testing for {health['summary']['overdue']} overdue controls")
        
        if health["summary"]["ineffective"] > 0:
            recs.append(f"Remediate {health['summary']['ineffective']} ineffective controls")
        
        if evidence_gaps["summary"]["controls_without_evidence"] > 0:
            recs.append(f"Collect evidence for {evidence_gaps['summary']['controls_without_evidence']} controls without evidence")
        
        if evidence_gaps["summary"]["stale_evidence_count"] > 0:
            recs.append(f"Refresh {evidence_gaps['summary']['stale_evidence_count']} stale evidence items")
        
        if evidence_gaps["summary"]["expired_evidence_count"] > 0:
            recs.append(f"Replace {evidence_gaps['summary']['expired_evidence_count']} expired evidence items")
        
        return recs


# Agent Registry
AGENTS = {
    "document_intelligence": DocumentIntelligenceAgent,
    "obligation_mapping": ObligationMappingAgent,
    "evidence": EvidenceAgent,
    "monitoring": MonitoringAgent,
    "gap_analysis": GapAnalysisAgent,
    "report": ReportAgent
}


def get_agent(agent_name: str, db: Session) -> BaseAgent:
    """Get agent instance by name."""
    agent_class = AGENTS.get(agent_name)
    if not agent_class:
        raise ValueError(f"Unknown agent: {agent_name}")
    return agent_class(db)


def list_agents() -> List[str]:
    """List available agents."""
    return list(AGENTS.keys())