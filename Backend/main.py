from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings

app = FastAPI(
    title="Backend Service",
    description="LLM orchestration and LangChain workflow for legal research triage",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "backend",
        "port": settings.backend_port,
        "mcp_url": settings.mcp_base_url
    }


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Backend",
        "description": "LLM orchestration for legal research",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "analyze": "/api/analyze",
            "extract_issue": "/api/extract-issue"
        }
    }
