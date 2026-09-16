"""
Vercel serverless entrypoint for FastAPI.
Vercel's Python runtime imports `app` from api/index.py.
We re-export the FastAPI app from app.main.
"""
from app.main import app  # noqa: F401

# Vercel expects `app` to be the ASGI callable
