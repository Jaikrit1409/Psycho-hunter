from app.db.database import Base
from app.db.init_db import init_db


def test_init_db_importable() -> None:
    assert callable(init_db)


def test_expected_model_tables_are_registered() -> None:
    expected_tables = {
        "clients",
        "sources",
        "documents",
        "document_chunks",
        "evidence",
        "briefings",
    }

    actual_tables = {table.name for table in Base.metadata.sorted_tables}
    assert expected_tables.issubset(actual_tables)
