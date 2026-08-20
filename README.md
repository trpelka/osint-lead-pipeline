# OSINT Lead Pipeline

A Python/FastAPI application for collecting, storing, searching, and managing OSINT leads.

## Overview

OSINT Lead Pipeline provides a REST API and browser dashboard for managing company leads.

The application can:

* Store company, domain, email, and notes
* Create, read, update, and delete leads
* Search leads by company or domain
* Paginate lead results
* Validate email addresses
* Prevent duplicate domains
* Scrape a company homepage for a publicly exposed email address
* Display lead statistics
* Run automated API tests

## Technology

* Python 3.12
* FastAPI
* Uvicorn
* Pydantic
* SQLite
* pytest
* HTTPX
* HTML/CSS
* GitHub Actions

## Architecture

```text
Browser
   |
   v
FastAPI
   |
   +---- REST API
   |
   +---- OSINT scraper
   |
   v
SQLite
```

The application is intentionally lightweight. SQLite is used for persistence and the API is served with Uvicorn.

## API

| Method | Endpoint               | Description                  |
| ------ | ---------------------- | ---------------------------- |
| GET    | `/api/leads`           | List leads                   |
| POST   | `/api/leads`           | Create a lead                |
| GET    | `/api/leads/{id}`      | Get a lead                   |
| PATCH  | `/api/leads/{id}`      | Update a lead                |
| DELETE | `/api/leads/{id}`      | Delete a lead                |
| GET    | `/api/stats`           | Return lead statistics       |
| GET    | `/api/scrape/{domain}` | Scrape a domain for an email |
| GET    | `/`                    | Browser dashboard            |

Interactive API documentation is available through FastAPI:

```text
/docs
```

## Running locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the application:

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

## Testing

Run the automated test suite:

```bash
pytest -v
```

The tests cover:

* Lead creation
* Lead retrieval
* Lead updates
* Lead deletion
* Search
* Statistics
* Email validation
* Duplicate-domain handling
* Missing-resource handling

## Project structure

```text
osint-lead-pipeline/
├── app/
│   ├── __init__.py
│   ├── main.py
│   └── static/
│       └── index.html
├── tests/
│   └── test_api.py
├── .github/
│   └── workflows/
├── requirements.txt
├── pytest.ini
├── .gitignore
└── README.md
```

## Scraper

The scraper sends an HTTP request to the specified HTTPS domain and searches the returned homepage HTML for email addresses using a regular expression.

If no email is found, it returns:

```text
contact@domain
```

The scraper is intentionally basic and is not intended to replace a full web-crawling or verification system.

## Current limitations

* No authentication or authorization
* Homepage HTML only for email extraction
* No email verification
* SQLite rather than PostgreSQL
* No background job processing
* No multi-user access control

## Possible production extensions

A production deployment could add:

* API-key or OAuth authentication
* PostgreSQL
* Background scraping jobs
* Rate limiting
* Structured logging
* Email verification
* Persistent scrape history
* Docker deployment
* Monitoring and health checks

## License

This project is provided for demonstration and portfolio purposes.
