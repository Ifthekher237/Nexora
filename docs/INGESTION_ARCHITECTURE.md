# Nexora Ingestion Architecture

Phase 2 adds a local-first Financial Data Ingestion Engine. Its job is to
collect real source metadata and files, store them under a traceable folder
structure, and maintain a consistent metadata index for later document
processing.

It does not implement RAG, embeddings, vector databases, or financial reasoning.

## Backend Modules

The ingestion backend lives under `backend/app/services/ingestion/`.

- `ingestion_manager.py` coordinates API and CLI operations.
- `sec_ingestion.py` fetches SEC company ticker mapping and submissions metadata.
- `rss_ingestion.py` fetches configured public RSS feeds.
- `local_file_ingestion.py` registers real local files such as reports and transcripts.
- `macro_ingestion.py` registers local macroeconomic CSV datasets.
- `asx_ingestion.py` provides honest manual ASX announcement registration.
- `metadata_service.py` manages CSV and JSON metadata indexes.
- `storage_service.py` creates folders, hashes content, and writes raw files.
- `validation_service.py` validates limits, source types, tickers, paths, and metadata.

FastAPI routes are exposed in `backend/app/api/routes_ingestion.py`.

## Configuration

`configs/ingestion_sources.yaml` defines:

- request timeout
- maximum documents per run
- storage and metadata roots
- SEC endpoint settings
- configured RSS feeds
- local upload extensions
- macro and ASX mode notes

## Storage Layout

Raw ingested content is stored under `data/raw/`:

- `data/raw/sec/`
- `data/raw/asx/`
- `data/raw/rss/`
- `data/raw/macro/`
- `data/raw/local_uploads/`

Metadata is stored under `data/metadata/`:

- `ingestion_index.csv`
- `ingestion_index.json`

## Metadata Schema

Every metadata record uses the same fields:

- `document_id`
- `source_type`
- `source_name`
- `company_name`
- `ticker`
- `market`
- `document_type`
- `title`
- `source_url`
- `local_path`
- `file_format`
- `ingested_at`
- `published_at`
- `period`
- `status`
- `error_message`
- `content_hash`
- `notes`

Some fields may be blank when a source does not provide them, but the schema
stays consistent.

## Duplicate Handling

Duplicate checks use:

- document ID
- source URL
- content hash

When a duplicate is detected, Nexora skips writing another raw file and returns
the existing metadata record. If a new record has useful values for blank fields,
the metadata service can fill those blanks without duplicating the document.

## SEC Ingestion

SEC ingestion uses public SEC endpoints:

- company ticker mapping from `www.sec.gov`
- company submissions metadata from `data.sec.gov`

It stores filing metadata as JSON, including accession number, filing date,
report date, form type, primary document, and a constructable filing URL when
available.

SEC can reject requests that do not include acceptable user-agent contact
information. Set `ingestion.default_user_agent` in
`configs/ingestion_sources.yaml` to a real project contact before regular SEC
use.

## RSS Ingestion

RSS ingestion fetches configured public feeds and stores each item as a small
text file with title, source URL, published date, and description or summary
when available.

Feed availability can vary. Failures are returned clearly instead of being
replaced with fake results.

## Local Files

Local file ingestion validates a path, checks the extension, calculates a SHA-256
hash, copies the file into raw storage, and records metadata. This supports
annual reports, quarterly reports, earnings transcripts, ASX announcements, and
manual datasets.

## Known Limitations

- SEC ingestion stores filing metadata, not full filing content.
- RSS item content depends on what each feed publishes.
- ASX live scraping is not implemented in Phase 2.
- Macro ingestion is local CSV first; no external macro API is added yet.
- No PDF text extraction, chunking, embeddings, RAG, or reasoning is implemented.

## Phase 3 Readiness

The metadata index and raw storage layout are ready for a Document Processing
Pipeline. Phase 3 can add parsing, text extraction, chunking, quality checks, and
document-level processing status without changing the ingestion foundation.
