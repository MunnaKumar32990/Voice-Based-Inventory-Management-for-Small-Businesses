"""Seed demo shop data without running the API server.

Usage (from repo root):
    cd backend && python ../scripts/seed_data.py
    # or
    cd backend && python -m app.db.seed
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.db.seed import seed_data  # noqa: E402

if __name__ == "__main__":
    asyncio.run(seed_data())
