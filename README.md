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

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

Configure the required environment variables for the database and model provider, then start the API:

```bash
uvicorn main:app --reload
```

The API will be available at the local Uvicorn address shown in the terminal.

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

## Author

**T. Rushendar Reddy**  
B.Tech — Artificial Intelligence and Machine Learning  
Vignan University, Hyderabad
