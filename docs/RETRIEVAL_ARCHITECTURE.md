# Nexora Retrieval Architecture

Phase 4 adds local semantic retrieval over processed Phase 3 chunks.

It does not generate final answers, run RAG, or perform financial reasoning.
Retrieval results are evidence candidates for Phase 5.

## Pipeline

1. Load chunk JSON files from `data/processed/chunks/`.
2. Generate local embeddings with `BAAI/bge-small-en-v1.5`.
3. Normalize embeddings for cosine-style search.
4. Store vectors in a local FAISS index.
5. Record vector metadata in CSV and JSON.
6. Search vectors with embedded user queries.
7. Join search results back to chunk text and source metadata.

## Embedding Model

The default model is `BAAI/bge-small-en-v1.5` because it is small enough for
local MacBook use while still producing useful semantic retrieval quality.

The config also includes `hkunlp/instructor-base` as a future fallback option,
but Phase 4 defaults to BGE small.

The first model load may download files into the local Hugging Face cache. Model
files are not stored in this repository.

## Vector Stores

### FAISS

FAISS is the primary working vector store. Nexora uses normalized embeddings with
`IndexFlatIP`, which gives cosine-style similarity scores.

Files:

- `data/vector_store/faiss/nexora.index`
- `data/vector_store/faiss/id_map.json`

### ChromaDB

ChromaDB is installed and scaffolded as a secondary local store. It uses a
persistent local directory under `data/vector_store/chroma/`. FAISS remains the
default and verified path.

## Metadata

Vector metadata is stored under:

- `data/vector_store/metadata/vector_index.csv`
- `data/vector_store/metadata/vector_index.json`

Each vector record includes:

- vector ID
- chunk ID
- processed document ID
- source document ID
- source type
- ticker, market, and document type
- section hint
- embedding model and dimension
- vector store
- indexed timestamp
- source chunk file
- status and error message

This preserves traceability from retrieval result back to chunk, processed
document, and original source record.

## Filters

Search supports metadata filters:

- ticker
- source type
- document type
- market
- section hint

Filters are applied against vector metadata before returning ranked results.

## Benchmarking

`benchmark_retrieval.py` runs simple sanity-check queries and saves:

- query text
- top result score
- number of results
- result chunk IDs
- timestamp

Output:

```text
data/vector_store/metadata/retrieval_benchmark_results.json
```

## Known Limitations

- No final RAG answer generation yet.
- No financial reasoning yet.
- Retrieval quality depends on processed chunk quality.
- The first embedding model download may take time.
- ChromaDB is secondary; FAISS is the verified default.
- Current indexed data is small because Phase 3 has only a few processed chunks.

## Phase 5 Readiness

Phase 5 can use retrieval results as evidence for the Core Financial RAG
Pipeline. The existing vector metadata gives Phase 5 source traceability,
ranking scores, chunk text, and document context.
