# Nexora Processing Architecture

Phase 3 adds the Document Processing Pipeline. It transforms raw ingested files
from Phase 2 into cleaned text, chunk JSON, and processing metadata that Phase 4
can load into a vector database.

This phase does not create embeddings, vector indexes, RAG, or financial
reasoning.

## Pipeline Flow

1. Read source records from `data/metadata/ingestion_index.csv`.
2. Resolve each record's `local_path`.
3. Load text from PDF, TXT, MD, JSON, or CSV.
4. Clean text without removing financial values.
5. Classify the document using simple rules.
6. Enrich document and chunk metadata with source traceability.
7. Split cleaned text into overlapping word chunks.
8. Save processed text and chunk JSON.
9. Save or update `data/processed/processing_metadata/processing_index.*`.

Each document is handled independently. If one document fails, the batch
continues and the failure is recorded.

## Backend Modules

Processing services live under `backend/app/services/processing/`.

- `processing_manager.py` coordinates the full pipeline.
- `document_loader.py` extracts text from supported file types.
- `text_cleaner.py` normalizes whitespace and noisy text.
- `chunking_service.py` creates word-based overlapping chunks.
- `classification_service.py` performs rule-based classification.
- `enrichment_service.py` adds source and section metadata.
- `quality_service.py` calculates text and chunk quality signals.
- `processing_metadata_service.py` manages the processing index.

FastAPI routes are exposed in `backend/app/api/routes_processing.py`.

## Supported File Types

- `.pdf` using `pypdf`
- `.txt`
- `.md`
- `.json`
- `.csv`

SEC metadata JSON is converted into readable filing text. CSV files are loaded
with Pandas using a small preview to avoid blindly processing large datasets.

## Processing Metadata

Every processed document record includes:

- processed and source document IDs
- source type and source name
- company, ticker, market, and document type
- source and processed local paths
- chunk JSON path
- processing status and error
- text length, word count, and chunk count
- detected category
- content hash
- notes

## Chunk Metadata

Each chunk includes:

- chunk ID
- processed and source document IDs
- chunk index
- chunk text
- word and character counts
- source metadata
- section hint
- creation timestamp

Chunks are saved as JSON in `data/processed/chunks/`.

## Text Cleaning

The cleaner removes repeated whitespace, null characters, noisy repeated
punctuation, and excessive blank lines. It deliberately preserves financial
numbers, percentages, currency symbols, dates, ratios, and financial terms.

## Chunking

Chunking is word-based with defaults from `configs/processing_config.yaml`:

- 350 words per chunk
- 60-word overlap
- short documents become one chunk

This creates embedding-ready chunks without generating embeddings yet.

## Classification

Classification is simple and rule-based. It uses source metadata first, then
file and text hints.

Categories:

- `annual_report`
- `quarterly_report`
- `sec_filing_metadata`
- `rss_news`
- `earnings_transcript`
- `macro_dataset`
- `asx_announcement`
- `unknown`

## Quality Checks

Quality status values are:

- `good`
- `warning`
- `failed`

Very short extracted text receives a warning. Empty text or failed extraction is
recorded as failed.

## Known Limitations

- No embeddings are generated in Phase 3.
- No vector database is created.
- No RAG pipeline is implemented.
- PDF extraction quality depends on whether the source PDF contains selectable
  text.
- SEC Phase 2 records are filing metadata, not full filing content.
- RSS records only contain feed-provided text.

## Phase 4 Readiness

Phase 4 can load `data/processed/chunks/*.json`, generate embeddings, and index
chunks in FAISS or ChromaDB while preserving source traceability through the
processing metadata.
