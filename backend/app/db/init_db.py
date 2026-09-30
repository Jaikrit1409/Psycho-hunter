from sqlalchemy import text

from app.db.database import Base, engine

# Import all models so SQLAlchemy is aware of them before metadata creation.
from app.models import Briefing, Client, Document, DocumentChunk, Evidence, Source  # noqa: F401


def init_db() -> None:
    """Initialize PostgreSQL extensions and create all configured tables idempotently."""
    if engine.dialect.name == "postgresql":
        with engine.begin() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS sources ADD COLUMN IF NOT EXISTS publisher VARCHAR(255);"
                )
            )

    Base.metadata.create_all(bind=engine)
