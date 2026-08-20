# osint-lead-pipeline

Scrapes company domains for contact emails, stores them in a database, and exposes a REST API with full CRUD.

## What it does

1. Takes a list of company domains
2. Fetches each homepage and extracts email addresses from the HTML
3. Falls back to `contact@domain` if none found
4. Stores leads in SQLite
5. Exposes a FastAPI REST API — list, search, create, update, delete, stats

## Stack

- Python 3.12
- FastAPI
- SQLite
- Pydantic (validation)
- pytest + TestClient (11 tests)
- Docker + Docker Compose (local deployment)

## Run locally

Requires Docker Desktop.

```
git clone https://github.com/YOUR_USERNAME/osint-lead-pipeline
cd osint-lead-pipeline
docker compose up --build
```

API: http://localhost:8000  
Docs: http://localhost:8000/docs

## Run in browser (no install)

Open the notebook in Google Colab — scrapes targets, runs the API, executes all tests, displays results.

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/YOUR_USERNAME/osint-lead-pipeline/blob/main/notebook.ipynb)

## API endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/leads` | List leads — supports `?search=`, `?skip=`, `?limit=` |
| GET | `/api/leads/{id}` | Get one lead |
| POST | `/api/leads` | Create lead |
| PATCH | `/api/leads/{id}` | Update lead |
| DELETE | `/api/leads/{id}` | Delete lead |
| GET | `/api/stats` | Totals |
| GET | `/docs` | Swagger UI |

## Tests

```
cd app
pip install fastapi uvicorn pydantic pytest httpx
pytest -v
```

11 tests — CRUD, validation, duplicates, pagination, error handling.

## Known gaps

- No authentication (API key layer would be next)
- Scraper is basic — regex email extraction from homepage HTML only
- SQLite only — PostgreSQL would be the production move
