# AIVOA-QMS Backend

## Overview

AIVOA-QMS Backend is the server-side application for the AI-Powered Pharmaceutical Quality Management System. It is built using FastAPI and integrates LangGraph, LangChain, Groq's Llama 3.3 model, SQLAlchemy, and MySQL to automate pharmaceutical complaint processing.

The backend accepts complaint text or uploaded documents, extracts structured complaint information, validates completeness, performs AI-assisted risk assessment, detects duplicate complaints, and stores records in a MySQL database.

---

## Features

- AI-powered complaint extraction
- Natural language complaint processing
- PDF and text document upload
- Complaint completeness validation
- AI-assisted risk assessment
- Root cause hypothesis generation
- CAPA recommendations
- Duplicate complaint detection
- Complaint lifecycle management
- MySQL database integration

---

## Technology Stack

- Python
- FastAPI
- LangGraph
- LangChain
- Groq (Llama 3.3 70B)
- SQLAlchemy
- MySQL
- Pydantic

---

## Project Structure

```text
AIVOA-QMS-Backend/
│── main.py
│── workflow.py
│── database.py
│── schemas.py
│── requirements.txt
│── .env
```

---

## Workflow

```text
User Prompt / PDF
        │
        ▼
      FastAPI
        │
        ▼
    LangGraph
        │
        ├── Complaint Extraction
        ├── Completeness Validation
        └── Risk Assessment
        │
        ▼
Structured JSON Response
        │
        ▼
React Frontend
        │
        ▼
MySQL Database
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/extract` | Extract complaint information from text |
| POST | `/api/upload-extract` | Process uploaded complaint documents |
| POST | `/api/check-duplicate` | Check for duplicate complaints |
| POST | `/api/complaints` | Save complaint |
| GET | `/api/complaints` | Retrieve all complaints |
| PATCH | `/api/complaints/{id}/status` | Update complaint status |



## Author

**T. Rushendar Reddy**

Email:trushendarreddy@gmail.com

B.Tech in Artificial Intelligence and Machine Learning

Vignan University,

Hyderabad,Telangana
