-- CONTROLLENS Database Schema
-- PostgreSQL with pgvector extension

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- =====================================================
-- CORE TABLES
-- =====================================================

-- Regulations table
CREATE TABLE regulations (
    id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    short_name VARCHAR(100),
    jurisdiction VARCHAR(100),
    regulator VARCHAR(200),
    publication_date DATE,
    effective_date DATE,
    status VARCHAR(50) DEFAULT 'active',
    description TEXT,
    source_url VARCHAR(1000),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Regulatory sections (articles, clauses, etc.)
CREATE TABLE regulatory_sections (
    id VARCHAR(50) PRIMARY KEY,
    regulation_id VARCHAR(50) NOT NULL REFERENCES regulations(id),
    section_number VARCHAR(50),
    title VARCHAR(500),
    content TEXT,
    parent_section_id VARCHAR(50) REFERENCES regulatory_sections(id),
    section_type VARCHAR(50), -- article, clause, paragraph, annex, etc.
    page_start INTEGER,
    page_end INTEGER,
    embedding vector(384),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Obligations extracted from regulations
CREATE TABLE obligations (
    id VARCHAR(50) PRIMARY KEY,
    regulation_id VARCHAR(50) NOT NULL REFERENCES regulations(id),
    section_id VARCHAR(50) REFERENCES regulatory_sections(id),
    obligation_text TEXT NOT NULL,
    obligation_type VARCHAR(50), -- mandatory, recommended, conditional
    category VARCHAR(100), -- data_protection, financial_reporting, etc.
    risk_level VARCHAR(20) DEFAULT 'medium', -- low, medium, high, critical
    status VARCHAR(50) DEFAULT 'active',
    effective_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Policies
CREATE TABLE policies (
    id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    policy_type VARCHAR(100), -- internal, regulatory, operational
    owner_department VARCHAR(100),
    owner_role VARCHAR(100),
    version VARCHAR(20),
    status VARCHAR(50) DEFAULT 'active', -- draft, active, archived, superseded
    effective_date DATE,
    review_date DATE,
    document_id VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Business Processes
CREATE TABLE processes (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    department VARCHAR(100),
    process_owner VARCHAR(100),
    risk_rating VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Controls
CREATE TABLE controls (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    control_type VARCHAR(50), -- preventive, detective, corrective
    control_category VARCHAR(100), -- IT, financial, operational, compliance
    frequency VARCHAR(50), -- daily, weekly, monthly, quarterly, annually, ad_hoc
    automation_level VARCHAR(50), -- manual, semi_automated, fully_automated
    status VARCHAR(50) DEFAULT 'active', -- active, inactive, deprecated
    design_effectiveness VARCHAR(20), -- effective, partially_effective, ineffective
    operating_effectiveness VARCHAR(20), -- effective, partially_effective, ineffective
    last_tested_date DATE,
    next_test_date DATE,
    process_id VARCHAR(50) REFERENCES processes(id),
    policy_id VARCHAR(50) REFERENCES policies(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Control Owners
CREATE TABLE control_owners (
    id VARCHAR(50) PRIMARY KEY,
    control_id VARCHAR(50) NOT NULL REFERENCES controls(id),
    owner_type VARCHAR(50), -- primary, secondary, reviewer
    person_name VARCHAR(200),
    person_email VARCHAR(200),
    department VARCHAR(100),
    role VARCHAR(100),
    assigned_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Evidence
CREATE TABLE evidence (
    id VARCHAR(50) PRIMARY KEY,
    control_id VARCHAR(50) NOT NULL REFERENCES controls(id),
    evidence_type VARCHAR(50), -- document, screenshot, log, report, attestation
    title VARCHAR(500),
    description TEXT,
    file_path VARCHAR(1000),
    file_hash VARCHAR(64),
    source_system VARCHAR(100),
    collected_by VARCHAR(200),
    collected_at TIMESTAMP WITH TIME ZONE,
    period_start DATE,
    period_end DATE,
    status VARCHAR(50) DEFAULT 'submitted', -- submitted, verified, rejected, expired
    verification_notes TEXT,
    verified_by VARCHAR(200),
    verified_at TIMESTAMP WITH TIME ZONE,
    expiry_date DATE,
    embedding vector(384),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Transactions
CREATE TABLE transactions (
    id VARCHAR(50) PRIMARY KEY,
    transaction_id VARCHAR(100) UNIQUE NOT NULL,
    transaction_date TIMESTAMP WITH TIME ZONE NOT NULL,
    transaction_type VARCHAR(100),
    amount DECIMAL(18, 2),
    currency VARCHAR(3) DEFAULT 'USD',
    account_id VARCHAR(50),
    counterparty VARCHAR(200),
    description TEXT,
    status VARCHAR(50), -- completed, pending, failed, reversed
    risk_score DECIMAL(5, 2),
    flags TEXT[],
    process_id VARCHAR(50) REFERENCES processes(id),
    control_id VARCHAR(50) REFERENCES controls(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Exceptions
CREATE TABLE exceptions (
    id VARCHAR(50) PRIMARY KEY,
    exception_number VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(500),
    description TEXT,
    exception_type VARCHAR(100), -- control_failure, policy_violation, regulatory_breach, process_deviation
    severity VARCHAR(20) DEFAULT 'medium', -- low, medium, high, critical
    status VARCHAR(50) DEFAULT 'open', -- open, investigating, remediated, closed, accepted_risk
    detected_date DATE NOT NULL,
    detected_by VARCHAR(200),
    control_id VARCHAR(50) REFERENCES controls(id),
    process_id VARCHAR(50) REFERENCES processes(id),
    obligation_id VARCHAR(50) REFERENCES obligations(id),
    transaction_id VARCHAR(50) REFERENCES transactions(id),
    root_cause TEXT,
    remediation_plan TEXT,
    remediation_deadline DATE,
    actual_resolution_date DATE,
    assigned_to VARCHAR(200),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Risk Assessments
CREATE TABLE risk_assessments (
    id VARCHAR(50) PRIMARY KEY,
    entity_type VARCHAR(50), -- obligation, control, process, policy
    entity_id VARCHAR(50) NOT NULL,
    risk_category VARCHAR(100),
    inherent_risk VARCHAR(20), -- low, medium, high, critical
    residual_risk VARCHAR(20), -- low, medium, high, critical
    likelihood VARCHAR(20), -- rare, unlikely, possible, likely, almost_certain
    impact VARCHAR(20), -- insignificant, minor, moderate, major, catastrophic
    risk_score DECIMAL(5, 2),
    mitigation_status VARCHAR(50),
    assessed_by VARCHAR(200),
    assessed_date DATE,
    next_review_date DATE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Mapping Reviews (Human-in-the-loop)
CREATE TABLE mapping_reviews (
    id VARCHAR(50) PRIMARY KEY,
    mapping_type VARCHAR(50), -- obligation_to_policy, policy_to_process, process_to_control, control_to_evidence
    source_entity_type VARCHAR(50),
    source_entity_id VARCHAR(50),
    target_entity_type VARCHAR(50),
    target_entity_id VARCHAR(50),
    confidence_score DECIMAL(5, 2),
    ai_reasoning TEXT,
    status VARCHAR(50) DEFAULT 'proposed', -- proposed, accepted, rejected, needs_review
    reviewed_by VARCHAR(200),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    review_decision VARCHAR(50), -- accept, reject, needs_more_info
    review_comments TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Audit Events
CREATE TABLE audit_events (
    id VARCHAR(50) PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id VARCHAR(50),
    user_id VARCHAR(200),
    user_role VARCHAR(100),
    action VARCHAR(100),
    old_values JSONB,
    new_values JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Document Ingestion Tracking
CREATE TABLE documents (
    id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(500),
    source VARCHAR(200),
    document_type VARCHAR(100), -- regulation, policy, procedure, evidence, report
    file_path VARCHAR(1000),
    file_hash VARCHAR(64),
    mime_type VARCHAR(100),
    page_count INTEGER,
    publication_date DATE,
    ingestion_status VARCHAR(50), -- pending, processing, completed, failed
    ingestion_error TEXT,
    chunk_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Document Chunks for RAG
CREATE TABLE document_chunks (
    id VARCHAR(50) PRIMARY KEY,
    document_id VARCHAR(50) NOT NULL REFERENCES documents(id),
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    section_title VARCHAR(500),
    section_number VARCHAR(50),
    page_number INTEGER,
    char_start INTEGER,
    char_end INTEGER,
    token_count INTEGER,
    embedding vector(384),
    chunk_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- INDEXES
-- =====================================================

-- Regulations indexes
CREATE INDEX idx_regulations_status ON regulations(status);
CREATE INDEX idx_regulations_jurisdiction ON regulations(jurisdiction);

-- Regulatory sections indexes
CREATE INDEX idx_regulatory_sections_regulation ON regulatory_sections(regulation_id);
CREATE INDEX idx_regulatory_sections_parent ON regulatory_sections(parent_section_id);
CREATE INDEX idx_regulatory_sections_embedding ON regulatory_sections USING hnsw (embedding vector_cosine_ops);

-- Obligations indexes
CREATE INDEX idx_obligations_regulation ON obligations(regulation_id);
CREATE INDEX idx_obligations_section ON obligations(section_id);
CREATE INDEX idx_obligations_category ON obligations(category);
CREATE INDEX idx_obligations_risk_level ON obligations(risk_level);
CREATE INDEX idx_obligations_status ON obligations(status);

-- Policies indexes
CREATE INDEX idx_policies_status ON policies(status);
CREATE INDEX idx_policies_owner ON policies(owner_department);
CREATE INDEX idx_policies_type ON policies(policy_type);

-- Processes indexes
CREATE INDEX idx_processes_department ON processes(department);
CREATE INDEX idx_processes_status ON processes(status);

-- Controls indexes
CREATE INDEX idx_controls_process ON controls(process_id);
CREATE INDEX idx_controls_policy ON controls(policy_id);
CREATE INDEX idx_controls_status ON controls(status);
CREATE INDEX idx_controls_type ON controls(control_type);
CREATE INDEX idx_controls_next_test ON controls(next_test_date);

-- Control owners indexes
CREATE INDEX idx_control_owners_control ON control_owners(control_id);
CREATE INDEX idx_control_owners_person ON control_owners(person_email);

-- Evidence indexes
CREATE INDEX idx_evidence_control ON evidence(control_id);
CREATE INDEX idx_evidence_status ON evidence(status);
CREATE INDEX idx_evidence_collected ON evidence(collected_at);
CREATE INDEX idx_evidence_expiry ON evidence(expiry_date);
CREATE INDEX idx_evidence_embedding ON evidence USING hnsw (embedding vector_cosine_ops);

-- Transactions indexes
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
CREATE INDEX idx_transactions_account ON transactions(account_id);
CREATE INDEX idx_transactions_process ON transactions(process_id);
CREATE INDEX idx_transactions_control ON transactions(control_id);
CREATE INDEX idx_transactions_risk ON transactions(risk_score);

-- Exceptions indexes
CREATE INDEX idx_exceptions_status ON exceptions(status);
CREATE INDEX idx_exceptions_severity ON exceptions(severity);
CREATE INDEX idx_exceptions_control ON exceptions(control_id);
CREATE INDEX idx_exceptions_obligation ON exceptions(obligation_id);
CREATE INDEX idx_exceptions_detected ON exceptions(detected_date);
CREATE INDEX idx_exceptions_assigned ON exceptions(assigned_to);

-- Risk assessments indexes
CREATE INDEX idx_risk_assessments_entity ON risk_assessments(entity_type, entity_id);
CREATE INDEX idx_risk_assessments_residual ON risk_assessments(residual_risk);

-- Mapping reviews indexes
CREATE INDEX idx_mapping_reviews_status ON mapping_reviews(status);
CREATE INDEX idx_mapping_reviews_source ON mapping_reviews(source_entity_type, source_entity_id);
CREATE INDEX idx_mapping_reviews_target ON mapping_reviews(target_entity_type, target_entity_id);

-- Audit events indexes
CREATE INDEX idx_audit_events_entity ON audit_events(entity_type, entity_id);
CREATE INDEX idx_audit_events_user ON audit_events(user_id);
CREATE INDEX idx_audit_events_timestamp ON audit_events(timestamp);

-- Documents indexes
CREATE INDEX idx_documents_status ON documents(ingestion_status);
CREATE INDEX idx_documents_type ON documents(document_type);

-- Document chunks indexes
CREATE INDEX idx_document_chunks_document ON document_chunks(document_id);
CREATE INDEX idx_document_chunks_embedding ON document_chunks USING hnsw (embedding vector_cosine_ops);

-- =====================================================
-- VIEWS FOR ANALYTICS
-- =====================================================

-- Obligation Coverage View
CREATE OR REPLACE VIEW v_obligation_coverage AS
SELECT
    o.id AS obligation_id,
    o.regulation_id,
    o.obligation_text,
    o.risk_level,
    o.category,
    COUNT(DISTINCT mr.target_entity_id) FILTER (WHERE mr.target_entity_type = 'policy' AND mr.status = 'accepted') AS policy_count,
    COUNT(DISTINCT c.id) AS control_count,
    COUNT(DISTINCT e.id) AS evidence_count,
    CASE
        WHEN COUNT(DISTINCT c.id) = 0 THEN 'no_controls'
        WHEN COUNT(DISTINCT e.id) = 0 THEN 'no_evidence'
        WHEN COUNT(DISTINCT e.id) < COUNT(DISTINCT c.id) THEN 'partial_evidence'
        ELSE 'covered'
    END AS coverage_status
FROM obligations o
LEFT JOIN mapping_reviews mr ON mr.source_entity_type = 'obligation' AND mr.source_entity_id = o.id
LEFT JOIN policies p ON p.id = mr.target_entity_id AND mr.target_entity_type = 'policy' AND mr.status = 'accepted'
LEFT JOIN mapping_reviews mr2 ON mr2.source_entity_type = 'policy' AND mr2.source_entity_id = p.id AND mr2.status = 'accepted'
LEFT JOIN processes pr ON pr.id = mr2.target_entity_id AND mr2.target_entity_type = 'process'
LEFT JOIN controls c ON c.process_id = pr.id AND c.status = 'active'
LEFT JOIN evidence e ON e.control_id = c.id AND e.status = 'verified'
GROUP BY o.id, o.regulation_id, o.obligation_text, o.risk_level, o.category;

-- Control Effectiveness View
CREATE OR REPLACE VIEW v_control_effectiveness AS
SELECT
    c.id AS control_id,
    c.name AS control_name,
    c.control_type,
    c.frequency,
    c.automation_level,
    c.design_effectiveness,
    c.operating_effectiveness,
    c.last_tested_date,
    c.next_test_date,
    COUNT(DISTINCT e.id) AS evidence_count,
    COUNT(DISTINCT e.id) FILTER (WHERE e.status = 'verified') AS verified_evidence_count,
    COUNT(DISTINCT e.id) FILTER (WHERE e.expiry_date < CURRENT_DATE) AS expired_evidence_count,
    COUNT(DISTINCT ex.id) AS exception_count,
    COUNT(DISTINCT ex.id) FILTER (WHERE ex.status = 'open') AS open_exception_count,
    CASE
        WHEN c.next_test_date < CURRENT_DATE THEN 'overdue'
        WHEN c.next_test_date <= CURRENT_DATE + INTERVAL '30 days' THEN 'due_soon'
        ELSE 'current'
    END AS test_status
FROM controls c
LEFT JOIN evidence e ON e.control_id = c.id
LEFT JOIN exceptions ex ON ex.control_id = c.id
WHERE c.status = 'active'
GROUP BY c.id, c.name, c.control_type, c.frequency, c.automation_level,
         c.design_effectiveness, c.operating_effectiveness, c.last_tested_date, c.next_test_date;

-- Exception Trends View
CREATE OR REPLACE VIEW v_exception_trends AS
SELECT
    DATE_TRUNC('month', detected_date) AS month,
    COUNT(*) AS total_exceptions,
    COUNT(*) FILTER (WHERE severity = 'critical') AS critical_count,
    COUNT(*) FILTER (WHERE severity = 'high') AS high_count,
    COUNT(*) FILTER (WHERE severity = 'medium') AS medium_count,
    COUNT(*) FILTER (WHERE severity = 'low') AS low_count,
    COUNT(*) FILTER (WHERE status = 'open') AS open_count,
    COUNT(*) FILTER (WHERE status = 'closed') AS closed_count,
    AVG(CASE WHEN actual_resolution_date IS NOT NULL
        THEN actual_resolution_date - detected_date ELSE NULL END) AS avg_resolution_days
FROM exceptions
GROUP BY DATE_TRUNC('month', detected_date)
ORDER BY month DESC;

-- Evidence Freshness View
CREATE OR REPLACE VIEW v_evidence_freshness AS
SELECT
    c.id AS control_id,
    c.name AS control_name,
    COUNT(e.id) AS total_evidence,
    COUNT(e.id) FILTER (WHERE e.status = 'verified') AS verified_evidence,
    MAX(e.collected_at) AS latest_evidence_date,
    MIN(e.expiry_date) AS earliest_expiry,
    COUNT(e.id) FILTER (WHERE e.expiry_date < CURRENT_DATE) AS expired_count,
    CASE
        WHEN MAX(e.collected_at) IS NULL THEN 'no_evidence'
        WHEN MAX(e.collected_at) < CURRENT_DATE - INTERVAL '90 days' THEN 'stale'
        WHEN MAX(e.collected_at) < CURRENT_DATE - INTERVAL '30 days' THEN 'aging'
        ELSE 'fresh'
    END AS freshness_status
FROM controls c
LEFT JOIN evidence e ON e.control_id = c.id
WHERE c.status = 'active'
GROUP BY c.id, c.name;

-- =====================================================
-- FUNCTIONS
-- =====================================================

-- Function to log audit events
CREATE OR REPLACE FUNCTION log_audit_event(
    p_event_type VARCHAR,
    p_entity_type VARCHAR,
    p_entity_id VARCHAR,
    p_user_id VARCHAR,
    p_user_role VARCHAR,
    p_action VARCHAR,
    p_old_values JSONB DEFAULT NULL,
    p_new_values JSONB DEFAULT NULL,
    p_ip_address VARCHAR DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    INSERT INTO audit_events (event_type, entity_type, entity_id, user_id, user_role, action, old_values, new_values, ip_address, user_agent)
    VALUES (p_event_type, p_entity_type, p_entity_id, p_user_id, p_user_role, p_action, p_old_values, p_new_values, p_ip_address, p_user_agent);
END;
$$ LANGUAGE plpgsql;

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at triggers
CREATE TRIGGER update_regulations_updated_at BEFORE UPDATE ON regulations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_regulatory_sections_updated_at BEFORE UPDATE ON regulatory_sections FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_obligations_updated_at BEFORE UPDATE ON obligations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_policies_updated_at BEFORE UPDATE ON policies FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_processes_updated_at BEFORE UPDATE ON processes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_controls_updated_at BEFORE UPDATE ON controls FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_evidence_updated_at BEFORE UPDATE ON evidence FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_exceptions_updated_at BEFORE UPDATE ON exceptions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_risk_assessments_updated_at BEFORE UPDATE ON risk_assessments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_mapping_reviews_updated_at BEFORE UPDATE ON mapping_reviews FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();