# OSINT Lead Pipeline

[![CI](https://github.com/trpelka/osint-lead-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/trpelka/osint-lead-pipeline/actions/workflows/ci.yml)

A small FastAPI + SQLite application for storing, searching and updating company
leads. It ships a zero-build HTML dashboard, an optional React UI and a Docker
setup.

This is a **lead book with a best-effort homepage scraper**, not an OSINT data
provider. It does not query breach data, social networks, company registries or
paid data sources. Everything in the database is entered through the API, and
the scraper only reads a company homepage that you name.

## What it does

- Create, read, update and delete leads (company, domain, email, notes)
- Search by company or domain and paginate with `skip` / `limit`
- Reject duplicate domains and malformed emails
- Store data in SQLite
- Try to find a publicly listed email address on a company homepage
- Show lead counts in the dashboard

## Technology

- Python 3.12, FastAPI, Uvicorn, Pydantic
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
     REST API       best-effort homepage fetch
          |
          v
       SQLite (leads.db)
```

## API

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/` | Service status as JSON |
| GET | `/dashboard` | Zero-build HTML dashboard |
| GET | `/api/leads` | List leads; supports `search`, `skip`, `limit` |
| POST | `/api/leads` | Create a lead |
| GET | `/api/leads/{id}` | Get a lead |
| PATCH | `/api/leads/{id}` | Update `company`, `email` or `notes` |
| DELETE | `/api/leads/{id}` | Delete a lead |
| GET | `/api/stats` | Return the number of stored leads |
| GET | `/api/scrape/{domain}` | Try to read a public email from a homepage |
| GET | `/docs` | Interactive API documentation |

`POST /api/leads` returns `409` when the domain already exists and `422` for an
invalid email or domain. Missing leads return `404`.

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
http://127.0.0.1:8000/dashboard   zero-build dashboard
http://127.0.0.1:8000/docs        interactive API docs
```

`leads.db` is created on first start. Set `LEADS_DB` to store it elsewhere:

```bash
LEADS_DB=/var/lib/leads/leads.db uvicorn app.main:app
```

Run the command from the repository root so the path to
`app/static/index.html` resolves correctly.

## Docker

```bash
docker compose up --build
```

Then open `http://127.0.0.1:8000/dashboard`. The compose file mounts
`./leads.db` into the container, so data survives image rebuilds.

## Optional React frontend

The `frontend/` directory contains a separate Vite + React + TypeScript UI:

```bash
cd frontend
npm install
npm run dev
```

The API origin comes from `VITE_API_BASE` and defaults to
`http://127.0.0.1:8000`:

```bash
VITE_API_BASE=https://api.example.com npm run dev
```

The React app is not served by the FastAPI container and its build output is not
copied into the image. The built-in `/dashboard` page is the supported
zero-build option.

## Testing

```bash
pip install -r requirements-dev.txt
pytest
ruff check .
```

The suite creates a throwaway database through `tests/conftest.py`, so it never
touches your development `leads.db` and it is safe to run repeatedly. The
scraper tests replace DNS resolution and the HTTP opener, so they do not make
network requests. Coverage includes CRUD, pagination order, search, duplicate
domains, email validation, private-address rejection and scrape fallbacks.

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
│   ├── conftest.py
│   └── test_api.py
├── .github/workflows/ci.yml
├── Dockerfile
├── compose.yaml
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── .gitignore
└── README.md
```

## Scraper

`GET /api/scrape/{domain}` requests `https://<domain>`, reads at most 512 KB of
HTML and returns the first email address in sorted order. If no address is
found, or the request fails, it returns `contact@<domain>`.

Guards:

- A bare public hostname is required. Schemes, ports, paths and IP literals are
  rejected with `400`.
- The hostname is resolved first, and every resolved address must be globally
  routable. Private, loopback, link-local and reserved addresses are rejected.
- Redirects are not followed.
- The request times out after 5 seconds and reads a bounded number of bytes.

These are best-effort checks, not a complete SSRF defence: DNS can change
between the resolution check and the request, and the returned address is never
verified. Do not expose this endpoint to untrusted users without adding
authentication and egress filtering.

## Current limitations

- No authentication or authorization
- CORS is open to all origins
- Homepage HTML only; no crawling and no email verification
- SQLite rather than PostgreSQL
- No background job processing or retries
- No rate limiting
- No multi-user access control

## Possible production extensions

- API-key or OAuth authentication
- PostgreSQL and migrations
- Background scraping jobs with a queue
- Rate limiting and egress filtering
- Structured logging and health checks
- Email verification
- Serving the built React app from FastAPI

## License

This project is provided for demonstration and portfolio purposes.
