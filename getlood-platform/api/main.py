"""
GETLOOD API Gateway - FastAPI Application
Main entry point for the GETLOOD backend API
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
from typing import Dict, Any

from api.routers import agents, chat, knowledge_bases, desktop, auth, workflows, health
from api.middleware.error_handler import ErrorHandlerMiddleware
from api.middleware.rate_limiter import RateLimitMiddleware
from api.middleware.logging_middleware import LoggingMiddleware
from core.adapters.mindsdb_client import create_client, MindsDBClient
from core.adapters.agent_adapter import AgentAdapter
from core.adapters.knowledge_base_adapter import KnowledgeBaseAdapter
from core.pipeline.pipeline_executor import PipelineExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global state
app_state: Dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("🚀 Starting GETLOOD API Gateway...")

    # Initialize MindsDB client
    logger.info("Connecting to MindsDB...")
    mindsdb_client = create_client()

    # Health check
    health = await mindsdb_client.health_check()
    if not health['sql']:
        raise Exception("MindsDB connection failed!")

    logger.info("✓ Connected to MindsDB")

    # Initialize adapters
    agent_adapter = AgentAdapter(mindsdb_client)
    kb_adapter = KnowledgeBaseAdapter(mindsdb_client)

    # Initialize pipeline executor
    pipeline_executor = PipelineExecutor(
        mindsdb_client=mindsdb_client,
        agent_adapter=agent_adapter,
        kb_adapter=kb_adapter
    )

    # Store in app state
    app_state['mindsdb_client'] = mindsdb_client
    app_state['agent_adapter'] = agent_adapter
    app_state['kb_adapter'] = kb_adapter
    app_state['pipeline_executor'] = pipeline_executor

    logger.info("✓ All services initialized")
    logger.info("🎉 GETLOOD API Gateway is ready!")

    yield

    # Shutdown
    logger.info("🛑 Shutting down GETLOOD API Gateway...")
    await mindsdb_client.close()
    logger.info("✓ Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="GETLOOD API Gateway",
    description="API Gateway for GETLOOD Agentique Platform powered by MindsDB",
    version="3.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8080"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Custom middleware
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(LoggingMiddleware)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add X-Process-Time header to all responses"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Include routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["Agents"])
app.include_router(knowledge_bases.router, prefix="/api/v1/kb", tags=["Knowledge Bases"])
app.include_router(desktop.router, prefix="/api/v1/desktop", tags=["Desktop"])
app.include_router(workflows.router, prefix="/api/v1/workflows", tags=["Workflows"])


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API info"""
    return {
        "name": "GETLOOD API Gateway",
        "version": "3.0.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/health"
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": str(exc),
            "path": str(request.url)
        }
    )


# Helper function to get app state
def get_app_state() -> Dict[str, Any]:
    """Get application state"""
    return app_state


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
