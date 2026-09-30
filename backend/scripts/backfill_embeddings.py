"""Backfill pgvector embeddings for document_chunks rows with NULL embedding.

Only touches rows WHERE embedding IS NULL. Uses the project's pinned
model (all-MiniLM-L6-v2, 384-dim) in batches with a single model load.
Safe to re-run: already-embedded rows are skipped.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sentence_transformers import SentenceTransformer
from app.db.base import SessionLocal, DocumentChunk

MODEL_NAME = "all-MiniLM-L6-v2"
BATCH_SIZE = 32


def main() -> None:
    db = SessionLocal()
    try:
        rows = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.embedding.is_(None))
            .order_by(DocumentChunk.document_id, DocumentChunk.chunk_index)
            .all()
        )
        print(f"Chunks missing embeddings: {len(rows)}")
        if not rows:
            return

        print(f"Loading {MODEL_NAME} (once)...")
        model = SentenceTransformer(MODEL_NAME)

        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i : i + BATCH_SIZE]
            vectors = model.encode(
                [r.content for r in batch],
                convert_to_numpy=True,
                show_progress_bar=False,
            ).tolist()
            for row, vec in zip(batch, vectors):
                assert len(vec) == 384, f"unexpected dim {len(vec)}"
                row.embedding = vec
            db.commit()
            print(f"  embedded {min(i + BATCH_SIZE, len(rows))}/{len(rows)}")

        remaining = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.embedding.is_(None))
            .count()
        )
        print(f"Done. Still missing: {remaining}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
