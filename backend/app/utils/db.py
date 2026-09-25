"""Plain SQLite persistence layer for ClausePilot.

Design principles:
- No ORM in Phase 1 — raw sqlite3 only.
- Schema is defined here; services call db.py functions directly.
- A proper ORM (e.g. SQLAlchemy, SQLModel) can be layered on later
  without restructuring the application because all DB access is
  isolated to this module and the service layer.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# ─────────────────────────────────────────────────────────────
# DDL
# ─────────────────────────────────────────────────────────────

_CREATE_DOCUMENTS = """
CREATE TABLE IF NOT EXISTS documents (
    id                  TEXT PRIMARY KEY,
    original_filename   TEXT NOT NULL,
    server_filename     TEXT NOT NULL UNIQUE,
    file_size_bytes     INTEGER NOT NULL,
    page_count          INTEGER NOT NULL DEFAULT 0,
    upload_timestamp    TEXT NOT NULL,
    processing_status   TEXT NOT NULL DEFAULT 'uploaded',
    error_message       TEXT
);
"""

_CREATE_DOCUMENT_PAGES = """
CREATE TABLE IF NOT EXISTS document_pages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id     TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_number     INTEGER NOT NULL,
    text            TEXT NOT NULL DEFAULT '',
    UNIQUE (document_id, page_number)
);
"""

_CREATE_CHUNKS = """
CREATE TABLE IF NOT EXISTS chunks (
    id                  TEXT PRIMARY KEY,
    document_id         TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_number         INTEGER NOT NULL,
    chunk_index         INTEGER NOT NULL,
    text                TEXT NOT NULL,
    embedding_reference TEXT,
    UNIQUE (document_id, chunk_index)
);
"""

_CREATE_CLAUSES = """
CREATE TABLE IF NOT EXISTS clauses (
    id              TEXT PRIMARY KEY,
    document_id     TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_number     INTEGER NOT NULL,
    clause_number   TEXT,
    title           TEXT,
    text            TEXT NOT NULL,
    category        TEXT,
    importance      TEXT NOT NULL DEFAULT 'MEDIUM'
);
"""

_CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_doc_pages_doc_id ON document_pages(document_id);",
    "CREATE INDEX IF NOT EXISTS idx_doc_pages_lookup ON document_pages(document_id, page_number);",
    "CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON chunks(document_id);",
    "CREATE INDEX IF NOT EXISTS idx_chunks_lookup ON chunks(document_id, chunk_index);",
    "CREATE INDEX IF NOT EXISTS idx_clauses_doc_id ON clauses(document_id);",
    "CREATE INDEX IF NOT EXISTS idx_clauses_category ON clauses(category);",
    "CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(processing_status);",
]

_ALL_TABLES = [
    _CREATE_DOCUMENTS,
    _CREATE_DOCUMENT_PAGES,
    _CREATE_CHUNKS,
    _CREATE_CLAUSES,
]

# ─────────────────────────────────────────────────────────────
# Connection helper
# ─────────────────────────────────────────────────────────────


def _get_db_path() -> str:
    return get_settings().database_path


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Yield a sqlite3 connection with WAL journal mode and row factory.
    Foreign keys and performance optimizations are enforced.
    """
    path = _get_db_path()
    # Ensure parent directory exists
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-64000")  # 64MB memory cache
    conn.execute("PRAGMA temp_store=MEMORY")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────
# Initialisation
# ─────────────────────────────────────────────────────────────


def init_db() -> None:
    """Create all tables and performance indices if they do not exist. Safe to call multiple times."""
    logger.info("Initialising database at %s", _get_db_path())
    with get_connection() as conn:
        for ddl in _ALL_TABLES:
            conn.execute(ddl)
        for idx in _CREATE_INDEXES:
            conn.execute(idx)
    logger.info("Database and performance indices ready")
