from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings

app = FastAPI(
    title="MCP Service",
    description="Wrapper service for external legal APIs (CourtListener, Open States, IPinfo)",
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
        "service": "mcp",
        "port": settings.mcp_port
    }


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "MCP",
        "description": "Wrapper service for external legal APIs",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "geo": "/geo/*",
            "cases": "/cases/*",
            "bills": "/bills/*"
        }
    }
