# Backend Tests
import pytest
from datetime import date, datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base, init_db, drop_db
from app.db.base import (
    Regulation, RegulatorySection, Obligation, Policy, Process,
    Control, Evidence, Transaction, Exception as Exc,
    RiskAssessment, MappingReview, Document, DocumentChunk
)
from app.services.analytics import AnalyticsEngine
from app.services.retrieval import HybridRetriever, EvidenceAttributor
from app.agents.tools import AgentTools

# Test database
TEST_DATABASE_URL = "postgresql://controllens:controllens@localhost:5432/controllens_test"

@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    yield session
    session.close()
    transaction.rollback()
    connection.close()

class TestDatabase:
    def test_create_regulation(self, db_session):
        reg = Regulation(
            id="TEST_REG_001",
            title="Test Regulation",
            short_name="TEST",
            jurisdiction="Testland",
            regulator="Test Authority",
            status="active"
        )
        db_session.add(reg)
        db_session.commit()
        
        found = db_session.query(Regulation).filter(Regulation.id == "TEST_REG_001").first()
        assert found is not None
        assert found.title == "Test Regulation"

    def test_create_obligation(self, db_session):
        reg = Regulation(id="TEST_REG_002", title="Test Reg 2", status="active")
        db_session.add(reg)
        db_session.flush()
        
        obl = Obligation(
            id="TEST_OBL_001",
            regulation_id=reg.id,
            obligation_text="The organization shall test things.",
            risk_level="high",
            category="testing"
        )
        db_session.add(obl)
        db_session.commit()
        
        found = db_session.query(Obligation).filter(Obligation.id == "TEST_OBL_001").first()
        assert found is not None
        assert found.risk_level == "high"

    def test_create_control_with_evidence(self, db_session):
        proc = Process(id="TEST_PROC_001", name="Test Process", status="active")
        db_session.add(proc)
        db_session.flush()
        
        ctl = Control(
            id="TEST_CTL_001",
            name="Test Control",
            control_type="preventive",
            control_category="IT",
            frequency="monthly",
            automation_level="manual",
            status="active",
            process_id=proc.id
        )
        db_session.add(ctl)
        db_session.flush()
        
        ev = Evidence(
            id="TEST_EVD_001",
            control_id=ctl.id,
            evidence_type="document",
            title="Test Evidence",
            status="verified",
            collected_at="2024-01-15T10:00:00Z"
        )
        db_session.add(ev)
        db_session.commit()
        
        found_ev = db_session.query(Evidence).filter(Evidence.control_id == ctl.id).first()
        assert found_ev is not None
        assert found_ev.status == "verified"

class TestAnalytics:
    def test_obligation_coverage_calculation(self, db_session):
        # Setup: Regulation -> Obligation -> Policy -> Process -> Control -> Evidence
        reg = Regulation(id="REG_TEST", title="Test Regulation", status="active")
        db_session.add(reg)
        
        obl = Obligation(
            id="OBL_TEST_001", regulation_id=reg.id,
            obligation_text="Test obligation", risk_level="high", category="test"
        )
        db_session.add(obl)
        
        pol = Policy(id="POL_TEST_001", title="Test Policy", status="active")
        db_session.add(pol)
        
        proc = Process(id="PROC_TEST_001", name="Test Process", status="active")
        db_session.add(proc)
        
        ctl = Control(
            id="CTL_TEST_001", name="Test Control", control_type="detective",
            control_category="IT", frequency="monthly", automation_level="manual",
            status="active", process_id=proc.id
        )
        db_session.add(ctl)
        
        ev = Evidence(
            id="EVD_TEST_001", control_id=ctl.id, evidence_type="document",
            title="Test Evidence", status="verified"
        )
        db_session.add(ev)
        
        # Create accepted mappings
        mr1 = MappingReview(
            id="MAP_001", mapping_type="obligation_to_policy",
            source_entity_type="obligation", source_entity_id=obl.id,
            target_entity_type="policy", target_entity_id=pol.id,
            status="accepted", confidence_score=0.9
        )
        mr2 = MappingReview(
            id="MAP_002", mapping_type="policy_to_process",
            source_entity_type="policy", source_entity_id=pol.id,
            target_entity_type="process", target_entity_id=proc.id,
            status="accepted", confidence_score=0.9
        )
        db_session.add_all([mr1, mr2])
        db_session.commit()
        
        analytics = AnalyticsEngine(db_session)
        coverage = analytics.get_obligation_coverage()
        
        obl_cov = next((o for o in coverage["obligations"] if o["obligation_id"] == obl.id), None)
        assert obl_cov is not None
        assert obl_cov["coverage_status"] == "covered"
        assert obl_cov["control_count"] == 1
        assert obl_cov["verified_evidence_count"] == 1

    def test_control_effectiveness_calculation(self, db_session):
        proc = Process(id="PROC_EFF_001", name="Eff Process", status="active")
        db_session.add(proc)
        
        ctl = Control(
            id="CTL_EFF_001", name="Effective Control", control_type="preventive",
            control_category="IT", frequency="quarterly", automation_level="fully_automated",
            status="active", design_effectiveness="effective",
            operating_effectiveness="effective", process_id=proc.id,
            next_test_date=date.today() + timedelta(days=90)
        )
        db_session.add(ctl)
        
        # Add verified evidence (fresh, within execution window)
        now = datetime.now(timezone.utc)
        for i in range(3):
            ev = Evidence(
                id=f"EVD_EFF_{i}", control_id=ctl.id, evidence_type="log",
                title=f"Evidence {i}", status="verified",
                collected_at=now
            )
            db_session.add(ev)
        
        db_session.commit()
        
        analytics = AnalyticsEngine(db_session)
        effectiveness = analytics.get_control_execution_rate(ctl.id)
        
        assert effectiveness["controls"][0]["execution_rate_pct"] >= 80
        assert effectiveness["controls"][0]["is_overdue"] == False

    def test_evidence_completeness(self, db_session):
        proc = Process(id="PROC_EVD_001", name="EVD Process", status="active")
        db_session.add(proc)
        
        # Control with evidence
        ctl1 = Control(id="CTL_EVD_001", name="Control With Evidence", control_type="detective",
                       control_category="IT", frequency="monthly", automation_level="manual",
                       status="active", process_id=proc.id)
        db_session.add(ctl1)
        
        ev1 = Evidence(id="EVD_001", control_id=ctl1.id, evidence_type="document",
                       title="Evidence 1", status="verified")
        ev2 = Evidence(id="EVD_002", control_id=ctl1.id, evidence_type="log",
                       title="Evidence 2", status="verified")
        db_session.add_all([ev1, ev2])
        
        # Control without evidence
        ctl2 = Control(id="CTL_EVD_002", name="Control No Evidence", control_type="detective",
                       control_category="IT", frequency="monthly", automation_level="manual",
                       status="active", process_id=proc.id)
        db_session.add(ctl2)
        
        db_session.commit()
        
        analytics = AnalyticsEngine(db_session)
        completeness = analytics.get_evidence_completeness()
        
        ctl1_comp = next(c for c in completeness["controls"] if c["control_id"] == ctl1.id)
        ctl2_comp = next(c for c in completeness["controls"] if c["control_id"] == ctl2.id)
        
        assert ctl1_comp["completeness_pct"] == 100.0
        assert ctl1_comp["status"] == "complete"
        assert ctl2_comp["status"] == "no_evidence"

    def test_unresolved_gaps_detection(self, db_session):
        # Obligation without controls
        reg = Regulation(id="REG_GAP", title="Gap Regulation", status="active")
        db_session.add(reg)
        
        obl = Obligation(id="OBL_GAP_001", regulation_id=reg.id,
                         obligation_text="Gap obligation", risk_level="high", category="gap")
        db_session.add(obl)
        
        # Control with no evidence
        proc = Process(id="PROC_GAP_001", name="Gap Process", status="active")
        db_session.add(proc)
        
        ctl = Control(id="CTL_GAP_001", name="Gap Control", control_type="detective",
                      control_category="IT", frequency="monthly", automation_level="manual",
                      status="active", process_id=proc.id)
        db_session.add(ctl)
        
        # Overdue control (deterministic: always 30 days overdue)
        ctl_overdue = Control(id="CTL_GAP_002", name="Overdue Control", control_type="preventive",
                              control_category="IT", frequency="monthly", automation_level="manual",
                              status="active", process_id=proc.id,
                              next_test_date=date.today() - timedelta(days=30))
        db_session.add(ctl_overdue)
        
        # Open exception (deterministic: detected 5 days ago)
        exc = Exc(id="EXC_GAP_001", exception_number="EXC-2024-001",
                  title="Gap Exception", exception_type="control_failure",
                  severity="high", status="open", detected_date=date.today() - timedelta(days=5),
                  control_id=ctl.id)
        db_session.add(exc)
        
        db_session.commit()
        
        analytics = AnalyticsEngine(db_session)
        gaps = analytics.get_unresolved_gaps()
        
        assert gaps["total_gaps"] >= 4  # obligation gap, control gap, overdue, exception
        gap_types = set(g["gap_type"] for g in gaps["gaps"])
        assert "obligation_coverage" in gap_types
        assert "missing_evidence" in gap_types
        assert "overdue_testing" in gap_types
        assert "open_exception" in gap_types

class TestRetrieval:
    def test_hybrid_retrieval_returns_metadata(self, db_session, monkeypatch):
        # Avoid Hugging Face downloads: deterministic stub query embedding.
        monkeypatch.setattr(
            HybridRetriever, "_get_query_embedding", lambda self, q: [0.1] * 384
        )
        # Create document with chunks
        doc = Document(
            id="DOC_TEST_001", title="Test Doc", source="TEST",
            document_type="policy", ingestion_status="completed", chunk_count=2
        )
        db_session.add(doc)
        db_session.flush()
        
        chunk1 = DocumentChunk(
            id="CHK_001", document_id=doc.id, chunk_index=0,
            content="This is a test policy about data protection.",
            section_title="Data Protection", page_number=1,
            embedding=[0.1] * 384, chunk_metadata={}
        )
        chunk2 = DocumentChunk(
            id="CHK_002", document_id=doc.id, chunk_index=1,
            content="Access control requirements for systems.",
            section_title="Access Control", page_number=2,
            embedding=[0.2] * 384, chunk_metadata={}
        )
        db_session.add_all([chunk1, chunk2])
        db_session.commit()
        
        retriever = HybridRetriever(db_session)
        results = retriever.retrieve(
            "data protection", limit=5, source_types=["document_chunk"]
        )
        
        assert len(results) > 0
        for r in results:
            assert r.document_id is not None
            assert r.document_title is not None
            assert r.section_title is not None
            assert r.page_number is not None
            assert r.source_type == "document_chunk"

    def test_evidence_retrieval_for_control(self, db_session, monkeypatch):
        monkeypatch.setattr(
            HybridRetriever, "_get_query_embedding", lambda self, q: [0.1] * 384
        )
        proc = Process(id="PROC_RET_001", name="Ret Process", status="active")
        db_session.add(proc)
        
        ctl = Control(id="CTL_RET_001", name="Ret Control", control_type="detective",
                      control_category="IT", frequency="monthly", automation_level="manual",
                      status="active", process_id=proc.id)
        db_session.add(ctl)
        
        ev = Evidence(
            id="EVD_RET_001", control_id=ctl.id, evidence_type="document",
            title="Control Evidence", description="Evidence for control",
            status="verified", source_system="GRC",
            embedding=[0.1] * 384
        )
        db_session.add(ev)
        db_session.commit()
        
        retriever = HybridRetriever(db_session)
        results = retriever.retrieve(
            "control evidence", 
            filters={"control_id": ctl.id},
            source_types=["evidence"]
        )
        
        assert len(results) == 1
        assert results[0].source_type == "evidence"
        assert results[0].control_id == ctl.id
        assert results[0].evidence_type == "document"

class TestTraceability:
    def test_build_traceability_chain(self, db_session):
        # Build full chain
        reg = Regulation(id="REG_CHAIN", title="Chain Regulation", short_name="CHAIN", status="active")
        db_session.add(reg)
        
        obl = Obligation(id="OBL_CHAIN_001", regulation_id=reg.id,
                         obligation_text="Chain obligation", risk_level="medium", category="chain")
        db_session.add(obl)
        
        pol = Policy(id="POL_CHAIN_001", title="Chain Policy", status="active")
        db_session.add(pol)
        
        proc = Process(id="PROC_CHAIN_001", name="Chain Process", status="active")
        db_session.add(proc)
        
        ctl = Control(id="CTL_CHAIN_001", name="Chain Control", control_type="preventive",
                      control_category="IT", frequency="daily", automation_level="fully_automated",
                      status="active", process_id=proc.id)
        db_session.add(ctl)
        
        ev = Evidence(id="EVD_CHAIN_001", control_id=ctl.id, evidence_type="log",
                      title="Chain Evidence", status="verified")
        db_session.add(ev)
        
        exc = Exc(id="EXC_CHAIN_001", exception_number="EXC-CHAIN-001",
                  title="Chain Exception", exception_type="control_failure",
                  severity="medium", status="closed", detected_date="2024-01-01",
                  control_id=ctl.id)
        db_session.add(exc)
        
        # Mappings
        mr1 = MappingReview(id="MAP_C_01", mapping_type="obligation_to_policy",
                            source_entity_type="obligation", source_entity_id=obl.id,
                            target_entity_type="policy", target_entity_id=pol.id,
                            status="accepted")
        mr2 = MappingReview(id="MAP_C_02", mapping_type="policy_to_process",
                            source_entity_type="policy", source_entity_id=pol.id,
                            target_entity_type="process", target_entity_id=proc.id,
                            status="accepted")
        db_session.add_all([mr1, mr2])
        db_session.commit()
        
        from app.services.analytics import build_traceability_chain
        chain = build_traceability_chain(db_session, obl.id)
        
        assert chain["regulation"]["id"] == reg.id
        assert chain["obligation"]["id"] == obl.id
        assert len(chain["policies"]) == 1
        assert len(chain["processes"]) == 1
        assert len(chain["controls"]) == 1
        assert len(chain["evidence"]) == 1
        assert len(chain["exceptions"]) == 1

class TestAgentTools:
    def test_agent_tools_search_regulation(self, db_session):
        reg = Regulation(id="REG_TOOL_001", title="Tool Test Regulation", 
                         jurisdiction="Test", regulator="Test Authority", status="active")
        db_session.add(reg)
        db_session.commit()
        
        tools = AgentTools(db_session)
        results = tools.search_regulation("Tool Test")
        
        assert len(results) == 1
        assert results[0]["id"] == "REG_TOOL_001"

    def test_agent_tools_analyze_exceptions(self, db_session):
        proc = Process(id="PROC_TOOL_001", name="Tool Process", status="active")
        db_session.add(proc)
        
        exc = Exc(id="EXC_TOOL_001", exception_number="EXC-TOOL-001",
                  title="Tool Exception", exception_type="control_failure",
                  severity="critical", status="open", detected_date=date.today() - timedelta(days=5),
                  process_id=proc.id)
        db_session.add(exc)
        db_session.commit()
        
        tools = AgentTools(db_session)
        analysis = tools.analyze_exceptions(days=30)
        
        assert analysis["total"] == 1
        assert analysis["by_severity"]["critical"] == 1
        assert analysis["by_status"]["open"] == 1

class TestEvidenceAttribution:
    def test_verify_claim_with_evidence(self, db_session, monkeypatch):
        monkeypatch.setattr(
            HybridRetriever, "_get_query_embedding", lambda self, q: [0.1] * 384
        )
        proc = Process(id="PROC_ATTR_001", name="Attr Process", status="active")
        db_session.add(proc)
        
        ctl = Control(id="CTL_ATTR_001", name="Attr Control", control_type="detective",
                      control_category="IT", frequency="monthly", automation_level="manual",
                      status="active", process_id=proc.id)
        db_session.add(ctl)
        
        ev = Evidence(
            id="EVD_ATTR_001", control_id=ctl.id, evidence_type="document",
            title="Control Evidence", description="Evidence showing control operates",
            status="verified", source_system="GRC",
            embedding=[0.1] * 384
        )
        db_session.add(ev)
        db_session.commit()
        
        attributor = EvidenceAttributor(db_session)
        result = attributor.verify_claim("Control CTL_ATTR_001 has verified evidence", "control", ctl.id)
        
        assert result["supported"] == True
        assert result["evidence_count"] == 1
        assert result["insufficient_evidence"] == False

    def test_verify_claim_without_evidence(self, db_session, monkeypatch):
        monkeypatch.setattr(
            HybridRetriever, "_get_query_embedding", lambda self, q: [0.1] * 384
        )
        proc = Process(id="PROC_ATTR_002", name="Attr Process 2", status="active")
        db_session.add(proc)
        
        ctl = Control(id="CTL_ATTR_002", name="Attr Control 2", control_type="detective",
                      control_category="IT", frequency="monthly", automation_level="manual",
                      status="active", process_id=proc.id)
        db_session.add(ctl)
        db_session.commit()
        
        attributor = EvidenceAttributor(db_session)
        result = attributor.verify_claim("Control CTL_ATTR_002 has verified evidence", "control", ctl.id)
        
        assert result["supported"] == False
        assert result["evidence_count"] == 0
        assert result["insufficient_evidence"] == True

    def test_format_citations(self, db_session):
        from app.services.retrieval import RetrievalResult
        
        results = [
            RetrievalResult(
                id="EVD_001", content="Evidence content", score=0.9,
                source_type="evidence", source_id="EVD_001",
                metadata={"control_name": "Test Control", "evidence_type": "document"},
                evidence_type="document"
            ),
            RetrievalResult(
                id="SEC_001", content="Section content", score=0.8,
                source_type="regulatory_section", source_id="SEC_001",
                metadata={"regulation_short_name": "GDPR", "section_number": "Art. 5"},
                regulation_id="REG_GDPR"
            )
        ]
        
        attributor = EvidenceAttributor(db_session)
        citations = attributor.format_citations(results)
        
        assert "[1]" in citations
        assert "[2]" in citations
        assert "GDPR" in citations
        assert "Test Control" in citations

if __name__ == "__main__":
    pytest.main([__file__, "-v"])