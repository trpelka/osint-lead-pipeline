import ipaddress
import os
import re
import socket
import sqlite3
import urllib.error
import urllib.request
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator


app = FastAPI(title="OSINT Lead Pipeline")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.getenv("LEADS_DB", "leads.db")

# Public DNS hostname only: no scheme, port, path, IP literal or localhost.
DOMAIN_PATTERN = re.compile(
    r"^(?=.{1,253}$)"
    r"(?!-)[A-Za-z0-9-]{1,63}(?<!-)"
    r"(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*"
    r"\.[A-Za-z]{2,63}$"
)


def valid_domain(value):
    value = str(value or "").strip().lower()
    if not DOMAIN_PATTERN.match(value):
        raise ValueError("bad domain")
    return value


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            domain TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL,
            notes TEXT
        )
        """
    )

    conn.commit()
    conn.close()


init_db()


class LeadCreate(BaseModel):
    company: str
    domain: str
    email: str
    notes: Optional[str] = None

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, value):
        return valid_domain(value)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value):
            raise ValueError("bad email")
        return value


class LeadUpdate(BaseModel):
    company: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        if value is None:
            return value
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value):
            raise ValueError("bad email")
        return value


class LeadOut(BaseModel):
    id: int
    company: str
    domain: str
    email: str
    notes: Optional[str]


@app.get("/api/leads", response_model=list[LeadOut])
def list_leads(
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
):
    conn = get_db()

    if search:
        q = f"%{search}%"
        rows = conn.execute(
            """
            SELECT *
            FROM leads
            WHERE company LIKE ? OR domain LIKE ?
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """,
            (q, q, limit, skip),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT *
            FROM leads
            ORDER BY id DESC
            LIMIT ? OFFSET ?
            """,
            (limit, skip),
        ).fetchall()

    conn.close()

    return [dict(row) for row in rows]


@app.get("/api/leads/{lead_id}", response_model=LeadOut)
def get_lead(lead_id: int):
    conn = get_db()

    row = conn.execute(
        "SELECT * FROM leads WHERE id = ?",
        (lead_id,),
    ).fetchone()

    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Not found")

    return dict(row)


@app.post("/api/leads", response_model=LeadOut, status_code=201)
def create_lead(lead: LeadCreate):
    conn = get_db()

    try:
        cursor = conn.execute(
            """
            INSERT INTO leads (company, domain, email, notes)
            VALUES (?, ?, ?, ?)
            """,
            (
                lead.company,
                lead.domain,
                lead.email,
                lead.notes,
            ),
        )

        conn.commit()

        row = conn.execute(
            "SELECT * FROM leads WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()

        return dict(row)

    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail="Domain exists",
        ) from exc

    finally:
        conn.close()


@app.patch("/api/leads/{lead_id}", response_model=LeadOut)
def update_lead(lead_id: int, lead: LeadUpdate):
    conn = get_db()

    exists = conn.execute(
        "SELECT 1 FROM leads WHERE id = ?",
        (lead_id,),
    ).fetchone()

    if not exists:
        conn.close()
        raise HTTPException(status_code=404, detail="Not found")

    updates = {
        key: value
        for key, value in lead.model_dump().items()
        if value is not None
    }

    if updates:
        fields = ", ".join(f"{key} = ?" for key in updates)

        conn.execute(
            f"""
            UPDATE leads
            SET {fields}
            WHERE id = ?
            """,
            (*updates.values(), lead_id),
        )

        conn.commit()

    row = conn.execute(
        "SELECT * FROM leads WHERE id = ?",
        (lead_id,),
    ).fetchone()

    conn.close()

    return dict(row)


@app.delete("/api/leads/{lead_id}", status_code=204)
def delete_lead(lead_id: int):
    conn = get_db()

    exists = conn.execute(
        "SELECT 1 FROM leads WHERE id = ?",
        (lead_id,),
    ).fetchone()

    if not exists:
        conn.close()
        raise HTTPException(status_code=404, detail="Not found")

    conn.execute(
        "DELETE FROM leads WHERE id = ?",
        (lead_id,),
    )

    conn.commit()
    conn.close()


@app.get("/api/stats")
def stats():
    conn = get_db()

    total = conn.execute(
        "SELECT COUNT(*) FROM leads"
    ).fetchone()[0]

    conn.close()

    return {
        "total_leads": total
    }


MAX_HTML_BYTES = 512 * 1024


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(
            req.full_url, code, "redirect blocked", headers, fp
        )


def resolve_public_addresses(domain: str):
    """Resolve a hostname and reject anything that is not globally routable."""
    try:
        infos = socket.getaddrinfo(domain, 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError("unresolvable domain") from exc

    addresses = [ipaddress.ip_address(info[4][0]) for info in infos]

    if not addresses or any(not address.is_global for address in addresses):
        raise ValueError("non-public address")

    return addresses


def scrape_email(domain: str) -> str:
    """Fetch a public homepage and return the first e-mail address found.

    The endpoint accepts a bare public hostname only: no scheme, port, path or
    IP literal. The hostname is resolved before the request and rejected when
    any resolved address is not globally routable, redirects are not followed,
    and at most 512 KB of HTML is read. This is a best-effort guard, not a
    complete SSRF defence: DNS can still change between the check and the
    request.
    """
    try:
        domain = valid_domain(domain)
        resolve_public_addresses(domain)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid domain") from exc

    try:
        request = urllib.request.Request(
            f"https://{domain}",
            headers={"User-Agent": "Mozilla/5.0"},
        )

        opener = urllib.request.build_opener(_NoRedirect)

        with opener.open(request, timeout=5) as response:
            html = response.read(MAX_HTML_BYTES).decode(errors="ignore")

        emails = sorted(
            set(
                re.findall(
                    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
                    html,
                )
            )
        )

        return emails[0] if emails else f"contact@{domain}"

    except Exception:
        return f"contact@{domain}"


@app.get("/api/scrape/{domain}")
def scrape_domain(domain: str):
    email = scrape_email(domain)

    return {
        "domain": domain,
        "email": email,
    }


@app.get("/")
def root():
    return {
        "name": "OSINT Lead Pipeline",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/dashboard")
def dashboard():
    return FileResponse("app/static/index.html")
