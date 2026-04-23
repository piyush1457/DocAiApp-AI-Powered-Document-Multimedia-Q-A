"""
Main entry point for the DocAiApp FastAPI backend.
Initializes the application, includes routes, and sets up middleware.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.routes import auth, upload, chat, files, summary

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
        "http://localhost:3003",
        "http://127.0.0.1:3003",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(upload.router, prefix=f"{settings.API_V1_STR}/upload", tags=["upload"])
app.include_router(chat.router, prefix=f"{settings.API_V1_STR}/chat", tags=["chat"])
app.include_router(files.router, prefix=f"{settings.API_V1_STR}/files", tags=["files"])
app.include_router(summary.router, prefix=f"{settings.API_V1_STR}/summary", tags=["summary"])



@app.get("/health")
async def health_check():
    """
    Dedicated health check endpoint for Docker/K8s.
    """
    return {"status": "healthy", "timestamp": settings.VERSION}


@app.get("/")
async def root():
    """
    Health check endpoint.
    """
    return {
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
    }
