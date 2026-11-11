import os
import tempfile
from pathlib import Path

import pytest

# Point the app at a throwaway database before app.main is imported.
_TMP_DIR = Path(tempfile.mkdtemp(prefix="leads-test-"))
os.environ["LEADS_DB"] = str(_TMP_DIR / "leads.db")

from app.main import get_db  # noqa: E402


@pytest.fixture(autouse=True)
def clean_leads():
    conn = get_db()
    conn.execute("DELETE FROM leads")
    conn.commit()
    conn.close()
    yield
