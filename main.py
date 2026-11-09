"""Compatibility entry point; canonical FastAPI app lives in backend/app."""

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app  # noqa: E402

__all__ = ["app"]
