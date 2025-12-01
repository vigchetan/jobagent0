"""FastAPI application entry point"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import router
from backend.config import settings
from backend.utils.workspace import ensure_workspace_exists
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Modern lifespan context manager for FastAPI application.

    This replaces the deprecated @app.on_event("startup") decorator.
    Handles startup and shutdown events in a single context manager.
    """
    # Startup
    logger.info("Starting JobAgent0 Resume Parser")
    logger.info(f"Workspace directory: {settings.workspace_path}")
    ensure_workspace_exists()

    yield

    # Shutdown (if needed in the future)
    logger.info("Shutting down JobAgent0 Resume Parser")


# Create FastAPI app with lifespan
app = FastAPI(
    title="JobAgent0 Resume Parser",
    description="Resume upload and parsing service",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS for Chrome Extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,  # Chrome extension origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api", tags=["resume"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "JobApp Resume Parser",
        "status": "running",
        "version": "1.0.0",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True,  # Enable auto-reload during development
    )
