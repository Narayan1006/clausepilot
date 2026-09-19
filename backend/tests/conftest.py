"""
pytest configuration for ClausePilot backend tests.
Sets PYTHONPATH so that `app` package is importable.
"""
import sys
import os
from pathlib import Path

# Add backend root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Override settings for tests — use temp paths
os.environ.setdefault("DATABASE_PATH", ":memory:")
os.environ.setdefault("UPLOAD_DIR", "/tmp/clausepilot_test_uploads")
os.environ.setdefault("GROQ_API_KEY", "")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")
