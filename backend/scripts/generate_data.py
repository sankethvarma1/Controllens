#!/usr/bin/env python3
"""
Synthetic Data Generator for CONTROLLENS
Creates realistic fictional organizational data with deliberate problems for testing.
"""
import os
import sys
import random
from datetime import date, datetime, timedelta
from decimal import Decimal
from faker import Faker
from sqlalchemy import text
from sqlalchemy.orm import Session

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.base import (
    engine, SessionLocal, Base,
    Regulation, RegulatorySection, Obligation, Policy, Process,
    Control, ControlOwner, Evidence, Transaction, Exception as Exc,
    RiskAssessment, MappingReview, AuditEvent, Document, DocumentChunk,
    init_db, drop_db
)

fake = Faker()
random.seed(42)
Faker.seed(42)

# =====================================================
# CONFIGURATION
# =====================================================

NUM_REGULATIONS = 5
NUM_SECTIONS_PER_REG = 8
NUM_OBLIGATIONS_PER_SECTION = 3
NUM_POLICIES = 12
NUM_PROCESSES = 15
NUM_CONTROLS = 40
NUM_EVIDENCE_PER_CONTROL = 3
NUM_TRANSACTIONS = 500
NUM_EXCEPTIONS = 30
NUM_RISK_ASSESSMENTS = 50
NUM_MAPPING_REVIEWS = 60

# Deliberate problem ratios
RATIO_OBLIGATIONS_WITHOUT_CONTROLS = 0.25
RATIO_CONTROLS_WITHOUT_EVIDENCE = 0.30
RATIO_STALE_EVIDENCE = 0.20
RATIO_FAILED_CONTROLS = 0.15
RATIO_TRANSACTION_ANOMALIES = 0.10
RATIO_CONFLICTING_MAPPINGS = 0.10

# =====================================================
# REFERENCE DATA
# =====================================================

REGULATIONS_DATA = [
    {
        "id": "REG_GDPR",
        "title": "General Data Protection Regulation (EU) 2016/679",
        "short_name": "GDPR",
        "jurisdiction": "European Union",
        "regulator": "European Data Protection Board",
        "publication_date": date(2016, 4, 27),
        "effective_date": date(2018, 5, 25),
        "status": "active",
        "description": "Regulation on data protection and privacy in the EU and EEA",
        "source_url": "https://eur-lex.europa.eu/eli/reg/2016/679/oj"
    },
    {
        "id": "REG_SOX",
        "title": "Sarbanes-Oxley Act of 2002",
        "short_name": "SOX",
        "jurisdiction": "United States",
        "regulator": "SEC / PCAOB",
        "publication_date": date(2002, 7, 30),
        "effective_date": date(2002, 7, 30),
        "status": "active",
        "description": "Federal law establishing auditing and financial regulation requirements",
        "source_url": "https://www.govinfo.gov/app/details/PLAW-107publ204"
    },
    {
        "id": "REG_BASL3",
        "title": "Basel III: International Regulatory Framework for Banks",
        "short_name": "Basel III",
        "jurisdiction": "International",
        "regulator": "Basel Committee on Banking Supervision",
        "publication_date": date(2010, 12, 16),
        "effective_date": date(2013, 1, 1),
        "status": "active",
        "description": "Global regulatory standard on bank capital adequacy, stress testing and market liquidity risk",
        "source_url": "https://www.bis.org/bcbs/basel3.htm"
    },
    {
        "id": "REG_CCPA",
        "title": "California Consumer Privacy Act of 2018",
        "short_name": "CCPA",
        "jurisdiction": "California, USA",
        "regulator": "California Attorney General",
        "publication_date": date(2018, 6, 28),
        "effective_date": date(2020, 1, 1),
        "status": "active",
        "description": "State statute enhancing privacy rights and consumer protection for California residents",
        "source_url": "https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?lawCode=CIV&division=3.&title=1.81.5.&part=4.&chapter=&article="
    },
    {
        "id": "REG_PCI_DSS",
        "title": "Payment Card Industry Data Security Standard v4.0",
        "short_name": "PCI DSS v4.0",
        "jurisdiction": "Global",
        "regulator": "PCI Security Standards Council",
        "publication_date": date(2022, 3, 31),
        "effective_date": date(2024, 3, 31),
        "status": "active",
        "description": "Information security standard for organizations that handle branded credit cards",
        "source_url": "https://www.pcisecuritystandards.org/document_library"
    }
]

OBLIGATION_CATEGORIES = [
    "data_protection", "financial_reporting", "access_control",
    "incident_response", "risk_management", "vendor_management",
    "business_continuity", "audit_logging", "encryption",
    "data_retention", "consent_management", "breach_notification"
]

CONTROL_TYPES = ["preventive", "detective", "corrective"]
CONTROL_CATEGORIES = ["IT", "financial", "operational", "compliance"]
FREQUENCIES = ["daily", "weekly", "monthly", "quarterly", "annually", "ad_hoc"]
AUTOMATION_LEVELS = ["manual", "semi_automated", "fully_automated"]
EVIDENCE_TYPES = ["document", "screenshot", "log", "report", "attestation"]
EXCEPTION_TYPES = ["control_failure", "policy_violation", "regulatory_breach", "process_deviation"]
SEVERITIES = ["low", "medium", "high", "critical"]
RISK_LEVELS = ["low", "medium", "high", "critical"]
MAPPING_STATUSES = ["proposed", "accepted", "rejected", "needs_review"]
REVIEW_DECISIONS = ["accept", "reject", "needs_more_info"]

DEPARTMENTS = [
    "Information Technology", "Finance", "Legal & Compliance",
    "Risk Management", "Internal Audit", "Human Resources",
    "Operations", "Security", "Data Privacy"
]

ROLES = [
    "Chief Information Security Officer", "Chief Financial Officer",
    "Chief Risk Officer", "Data Protection Officer", "Compliance Manager",
    "Internal Audit Director", "IT Security Manager", "Privacy Analyst",
    "Control Owner", "Process Owner"
]


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def random_date(start: date, end: date) -> date:
    """Generate random date between start and end."""
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))


def random_datetime(start: datetime, end: datetime) -> datetime:
    """Generate random datetime between start and end."""
    delta = end - start
    return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))


def weighted_choice(choices: dict) -> any:
    """Choose from dict of {value: weight}."""
    total = sum(choices.values())
    r = random.uniform(0, total)
    upto = 0
    for choice, weight in choices.items():
        if upto + weight >= r:
            return choice
        upto += weight
    return list(choices.keys())[-1]


# =====================================================
# DATA GENERATION
# =====================================================

def generate_regulations(db: Session) -> list:
    """Generate regulations."""
    print("Generating regulations...")
    regulations = []
    for reg_data in REGULATIONS_DATA:
        reg = Regulation(**reg_data)
        db.add(reg)
        regulations.append(reg)
    db.flush()
    return regulations


def generate_sections(db: Session, regulations: list) -> list:
    """Generate regulatory sections."""
    print("Generating regulatory sections...")
    sections = []
    section_types = ["article", "clause", "paragraph", "annex", "recital", "chapter"]
    
    for reg in regulations:
        num_sections = random.randint(6, 10)
        for i in range(num_sections):
            sec = RegulatorySection(
                id=f"SEC_{reg.id}_{i+1:03d}",
                regulation_id=reg.id,
                section_number=f"Article {i+1}" if i < 5 else f"Annex {i-4}",
                title=fake.sentence(nb_words=6).rstrip('.'),
                content=fake.paragraph(nb_sentences=5),
                section_type=random.choice(section_types),
                page_start=random.randint(1, 50),
                page_end=random.randint(51, 200)
            )
            db.add(sec)
            sections.append(sec)
    db.flush()
    return sections


def generate_obligations(db: Session, regulations: list, sections: list) -> list:
    """Generate obligations from regulations."""
    print("Generating obligations...")
    obligations = []
    
    for reg in regulations:
        reg_sections = [s for s in sections if s.regulation_id == reg.id]
        for section in reg_sections:
            num_obligations = random.randint(2, 4)
            for j in range(num_obligations):
                risk_level = weighted_choice({"low": 0.2, "medium": 0.5, "high": 0.25, "critical": 0.05})
                obl = Obligation(
                    id=f"OBL_{reg.id}_{section.id[-3:]}_{j+1:02d}",
                    regulation_id=reg.id,
                    section_id=section.id,
                    obligation_text=f"The organization shall {fake.sentence(nb_words=10).lower().rstrip('.')}.",
                    obligation_type=weighted_choice({"mandatory": 0.7, "recommended": 0.2, "conditional": 0.1}),
                    category=random.choice(OBLIGATION_CATEGORIES),
                    risk_level=risk_level,
                    status="active",
                    effective_date=reg.effective_date
                )
                db.add(obl)
                obligations.append(obl)
    db.flush()
    return obligations


def generate_policies(db: Session) -> list:
    """Generate policies."""
    print("Generating policies...")
    policies = []
    
    policy_templates = [
        ("Data Protection Policy", "data_protection", "Legal & Compliance", "Data Protection Officer"),
        ("Access Control Policy", "access_control", "Information Technology", "CISO"),
        ("Incident Response Policy", "incident_response", "Security", "Security Manager"),
        ("Vendor Risk Management Policy", "vendor_management", "Risk Management", "CRO"),
        ("Business Continuity Policy", "business_continuity", "Operations", "COO"),
        ("Financial Reporting Policy", "financial_reporting", "Finance", "CFO"),
        ("Audit Logging Policy", "audit_logging", "Internal Audit", "Audit Director"),
        ("Encryption Policy", "encryption", "Information Technology", "CISO"),
        ("Data Retention Policy", "data_retention", "Legal & Compliance", "DPO"),
        ("Consent Management Policy", "consent_management", "Legal & Compliance", "DPO"),
        ("Breach Notification Policy", "breach_notification", "Legal & Compliance", "DPO"),
        ("Risk Assessment Policy", "risk_management", "Risk Management", "CRO"),
    ]
    
    for i, (title, ptype, dept, role) in enumerate(policy_templates):
        pol = Policy(
            id=f"POL_{i+1:03d}",
            title=title,
            description=fake.paragraph(nb_sentences=3),
            policy_type="internal",
            owner_department=dept,
            owner_role=role,
            version=f"v{random.randint(1, 4)}.{random.randint(0, 9)}",
            status=weighted_choice({"active": 0.8, "draft": 0.1, "archived": 0.1}),
            effective_date=random_date(date(2020, 1, 1), date(2024, 1, 1)),
            review_date=random_date(date(2024, 1, 1), date(2025, 12, 31)),
            document_id=f"DOC_POL_{i+1:03d}"
        )
        db.add(pol)
        policies.append(pol)
    db.flush()
    return policies


def generate_processes(db: Session) -> list:
    """Generate business processes."""
    print("Generating business processes...")
    processes = []
    
    process_templates = [
        ("Customer Onboarding", "Operations", "Head of Operations"),
        ("Payment Processing", "Finance", "Treasury Manager"),
        ("Data Subject Access Request Handling", "Legal & Compliance", "DPO"),
        ("Incident Management", "Security", "Security Manager"),
        ("Vendor Onboarding", "Risk Management", "Vendor Risk Manager"),
        ("Financial Close", "Finance", "Controller"),
        ("Access Provisioning", "Information Technology", "IT Security Manager"),
        ("Backup and Recovery", "Information Technology", "Infrastructure Manager"),
        ("Change Management", "Information Technology", "Change Manager"),
        ("Risk Assessment", "Risk Management", "Risk Analyst"),
        ("Internal Audit Execution", "Internal Audit", "Audit Manager"),
        ("Policy Review and Approval", "Legal & Compliance", "Compliance Manager"),
        ("Data Classification", "Information Technology", "Data Governance Lead"),
        ("Third Party Monitoring", "Risk Management", "Vendor Risk Manager"),
        ("Regulatory Reporting", "Finance", "Regulatory Reporting Lead"),
    ]
    
    for i, (name, dept, owner) in enumerate(process_templates):
        proc = Process(
            id=f"PRC_{i+1:03d}",
            name=name,
            description=fake.paragraph(nb_sentences=2),
            department=dept,
            process_owner=owner,
            risk_rating=weighted_choice({"low": 0.2, "medium": 0.5, "high": 0.25, "critical": 0.05}),
            status="active"
        )
        db.add(proc)
        processes.append(proc)
    db.flush()
    return processes


def generate_controls(db: Session, processes: list, policies: list) -> list:
    """Generate controls mapped to processes and policies."""
    print("Generating controls...")
    controls = []
    
    control_templates = [
        ("Multi-Factor Authentication Enforcement", "preventive", "IT", "daily", "fully_automated"),
        ("Quarterly Access Recertification", "detective", "IT", "quarterly", "semi_automated"),
        ("Annual Risk Assessment", "detective", "operational", "annually", "manual"),
        ("Daily Transaction Monitoring", "detective", "financial", "daily", "fully_automated"),
        ("Monthly Bank Reconciliation", "detective", "financial", "monthly", "semi_automated"),
        ("Incident Response Plan Testing", "corrective", "operational", "annually", "manual"),
        ("Vendor Due Diligence Review", "preventive", "compliance", "annually", "manual"),
        ("Data Encryption at Rest", "preventive", "IT", "continuous", "fully_automated"),
        ("Data Encryption in Transit", "preventive", "IT", "continuous", "fully_automated"),
        ("Backup Integrity Verification", "detective", "IT", "weekly", "semi_automated"),
        ("Change Approval Workflow", "preventive", "IT", "per_change", "semi_automated"),
        ("Segregation of Duties Review", "detective", "financial", "quarterly", "manual"),
        ("Privacy Impact Assessment", "preventive", "compliance", "per_project", "manual"),
        ("Data Retention Schedule Execution", "preventive", "operational", "monthly", "semi_automated"),
        ("Consent Record Maintenance", "preventive", "compliance", "continuous", "fully_automated"),
        ("Breach Detection Alerting", "detective", "IT", "continuous", "fully_automated"),
        ("Security Awareness Training", "preventive", "operational", "annually", "manual"),
        ("Privileged Access Review", "detective", "IT", "monthly", "semi_automated"),
        ("Vulnerability Scanning", "detective", "IT", "weekly", "fully_automated"),
        ("Patch Management", "preventive", "IT", "monthly", "semi_automated"),
    ]
    
    for i, (name, ctype, category, freq, auto) in enumerate(control_templates):
        # Some controls without policies (deliberate problem)
        policy = random.choice(policies) if random.random() > 0.15 else None
        process = random.choice(processes)
        
        # Deliberate: some controls with poor effectiveness
        design_eff = weighted_choice({"effective": 0.6, "partially_effective": 0.3, "ineffective": 0.1})
        operating_eff = weighted_choice({"effective": 0.5, "partially_effective": 0.35, "ineffective": 0.15})
        
        last_tested = random_date(date(2023, 1, 1), date(2024, 10, 1))
        next_test = last_tested + timedelta(days={
            "daily": 1, "weekly": 7, "monthly": 30, "quarterly": 90,
            "annually": 365, "ad_hoc": 180, "continuous": 1, "per_change": 30, "per_project": 90
        }.get(freq, 90))
        
        # Deliberate: some overdue controls
        if random.random() < 0.1:
            next_test = date(2023, 12, 1)  # Overdue
        
        ctl = Control(
            id=f"CTL_{i+1:03d}",
            name=name,
            description=fake.paragraph(nb_sentences=2),
            control_type=ctype,
            control_category=category,
            frequency=freq,
            automation_level=auto,
            status="active",
            design_effectiveness=design_eff,
            operating_effectiveness=operating_eff,
            last_tested_date=last_tested,
            next_test_date=next_test,
            process_id=process.id,
            policy_id=policy.id if policy else None
        )
        db.add(ctl)
        controls.append(ctl)
    db.flush()
    return controls


def generate_control_owners(db: Session, controls: list) -> list:
    """Generate control owners."""
    print("Generating control owners...")
    owners = []
    
    for control in controls:
        # Primary owner
        owner1 = ControlOwner(
            id=f"COW_{control.id}_1",
            control_id=control.id,
            owner_type="primary",
            person_name=fake.name(),
            person_email=fake.company_email(),
            department=control.process.department if control.process else random.choice(DEPARTMENTS),
            role=random.choice(ROLES),
            assigned_date=random_date(date(2022, 1, 1), date(2024, 1, 1))
        )
        db.add(owner1)
        owners.append(owner1)
        
        # Secondary owner (50% chance)
        if random.random() < 0.5:
            owner2 = ControlOwner(
                id=f"COW_{control.id}_2",
                control_id=control.id,
                owner_type="secondary",
                person_name=fake.name(),
                person_email=fake.company_email(),
                department=random.choice(DEPARTMENTS),
                role=random.choice(ROLES),
                assigned_date=random_date(date(2022, 1, 1), date(2024, 1, 1))
            )
            db.add(owner2)
            owners.append(owner2)
    db.flush()
    return owners


def generate_evidence(db: Session, controls: list) -> list:
    """Generate evidence for controls with deliberate gaps."""
    print("Generating evidence...")
    evidence_list = []
    
    for control in controls:
        # Deliberate: some controls without evidence
        if random.random() < RATIO_CONTROLS_WITHOUT_EVIDENCE:
            continue
            
        num_evidence = random.randint(1, NUM_EVIDENCE_PER_CONTROL)
        for j in range(num_evidence):
            collected = random_datetime(
                datetime(2023, 1, 1), datetime(2024, 10, 15)
            )
            
            # Deliberate: some stale evidence
            if random.random() < RATIO_STALE_EVIDENCE:
                collected = random_datetime(
                    datetime(2022, 1, 1), datetime(2023, 1, 1)
                )
            
            expiry = collected.date() + timedelta(days=random.randint(90, 365))
            status = weighted_choice({"verified": 0.7, "submitted": 0.2, "rejected": 0.05, "expired": 0.05})
            
            ev = Evidence(
                id=f"EVD_{control.id}_{j+1:02d}",
                control_id=control.id,
                evidence_type=random.choice(EVIDENCE_TYPES),
                title=f"Evidence for {control.name} - {fake.sentence(nb_words=4).rstrip('.')}",
                description=fake.paragraph(nb_sentences=2),
                file_path=f"/evidence/{control.id}/{fake.uuid4()}.pdf",
                file_hash=fake.sha256(),
                source_system=random.choice(["GRC Platform", "SIEM", "HRIS", "ERP", "Document Management"]),
                collected_by=fake.name(),
                collected_at=collected,
                period_start=collected.date() - timedelta(days=random.randint(30, 90)),
                period_end=collected.date(),
                status=status,
                verification_notes=fake.sentence() if status == "verified" else None,
                verified_by=fake.name() if status == "verified" else None,
                verified_at=collected + timedelta(days=random.randint(1, 7)) if status == "verified" else None,
                expiry_date=expiry if random.random() > 0.1 else date(2023, 6, 1)  # Some expired
            )
            db.add(ev)
            evidence_list.append(ev)
    db.flush()
    return evidence_list


def generate_transactions(db: Session, processes: list, controls: list) -> list:
    """Generate transactions with anomalies."""
    print("Generating transactions...")
    transactions = []
    
    txn_types = ["payment", "transfer", "withdrawal", "deposit", "adjustment", "fee", "refund"]
    statuses = ["completed", "pending", "failed", "reversed"]
    
    for i in range(NUM_TRANSACTIONS):
        process = random.choice(processes)
        control = random.choice(controls) if random.random() < 0.7 else None
        
        # Deliberate anomalies
        is_anomaly = random.random() < RATIO_TRANSACTION_ANOMALIES
        amount = Decimal(str(round(random.uniform(-10000, 100000), 2)))
        if is_anomaly:
            amount = Decimal(str(round(random.uniform(50000, 500000), 2)))
        
        risk_score = round(random.uniform(0, 30), 2)
        if is_anomaly:
            risk_score = round(random.uniform(70, 100), 2)
        
        flags = []
        if is_anomaly:
            flags = random.sample(
                ["large_amount", "unusual_counterparty", "off_hours", "high_risk_country",
                 "velocity_check", "structuring", "round_amount"],
                k=random.randint(2, 4)
            )
        
        txn = Transaction(
            id=f"TXN_{i+1:05d}",
            transaction_id=f"TXN-{fake.date_time_this_year().strftime('%Y%m%d')}-{i+1:05d}",
            transaction_date=random_datetime(
                datetime(2024, 1, 1), datetime(2024, 10, 31)
            ),
            transaction_type=random.choice(txn_types),
            amount=amount,
            currency="USD",
            account_id=f"ACC-{random.randint(1000, 9999)}",
            counterparty=fake.company() if not is_anomaly else "UNKNOWN ENTITY " + fake.lexify(text="?????"),
            description=fake.sentence(),
            status=random.choice(statuses) if not is_anomaly else "flagged",
            risk_score=risk_score,
            flags=flags,
            process_id=process.id,
            control_id=control.id if control else None
        )
        db.add(txn)
        transactions.append(txn)
    db.flush()
    return transactions


def generate_exceptions(db: Session, controls: list, processes: list,
                        obligations: list, transactions: list) -> list:
    """Generate exceptions with deliberate issues."""
    print("Generating exceptions...")
    exceptions = []
    
    for i in range(NUM_EXCEPTIONS):
        exc_type = random.choice(EXCEPTION_TYPES)
        severity = weighted_choice({"low": 0.2, "medium": 0.4, "high": 0.3, "critical": 0.1})
        status = weighted_choice({
            "open": 0.3, "investigating": 0.2, "remediated": 0.3,
            "closed": 0.15, "accepted_risk": 0.05
        })
        
        control = random.choice(controls) if random.random() < 0.7 else None
        process = random.choice(processes)
        obligation = random.choice(obligations) if random.random() < 0.4 else None
        transaction = random.choice(transactions) if random.random() < 0.3 else None
        
        detected = random_date(date(2023, 1, 1), date(2024, 10, 1))
        deadline = detected + timedelta(days=random.randint(30, 180))
        resolved = None
        if status in ["remediated", "closed"]:
            resolved = detected + timedelta(days=random.randint(1, 120))
        
        exc = Exc(
            id=f"EXC_{i+1:04d}",
            exception_number=f"EXC-{detected.year}-{i+1:04d}",
            title=f"{exc_type.replace('_', ' ').title()}: {fake.sentence(nb_words=5).rstrip('.')}",
            description=fake.paragraph(nb_sentences=3),
            exception_type=exc_type,
            severity=severity,
            status=status,
            detected_date=detected,
            detected_by=fake.name(),
            control_id=control.id if control else None,
            process_id=process.id,
            obligation_id=obligation.id if obligation else None,
            transaction_id=transaction.id if transaction else None,
            root_cause=fake.paragraph(nb_sentences=2) if status != "open" else None,
            remediation_plan=fake.paragraph(nb_sentences=2) if status in ["investigating", "open"] else None,
            remediation_deadline=deadline,
            actual_resolution_date=resolved,
            assigned_to=fake.name()
        )
        db.add(exc)
        exceptions.append(exc)
    db.flush()
    return exceptions


def generate_risk_assessments(db: Session, obligations: list, controls: list,
                               exceptions: list) -> list:
    """Generate risk assessments."""
    print("Generating risk assessments...")
    assessments = []
    
    entities = [
        ("obligation", obligations),
        ("control", controls),
        ("exception", exceptions)
    ]
    
    for entity_type, entity_list in entities:
        for entity in random.sample(entity_list, min(len(entity_list), NUM_RISK_ASSESSMENTS // 3)):
            inherent = weighted_choice({"low": 0.1, "medium": 0.3, "high": 0.4, "critical": 0.2})
            residual = weighted_choice({"low": 0.3, "medium": 0.4, "high": 0.2, "critical": 0.1})
            
            # Risk score calculation
            risk_map = {"low": 1, "medium": 2, "high": 3, "critical": 4}
            likelihood_map = {"rare": 1, "unlikely": 2, "possible": 3, "likely": 4, "almost_certain": 5}
            impact_map = {"insignificant": 1, "minor": 2, "moderate": 3, "major": 4, "catastrophic": 5}
            
            likelihood = weighted_choice({
                "rare": 0.1, "unlikely": 0.2, "possible": 0.3, "likely": 0.3, "almost_certain": 0.1
            })
            impact = weighted_choice({
                "insignificant": 0.1, "minor": 0.2, "moderate": 0.3, "major": 0.3, "catastrophic": 0.1
            })
            
            risk_score = round(likelihood_map[likelihood] * impact_map[impact] * 5, 2)
            
            ra = RiskAssessment(
                id=f"RSK_{entity_type[:3]}_{entity.id}",
                entity_type=entity_type,
                entity_id=entity.id,
                risk_category=entity.category if hasattr(entity, 'category') else random.choice(OBLIGATION_CATEGORIES),
                inherent_risk=inherent,
                residual_risk=residual,
                likelihood=likelihood,
                impact=impact,
                risk_score=risk_score,
                mitigation_status=weighted_choice({"implemented": 0.4, "in_progress": 0.3, "planned": 0.2, "not_started": 0.1}),
                assessed_by=fake.name(),
                assessed_date=random_date(date(2023, 1, 1), date(2024, 10, 1)),
                next_review_date=random_date(date(2024, 11, 1), date(2025, 10, 1)),
                notes=fake.paragraph(nb_sentences=2)
            )
            db.add(ra)
            assessments.append(ra)
    db.flush()
    return assessments


def generate_mapping_reviews(db: Session, obligations: list, policies: list,
                              processes: list, controls: list) -> list:
    """Generate mapping reviews with human-in-the-loop states."""
    print("Generating mapping reviews...")
    reviews = []
    
    mapping_types = [
        ("obligation_to_policy", "obligation", "policy"),
        ("policy_to_process", "policy", "process"),
        ("process_to_control", "process", "control"),
        ("control_to_evidence", "control", "evidence")
    ]
    
    # Create realistic mappings
    for mapping_type, source_type, target_type in mapping_types:
        source_entities = {
            "obligation": obligations,
            "policy": policies,
            "process": processes,
            "control": controls
        }[source_type]
        
        target_entities = {
            "policy": policies,
            "process": processes,
            "control": controls,
            "evidence": []  # Evidence handled differently
        }.get(target_type, [])
        
        if not target_entities:
            continue
        
        for source in random.sample(source_entities, min(len(source_entities), 15)):
            num_mappings = random.randint(1, 3)
            for _ in range(num_mappings):
                target = random.choice(target_entities)
                confidence = round(random.uniform(0.4, 0.95), 2)
                
                # Deliberate: some conflicting/low confidence mappings
                if random.random() < RATIO_CONFLICTING_MAPPINGS:
                    confidence = round(random.uniform(0.2, 0.5), 2)
                
                status = weighted_choice({
                    "proposed": 0.3, "accepted": 0.5, "rejected": 0.1, "needs_review": 0.1
                })
                
                review = MappingReview(
                    id=f"MAP_{fake.uuid4()[:16]}",
                    mapping_type=mapping_type,
                    source_entity_type=source_type,
                    source_entity_id=source.id,
                    target_entity_type=target_type,
                    target_entity_id=target.id,
                    confidence_score=confidence,
                    ai_reasoning=f"AI analysis suggests {source_type} '{getattr(source, 'name', getattr(source, 'title', source.id)[:50])}' maps to {target_type} '{getattr(target, 'name', getattr(target, 'title', target.id)[:50])}' based on semantic similarity and regulatory alignment.",
                    status=status,
                    reviewed_by=fake.name() if status != "proposed" else None,
                    reviewed_at=random_datetime(datetime(2024, 1, 1), datetime(2024, 10, 15)) if status != "proposed" else None,
                    review_decision=random.choice(REVIEW_DECISIONS) if status != "proposed" else None,
                    review_comments=fake.sentence() if status != "proposed" else None
                )
                db.add(review)
                reviews.append(review)
    db.flush()
    return reviews


def generate_audit_events(db: Session, *entity_lists) -> list:
    """Generate audit trail events."""
    print("Generating audit events...")
    events = []
    
    all_entities = []
    for lst in entity_lists:
        all_entities.extend(lst)
    
    for _ in range(100):
        entity = random.choice(all_entities) if all_entities else None
        event = AuditEvent(
            id=f"AUD_{fake.uuid4()[:12]}",
            event_type=random.choice(["create", "update", "delete", "review", "approve", "reject"]),
            entity_type=type(entity).__name__.lower() if entity else "system",
            entity_id=entity.id if entity else None,
            user_id=fake.uuid4()[:12],
            user_role=random.choice(ROLES),
            action=random.choice(["created", "updated", "mapped", "reviewed", "approved", "rejected"]),
            old_values={"field": "old_value"} if random.random() < 0.5 else None,
            new_values={"field": "new_value"} if random.random() < 0.5 else None,
            ip_address=fake.ipv4(),
            user_agent=fake.user_agent()
        )
        db.add(event)
        events.append(event)
    db.flush()
    return events


def generate_documents_and_chunks(db: Session) -> list:
    """Generate sample documents and chunks for RAG."""
    print("Generating documents and chunks...")
    documents = []
    
    # Sample public domain / fictional regulatory documents
    doc_templates = [
        ("GDPR Full Text", "REG_GDPR", "regulation", 99),
        ("SOX Act Summary", "REG_SOX", "regulation", 50),
        ("Basel III Framework", "REG_BASL3", "regulation", 120),
        ("CCPA Overview", "REG_CCPA", "regulation", 40),
        ("PCI DSS Requirements", "REG_PCI_DSS", "regulation", 80),
        ("Data Protection Policy v2.3", "POL_001", "policy", 15),
        ("Access Control Policy v1.8", "POL_002", "policy", 12),
        ("Incident Response Plan", "POL_003", "policy", 25),
    ]
    
    for title, source_id, doc_type, pages in doc_templates:
        doc = Document(
            id=f"DOC_{fake.uuid4()[:12]}",
            title=title,
            source=source_id,
            document_type=doc_type,
            file_path=f"/documents/{title.lower().replace(' ', '_')}.pdf",
            file_hash=fake.sha256(),
            mime_type="application/pdf",
            page_count=pages,
            publication_date=random_date(date(2020, 1, 1), date(2024, 1, 1)),
            ingestion_status="completed",
            chunk_count=0
        )
        db.add(doc)
        db.flush()
        
        # Generate chunks
        num_chunks = pages * 2  # ~2 chunks per page
        for chunk_idx in range(num_chunks):
            chunk = DocumentChunk(
                id=f"CHK_{doc.id}_{chunk_idx:04d}",
                document_id=doc.id,
                chunk_index=chunk_idx,
                content=fake.paragraph(nb_sentences=5),
                section_title=fake.sentence(nb_words=4).rstrip('.'),
                section_number=f"{chunk_idx // 2 + 1}.{chunk_idx % 2 + 1}",
                page_number=(chunk_idx // 2) + 1,
                char_start=chunk_idx * 500,
                char_end=(chunk_idx + 1) * 500,
                token_count=random.randint(100, 400),
                chunk_metadata={
                    "source": source_id,
                    "document_type": doc_type,
                    "chunk_index": chunk_idx
                }
            )
            db.add(chunk)
        
        doc.chunk_count = num_chunks
        documents.append(doc)
    
    db.flush()
    return documents


# =====================================================
# MAIN GENERATION
# =====================================================

def main():
    print("=" * 60)
    print("CONTROLLENS - Synthetic Data Generation")
    print("=" * 60)
    
    # Initialize database
    print("\nInitializing database...")
    init_db()
    
    db = SessionLocal()
    try:
        # Check if data already exists
        existing_regs = db.query(Regulation).count()
        if existing_regs > 0:
            print(f"Database already contains {existing_regs} regulations. Skipping generation.")
            response = input("Force regenerate? (y/N): ")
            if response.lower() != 'y':
                return
            print("Dropping and recreating...")
            drop_db()
            init_db()
        
        # Generate in dependency order
        regulations = generate_regulations(db)
        sections = generate_sections(db, regulations)
        obligations = generate_obligations(db, regulations, sections)
        policies = generate_policies(db)
        processes = generate_processes(db)
        controls = generate_controls(db, processes, policies)
        owners = generate_control_owners(db, controls)
        evidence = generate_evidence(db, controls)
        transactions = generate_transactions(db, processes, controls)
        exceptions = generate_exceptions(db, controls, processes, obligations, transactions)
        risk_assessments = generate_risk_assessments(db, obligations, controls, exceptions)
        mapping_reviews = generate_mapping_reviews(db, obligations, policies, processes, controls)
        audit_events = generate_audit_events(db, regulations, obligations, policies, processes, controls, exceptions)
        documents = generate_documents_and_chunks(db)
        
        # Commit all
        print("\nCommitting to database...")
        db.commit()
        
        # Print summary
        print("\n" + "=" * 60)
        print("DATA GENERATION COMPLETE")
        print("=" * 60)
        print(f"Regulations:        {len(regulations)}")
        print(f"Regulatory Sections: {len(sections)}")
        print(f"Obligations:        {len(obligations)}")
        print(f"Policies:           {len(policies)}")
        print(f"Processes:          {len(processes)}")
        print(f"Controls:           {len(controls)}")
        print(f"Control Owners:     {len(owners)}")
        print(f"Evidence:           {len(evidence)}")
        print(f"Transactions:       {len(transactions)}")
        print(f"Exceptions:         {len(exceptions)}")
        print(f"Risk Assessments:   {len(risk_assessments)}")
        print(f"Mapping Reviews:    {len(mapping_reviews)}")
        print(f"Audit Events:       {len(audit_events)}")
        print(f"Documents:          {len(documents)}")
        
        # Verify deliberate problems
        print("\n--- DELIBERATE PROBLEMS VERIFICATION ---")
        obligations_no_controls = db.execute(
            text("""SELECT COUNT(*) FROM obligations o
               LEFT JOIN mapping_reviews mr ON mr.source_entity_type='obligation' AND mr.source_entity_id=o.id AND mr.status='accepted'
               LEFT JOIN policies p ON p.id=mr.target_entity_id
               LEFT JOIN mapping_reviews mr2 ON mr2.source_entity_type='policy' AND mr2.source_entity_id=p.id AND mr2.status='accepted'
               LEFT JOIN processes pr ON pr.id=mr2.target_entity_id
               LEFT JOIN controls c ON c.process_id=pr.id
               WHERE c.id IS NULL""")
        ).scalar()
        print(f"Obligations without controls: {obligations_no_controls}")
        
        controls_no_evidence = db.execute(
            text("SELECT COUNT(*) FROM controls c LEFT JOIN evidence e ON e.control_id=c.id WHERE e.id IS NULL AND c.status='active'")
        ).scalar()
        print(f"Controls without evidence: {controls_no_evidence}")
        
        stale_evidence = db.execute(
            text("SELECT COUNT(*) FROM evidence WHERE collected_at < '2023-01-01' AND status='verified'")
        ).scalar()
        print(f"Stale evidence (>1 year old): {stale_evidence}")
        
        overdue_controls = db.execute(
            text("SELECT COUNT(*) FROM controls WHERE next_test_date < CURRENT_DATE AND status='active'")
        ).scalar()
        print(f"Overdue controls: {overdue_controls}")
        
        open_exceptions = db.execute(
            text("SELECT COUNT(*) FROM exceptions WHERE status='open'")
        ).scalar()
        print(f"Open exceptions: {open_exceptions}")
        
        proposed_mappings = db.execute(
            text("SELECT COUNT(*) FROM mapping_reviews WHERE status='proposed'")
        ).scalar()
        print(f"Proposed mappings awaiting review: {proposed_mappings}")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()