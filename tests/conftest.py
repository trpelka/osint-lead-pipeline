import os
import tempfile
from pathlib import Path

import pytest

# Point the app at a throwaway database before app.main is imported.
_TMP_DIR = Path(tempfile.mkdtemp(prefix="leads-test-"))
os.environ["LEADS_DB"] = str(_TMP_DIR / "leads.db")
os.environ["LEADS_API_KEY"] = "test-key"

from app import main  # noqa: E402
from app.main import get_db  # noqa: E402

# The app creates tables in its lifespan; TestClient without a context manager
# does not run it, so the test suite initialises its throwaway DB explicitly.
main.init_db()


@pytest.fixture(autouse=True)
def clean_leads():
    conn = get_db()
    conn.execute("DELETE FROM leads")
    conn.commit()
    conn.close()
    yield
