# CONTROLLENS
**Regulatory & Control Intelligence Platform**

A full-stack platform for connecting regulations to controls with complete traceability, evidence-based reasoning, and human-in-the-loop governance.

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://postgresql.org)
[![pgvector](https://img.shields.io/badge/pgvector-enabled-orange.svg)](https://github.com/pgvector/pgvector)
[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg)](https://docker.com)

---

## Problem

Organizations struggle to maintain traceability across their regulatory compliance framework:

- **Regulations** → **Obligations** → **Policies** → **Processes** → **Controls** → **Evidence** → **Transactions** → **Exceptions** → **Risk**

Key challenges:
- Obligations without adequate control coverage
- Controls lacking supporting evidence
- Stale or expired evidence
- No clear audit trail for mapping decisions
- Difficulty answering "Why was this control flagged?" or "What evidence supports this mapping?"

---

## Solution

CONTROLLENS provides a unified platform that:

1. **Maps the complete chain** from regulation to exception with visual traceability
2. **Calculates deterministic analytics** (coverage, effectiveness, risk exposure) - no LLM hallucination
3. **Implements hybrid RAG** for evidence retrieval with source attribution
4. **Enforces human-in-the-loop** for all AI-generated mappings
4. **Provides investigation interface** with evidence-backed answers
5. **Maintains full audit trail** of all changes and decisions

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                       │
│  Dashboard | Regulations | Obligations | Controls | Evidence   │
│  Exceptions | Traceability | Review | Investigate | Audit      │
└─────────────────────────────┬───────────────────────────────────┘
                              │ REST API
┌─────────────────────────────▼───────────────────────────────────┐
│                      Backend (FastAPI)                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │
│  │Analytics │ │ Retrieval│ │ Document │ │     Agents       │  │
│  │ Engine   │ │ (Hybrid) │ │ Pipeline │ │ 6 Specialized    │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘  │
└─────────────────────────────┬───────────────────────────────────┘
                              │ SQL + Vector
┌─────────────────────────────▼───────────────────────────────────┐
│                  PostgreSQL + pgvector                          │
│  Regulations, Obligations, Policies, Processes, Controls,      │
│  Evidence, Transactions, Exceptions, Risk, Mappings, Audit     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Model

### Core Entities

| Entity | Description | Key Fields |
|--------|-------------|------------|
| `regulations` | Regulatory frameworks (GDPR, SOX, Basel III, etc.) | id, title, jurisdiction, regulator, dates |
| `regulatory_sections` | Articles, clauses, annexes | regulation_id, section_number, content, embedding |
| `obligations` | Extracted requirements | regulation_id, section_id, text, risk_level, category |
| `policies` | Internal policies | title, owner_department, version, status |
| `processes` | Business processes | name, department, process_owner, risk_rating |
| `controls` | Control activities | type, category, frequency, automation, effectiveness |
| `evidence` | Supporting documents | control_id, type, status, dates, embedding |
| `transactions` | Business transactions | amount, risk_score, flags, process/control links |
| `exceptions` | Control failures, violations | severity, status, root_cause, remediation |
| `risk_assessments` | Risk evaluations | inherent/residual risk, likelihood, impact |
| `mapping_reviews` | Human-in-the-loop mappings | source/target, confidence, status, decision |
| `audit_events` | Immutable audit trail | entity, user, action, old/new values |

### Relationships

```
Regulation 1──∞ RegulatorySection 1──∞ Obligation
Obligation ∞──∞ Policy (via mapping_reviews)
Policy ∞──∞ Process (via mapping_reviews)
Process 1──∞ Control
Control 1──∞ Evidence
Control 1──∞ Transaction
Control 1──∞ Exception
Obligation 1──∞ Exception
```

---

## RAG Architecture

### Document Pipeline
```
Document → Parser → Cleaner → Section Detector → Chunker → Embedder → pgvector
```

- **Parser**: PDF (pdfplumber), DOCX (python-docx), Text
- **Cleaner**: Normalizes whitespace, removes control characters
- **Section Detector**: Regex-based heading detection (Article 1, 1.1, etc.)
- **Chunker**: RecursiveCharacterTextSplitter (500 tokens, 100 overlap)
- **Embedder**: sentence-transformers (all-MiniLM-L6-v2, 384-dim)
- **Storage**: pgvector with HNSW index

### Hybrid Retrieval
```
Query → Query Embedding
        ↓
    ┌───┴───┐
    │       │
Semantic  Lexical (tsvector)
Search    Search
    │       │
    └───┬───┘
        ↓
   Re-rank (source priority + score)
        ↓
   Top-K Results with Full Metadata
```

Every result retains: document_id, title, section, page, control_id, regulation_id

---

## Agent Architecture

Six specialized agents using deterministic tools:

| Agent | Purpose | Key Tools |
|-------|---------|-----------|
| **Document Intelligence** | Analyze documents, extract obligations | `search_regulation`, `get_obligation` |
| **Obligation Mapping** | Propose obligation→policy→process→control mappings | `map_obligation_to_policy`, `map_policy_to_process`, `map_process_to_control` |
| **Evidence** | Collect, validate, identify gaps | `search_evidence`, `get_evidence_completeness`, `verify_evidence_claim` |
| **Monitoring** | Continuous control/exception monitoring | `check_control_health`, `monitor_exceptions`, `detect_transaction_anomalies` |
| **Gap Analysis** | Identify framework gaps | `find_unresolved_gaps`, `analyze_obligation_gaps`, `analyze_control_gaps` |
| **Report** | Generate compliance reports | `generate_dashboard_report`, `generate_traceability_report` |

**Tool Principle**: LLM reasons over tool results, never invents facts.

---

## Responsible AI

1. **No Auto-Acceptance**: All AI mappings start as `PROPOSED` - require human review
2. **Evidence Attribution**: Every answer cites source documents with metadata
3. **Insufficient Evidence Handling**: Explicitly states when evidence is lacking
4. **Deterministic Analytics**: Metrics calculated in SQL/Python, not by LLM
5. **Audit Trail**: All decisions (accept/reject) logged with user, timestamp, rationale
6. **Mapping States**: `PROPOSED` → `ACCEPTED` / `REJECTED` / `NEEDS_REVIEW`

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- NVIDIA API key for Nemotron (optional, for LLM features)

### 1. Clone and Configure
```bash
git clone <repo>
cd controllens
cp .env.example .env
# Edit .env with your values
```

### 2. Start Services
```bash
docker-compose up -d
```

This starts:
- PostgreSQL + pgvector on port 5432
- FastAPI backend on port 8000
- Next.js frontend on port 3000

### 3. Initialize Data
```bash
# Generate synthetic data
docker-compose exec backend python scripts/generate_data.py

# Ingest sample documents
docker-compose exec backend python -c "
from app.services.document_pipeline import ingest_sample_documents
from app.db.base import SessionLocal
db = SessionLocal()
ingest_sample_documents(db)
"
```

### 4. Access Application
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/api/v1/docs
- **Health Check**: http://localhost:8000/health

---

## API Endpoints

### Core Resources
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET/POST | `/api/v1/regulations` | List/create regulations |
| GET | `/api/v1/regulations/{id}/sections` | Get regulation sections |
| GET/POST | `/api/v1/obligations` | List/create obligations |
| GET | `/api/v1/obligations/{id}/coverage` | Obligation coverage analysis |
| GET/POST | `/api/v1/policies` | List/create policies |
| GET/POST | `/api/v1/processes` | List/create processes |
| GET/POST | `/api/v1/controls` | List/create controls |
| GET | `/api/v1/controls/{id}/effectiveness` | Control effectiveness analysis |
| GET/POST | `/api/v1/evidence` | List/create evidence |
| GET/POST | `/api/v1/transactions` | Query transactions |
| GET/POST | `/api/v1/exceptions` | List/create exceptions |
| PATCH | `/api/v1/exceptions/{id}` | Update exception status |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/analytics/dashboard` | Dashboard summary |
| GET | `/api/v1/analytics/obligation-coverage` | Coverage analysis |
| GET | `/api/v1/analytics/control-coverage` | Control coverage |
| GET | `/api/v1/analytics/evidence-completeness` | Evidence completeness |
| GET | `/api/v1/analytics/evidence-freshness` | Evidence freshness |
| GET | `/api/v1/analytics/risk-exposure` | Risk exposure |
| GET | `/api/v1/analytics/gaps` | Unresolved gaps |
| GET | `/api/v1/analytics/trends` | Trend metrics |

### Traceability & Investigation
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/traceability/{obligation_id}` | Full traceability chain |
| POST | `/api/v1/investigate` | AI investigation with evidence |
| POST | `/api/v1/retrieval/search` | Hybrid search |

### Human-in-the-Loop
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/mapping-reviews` | List proposed mappings |
| PATCH | `/api/v1/mapping-reviews/{id}` | Accept/reject mapping |

### Audit
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/audit` | Audit trail |

### Documents
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/v1/documents` | List/create documents |
| GET | `/api/v1/documents/{id}/chunks` | Document chunks |
| POST | `/api/v1/documents/ingest` | Ingest document |

---

## Testing

```bash
# Backend tests
docker-compose exec backend pytest tests/ -v

# Specific test categories
docker-compose exec backend pytest tests/test_analytics.py -v
docker-compose exec backend pytest tests/test_retrieval.py -v
docker-compose exec backend pytest tests/test_traceability.py -v
docker-compose exec backend pytest tests/test_evidence_attribution.py -v
```

### Key Test: Evidence Attribution
```python
# tests/test_evidence_attribution.py
def test_ai_cannot_claim_missing_evidence():
    """Ensure AI responses cannot reference non-retrieved evidence."""
    response = investigate("What evidence supports CTL_999?")  # Non-existent
    assert response.insufficient_evidence == True
    assert len(response.evidence) == 0
```

---

## Deployment

### Production Checklist
- [ ] Set strong `SECRET_KEY` and `POSTGRES_PASSWORD`
- [ ] Configure `LLM_API_KEY` for Nemotron
- [ ] Use managed PostgreSQL (RDS, Cloud SQL) with pgvector
- [ ] Enable TLS/SSL termination
- [ ] Configure backup strategy for PostgreSQL
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure log aggregation
- [ ] Run database migrations with Alembic

### Kubernetes (Optional)
```yaml
# Not included in MVP - use docker-compose or managed services
# For K8s: deploy postgres, backend (HPA), frontend (HPA), ingress
```

---

## Limitations

1. **Synthetic Data Only**: Uses fictional organizational data for demonstration
2. **No Real Document Processing**: Sample documents are text files, not actual regulations
3. **LLM Integration Stubbed**: Nemotron integration requires API key; investigation uses template responses
4. **No Authentication**: MVP lacks auth/authorization (add OAuth2/OIDC for production)
5. **Single Tenant**: No multi-organization support
6. **Limited Document Types**: PDF/DOCX parsing basic; no OCR for scanned docs
7. **No Real-time Updates**: WebSocket notifications not implemented

---

## Future Work

- [ ] Authentication & RBAC (OAuth2/OIDC)
- [ ] Multi-tenant architecture
- [ ] Real regulatory document ingestion (EUR-Lex, SEC EDGAR, etc.)
- [ ] Advanced NLI for evidence verification
- [ ] Automated control testing schedules
- [ ] Risk quantification (FAIR model)
- [ ] Regulatory change monitoring
- [ ] Export reports (PDF, Excel)
- [ ] Webhook integrations (ServiceNow, Jira)
- [ ] Mobile-responsive improvements
- [ ] Unit/integration test coverage >80%
- [ ] Performance optimization (query tuning, caching)

---

## License

MIT License - See LICENSE file for details.

---

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Run linting: `ruff check .` / `black .`
5. Submit PR

---

## Acknowledgments

- **pgvector** for vector similarity search in PostgreSQL
- **sentence-transformers** for embeddings
- **FastAPI** for the API framework
- **Next.js** for the frontend framework
- **NVIDIA Nemotron** for LLM capabilities
- **Faker** for synthetic data generation