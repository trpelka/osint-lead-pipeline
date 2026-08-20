import os
import re
import sqlite3
import urllib.request
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator


app = FastAPI(title="OSINT Lead Pipeline")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "leads.db"


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


class LeadOut(BaseModel):
    id: int
    company: str
    domain: str
    email: str
    notes: Optional[str]


@app.get("/api/leads", response_model=list[LeadOut])
def list_leads(
    search: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 20,
):
    conn = get_db()

    if search:
        q = f"%{search}%"
        rows = conn.execute(
            """
            SELECT *
            FROM leads
            WHERE company LIKE ? OR domain LIKE ?
            LIMIT ? OFFSET ?
            """,
            (q, q, limit, skip),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT *
            FROM leads
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

    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Domain exists",
        )

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


def scrape_email(domain: str) -> str:
    try:
        request = urllib.request.Request(
            f"https://{domain}",
            headers={"User-Agent": "Mozilla/5.0"},
        )

        html = urllib.request.urlopen(
            request,
            timeout=5,
        ).read().decode(errors="ignore")

        emails = list(
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
from fastapi.responses import FileResponse


@app.get("/dashboard")
def dashboard():
    return FileResponse("app/static/index.html")