# ADR-012: pgvector for Embeddings over Dedicated Vector DB

- Status: Accepted
- Date: 05-10-2026
- Tags: ai, embeddings, search, database

## Context

The v6 phase introduces a RAG (Retrieval-Augmented Generation) feature that requires storing and querying vector embeddings of course materials. This requires an approximate nearest-neighbor search capability.

Dedicated vector databases (Pinecone, Weaviate, Qdrant, Chroma) are purpose- built for this, but add another operational component. Since the primary database is already PostgreSQL, the `pgvector` extension can provide vector search without adding infrastructure.

## Decision

I will use the `pgvector` PostgreSQL extension for storing and querying embeddings. Embeddings will be stored in a `vector(N)` column where N matches the dimensionality of the chosen embedding model.

- `HNSW` or `IVFFlat` indexes will be used for approximate nearest-neighbor queries depending on dataset size.
- The `pgvector` Python client (`pgvector` package) integrates with SQLAlchemy's type system.
- This decision applies to the v6 RAG feature; it does not affect FTS (ADR-011), which operates independently.
- Performance will be monitored; migration to a dedicated vector database remains an option if query latency or index build time becomes unacceptable at scale.

## Consequences

**Positive:**
- No additional service to operate; embeddings live alongside the data they describe in the same database.
- ACID transactions cover embedding inserts and updates, maintaining consistency between document content and its vector representation.
- SQLAlchemy integration is straightforward via the `pgvector` library.

**Negative:**
- `pgvector` approximate nearest-neighbor performance does not match specialized vector databases at very large scale (hundreds of millions of vectors).
- Index build time for large embedding sets can be significant.
- Memory requirements for HNSW indexes grow with dataset size and may affect the RDS instance sizing.

**Neutral:**
- Embedding generation itself is handled by an external LLM provider's embedding API (e.g., OpenAI `text-embedding-*`); pgvector only stores and queries the resulting vectors.

## Alternatives Considered

**Pinecone:** Managed, scalable, excellent performance. Rejected due to additional cost, vendor dependency, and operational surface at this scale.

**Qdrant / Weaviate:** Open-source dedicated vector databases. Rejected for the same reasons as Pinecone at this phase; viable if pgvector becomes a bottleneck.

## Links

- Related: ADR-008 (PostgreSQL), ADR-011 (FTS), ADR-029 (Airflow/ETL)