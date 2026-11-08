# OSINT Lead Pipeline

A Python/FastAPI application for collecting, storing, searching and managing company leads, with a zero-build browser dashboard, an optional React UI and Docker support.

## Overview

The application provides a REST API and a browser dashboard for managing company leads.

It can:

- Store company, domain, email and notes
- Create, read, update and delete leads
- Search leads by company or domain
- Paginate lead results with `skip` / `limit`
- Validate email addresses
- Prevent duplicate domains
- Scrape a company homepage for a publicly exposed email address
- Display lead statistics
- Run automated API tests

## Technology

- Python 3.12
- FastAPI, Uvicorn, Pydantic
- SQLite
- pytest, HTTPX
- HTML/CSS dashboard
- React 19 + Vite + TypeScript (optional frontend)
- Docker / Docker Compose
- GitHub Actions

## Architecture

```text
Browser dashboard          React UI (optional)
        |                       |
        +-----------+-----------+
                    |
                    v
                 FastAPI
                    |
          +---------+---------+
          |                   |
     REST API          homepage scraper
          |
          v
       SQLite (leads.db)
```

The application is intentionally lightweight. SQLite is used for persistence and the API is served with Uvicorn.

## API

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/` | Service status as JSON |
| GET | `/dashboard` | Browser dashboard (static HTML) |
| GET | `/api/leads` | List leads; supports `search`, `skip`, `limit` |
| POST | `/api/leads` | Create a lead |
| GET | `/api/leads/{id}` | Get a lead |
| PATCH | `/api/leads/{id}` | Update a lead |
| DELETE | `/api/leads/{id}` | Delete a lead |
| GET | `/api/stats` | Return lead statistics |
| GET | `/api/scrape/{domain}` | Scrape a domain for an email |
| GET | `/docs` | Interactive API documentation |

`POST /api/leads` returns `409` when the domain already exists and `422` for an invalid email. Missing leads return `404`.

## Running locally

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/dashboard   browser dashboard
http://127.0.0.1:8000/docs        interactive API docs
```

`leads.db` is created in the working directory on first start. Run the command from the repository root so the path to `app/static/index.html` resolves correctly.

## Docker

```bash
docker compose up --build
```

Then open `http://127.0.0.1:8000/dashboard`. The compose file mounts `./leads.db` into the container, so data survives image rebuilds.

## Optional React frontend

The `frontend/` directory contains a separate Vite + React + TypeScript UI:

```bash
cd frontend
npm install
npm run dev
```

Important: `API_BASE` in [`frontend/src/App.tsx`](./frontend/src/App.tsx) is currently hardcoded to a GitHub Codespaces URL. Change it to your own API origin (for example `http://127.0.0.1:8000`) before running.

The React app is not served by the FastAPI container, and `npm run build` output is not copied into the image. The built-in `/dashboard` page is the zero-build option; the React app is for local development or separate hosting.

## Testing

```bash
pytest -v
```

The tests cover:

- Service root and statistics
- Lead creation, retrieval, updates and deletion
- Search and pagination
- Email validation
- Duplicate-domain handling
- Missing-resource handling

The tests use the real `leads.db`. Because the create test inserts a fixed domain, delete `leads.db` between runs or run in a fresh checkout to avoid a `409 Domain exists` failure.

## Project structure

```text
osint-lead-pipeline/
├── app/
│   ├── __init__.py
│   ├── main.py
│   └── static/
│       └── index.html
├── frontend/                  React + Vite UI
│   └── src/
│       └── App.tsx
├── tests/
│   └── test_api.py
├── osint_lead_pipeline.ipynb  notebook walkthrough
├── Dockerfile
├── compose.yaml
├── requirements.txt
├── pytest.ini
├── .gitignore
└── README.md
```

## Scraper

`GET /api/scrape/{domain}` sends an HTTP request to the specified HTTPS domain and searches the returned homepage HTML for email addresses using a regular expression.

If no email is found, it returns:

```text
contact@domain
```

The scraper is intentionally basic: HTTPS only, a 5-second timeout, homepage HTML only, and no verification of the address it finds.

## Current limitations

- No authentication or authorization
- CORS is open to all origins
- Homepage HTML only for email extraction
- No email verification
- SQLite rather than PostgreSQL
- No background job processing
- No multi-user access control
- No rate limiting
- Tests share the development database
- The React frontend has a hardcoded API base URL

## Possible production extensions

A production deployment could add:

- API-key or OAuth authentication
- PostgreSQL
- Background scraping jobs
- Rate limiting
- Structured logging
- Email verification
- Persistent scrape history
- Serving the built React app from FastAPI
- Monitoring and health checks

## License

This project is provided for demonstration and portfolio purposes.
