from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import settings
from routers import analyze, dev, websocket_analyze
from services.mcp_client import initialize_mcp_client, close_mcp_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for application startup and shutdown.
    Initializes MCP client connection on startup and closes on shutdown.
    """
    # Startup: Initialize MCP client
    await initialize_mcp_client()
    print(f"[Backend] MCP client connected to {settings.mcp_base_url}/mcp")
    
    yield
    
    # Shutdown: Close MCP client
    await close_mcp_client()
    print("[Backend] MCP client disconnected")


app = FastAPI(
    title="Precedent Brief - Backend API",
    description="""
AI-powered legal research triage service.

This Backend orchestrates LangChain workflows to:
- Extract legal issues from plain-English questions
- Search case law and legislation via the MCP service
- Reduce results to only pertinent authorities
- Generate structured research briefs

The Backend sits between the Frontend and the MCP wrapper service,
managing all LLM interactions and workflow orchestration.
    """,
    version="1.0.0",
    contact={
        "name": "Precedent Brief",
    },
    license_info={
        "name": "Proprietary"
    },
    lifespan=lifespan
)

# CORS middleware - Required for WebSocket connections from browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(analyze.router, tags=["analysis"])
app.include_router(websocket_analyze.router, tags=["websocket"])
app.include_router(dev.router, tags=["development"])


@app.get("/health", tags=["system"])
async def health_check():
    """
    Health check endpoint.
    
    Returns service status and configuration information.
    """
    return {
        "status": "ok",
        "service": "backend",
        "port": settings.backend_port,
        "mcp_url": settings.mcp_base_url,
        "llm_model": settings.anthropic_model
    }


@app.get("/", tags=["system"])
async def root():
    """
    Root endpoint with service information.
    
    Provides an overview of available endpoints and service metadata.
    """
    return {
        "service": "Precedent Brief - Backend",
        "description": "LLM orchestration and LangChain workflow for legal research triage",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health",
            "analyze": "/api/analyze"
        }
    }
