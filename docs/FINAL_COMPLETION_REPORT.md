# CONTROLLEENS — FINAL COMPLETION REPORT

## 1. Executive Summary
- What CONTROLLEENS is
- CONTROLLEENS (repo folder `controllens`, app title CONTROLLENS) is a full-stack Regulatory & Control Intelligence Platform. It connects Regulation → Obligation → Policy → Process → Control → Evidence → Transaction → Exception → Risk, with deterministic analytics, pgvector-backed retrieval, evidence attribution, agent tools, a human-in-the-loop mapping review flow, a Next.js frontend, and a FastAPI backend.
- What business/technical problem it solves
- Organizations lose traceability across compliance: obligations without controls, controls without evidence, stale/expired evidence, overdue testing, open exceptions, and no audit trail for AI-proposed mappings. CONTROLLEENS makes the full chain queryable, computes coverage/effectiveness/risk/gaps deterministically (no LLM math), retrieves evidence with source metadata, and requires human accept/reject for mappings.
- Current completion percentage
- **~85%**
- Final classification:
- **MVP NEARLY COMPLETE**

## 2. What Was Already Built
List everything that existed before this finalization phase:
- backend
- FastAPI app (`backend/app/main.py`, 1071 lines) with ~40 endpoints; config, schemas (676 lines), services, agents scaffolds; `requirements.txt` pinned.
- database
- SQLAlchemy models (15 tables), `schema.sql` (502 lines) with tables, HNSW indexes, 4 analytics views, audit function, updated_at triggers.
- API
- Route code for health, regulations, obligations, policies, processes, controls, evidence, transactions, exceptions, risk-assessments, mapping-reviews, audit, analytics x8, traceability, investigate, documents, retrieval, agents, admin.
- analytics
- `AnalyticsEngine` (845 lines): execution rate, exception rate/spikes, completeness, freshness, obligation coverage, control coverage, risk exposure, gaps, trends, dashboard, effectiveness composite, traceability chain builder.
- document pipeline
- Parser (PDF/DOCX/text), cleaner, section detector, chunker, embedding generator, ingest pipeline, 4 sample documents.
- embeddings
- `all-MiniLM-L6-v2` wired in both ingestion and query paths; `Vector(384)` columns; 384-dimension config.
- pgvector
- Extension, `vector(384)` columns x3, HNSW cosine indexes x3.
- retrieval
- `HybridRetriever` (3 source types + rerank) and `EvidenceAttributor` (verify_claim, format_citations).
- evidence attribution
- `verify_claim` supported/insufficient_evidence contract + citation formatter.
- agent tools
- `AgentTools` (~640 lines) covering regulation, obligation, policy, process, control, evidence, transaction, exception, traceability, risk, audit; 6 agent classes + registry.
- investigation
- `/investigate` endpoint with keyword routing to tools/retrieval + answer composer.
- frontend
- 11 routes (dashboard, regulations, obligations, controls, evidence, exceptions, traceability, review, investigate, audit + root), full `api.ts` client (414 lines), Tailwind styling.
- Docker
- `docker-compose.yml` (postgres pgvector/pg16 + backend + frontend), backend + frontend Dockerfiles.
- tests
- `tests/test_core.py` (488 lines, 15 tests: database, analytics, retrieval, traceability, agent tools, attribution).
- documentation
- `README.md` (364 lines), `.env.example`, `.gitignore`.

## 3. Problems Found During Audit
For every issue:
- problem
- **P1 — Backend would not start.** `ModuleNotFoundError: No module named 'langchain'`.
- root cause
- `document_pipeline.py` imported `from langchain.text_splitter import ...`, but installed package is `langchain-text-splitters==0.0.1` (import path `langchain_text_splitters`). Secondary: `main.py` used `List[Dict]` while only importing `List, Optional`.
- affected component
- FastAPI startup; document ingestion; all `/documents/ingest` and `/admin/*` paths.
- severity
- CRITICAL (total backend outage).
- impact
- Zero API availability until fixed.
- problem
- **P2 — Analytics join crash.** `DuplicateAlias: table name "mapping_reviews" specified more than once`.
- root cause
- `_get_linked_policies` / `_get_linked_processes` joined `MappingReview` twice with no aliases.
- affected component
- Obligation coverage, gaps, traceability chain, dependent agent tools; 4+ tests.
- severity
- HIGH.
- impact
- Coverage always errored; gaps/traceability unusable.
- problem
- **P3 — Retrieval SQL broken.** `vector <=> numeric[]` + SQLAlchemy `::` misparse + dead SQL + column rename miss.
- root cause
- Python list bind param sent as Postgres `numeric[]`; `::vector` casts misparsed by `text()` (`:` = bind prefix); dead first SQL block referenced dropped `dc.metadata` column; `_search_regulatory_sections` lacked any cast; model field is `chunk_metadata`.
- affected component
- All semantic search.
- severity
- HIGH.
- impact
- Every vector query errored; RAG non-functional.
- problem
- **P4 — Time-bomb test dates + wrong frequency.**
- root cause
- Hardcoded 2024 dates with `days=30/90` windows while system date is 2026; `daily` frequency expects 90 executions but test supplies 3 evidence rows.
- affected component
- `test_control_effectiveness_calculation`, `test_agent_tools_analyze_exceptions` (and fragile gap/overdue fixtures).
- severity
- MEDIUM (tests only; production logic sound).
- impact
- False test failures masking real status.
- problem
- **P5 — Test/model fixture mismatch.**
- root cause
- Tests used `metadata={}`; production column is `chunk_metadata`. Evidence fixtures had no embedding while retrieval filters `IS NOT NULL`. Tests also hit live Hugging Face on every query-embedding call.
- affected component
- Retrieval + attribution tests.
- severity
- MEDIUM.
- impact
- Tests errored/slow (~27s) and risked HF 429 rate limits.
- problem
- **P6 — Frontend type/build breaks.**
- root cause
- `page.tsx` held an AppLayout-with-children component (invalid as a Next.js page); missing `Link`, `ChevronRight`, `getSeverityColor` imports; missing `InvestigationResponse`, `RetrievalResultResponse`, `MappingReviewResponse`, `AuditEventResponse.ip_address/user_agent`, `EvidenceItem.file_path` types; null-unsafe audit rendering; `tsconfig` lacked `target` (ES5 default broke `Set` iteration).
- affected component
- `tsc --noEmit` and `next build`.
- severity
- HIGH (no shippable UI until fixed).
- impact
- Production build failed.
- problem
- **P7 — Investigation is stub, not Nemotron.**
- root cause
- No HTTP/LLM call exists anywhere; `_generate_answer` is explicitly labeled "placeholder for LLM" with template strings. Config keys (`LLM_MODEL`, `LLM_API_KEY`) are inert.
- affected component
- `/investigate` answer quality claims.
- severity
- MEDIUM (honesty risk, not outage).
- impact
- Cannot be presented as Nemotron-powered.

## 4. Fixes Implemented
For EVERY fix:
- exact problem fixed
- **P1 — Backend startup.**
- file(s) changed
- `backend/app/services/document_pipeline.py`, `backend/app/main.py`.
- what was changed
- Import → `from langchain_text_splitters import RecursiveCharacterTextSplitter`; `from typing import List, Optional, Dict`.
- why the change was necessary
- Use the installed package instead of adding the full `langchain` dependency; `Dict` was genuinely referenced.
- how it was verified
- `py_compile` OK, `import app.main` OK, uvicorn boot + `GET /health → 200 {"status":"ok","database":"healthy"}` + `/api/v1/openapi.json → 200`.
- exact problem fixed
- **P2 — Analytics joins.**
- file(s) changed
- `backend/app/services/analytics.py`.
- what was changed
- Added `aliased` import; `_get_linked_policies` / `_get_linked_processes` now use `mr_target = aliased(MappingReview)`, `mr_source = aliased(MappingReview)` with `mr_source.id == mr_target.id` same-row condition. Logic preserved.
- why the change was necessary
- Same table joined twice requires distinct aliases; same-row condition preserves the original single-mapping-row intent.
- how it was verified
- `test_obligation_coverage_calculation` + `test_build_traceability_chain` pass; later full 7-test analytics/agent/traceability subset passes.
- exact problem fixed
- **P4 — Time-dependent tests.**
- file(s) changed
- `backend/tests/test_core.py`.
- what was changed
- Added `datetime` imports; effectiveness fixture → `frequency="quarterly"`, `next_test_date=today+90d`, `collected_at=now(UTC)`; gap overdue → `today-30d`, gap exception → `today-5d`; tool exception → `today-5d`.
- why the change was necessary
- Tests must be date-relative; `daily`+3 rows could never reach the asserted ≥80% rate. Production logic untouched.
- how it was verified
- 7-test analytics/agent/traceability subset: 7 passed.
- exact problem fixed
- **P3 — pgvector binding.**
- file(s) changed
- `backend/app/services/retrieval.py`.
- what was changed
- All three `_search_*` methods: embedding list → `'[v1,v2,...]'` string + `CAST(:query_embedding AS vector)` (avoids `text()` `::` misparse); added `<alias>.embedding IS NOT NULL` guards; removed dead first SQL block referencing `dc.metadata`; added missing cast to regulatory-sections path.
- why the change was necessary
- psycopg2 sends Python lists as `numeric[]`; pgvector needs a `vector` value; `CAST()` survives SQLAlchemy parsing where `::` does not; NULL embeddings would otherwise yield NULL scores.
- how it was verified
- `py_compile` OK; real end-to-end retrieval (Phase 6) returned scored rows; mocked suite passes without HF.
- exact problem fixed
- **P5 — Test fixtures.**
- file(s) changed
- `backend/tests/test_core.py`.
- what was changed
- `metadata={}` → `chunk_metadata={}`; Evidence fixtures given `embedding=[0.1]*384`; retrieval/attribution tests monkeypatch `HybridRetriever._get_query_embedding → [0.1]*384` (no HF download).
- why the change was necessary
- Fixtures must match production schema; stubbing query embeddings makes tests deterministic and avoids 429s. Production field not renamed.
- how it was verified
- `TestRetrieval` + `TestEvidenceAttribution`: 5 passed in 0.93s (previously ~27s with HF loads); full suite 15/15.
- exact problem fixed
- **P6 — Frontend.**
- file(s) changed
- `frontend/src/app/review/page.tsx`, `frontend/src/app/traceability/page.tsx`, `frontend/src/app/investigate/page.tsx`, `frontend/src/app/audit/page.tsx`, `frontend/src/lib/api.ts`, `frontend/tsconfig.json`, `frontend/src/components/AppShell.tsx` (new), `frontend/src/app/layout.tsx`, `frontend/src/app/page.tsx`.
- what was changed
- Fixed invalid JSX `else if` → ternary; added missing `Link`, `ChevronRight`, `getSeverityColor` imports; added `target: ES2017`; added missing `InvestigationResponse`, `RetrievalResultResponse`, `MappingReviewResponse`, `AuditEventResponse.ip_address/user_agent`, `EvidenceItem.file_path` types; null-safe audit rendering; typed implicit-`any` map params; moved sidebar shell `page.tsx` → `components/AppShell.tsx`, root `page.tsx` → redirect to `/dashboard`, root layout renders `<AppShell>`.
- why the change was necessary
- Each was a genuine compile/build error; shell move preserves the existing sidebar UI while satisfying App Router page/layout contracts. No new UI added.
- how it was verified
- `npx tsc --noEmit` clean; `npm run build` success, 12 routes (audit, controls, dashboard, evidence, exceptions, investigate, obligations, regulations, review, traceability, /, _not-found).

## 5. Final Architecture
Explain:
- frontend
- Next.js 14 App Router + React 18 + Tailwind. 11 feature routes + root redirect. Shared `AppShell` sidebar/topbar from root layout. `lib/api.ts` axios client mirrors backend endpoints with typed interfaces. Recharts/lucide/date-fns for viz/icons/dates.
- backend
- FastAPI (`app/main.py`) with lifespan `init_db()`, CORS, ~40 endpoints across health, CRUD resources, analytics, traceability, investigate, documents, retrieval, agents, admin. Pydantic schemas (676 lines). Deterministic services + thin agent wrappers.
- database
- PostgreSQL 16 (local Homebrew) + `vector` 0.8.0; 15 tables; SQLAlchemy 2.0 models; `schema.sql` as Docker init reference.
- pgvector
- `Vector(384)` on `regulatory_sections.embedding`, `evidence.embedding`, `document_chunks.embedding`; HNSW `vector_cosine_ops` indexes x3.
- document ingestion
- `DocumentIngestionPipeline`: mime detect → SHA256 dedupe → parse (pdfplumber/DOCX/text) → clean → heading section detect → `RecursiveCharacterTextSplitter` (500/100) → `SentenceTransformer` batch encode → `DocumentChunk` rows with `chunk_metadata`.
- embedding model
- `all-MiniLM-L6-v2`, 384-dim, lazy-loaded singleton per `EmbeddingGenerator` instance.
- retrieval
- `HybridRetriever.retrieve()` fans out to chunk/evidence/section searches (semantic cosine + metadata filters), reranks by source priority (evidence 1.0, section 0.9, chunk 0.8), returns `RetrievalResult` with full source metadata. Note: named "hybrid" but current SQL is semantic + metadata filtering + rerank; the original tsvector lexical branch was dead code and removed.
- evidence attribution
- `EvidenceAttributor.verify_claim`: retrieves with entity-scoped filters, reports `supported/evidence_count/insufficient_evidence`, `format_citations` renders `[n]` source lines. No NLI entailment — support = retrieval hit (documented limitation).
- analytics
- Pure SQL/Python `AnalyticsEngine`: no LLM math. Coverage walks accepted mappings; effectiveness composites design/operating/evidence/freshness/execution/exception-penalty; gaps aggregate 5 gap types; dashboard rolls them up.
- agent tools
- `AgentTools` = deterministic DB/analytics/retrieval functions; 6 agent classes (`agents.py`) are thin facades + `get_agent/list_agents` registry; `/agents/{name}/run` dispatches via action map.
- investigation/LLM layer
- Keyword router (control+evidence / obligation+coverage / exception / trace → tools, else general retrieval) + `_generate_answer` template composer. **Stub/mock mode** — no model call (see §11).

## 6. End-to-End Data Flow
Explain the complete flow:

document
→ ingestion
→ parsing
→ cleaning
→ chunking
→ embedding
→ PostgreSQL/pgvector
→ query
→ retrieval
→ evidence attribution
→ analytics/agent
→ investigation
→ frontend

Only describe components that actually work.
- `document` — a `.txt`/`.pdf`/`.docx` file on disk (verified with 4 `.txt` samples).
- `→ ingestion` — `POST /documents/ingest` or `ingest_sample_documents()` creates `documents` row (`processing`), dedupes by SHA256.
- `→ parsing` — `DocumentParser` returns `(text, page)` tuples (txt verified).
- `→ cleaning` — `TextCleaner` strips control chars/BOM, normalizes whitespace.
- `→ chunking` — `SectionDetector` finds headings; `Chunker` splits to ~500-char overlapping chunks with section/page/char offsets + token estimate.
- `→ embedding` — `EmbeddingGenerator` (`all-MiniLM-L6-v2`) batch-encodes chunk texts → 384-float lists.
- `→ PostgreSQL/pgvector` — `document_chunks` rows with `embedding vector(384)` + `chunk_metadata`; verified 121/121 embedded.
- `→ query` — user question via `/retrieval/search`, `/investigate`, or frontend Investigate page.
- `→ retrieval` — query embedded (same model), `CAST(:q AS vector)` cosine search with metadata filters + `IS NOT NULL` guards, reranked. Verified live: "data protection principles" → 5 chunks with scores/titles/sections/pages.
- `→ evidence attribution` — `verify_claim` returns support flag + evidence dicts + `insufficient_evidence`; `format_citations` renders sources. Verified live.
- `→ analytics/agent` — deterministic coverage/effectiveness/gaps/traceability via `AnalyticsEngine`/`AgentTools` (verified via tests + live `/analytics/*`).
- `→ investigation` — router selects tools, `_generate_answer` composes a **template summary** (stub) over the real evidence payload.
- `→ frontend` — Investigate page posts question, renders answer + confidence + tools-used + evidence cards with scores/sources; Dashboard/Traceability/Review pages render analytics chains.

## 7. Database
Document:
- PostgreSQL version/environment
- Local: Homebrew PostgreSQL 16.15. Docker compose targets `pgvector/pgvector:pg16` (unverified here — no daemon).
- pgvector version
- `0.8.0` in both `controllens` and `controllens_test` (hand-built from source for PG16 locally; official image in compose).
- tables
- 15: regulations, regulatory_sections, obligations, policies, processes, controls, control_owners, evidence, transactions, exceptions, risk_assessments, mapping_reviews, audit_events, documents, document_chunks.
- important relationships
- regulation 1—∞ sections/obligations; section 1—∞ obligations; process/policy 1—∞ controls; control 1—∞ owners/evidence/transactions/exceptions; obligation/process/control 1—∞ exceptions; document 1—∞ chunks. MappingReview and RiskAssessment are **polymorphic** (`*_type` + `*_id`, no FKs) queried explicitly; RiskAssessment/MappingReview ORM convenience relationships were intentionally removed (they crashed mapper configuration).
- vector dimension
- **384** everywhere (model, config, SQLAlchemy, DDL, live `atttypmod=384`).
- embedding column(s)
- `regulatory_sections.embedding`, `evidence.embedding`, `document_chunks.embedding` — all `vector(384)`, nullable.
- indexes
- B-tree on status/FK/date/risk columns; HNSW `vector_cosine_ops` on all 3 embedding columns; composite `(entity_type, entity_id)` and `(source_entity_type, source_entity_id)` / target equivalents.
- views
- `v_obligation_coverage`, `v_control_effectiveness`, `v_exception_trends`, `v_evidence_freshness`.
- triggers if applicable
- `update_*_updated_at` triggers on 11 tables; `log_audit_event()` function (used by mapping-review endpoint).

## 8. Machine Learning / Embeddings
Document:
- embedding model
- `sentence-transformers/all-MiniLM-L6-v2`, verified by loading the model and reading `384` from its pooling layer + encoded shape `(1, 384)`.
- why 384 dimensions are used
- Because that is the model's native output width. Nothing was chosen or tuned; 1536 (OpenAI-scale) never applied here. Schema/SQLAlchemy/config were aligned **down to the model**, not the reverse.
- how embeddings are generated
- `EmbeddingGenerator.embed(texts)` → `model.encode(texts, convert_to_numpy=True, show_progress_bar=False).tolist()`; ingestion batch-encodes all chunk texts at once.
- where embeddings are stored
- pgvector `vector(384)` columns listed in §7; live count 121/121 chunks embedded.
- how query embeddings are generated
- Identical model + method in `HybridRetriever._get_query_embedding` (single-text encode). Tests monkeypatch this to `[0.1]*384` for determinism.
- how similarity is calculated
- Postgres `embedding <=> query` (cosine distance) → `1 - distance` as `semantic_score`, `ORDER BY semantic_score DESC LIMIT n`.
- limitations
- Model loader instantiates `SentenceTransformer` per call (no shared singleton/cache) — verified 4 loads in one script; slow + HF 429-prone under load. No GPU, no batching at query time, no embedding version tracking, NULL embeddings excluded from search.

## 9. RAG / Retrieval
Explain:
- document ingestion
- Verified live: 4 sample docs → 10/5/51/55 chunks (121 total), all `completed`, all embedded.
- chunking
- 500-char recursive splits, 100 overlap, with section title/number, page, char offsets, token estimate, `chunk_metadata {section_level, chunk_index}`.
- retrieval
- Per-source parameterized SQL with metadata filters + `embedding IS NOT NULL` + cosine ordering + limit; Python-side source-priority rerank.
- hybrid retrieval if implemented
- **Partially.** The name says hybrid, but the shipped implementation is semantic-vector + metadata-filter + rerank. A tsvector lexical branch existed only as dead/overwritten SQL and was removed rather than repaired. Do not present lexical fusion as working.
- similarity search
- Verified live with real 384-dim query embedding: top hit 0.5402 "Data Protection Policy v2.3 / Principles / p1".
- evidence attribution
- `supported = len(results) > 0`; `insufficient_evidence = not supported`; citations include doc/section/page or evidence/control/type or regulation/section. Verified live (`supported=True, count=10`).
- metadata
- Every `RetrievalResult` carries `document_id/title`, `section_title/number`, `page_number`, `control_id`, `evidence_type`, `regulation_id` plus raw `metadata` JSON.
- citations/source references
- `format_citations` verified: `[1] Document: Data Protection Policy v2.3, Section: Principles, Page: 1 ...`.
- known limitations
- No lexical fusion, no cross-encoder rerank, no entailment check (retrieval-hit = "supported"), per-call model loads, NULL-embedding rows invisible to search, no pagination cursors.

## 10. Agent Architecture
List:
- available tools
- `search_regulation`, `get_regulation_sections`, `get/search_obligation(s)`, `get_obligation_coverage`, `get_weak_obligations`, `get/search_policy(ies)`, `get_process`, `get/search_control(s)`, `get_control_effectiveness`, `get_overdue_controls`, `search_evidence`, `get_evidence_completeness`, `get_stale_evidence`, `query_transactions`, `get_high_risk_transactions`, `analyze_exceptions`, `get_open_exceptions`, `build_traceability_chain`, `get_mapping_reviews`, `get_proposed_mappings`, `get_risk_assessment`, `get_high_risk_entities`, `get_audit_trail`.
- what each tool does
- Thin deterministic wrappers: filtered SQLAlchemy queries or `AnalyticsEngine` computations or `HybridRetriever` searches; see `tools.py` docstrings. No LLM inside tools.
- what data each tool accesses
- The tool's entity tables + join tables (`mapping_reviews` for links, `evidence`/`exceptions` for effectiveness, `transactions` for anomaly queries).
- how the agent uses tools
- `/investigate` keyword-routes to 1+ tools, `/agents/{name}/run` dispatches `action → method(**parameters)`. The 6 agent classes add narrative wrappers (e.g. ReportAgent recommendations) over tool outputs.
- error handling
- Unknown agent/action → 400; tool exception → 500 with message; missing entity → tool returns `None`/`{"error": ...}` and endpoint maps to 404 where applicable; retrieval with no rows → `insufficient_evidence` path rather than exception.
- what is real vs mocked
- Real: all tools, analytics, retrieval, attribution. Mocked/stub: the final natural-language answer composer (templates, not an LLM).

## 11. LLM / Nemotron Status
Be completely honest.

State:
- whether real Nemotron inference is implemented
- **NO.** No real Nemotron (or any LLM) inference exists in this codebase.
- model/API used
- None called. `httpx==0.26.0` is installed but never used for LLM calls; no `chat.completions`, no `requests.post`, no API-key header code exists.
- configuration
- `config.py` / `.env.example` / `compose` carry `LLM_MODEL=nvidia/nemotron-3-ultra`, `LLM_BASE_URL=https://integrate.api.nvidia.com/v1`, `LLM_API_KEY` — all inert.
- how prompts are constructed
- They are not. There is no prompt template, system message, or context serializer for an LLM.
- how retrieved evidence is supplied
- It is not supplied to any model. Evidence is returned to the API caller alongside a template string.
- fallback/mock behavior
- The **only** behavior: `_generate_answer()` returns "Insufficient evidence..." when empty, else `Found N relevant results...` / traceability counts. This is clearly labeled "placeholder for LLM" in code.
- what remains if integration is incomplete
- API-key handling, prompt builder (question + evidence JSON + citations instruction), Nemotron chat call with timeout/retry/auth-error mapping, streaming (optional), answer-vs-evidence consistency check, cost/latency logging, eval harness. Do not demo this as "Nemotron-powered."

## 12. API Inventory
Create a table:

Endpoint | Method | Purpose | Verified? | Result

Include all important endpoints.

| Endpoint | Method | Purpose | Verified? | Result |
|---|---|---|---|---|
| /health | GET | Liveness + DB check | YES (live) | 200 `{"status":"ok","database":"healthy"}` |
| /api/v1/openapi.json | GET | Schema/docs | YES (live) | 200 |
| /api/v1/regulations | GET/POST | List/create regulations | CODE ONLY | Not live-tested (no seed) |
| /api/v1/regulations/{id} | GET/PATCH | Read/update regulation | CODE ONLY | — |
| /api/v1/regulations/{id}/sections | GET | Regulation sections | CODE ONLY | — |
| /api/v1/obligations | GET/POST | List/create obligations | CODE ONLY | — |
| /api/v1/obligations/{id} | GET | Read obligation | CODE ONLY | — |
| /api/v1/obligations/{id}/coverage | GET | Single-obligation coverage | CODE (via tests) | Analytics logic passes |
| /api/v1/policies | GET/POST | List/create policies | CODE ONLY | — |
| /api/v1/policies/{id} | GET | Read policy | CODE ONLY | — |
| /api/v1/processes | GET/POST | List/create processes | CODE ONLY | — |
| /api/v1/processes/{id} | GET | Read process | CODE ONLY | — |
| /api/v1/controls | GET/POST | List/create controls | CODE ONLY | — |
| /api/v1/controls/{id} | GET | Read control + owners | CODE ONLY | — |
| /api/v1/controls/{id}/effectiveness | GET | Effectiveness composite | CODE (via tests) | Logic passes |
| /api/v1/evidence | GET/POST | List/create evidence | CODE ONLY | — |
| /api/v1/evidence/{id} | GET | Read evidence | CODE ONLY | — |
| /api/v1/transactions | GET/POST | Query/create transactions | CODE ONLY | — |
| /api/v1/exceptions | GET/POST | List/create exceptions | CODE ONLY | — |
| /api/v1/exceptions/{id} | GET/PATCH | Read/update exception | CODE ONLY | — |
| /api/v1/risk-assessments | GET/POST | List/create risk assessments | CODE ONLY | — |
| /api/v1/mapping-reviews | GET/POST | List/propose mappings | CODE ONLY | — |
| /api/v1/mapping-reviews/{id} | PATCH | Human accept/reject + audit log | CODE ONLY | — |
| /api/v1/audit | GET | Audit trail | CODE ONLY | — |
| /api/v1/analytics/dashboard | GET | Dashboard rollup | YES (live) | 200, zeros (no seed data) |
| /api/v1/analytics/obligation-coverage | GET | Coverage analysis | YES (tests) | Pass |
| /api/v1/analytics/control-coverage | GET | Control coverage | YES (tests) | Pass |
| /api/v1/analytics/evidence-completeness | GET | Completeness | YES (tests) | Pass |
| /api/v1/analytics/evidence-freshness | GET | Freshness | YES (tests) | Pass |
| /api/v1/analytics/risk-exposure | GET | Risk exposure | YES (tests) | Pass |
| /api/v1/analytics/gaps | GET | Unresolved gaps | YES (live+tests) | Live 200 `total_gaps:0`; logic passes |
| /api/v1/analytics/trends | GET | Weekly trends | CODE ONLY | — |
| /api/v1/traceability/{obligation_id} | GET | Full chain | YES (tests) | Pass |
| /api/v1/investigate | POST | Tool-routed investigation | YES (live) | 200, 10 evidence, stub answer |
| /api/v1/documents | GET/POST | List/create docs | CODE ONLY | — |
| /api/v1/documents/{id} | GET | Read doc | CODE ONLY | — |
| /api/v1/documents/{id}/chunks | GET | Doc chunks | CODE ONLY | — |
| /api/v1/documents/ingest | POST | Ingest file | YES (direct call) | 4 docs, 121 chunks |
| /api/v1/retrieval/search | POST | Hybrid search | YES (direct call) | 5 scored chunks live |
| /api/v1/agents | GET | List agents | CODE ONLY | — |
| /api/v1/agents/{name}/run | POST | Run agent action | CODE (via tools tests) | Tools pass |
| /api/v1/admin/generate-data | POST | Seed synthetic data | NOT RUN | Seed not executed (regulations/controls = 0) |
| /api/v1/admin/ingest-samples | POST | Ingest samples | YES (direct call) | Equivalent function verified |

## 13. Frontend
Document:
- framework
- Next.js 14.2 App Router, React 18, Tailwind, axios, recharts, lucide-react, date-fns, clsx/tailwind-merge. `target: ES2017`.
- pages/routes
- 12 built routes: `/` (→/dashboard redirect), `/dashboard`, `/regulations`, `/obligations`, `/controls`, `/evidence`, `/exceptions`, `/traceability`, `/review`, `/investigate`, `/audit`, `/_not-found`. Shared `AppShell` sidebar/topbar via root layout.
- API communication
- `NEXT_PUBLIC_API_URL` (default `http://localhost:8000/api/v1`) + `next.config.js` `/api/v1/* → localhost:8000` rewrite; typed `ApiClient` mirrors backend.
- charts
- Recharts dependency present; dashboard verified as metric cards/alerts/quick-links/coverage summary (chart-heavy trend views exist in analytics API, UI wiring not separately verified beyond build).
- analytics views
- Dashboard, obligations coverage table, traceability chain, review queue, audit trail pages exist and compile.
- investigation UI
- Posts question, shows answer/confidence/tools-used/evidence cards with scores and source metadata.
- error/loading handling
- Dashboard shows loading skeletons + error card with retry; audit/evidence lists show empty states.
- build result
- `npx tsc --noEmit`: **clean**. `npm run build`: **success**, 12/12 static routes, First Load ~87–125 kB.

## 14. Testing
Report:
- total tests
- **15** (`pytest --collect-only`).
- passed
- **15** (`pytest tests/test_core.py -q`: `15 passed in 0.52–0.65s`, re-run twice).
- failed
- **0** (final state).
- skipped
- 0.
- warnings
- Only HF Hub "unauthenticated requests" warnings during the one live-model verification (not in suite; suite is mocked).
- important test categories
- Database CRUD 3/3; Analytics 4/4 (coverage, effectiveness, completeness, gaps); Retrieval 2/2 (mocked, deterministic); Traceability 1/1; AgentTools 2/2; Attribution 3/3.
- any tests not executed and why
- No live-model suite exists by design; the single live RAG verification (ingest + real retrieval + attribution) was executed once via scripts (not as a pytest) to avoid repeated HF downloads/429s. Full synthetic seed (`generate_data.py`) was not executed, so analytics-on-seed-data is covered only by unit fixtures.

## 15. Security
Document:
- environment variables
- `DATABASE_URL`, `POSTGRES_PASSWORD`, `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`, `SECRET_KEY`, `NEXT_PUBLIC_API_URL`, optional SMTP/S3 — all via env with `.env.example` placeholders.
- secret handling
- No `.env` file exists in repo; git history contains no secrets (verified `git status` shows no `.env`/secret matches; `.gitignore` covers `.env*`).
- .gitignore
- Covers `node_modules/`, `__pycache__/`, `.pytest_cache/`, `.next/`, `*.tsbuildinfo`, `.env*`, logs, coverage, sqlite, IDE/OS artifacts.
- API validation
- Pydantic request/response models on all routes; query limits (`le=100/200/500`); 404s on missing entities; mapping-review PATCH requires `user_id`/`user_role` query params and writes audit rows.
- database security considerations
- Local dev uses trust-auth `controllens:controllens`; production must rotate `POSTGRES_PASSWORD`/`SECRET_KEY`, restrict CORS origins (currently localhost), and put Postgres behind private networking (compose exposes 5432 for dev).
- known security limitations
- No authN/authZ (no login, JWT, or RBAC); no rate limiting; `SECRET_KEY` default is a dev placeholder; LLM key handling unimplemented (no model calls yet); file-ingest takes server-local paths (no upload sandboxing).

## 16. Docker / Deployment
Document:
- Dockerfiles
- `backend/Dockerfile` (python:3.11-slim, gcc/libpq/curl, pip install, non-root `appuser`, port 8000, healthcheck on `/health`); `frontend/Dockerfile` (node:20-alpine multi-stage, standalone output, non-root `nextjs`, port 3000).
- docker-compose
- `postgres` (`pgvector/pgvector:pg16`, volume `postgres_data`, schema.sql init, healthcheck), `backend` (uvicorn reload, depends on postgres healthy), `frontend` (`npm run dev`, depends on backend).
- services
- postgres :5432, backend :8000, frontend :3000.
- ports
- As above.
- environment variables
- Compose reads `POSTGRES_PASSWORD`, `LLM_API_KEY/BASE_URL/MODEL`, `SECRET_KEY`; frontend `NEXT_PUBLIC_API_URL`.
- database
- Container DB would init `vector` extension + schema via `schema.sql` mount (matches local verified versions).
- what was actually verified
- **Nothing via Docker.** `docker` binary is absent in this environment (`command not found`).
- what remains unverified because of environment limitations
- **UNVERIFIED — ENVIRONMENT LIMITATION**: `docker compose build/up`, container healthchecks, init-script bootstrap, inter-service networking, production frontend `standalone` serve. Do not claim Docker works.

## 17. Git / Repository
Document:
- repository initialized?
- Yes, in Phase 9. Two commits: `07160c3` (working project) + `a20d2a9` (tsbuildinfo gitignore). Final `git status` clean at commit time.
- commit status
- `main` @ `a20d2a9`; working tree clean except this report file when written (to be committed by maintainer).
- important files
- 52 tracked files including backend app/services/tests, frontend src, compose, Dockerfiles, README, `.env.example`, `.gitignore`.
- files excluded by .gitignore
- Verified absent from tracking: `node_modules/`, `.next/`, `__pycache__/`, `.pytest_cache/`, `*.tsbuildinfo`, `.env*`, logs.
- secrets excluded?
- Yes — no `.env` file exists; staged set contained only `.env.example` (placeholders); grep for secret/token/password filenames in status: clean.

## 18. Known Limitations
Be explicit about:
- dataset size
- Live DB has **only** 4 sample docs / 121 chunks; zero regulations/obligations/controls/policies (synthetic seeder never run). All analytics-on-empty-DB return zeros — correct but unimpressive for demo.
- model limitations
- `all-MiniLM-L6-v2` is a small general English model; no domain fine-tuning; no multilingual guarantee; per-call loader (slow, 429-prone); 384-dim fixed.
- mock/stub functionality
- Investigation answers are templates; agent "reasoning" is keyword routing + wrappers; attribution `supported` = retrieval hit (no entailment model).
- local environment limitations
- Homebrew PG16 + hand-built pgvector (non-reproducible); no Docker daemon; no GPU; HF cache required for offline model loads.
- Docker limitations
- Fully unverified (see §16).
- HF/API rate limits
- Live embedding loads hit `huggingface.co` without token (warnings observed); suite avoids this via monkeypatched stub embeddings; repeated live loads must not be looped (prior audit hit 429s).
- production-readiness limitations
- No auth, no migrations (`alembic/versions` empty), no pagination cursors, no upload sandbox, no TLS, no monitoring/logging infra, no backup story, dev CORS/secrets.

## 19. Remaining Work
Separate into:

CRITICAL
- Run `scripts/generate_data.py` seeder and re-verify analytics/gaps/dashboard with non-zero data (currently all zeros live).
- Wire real Nemotron (or formally descope it): prompt builder, API call, evidence injection, error/timeout handling, eval — or remove "Nemotron" from user-facing claims.
- Add `SentenceTransformer` singleton/cache (one load per process) to eliminate per-query loads + 429 exposure.
- Create Alembic baseline migration (`alembic init` env + autogenerate + `upgrade head` test).
- Verify `docker compose up` + healthchecks on a Docker host (currently impossible here).

HIGH
- Restore a true hybrid lexical branch (tsvector) with tests, or rename "hybrid" to "semantic + metadata" everywhere including README.
- Add entailment/NLI check to `verify_claim` (currently retrieval-hit).
- Paginate list endpoints consistently on frontend (large datasets will stall).
- Add authN/authZ (even basic API key or OAuth) before any shared deployment.
- Commit this report + seeder outputs; tag `v0.1-mvp`.

MEDIUM
- Upload-based document ingest (currently server-local path only).
- HNSW tuning (`m`, `ef_construction`) + `VACUUM ANALYZE` after bulk ingest.
- Embedding version column + re-embed job.
- Trend charts wiring on dashboard from `/analytics/trends`.
- README refresh to match stub-vs-real status (especially LLM + hybrid claims).

FUTURE ENHANCEMENT
- Multi-tenancy, RBAC roles, SSO.
- Regulatory source connectors (EUR-Lex/SEC), change monitoring.
- FAIR risk quantification, control test scheduling, PDF/Excel export, ServiceNow/Jira webhooks, mobile polish, >80% coverage, query caching.

## 20. Final Completion Assessment
Give:
- completion percentage
- **85%**
- final classification
- **MVP NEARLY COMPLETE**
- exact evidence supporting that classification
- Backend boots + `/health` 200 + OpenAPI 200 (live). 15/15 pytest pass (0.52s). RAG live: 4 docs → 121 chunks, 121/121 embedded, 384-dim confirmed in SQL, real query → 5 scored chunks, attribution `supported=True` with citations, live `/investigate` → 10 evidence items. `tsc` clean + `next build` 12/12 routes. Git clean with 2 commits, no secrets. Missing for COMPLETE: seeded business data (zeros live), real LLM, Docker verification, Alembic baseline — all documented, none hidden.
- whether the project is demo-ready
- **PARTIAL.** RAG + traceability + analytics-code + UI-build demo well; but empty business tables + stub answers + unverified Docker mean a live stakeholder demo needs the seeder run first and an honesty slide on Nemotron.
- whether it is resume-ready
- **YES WITH LIMITATIONS.** Strong evidence-backed story (pgvector 384 audit, DuplicateAlias fix, CAST-vs-`::` diagnosis, deterministic tests, live RAG numbers) provided the limitations section travels with it.
- what must be fixed before an interview/demo
- Run seeder; either wire Nemotron or relabel Investigate as "retrieval + template summary (LLM-ready)"; rehearse the 429/rate-limit answer; bring Docker-host evidence or mark it unverified.
- what can safely remain future work
- Auth, migrations automation beyond baseline, lexical fusion, NLI attribution, exports/webhooks, multi-tenancy.

## 21. Reproduction Guide
Provide exact commands for:
- installation
- `brew install postgresql@16` (+ pgvector 0.8.0 built for PG16, see §7 note); `cd backend && pip install -r requirements.txt`; `cd ../frontend && npm install`.
- environment setup
- `cp .env.example .env` (fill `POSTGRES_PASSWORD`, `SECRET_KEY`; `LLM_API_KEY` optional/unused); `brew services start postgresql@16`.
- database setup
- `createdb -O controllens controllens controllens_test`; `psql -d <db> -c "CREATE EXTENSION IF NOT EXISTS vector;"` (both DBs).
- seeding
- `cd backend && python3 scripts/generate_data.py` (NOT run in this finalization — do it before demo).
- ingestion
- `python3 -c "from app.db.base import SessionLocal; from app.services.document_pipeline import ingest_sample_documents; db=SessionLocal(); print(len(ingest_sample_documents(db))))"` → expect 4 docs / 121 chunks.
- backend startup
- `cd backend && python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8001` → `curl http://127.0.0.1:8001/health` → 200.
- frontend startup
- `cd frontend && npm run dev` → http://localhost:3000 (rewrites `/api/v1/*` to backend).
- tests
- `cd backend && python3 -m pytest tests/test_core.py -q` → expect `15 passed`.
- build
- `cd frontend && npx tsc --noEmit` (clean) `&& npm run build` (12 routes).
- Docker startup if verified
- **UNVERIFIED — ENVIRONMENT LIMITATION**: `docker compose up --build` was never run here (no daemon). On a Docker host: `cp .env.example .env && docker compose up --build`, then `curl localhost:8000/health`.

## 22. Interview Preparation Summary
Create concise explanations of:
- why PostgreSQL
- One store for relational compliance data + vectors avoids a second database; JSONB for metadata, views for analytics, triggers for audit timestamps, B-tree + HNSW in one engine.
- why pgvector
- Native `vector(384)` type + `<=>` cosine operator + HNSW `vector_cosine_ops` indexes keeps similarity search transactional and filterable alongside metadata (no sync jobs to an external index).
- why 384-dimensional embeddings
- Not a choice: `all-MiniLM-L6-v2` natively emits 384 floats (verified from pooling layer + `(1,384)` encode shape). Schema, SQLAlchemy `Vector(384)`, config, and live `atttypmod=384` were aligned to the model. 1536 belongs to a different (OpenAI-scale) model family and was never used here.
- how RAG works here
- Ingest → parse/clean → heading sections → 500/100 recursive chunks with offsets → batch-encode with MiniLM → `document_chunks` rows → query-encode same model → cosine search with metadata filters → rerank → attribute/cite. Verified: 4 docs, 121 chunks, live top hit 0.54 "Data Protection Policy / Principles".
- how retrieval works
- Parameterized SQL per source, `embedding IS NOT NULL` guards, `CAST(:q AS vector)` (because SQLAlchemy `text()` misparses `::` casts and psycopg2 lists arrive as `numeric[]`), `ORDER BY 1-distance LIMIT n`, then source-priority rerank (evidence > section > chunk).
- how evidence attribution works
- Entity-scoped retrieval; `supported = hits > 0`, else explicit `insufficient_evidence`; citations formatted with doc/section/page or control/evidence-type. Honest limitation: no NLI — a hit counts as support.
- how agent tools work
- Deterministic functions only (SQLAlchemy queries + analytics math + retriever). Agents are thin facades; the API dispatches `agent/action → method`. The LLM (when added) would only reason over tool outputs, never compute metrics.
- how analytics are calculated
- SQL counts + Python rollups, zero LLM involvement. Coverage walks accepted `mapping_reviews`; effectiveness = weighted design/operating/evidence/freshness/execution/exception-penalty; gaps union 5 detectors; dashboard sums them.
- how frontend/backend communicate
- Typed axios client (`NEXT_PUBLIC_API_URL`) + Next rewrite fallback; dashboard/traceability/review/investigate pages consume analytics/traceability/mapping/investigation endpoints; build-time verified, runtime dashboard fetch verified against live backend.
- what the main engineering challenges were
- (1) `langchain` vs `langchain_text_splitters` import split killing startup; (2) self-join `DuplicateAlias` on polymorphic mapping table fixed with `aliased()` + same-row condition; (3) `vector <=> numeric[]` + `::` misparse fixed with string-serialized vectors + `CAST()`; (4) `metadata`→`chunk_metadata` rename fallout across SQL/tests; (5) time-bomb 2024 test dates vs 2026 clock; (6) HF 429 avoidance via stubbed query embeddings in tests + single live verification; (7) App Router page-vs-layout contract for the sidebar shell.
- what limitations remain
- Stub investigation answers (no Nemotron call), semantic+metadata only (no lexical fusion), retrieval-hit attribution, empty business seed, per-call model loads, no auth/migrations/Docker proof. All are listed in §18–19 with concrete next steps.
