import os

import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url

from app.core.config import settings
from app.db.database import engine


@pytest.mark.skipif(
    not os.getenv("PSYCHO_HUNTER_DB_TEST", "").lower() in {"1", "true", "yes"},
    reason="Live database connectivity test is disabled by default.",
)
def test_database_connection() -> None:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        assert result.scalar_one() == 1


def test_database_url_is_configured() -> None:
    parsed = make_url(settings.DATABASE_URL)
    assert parsed.get_backend_name() == "postgresql"
    assert parsed.username == "psycho_hunter"
    assert parsed.database == "psycho_hunter"
