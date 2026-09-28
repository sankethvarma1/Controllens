"""
RAG Retrieval System for CONTROLLENS
Hybrid retrieval: semantic + metadata filtering + lexical matching
"""
from datetime import date
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from sqlalchemy import text, func, and_, or_
from sqlalchemy.orm import Session
import numpy as np

from app.db.base import DocumentChunk, Evidence, RegulatorySection, SessionLocal


@dataclass
class RetrievalResult:
    """Result from retrieval with source metadata."""
    id: str
    content: str
    score: float
    source_type: str  # 'document_chunk', 'evidence', 'regulatory_section'
    source_id: str
    metadata: Dict[str, Any]
    
    # Source-specific fields
    document_id: Optional[str] = None
    document_title: Optional[str] = None
    section_title: Optional[str] = None
    section_number: Optional[str] = None
    page_number: Optional[int] = None
    control_id: Optional[str] = None
    evidence_type: Optional[str] = None
    regulation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "score": round(self.score, 4),
            "source_type": self.source_type,
            "source_id": self.source_id,
            "metadata": self.metadata,
            "document_id": self.document_id,
            "document_title": self.document_title,
            "section_title": self.section_title,
            "section_number": self.section_number,
            "page_number": self.page_number,
            "control_id": self.control_id,
            "evidence_type": self.evidence_type,
            "regulation_id": self.regulation_id
        }


class HybridRetriever:
    """Hybrid retrieval combining semantic, lexical, and metadata filtering."""
    
    def __init__(self, db: Session):
        self.db = db
        self.default_limit = 10
    
    def retrieve(self, query: str, 
                 filters: Optional[Dict[str, Any]] = None,
                 limit: int = None,
                 source_types: Optional[List[str]] = None) -> List[RetrievalResult]:
        """
        Hybrid retrieval across all sources.
        
        Args:
            query: Search query
            filters: Metadata filters (e.g., {"regulation_id": "REG_GDPR", "control_id": "CTL_001"})
            limit: Max results
            source_types: Limit to specific sources ['document_chunk', 'evidence', 'regulatory_section']
        
        Returns:
            List of RetrievalResult with scores and source metadata
        """
        limit = limit or self.default_limit
        source_types = source_types or ['document_chunk', 'evidence', 'regulatory_section']
        
        all_results = []
        
        if 'document_chunk' in source_types:
            all_results.extend(self._search_document_chunks(query, filters, limit))
        
        if 'evidence' in source_types:
            all_results.extend(self._search_evidence(query, filters, limit))
        
        if 'regulatory_section' in source_types:
            all_results.extend(self._search_regulatory_sections(query, filters, limit))
        
        # Combine and re-rank
        combined = self._rerank_results(all_results, query)
        
        return combined[:limit]
    
    def _search_document_chunks(self, query: str, filters: Dict, limit: int) -> List[RetrievalResult]:
        """Search document chunks with semantic + metadata filtering."""
        # Build filter conditions
        # Only rows with embeddings can be scored with pgvector cosine distance.
        where_conditions = ["dc.embedding IS NOT NULL"]
        params = {"query": query, "limit": limit}
        
        if filters:
            if filters.get("document_id"):
                where_conditions.append("dc.document_id = :document_id")
                params["document_id"] = filters["document_id"]
            if filters.get("document_type"):
                where_conditions.append("d.document_type = :document_type")
                params["document_type"] = filters["document_type"]
            if filters.get("source"):
                where_conditions.append("d.source = :source")
                params["source"] = filters["source"]
        
        where_clause = " AND ".join(where_conditions)
        
        # Semantic search with pgvector cosine distance.
        # NOTE: use CAST(... AS vector) instead of ::vector because SQLAlchemy
        # text() treats ':' as a bind-param prefix and misparses '::' casts.
        # The embedding is passed as a '[v1,v2,...]' string which pgvector parses.
        query_embedding = self._get_query_embedding(query)
        
        sql = f"""
            SELECT 
                dc.id,
                dc.content,
                dc.section_title,
                dc.section_number,
                dc.page_number,
                dc.chunk_metadata,
                d.id as document_id,
                d.title as document_title,
                d.source,
                d.document_type,
                1 - (dc.embedding <=> CAST(:query_embedding AS vector)) as semantic_score
            FROM document_chunks dc
            JOIN documents d ON d.id = dc.document_id
            WHERE {where_clause}
            ORDER BY semantic_score DESC
            LIMIT :limit
        """
        
        params["query_embedding"] = "[" + ",".join(map(str, query_embedding)) + "]"
        
        results = self.db.execute(text(sql), params).fetchall()
        
        return [
            RetrievalResult(
                id=row.id,
                content=row.content,
                score=float(row.semantic_score),
                source_type="document_chunk",
                source_id=row.id,
                metadata=row.chunk_metadata or {},
                document_id=row.document_id,
                document_title=row.document_title,
                section_title=row.section_title,
                section_number=row.section_number,
                page_number=row.page_number,
                regulation_id=row.source
            )
            for row in results
        ]
    
    def _search_evidence(self, query: str, filters: Dict, limit: int) -> List[RetrievalResult]:
        """Search evidence records."""
        where_conditions = ["e.status = 'verified'", "e.embedding IS NOT NULL"]
        params = {"query": query, "limit": limit}
        
        if filters:
            if filters.get("control_id"):
                where_conditions.append("e.control_id = :control_id")
                params["control_id"] = filters["control_id"]
            if filters.get("evidence_type"):
                where_conditions.append("e.evidence_type = :evidence_type")
                params["evidence_type"] = filters["evidence_type"]
        
        where_clause = " AND ".join(where_conditions)
        
        query_embedding = self._get_query_embedding(query)
        params["query_embedding"] = "[" + ",".join(map(str, query_embedding)) + "]"
        
        sql = f"""
            SELECT 
                e.id,
                e.title,
                e.description,
                e.evidence_type,
                e.control_id,
                e.collected_at,
                e.period_start,
                e.period_end,
                e.source_system,
                c.name as control_name,
                1 - (e.embedding <=> CAST(:query_embedding AS vector)) as semantic_score
            FROM evidence e
            JOIN controls c ON c.id = e.control_id
            WHERE {where_clause}
            ORDER BY semantic_score DESC
            LIMIT :limit
        """
        
        results = self.db.execute(text(sql), params).fetchall()
        
        return [
            RetrievalResult(
                id=row.id,
                content=f"{row.title}\n{row.description}" if row.description else row.title,
                score=float(row.semantic_score),
                source_type="evidence",
                source_id=row.id,
                metadata={
                    "evidence_type": row.evidence_type,
                    "collected_at": row.collected_at.isoformat() if row.collected_at else None,
                    "period_start": row.period_start.isoformat() if row.period_start else None,
                    "period_end": row.period_end.isoformat() if row.period_end else None,
                    "source_system": row.source_system,
                    "control_name": row.control_name
                },
                control_id=row.control_id,
                evidence_type=row.evidence_type
            )
            for row in results
        ]
    
    def _search_regulatory_sections(self, query: str, filters: Dict, limit: int) -> List[RetrievalResult]:
        """Search regulatory sections."""
        where_conditions = ["rs.embedding IS NOT NULL"]
        params = {"query": query, "limit": limit}
        
        if filters:
            if filters.get("regulation_id"):
                where_conditions.append("rs.regulation_id = :regulation_id")
                params["regulation_id"] = filters["regulation_id"]
            if filters.get("section_type"):
                where_conditions.append("rs.section_type = :section_type")
                params["section_type"] = filters["section_type"]
        
        where_clause = " AND ".join(where_conditions)
        
        query_embedding = self._get_query_embedding(query)
        params["query_embedding"] = "[" + ",".join(map(str, query_embedding)) + "]"
        
        sql = f"""
            SELECT 
                rs.id,
                rs.content,
                rs.title,
                rs.section_number,
                rs.section_type,
                rs.page_start,
                rs.page_end,
                r.id as regulation_id,
                r.title as regulation_title,
                r.short_name,
                1 - (rs.embedding <=> CAST(:query_embedding AS vector)) as semantic_score
            FROM regulatory_sections rs
            JOIN regulations r ON r.id = rs.regulation_id
            WHERE {where_clause}
            ORDER BY semantic_score DESC
            LIMIT :limit
        """
        
        results = self.db.execute(text(sql), params).fetchall()
        
        return [
            RetrievalResult(
                id=row.id,
                content=row.content,
                score=float(row.semantic_score),
                source_type="regulatory_section",
                source_id=row.id,
                metadata={
                    "section_title": row.title,
                    "section_number": row.section_number,
                    "section_type": row.section_type,
                    "page_start": row.page_start,
                    "page_end": row.page_end,
                    "regulation_title": row.regulation_title,
                    "regulation_short_name": row.short_name
                },
                document_title=row.regulation_title,
                section_title=row.title,
                section_number=row.section_number,
                regulation_id=row.regulation_id
            )
            for row in results
        ]
    
    def _get_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for query."""
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        embedding = model.encode([query], convert_to_numpy=True)[0]
        return embedding.tolist()
    
    def _rerank_results(self, results: List[RetrievalResult], query: str) -> List[RetrievalResult]:
        """Re-rank combined results."""
        # Simple re-ranking: boost by source type priority
        source_priority = {
            "evidence": 1.0,
            "regulatory_section": 0.9,
            "document_chunk": 0.8
        }
        
        for r in results:
            r.score *= source_priority.get(r.source_type, 0.5)
        
        # Sort by adjusted score
        results.sort(key=lambda x: x.score, reverse=True)
        return results


def retrieve_evidence_for_control(db: Session, control_id: str, query: str = None) -> List[RetrievalResult]:
    """Retrieve evidence for a specific control."""
    retriever = HybridRetriever(db)
    filters = {"control_id": control_id}
    if query:
        return retriever.retrieve(query, filters=filters, source_types=["evidence"])
    else:
        # Return all verified evidence for control
        return retriever.retrieve(control_id, filters=filters, source_types=["evidence"])


def retrieve_regulation_for_obligation(db: Session, obligation_id: str) -> List[RetrievalResult]:
    """Retrieve regulatory sections for an obligation."""
    from app.db.base import Obligation
    obligation = db.query(Obligation).filter(Obligation.id == obligation_id).first()
    if not obligation:
        return []
    
    retriever = HybridRetriever(db)
    filters = {"regulation_id": obligation.regulation_id}
    return retriever.retrieve(obligation.obligation_text, filters=filters, source_types=["regulatory_section"])


def retrieve_traceability_evidence(db: Session, entity_type: str, entity_id: str) -> Dict[str, List[RetrievalResult]]:
    """Retrieve all evidence for a traceability chain."""
    retriever = HybridRetriever(db)
    results = {}
    
    if entity_type == "obligation":
        # Get obligation
        from app.db.base import Obligation
        obl = db.query(Obligation).filter(Obligation.id == entity_id).first()
        if obl:
            results["regulation"] = retriever.retrieve(
                obl.obligation_text, 
                filters={"regulation_id": obl.regulation_id},
                source_types=["regulatory_section"]
            )
    
    elif entity_type == "control":
        results["evidence"] = retriever.retrieve(
            entity_id,
            filters={"control_id": entity_id},
            source_types=["evidence"]
        )
    
    return results


class EvidenceAttributor:
    """Ensure AI responses cite retrieved evidence."""
    
    def __init__(self, db: Session):
        self.db = db
        self.retriever = HybridRetriever(db)
    
    def verify_claim(self, claim: str, entity_type: str, entity_id: str) -> Dict[str, Any]:
        """Verify if a claim is supported by retrieved evidence."""
        # Retrieve relevant evidence
        results = self.retriever.retrieve(
            claim,
            filters=self._get_filters_for_entity(entity_type, entity_id),
            source_types=["evidence", "document_chunk", "regulatory_section"],
            limit=10
        )
        
        # Check if any result supports the claim
        # In practice, you'd use an NLI model or LLM to verify entailment
        supported = len(results) > 0
        
        return {
            "claim": claim,
            "supported": supported,
            "evidence_count": len(results),
            "evidence": [r.to_dict() for r in results[:5]],
            "insufficient_evidence": not supported
        }
    
    def _get_filters_for_entity(self, entity_type: str, entity_id: str) -> Dict[str, Any]:
        """Get retrieval filters for an entity."""
        if entity_type == "control":
            return {"control_id": entity_id}
        elif entity_type == "obligation":
            from app.db.base import Obligation
            obl = self.db.query(Obligation).filter(Obligation.id == entity_id).first()
            if obl:
                return {"regulation_id": obl.regulation_id}
        elif entity_type == "policy":
            return {"document_type": "policy", "source": entity_id}
        return {}
    
    def format_citations(self, results: List[RetrievalResult]) -> str:
        """Format retrieval results as citations."""
        if not results:
            return "No supporting evidence found."
        
        citations = []
        for i, r in enumerate(results, 1):
            if r.source_type == "evidence":
                cite = f"[{i}] Evidence {r.source_id} ({r.evidence_type}): {r.metadata.get('control_name', 'N/A')}"
            elif r.source_type == "regulatory_section":
                cite = f"[{i}] {r.metadata.get('regulation_short_name', 'Regulation')} {r.section_number}: {r.section_title}"
            else:
                cite = f"[{i}] Document: {r.document_title}, Section: {r.section_title}, Page: {r.page_number}"
            citations.append(cite)
        
        return "\n".join(citations)