# Psycho Hunter

## 1. Project purpose

Psycho Hunter is a public-source client intelligence and meeting briefing platform. The system will help teams gather and summarize publicly available information about a client or organization to support more informed meetings, outreach, and strategic conversations.

The platform is intentionally scoped to evidence-based public information collection and synthesis. It will not diagnose anyone, infer mental health status, or make speculative claims about sensitive personal attributes.

## 2. High-level architecture

The project is planned as a modular system with a Python backend, a React + Vite frontend, and a PostgreSQL + pgvector database for structured storage and vector search.

- Frontend: user-facing dashboard and briefing experience
- Backend: ingestion, processing, retrieval, and API services
- Database: metadata storage, source records, and vector embeddings
- AI layer: OpenAI embeddings and retrieval-augmented generation workflows
- Infrastructure: Docker and Docker Compose for local development

## 3. Technology stack

### Frontend
- React
- Vite
- Tailwind CSS

### Backend
- Python
- FastAPI
- Pydantic

### Database
- PostgreSQL
- pgvector

### AI
- OpenAI API
- embeddings
- RAG

### Infrastructure
- Docker
- docker-compose

## 4. Planned RAG pipeline

The initial architecture will use a retrieval-augmented generation pipeline built around public-source evidence.

Planned flow:
1. Accept a client's name and authorized or public source URLs.
2. Collect publicly available source content from approved URLs.
3. Normalize and chunk relevant content into evidence units.
4. Generate embeddings for text chunks.
5. Store embeddings and metadata in PostgreSQL with pgvector.
6. Retrieve the most relevant evidence for a query.
7. Use an LLM with retrieved evidence to generate a briefing summary.
8. Attach source URLs, publication dates, and confidence notes to outputs.

The system will emphasize traceability and evidence-backed summaries rather than unsupported speculation.

## 5. Planned database

The project will use PostgreSQL with pgvector to support:
- document storage
- source metadata
- embeddings
- similarity search
- filtering by date, source, or confidence

This provides a practical foundation for semantic retrieval and evidence ranking across public-source materials.

## 6. Planned frontend/backend responsibilities

### Frontend responsibilities
- Client briefing input form
- Source URL management
- Search and retrieval UI
- Briefing output display
- Evidence and source citation viewing
- Confidence and publication metadata presentation

### Backend responsibilities
- API layer for frontend interactions
- source ingestion orchestration
- content processing and normalization
- embeddings generation
- retrieval and ranking
- RAG response assembly
- validation of evidence quality and metadata

## 7. Privacy and evidence requirements

This project must remain strictly limited to public, authorized, and evidence-based information.

The system must not:
- diagnose a person's mental health
- infer psychological disorders
- infer sensitive personal attributes
- make unsupported personality claims
- treat speculation as fact

The system should instead focus on:
- publicly stated interests
- publicly stated likes/dislikes when explicitly expressed
- professional projects
- companies and organizations
- technologies discussed
- publicly stated opinions
- recurring public topics
- professional priorities
- important recent developments
- evidence and source URLs
- publication dates
- confidence levels

All outputs should be grounded in verifiable public sources, and source provenance should be preserved in the final briefing.

## Backend Development

FastAPI is the backend framework for the application. It provides the API layer for the service and the health endpoints used during early development.

### Install backend dependencies

```powershell
cd "d:\projects\psycho hunter\backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Start the development server

```powershell
cd "d:\projects\psycho hunter\backend"
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Run tests

```powershell
cd "d:\projects\psycho hunter\backend"
.\.venv\Scripts\Activate.ps1
pytest -q
```

### Start PostgreSQL with Docker Compose

```powershell
cd "d:\projects\psycho hunter"
docker compose up -d
```

### Check PostgreSQL containers

```powershell
cd "d:\projects\psycho hunter"
docker compose ps
```

### Stop PostgreSQL

```powershell
cd "d:\projects\psycho hunter"
docker compose down
```

The PostgreSQL service is currently infrastructure-only. Database tables and schema work will be added in a later step.
