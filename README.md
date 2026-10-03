# AIVOA-QMS — Complaint Processing Backend

AIVOA-QMS is a pharmaceutical complaint-management system built to turn messy complaint text and documents into structured records that a quality team can review consistently.

This repository contains the backend: the API, AI workflow, validation logic, database access, and complaint lifecycle operations.

## The problem

A complaint can arrive as free-form text or a document. Before a quality team can act on it, important fields have to be extracted, missing information identified, duplicates checked, and risk considered.

The backend turns that process into a repeatable workflow while keeping the resulting record structured and inspectable.

## Product workflow

```text
Text / PDF complaint
        ↓
      FastAPI
        ↓
     LangGraph
        ├── Extract complaint fields
        ├── Check completeness
        ├── Assess risk
        └── Generate review suggestions
        ↓
 Structured complaint record
        ↓
 MySQL persistence + lifecycle updates
        ↓
 React review interface
```

## What it handles

- Natural-language complaint extraction
- PDF and text document processing
- Complaint completeness validation
- AI-assisted risk assessment
- Root-cause hypotheses
- CAPA recommendations
- Duplicate complaint checks
- Complaint creation and retrieval
- Complaint status updates

The AI output is treated as assistance for the workflow, not as an unquestionable final decision.

## Architecture

The main application is split around the work the system performs:

- **FastAPI** — HTTP boundary and API endpoints
- **LangGraph / LangChain** — orchestrates the AI processing workflow
- **Pydantic** — request and response validation
- **SQLAlchemy** — database access
- **MySQL** — persistent complaint records
- **Groq / Llama 3.3 70B** — model used for the AI-assisted workflow

## API

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/extract` | Extract structured complaint information from text |
| POST | `/api/upload-extract` | Process a complaint document |
| POST | `/api/check-duplicate` | Check for possible duplicate complaints |
| POST | `/api/complaints` | Save a complaint |
| GET | `/api/complaints` | Retrieve complaints |
| PATCH | `/api/complaints/{id}/status` | Update complaint status |

## Run locally

### Requirements

- Python 3.11 or newer
- MySQL 8, or set `DATABASE_URL` to any SQLAlchemy-supported database

### Install and run

```bash
pip install -r requirements.txt
cp .env.example .env      # then fill in the values below
uvicorn main:app --reload
```

Interactive API docs are then at `http://localhost:8000/docs`.

### Environment

| Variable | Required | Purpose |
|---|---|---|
| `DATABASE_URL` | yes | SQLAlchemy connection string, e.g. `mysql+pymysql://user:pass@localhost:3306/aivoa_qms` |
| `GROQ_API_KEY` | for AI features | Key for the extraction and risk-assessment workflow |
| `GROQ_MODEL` | no | Defaults to `llama-3.3-70b-versatile` |

Without `GROQ_API_KEY` the app still starts and the complaint CRUD,
duplicate-check, and status endpoints work. Only extraction and risk
assessment need the model.

### Tests

```bash
pip install pytest httpx
pytest -q
```

16 tests over duplicate detection and the complaint status workflow, run
against an in-memory SQLite database so no MySQL server or API key is
needed. CI runs them on every push.

## Project structure

```text
main.py          # FastAPI application and routes
workflow.py      # AI processing workflow
database.py      # SQLAlchemy / MySQL access
schemas.py       # API and data schemas
requirements.txt # Python dependencies
```

## Project status

This is a working product-oriented prototype. It demonstrates the complaint-processing workflow and its integration points, but it is not presented as a validated pharmaceutical quality system. Production use would require stronger authentication and authorization, audit trails, model governance, validation, observability, and regulated deployment controls.

## Related repository

The React interface for the workflow lives in **AIVOA-QMS-Frontend**.

## License

MIT — see [LICENSE](LICENSE).

## Author

**T. Rushendar Reddy**  
B.Tech — Artificial Intelligence and Machine Learning  
Vignan University, Hyderabad
