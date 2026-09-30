# Psycho Hunter — Project Status

## Project Goal

Psycho Hunter is an evidence-based public/authorized-source client intelligence and pitch-personalization platform.

It should identify observable information such as:
- hobbies
- interests
- recurring topics
- technologies
- projects
- companies
- explicit preferences
- recent developments
- communication signals

Every useful insight should be traceable to supporting evidence.

The system must NOT:
- diagnose psychological conditions
- infer mental health
- infer sensitive personal attributes
- make unsupported personality claims
- treat speculation as fact

## Completed Steps

### Step 1
Initial project structure created.

### Step 2
FastAPI backend created and tested.

### Step 3
PostgreSQL + pgvector Docker environment configured.

Docker database:
- container: psycho-hunter-db
- PostgreSQL
- pgvector

IMPORTANT:
Never delete, recreate, reset, or wipe the PostgreSQL Docker volume unless explicitly instructed.

### Step 4
SQLAlchemy database layer and models implemented.

Existing conceptual models:
- Client
- Source
- Document
- DocumentChunk
- Evidence
- Briefing

### Step 5A
Client CRUD API completed.

Endpoints:
- POST /clients
- GET /clients
- GET /clients/{client_id}

### Step 5B
Source API completed.

Endpoints:
- POST /clients/{client_id}/sources
- GET /clients/{client_id}/sources
- GET /sources/{source_id}
- DELETE /sources/{source_id}

### Step 5C
Basic public document ingestion completed.

Endpoint:
- POST /sources/{source_id}/ingest

It retrieves publicly accessible HTML, extracts readable text, stores a Document, and generates content_hash.

No OpenAI, embeddings, RAG, or social-media API access is involved.

### Step 5D
Structured Insight layer completed.

Endpoints:
- POST /clients/{client_id}/insights
- GET /clients/{client_id}/insights
- GET /insights/{insight_id}

Supported categories:
- INTEREST
- HOBBY
- TOPIC
- TECHNOLOGY
- PROJECT
- COMPANY
- PREFERENCE
- RECENT_DEVELOPMENT

Confidence:
- low
- medium
- high

Insights can be linked to Evidence.

### Step 5E
Deterministic document chunking completed.

Endpoints:
- POST /documents/{document_id}/chunk
- GET /documents/{document_id}/chunks

Chunking uses a word-based sliding window with overlap.

Embeddings are NOT implemented yet.

## Latest Test Status

48 passed, 1 skipped, 2 warnings.

## Immediate Pending Fix

The DocumentChunk response currently exposes:

"embedding": null

Remove the embedding field from the API response schema.

Do NOT change the database schema or embedding field.

Run the complete pytest suite after the fix.

## Next Development Step

STEP 5F:
Automatic evidence-backed Hobbies & Interests extraction.

The intended pipeline is:

Document
↓
Chunks
↓
Extraction
↓
Structured Insight
↓
Evidence + confidence
↓
Later: pitch personalization

Step 5F must focus on observable evidence such as:
- hobbies
- interests
- recurring topics
- explicit preferences
- technologies
- projects
- companies
- recent developments

Do not implement psychological diagnosis or unsupported personality inference.

## Future Pipeline

Document
↓
Chunks
↓
Evidence-backed extraction
↓
Embeddings
↓
Vector search / RAG
↓
Pitch personalization
↓
Meeting briefing

## Important Development Rules

- Work one step at a time.
- Do not proceed beyond the requested step.
- Do not reset the PostgreSQL Docker volume.
- Do not wipe existing database data.
- Do not bypass website access controls.
- Do not access private information.
- Do not call OpenAI unless explicitly requested as part of a later step.
- Keep insights evidence-backed.
- Run the complete pytest suite after each development step.

STOP after creating PROJECT_STATUS.md.
