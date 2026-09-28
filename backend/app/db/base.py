# Database configuration and base models
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    create_engine, Column, String, Text, DateTime, Date, Integer,
    DECIMAL, Boolean, ForeignKey, Index, UniqueConstraint, ARRAY, JSON
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.sql import func
import uuid
import os

# Database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://controllens:controllens@localhost:5432/controllens"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def generate_id(prefix: str = "") -> str:
    """Generate a unique ID with optional prefix."""
    return f"{prefix}{uuid.uuid4().hex[:12]}"


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Regulation(Base, TimestampMixin):
    __tablename__ = "regulations"

    id = Column(String(50), primary_key=True, default=lambda: generate_id("REG"))
    title = Column(String(500), nullable=False)
    short_name = Column(String(100))
    jurisdiction = Column(String(100))
    regulator = Column(String(200))
    publication_date = Column(Date)
    effective_date = Column(Date)
    status = Column(String(50), default="active")
    description = Column(Text)
    source_url = Column(String(1000))

    sections = relationship("RegulatorySection", back_populates="regulation", lazy="dynamic")
    obligations = relationship("Obligation", back_populates="regulation", lazy="dynamic")


class RegulatorySection(Base, TimestampMixin):
    __tablename__ = "regulatory_sections"

    id = Column(String(50), primary_key=True, default=lambda: generate_id("SEC"))
    regulation_id = Column(String(50), ForeignKey("regulations.id"), nullable=False)
    section_number = Column(String(50))
    title = Column(String(500))
    content = Column(Text)
    parent_section_id = Column(String(50), ForeignKey("regulatory_sections.id"))
    section_type = Column(String(50))
    page_start = Column(Integer)
    page_end = Column(Integer)
    embedding = Column(Vector(384))

    regulation = relationship("Regulation", back_populates="sections")
    parent_section = relationship("RegulatorySection", remote_side=[id], backref="sub_sections")
    obligations = relationship("Obligation", back_populates="section", lazy="dynamic")


class Obligation(Base, TimestampMixin):
    __tablename__ = "obligations"

    id = Column(String(50), primary_key=True, default=lambda: generate_id("OBL"))
    regulation_id = Column(String(50), ForeignKey("regulations.id"), nullable=False)
    section_id = Column(String(50), ForeignKey("regulatory_sections.id"))
    obligation_text = Column(Text, nullable=False)
    obligation_type = Column(String(50))
    category = Column(String(100))
    risk_level = Column(String(20), default="medium")
    status = Column(String(50), default="active")
    effective_date = Column(Date)

    regulation = relationship("Regulation", back_populates="obligations")
    section = relationship("RegulatorySection", back_populates="obligations")
    exceptions = relationship("Exception", back_populates="obligation", lazy="dynamic")


class Policy(Base, TimestampMixin):
    __tablename__ = "policies"

    id = Column(String(50), primary_key=True, default=lambda: generate_id("POL"))
    title = Column(String(500), nullable=False)
    description = Column(Text)
    policy_type = Column(String(100))
    owner_department = Column(String(100))
    owner_role = Column(String(100))
    version = Column(String(20))
    status = Column(String(50), default="active")
    effective_date = Column(Date)
    review_date = Column(Date)
    document_id = Column(String(50))

    controls = relationship("Control", back_populates="policy", lazy="dynamic")


class Process(Base, TimestampMixin):
    __tablename__ = "processes"

    id = Column(String(50), primary_key=True, default=lambda: generate_id("PRC"))
    name = Column(String(500), nullable=False)
    description = Column(Text)
    department = Column(String(100))
    process_owner = Column(String(100))
    risk_rating = Column(String(20), default="medium")
    status = Column(String(50), default="active")

    controls = relationship("Control", back_populates="process", lazy="dynamic")
    transactions = relationship("Transaction", back_populates="process", lazy="dynamic")
    exceptions = relationship("Exception", back_populates="process", lazy="dynamic")


class Control(Base, TimestampMixin):
    __tablename__ = "controls"

    id = Column(String(50), primary_key=True, default=lambda: generate_id("CTL"))
    name = Column(String(500), nullable=False)
    description = Column(Text)
    control_type = Column(String(50))
    control_category = Column(String(100))
    frequency = Column(String(50))
    automation_level = Column(String(50))
    status = Column(String(50), default="active")
    design_effectiveness = Column(String(20))
    operating_effectiveness = Column(String(20))
    last_tested_date = Column(Date)
    next_test_date = Column(Date)
    process_id = Column(String(50), ForeignKey("processes.id"))
    policy_id = Column(String(50), ForeignKey("policies.id"))

    process = relationship("Process", back_populates="controls")
    policy = relationship("Policy", back_populates="controls")
    owners = relationship("ControlOwner", back_populates="control", lazy="dynamic")
    evidence = relationship("Evidence", back_populates="control", lazy="dynamic")
    transactions = relationship("Transaction", back_populates="control", lazy="dynamic")
    exceptions = relationship("Exception", back_populates="control", lazy="dynamic")


class ControlOwner(Base, TimestampMixin):
    __tablename__ = "control_owners"

    id = Column(String(50), primary_key=True, default=lambda: generate_id("COW"))
    control_id = Column(String(50), ForeignKey("controls.id"), nullable=False)
    owner_type = Column(String(50))
    person_name = Column(String(200))
    person_email = Column(String(200))
    department = Column(String(100))
    role = Column(String(100))
    assigned_date = Column(Date)

    control = relationship("Control", back_populates="owners")


class Evidence(Base, TimestampMixin):
    __tablename__ = "evidence"

    id = Column(String(50), primary_key=True, default=lambda: generate_id("EVD"))
    control_id = Column(String(50), ForeignKey("controls.id"), nullable=False)
    evidence_type = Column(String(50))
    title = Column(String(500))
    description = Column(Text)
    file_path = Column(String(1000))
    file_hash = Column(String(64))
    source_system = Column(String(100))
    collected_by = Column(String(200))
    collected_at = Column(DateTime(timezone=True))
    period_start = Column(Date)
    period_end = Column(Date)
    status = Column(String(50), default="submitted")
    verification_notes = Column(Text)
    verified_by = Column(String(200))
    verified_at = Column(DateTime(timezone=True))
    expiry_date = Column(Date)
    embedding = Column(Vector(384))

    control = relationship("Control", back_populates="evidence")


class Transaction(Base, TimestampMixin):
    __tablename__ = "transactions"

    id = Column(String(50), primary_key=True, default=lambda: generate_id("TXN"))
    transaction_id = Column(String(100), unique=True, nullable=False)
    transaction_date = Column(DateTime(timezone=True), nullable=False)
    transaction_type = Column(String(100))
    amount = Column(DECIMAL(18, 2))
    currency = Column(String(3), default="USD")
    account_id = Column(String(50))
    counterparty = Column(String(200))
    description = Column(Text)
    status = Column(String(50))
    risk_score = Column(DECIMAL(5, 2))
    flags = Column(ARRAY(Text))
    process_id = Column(String(50), ForeignKey("processes.id"))
    control_id = Column(String(50), ForeignKey("controls.id"))

    process = relationship("Process", back_populates="transactions")
    control = relationship("Control", back_populates="transactions")


class Exception(Base, TimestampMixin):
    __tablename__ = "exceptions"

    id = Column(String(50), primary_key=True, default=lambda: generate_id("EXC"))
    exception_number = Column(String(100), unique=True, nullable=False)
    title = Column(String(500))
    description = Column(Text)
    exception_type = Column(String(100))
    severity = Column(String(20), default="medium")
    status = Column(String(50), default="open")
    detected_date = Column(Date, nullable=False)
    detected_by = Column(String(200))
    control_id = Column(String(50), ForeignKey("controls.id"))
    process_id = Column(String(50), ForeignKey("processes.id"))
    obligation_id = Column(String(50), ForeignKey("obligations.id"))
    transaction_id = Column(String(50), ForeignKey("transactions.id"))
    root_cause = Column(Text)
    remediation_plan = Column(Text)
    remediation_deadline = Column(Date)
    actual_resolution_date = Column(Date)
    assigned_to = Column(String(200))

    control = relationship("Control", back_populates="exceptions")
    process = relationship("Process", back_populates="exceptions")
    obligation = relationship("Obligation", back_populates="exceptions")
    transaction = relationship("Transaction")


class RiskAssessment(Base, TimestampMixin):
    __tablename__ = "risk_assessments"

    id = Column(String(50), primary_key=True, default=lambda: generate_id("RSK"))
    entity_type = Column(String(50))
    entity_id = Column(String(50), nullable=False)
    risk_category = Column(String(100))
    inherent_risk = Column(String(20))
    residual_risk = Column(String(20))
    likelihood = Column(String(20))
    impact = Column(String(20))
    risk_score = Column(DECIMAL(5, 2))
    mitigation_status = Column(String(50))
    assessed_by = Column(String(200))
    assessed_date = Column(Date)
    next_review_date = Column(Date)
    notes = Column(Text)

    # Note: Polymorphic relationships (entity_type + entity_id) are not defined
    # as SQLAlchemy relationships since they lack proper foreign keys.
    # Use explicit queries in services/tools instead.


class MappingReview(Base, TimestampMixin):
    __tablename__ = "mapping_reviews"

    id = Column(String(50), primary_key=True, default=lambda: generate_id("MAP"))
    mapping_type = Column(String(50))
    source_entity_type = Column(String(50))
    source_entity_id = Column(String(50))
    target_entity_type = Column(String(50))
    target_entity_id = Column(String(50))
    confidence_score = Column(DECIMAL(5, 2))
    ai_reasoning = Column(Text)
    status = Column(String(50), default="proposed")
    reviewed_by = Column(String(200))
    reviewed_at = Column(DateTime(timezone=True))
    review_decision = Column(String(50))
    review_comments = Column(Text)

    # Note: Polymorphic relationships (source_entity_type + source_entity_id) 
    # are not defined as SQLAlchemy relationships since they lack proper foreign keys.
    # Use explicit queries in services/tools instead.


class AuditEvent(Base, TimestampMixin):
    __tablename__ = "audit_events"

    id = Column(String(50), primary_key=True, default=lambda: generate_id("AUD"))
    event_type = Column(String(100), nullable=False)
    entity_type = Column(String(50))
    entity_id = Column(String(50))
    user_id = Column(String(200))
    user_role = Column(String(100))
    action = Column(String(100))
    old_values = Column(JSONB)
    new_values = Column(JSONB)
    ip_address = Column(String(45))
    user_agent = Column(Text)


class Document(Base, TimestampMixin):
    __tablename__ = "documents"

    id = Column(String(50), primary_key=True, default=lambda: generate_id("DOC"))
    title = Column(String(500))
    source = Column(String(200))
    document_type = Column(String(100))
    file_path = Column(String(1000))
    file_hash = Column(String(64))
    mime_type = Column(String(100))
    page_count = Column(Integer)
    publication_date = Column(Date)
    ingestion_status = Column(String(50))
    ingestion_error = Column(Text)
    chunk_count = Column(Integer, default=0)

    chunks = relationship("DocumentChunk", back_populates="document", lazy="dynamic")


class DocumentChunk(Base, TimestampMixin):
    __tablename__ = "document_chunks"

    id = Column(String(50), primary_key=True, default=lambda: generate_id("CHK"))
    document_id = Column(String(50), ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    section_title = Column(String(500))
    section_number = Column(String(50))
    page_number = Column(Integer)
    char_start = Column(Integer)
    char_end = Column(Integer)
    token_count = Column(Integer)
    embedding = Column(Vector(384))
    chunk_metadata = Column(JSONB)

    document = relationship("Document", back_populates="chunks")


# Dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def drop_db():
    """Drop all tables (use with caution)."""
    Base.metadata.drop_all(bind=engine)