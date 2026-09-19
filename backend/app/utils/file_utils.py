"""File system utility helpers for ClausePilot."""
from __future__ import annotations

from pathlib import Path

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_upload_dir() -> Path:
    """Return the upload directory, creating it if necessary."""
    path = Path(get_settings().upload_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_document_path(server_filename: str) -> Path:
    """
    Return the absolute path for a stored document.
    Only server-generated filenames (UUIDs) are accepted here.
    """
    upload_dir = get_upload_dir()
    # Safety: strip any path components — server_filename must be a bare name
    safe_name = Path(server_filename).name
    return upload_dir / safe_name


def delete_document_file(server_filename: str) -> bool:
    """
    Delete the stored file.  Returns True if deleted, False if not found.
    """
    path = get_document_path(server_filename)
    if path.exists():
        path.unlink()
        logger.info("Deleted file: %s", path.name)
        return True
    logger.warning("File not found for deletion: %s", path.name)
    return False
