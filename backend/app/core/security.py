"""
Security helpers for ClausePilot backend.
- Allowed MIME/extension validation
- File size validation
- Safe server-side filename generation (UUID-based)
"""
from __future__ import annotations

import re
import uuid
from pathlib import Path

# Explicitly allowed MIME types for upload
ALLOWED_MIME_TYPES: frozenset[str] = frozenset(
    {
        "application/pdf",
    }
)

# Extension whitelist (secondary check)
ALLOWED_EXTENSIONS: frozenset[str] = frozenset({".pdf"})

# Reject filenames with path traversal or null bytes
_UNSAFE_FILENAME_PATTERN = re.compile(r"[\\/:*?\"<>|\x00]")


def validate_file_type(filename: str, content_type: str) -> None:
    """
    Raise ValueError if the file type is not permitted.
    Checks both the MIME type and the file extension.
    """
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{suffix}'. "
            f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    if content_type not in ALLOWED_MIME_TYPES:
        raise ValueError(
            f"Unsupported MIME type '{content_type}'. "
            f"Allowed: {', '.join(sorted(ALLOWED_MIME_TYPES))}"
        )


def validate_file_size(size_bytes: int, max_bytes: int) -> None:
    """Raise ValueError if the file exceeds the allowed size."""
    if size_bytes > max_bytes:
        max_mb = max_bytes / (1024 * 1024)
        actual_mb = size_bytes / (1024 * 1024)
        raise ValueError(
            f"File size {actual_mb:.1f} MB exceeds the maximum allowed "
            f"size of {max_mb:.1f} MB."
        )


def sanitize_original_filename(filename: str) -> str:
    """
    Return a sanitised display name for metadata storage only.
    Never use this as a filesystem path.
    """
    # Strip directory components
    name = Path(filename).name
    # Replace unsafe characters with underscores
    name = _UNSAFE_FILENAME_PATTERN.sub("_", name)
    # Collapse multiple underscores
    name = re.sub(r"_+", "_", name).strip("_")
    # Limit length
    if len(name) > 255:
        stem = Path(name).stem[:200]
        suffix = Path(name).suffix
        name = stem + suffix
    return name or "unnamed_document.pdf"


def generate_server_filename(original_filename: str) -> str:
    """
    Generate a UUID-based server-side filename.
    The original filename is NEVER used as a filesystem path.
    """
    suffix = Path(original_filename).suffix.lower() or ".pdf"
    return f"{uuid.uuid4()}{suffix}"
