"""
Orchestrator API - Main FastAPI application.

Production-grade API for multi-agent orchestration.

Demonstrates:
- API composition with routers
- CORS configuration
- Lifecycle management (startup/shutdown)
- Health checks
- Error handling
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import logging
import sys

from .api import runs, sessions, registries, checkpoints, memory, artifacts
from .api.models import HealthCheckResponse, ErrorResponse
from .services.registry_manager import init_registry_manager, get_registry_manager
from .services.storage import init_storage
from .config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AgentMesh Orchestrator",
    description="Production-scale multi-agent orchestration platform for insurance claims processing",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
# Note: In production, restrict origins to specific domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3016",  # Frontend URL
        "http://localhost:3000",  # Alternative frontend port
        "http://frontend:3000",   # Docker internal
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors.

    Demonstrates: Consistent error response format
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            detail=str(exc),
            error_type=type(exc).__name__,
            timestamp=datetime.utcnow().isoformat() + "Z"
        ).model_dump()
    )


# Include routers
app.include_router(runs.router)
app.include_router(sessions.router)
app.include_router(registries.router)
app.include_router(checkpoints.router)
app.include_router(memory.router)
app.include_router(artifacts.router)


@app.on_event("startup")
async def startup():
    """
    Initialize on startup.

    Demonstrates:
    - Dependency initialization
    - Registry loading
    - Configuration validation
    """
    logger.info("=" * 60)
    logger.info("Starting AgentMesh Orchestrator")
    logger.info("=" * 60)

    try:
        # Load configuration
        config = get_config()
        logger.info(f"Configuration loaded")
        logger.info(f"  - Storage path: {config.storage_path}")
        logger.info(f"  - Tools base URL: {config.tools_base_url}")
        logger.info(f"  - Max workflow duration: {config.workflow.max_duration_seconds}s")

        # Initialize storage
        logger.info("Initializing storage...")
        init_storage(config.storage_path)
        logger.info("Storage initialized successfully")

        # Initialize registries
        logger.info("Initializing registries...")
        init_registry_manager()

        registry = get_registry_manager()
        stats = registry.get_stats()

        logger.info("Registries loaded successfully:")
        logger.info(f"  - Agents: {stats['counts']['agents']}")
        logger.info(f"  - Tools: {stats['counts']['tools']}")
        logger.info(f"  - Models: {stats['counts']['models']}")
        logger.info(f"  - Workflows: {stats['counts']['workflows']}")

        logger.info("=" * 60)
        logger.info("Orchestrator ready - API available at /docs")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Failed to initialize orchestrator: {e}", exc_info=True)
        raise


@app.on_event("shutdown")
async def shutdown():
    """
    Cleanup on shutdown.

    Demonstrates:
    - Graceful shutdown
    - Resource cleanup
    """
    logger.info("Shutting down Orchestrator")

    # Cancel any running workflows
    from .services.workflow_executor import get_workflow_executor
    executor = get_workflow_executor()

    running_sessions = executor.get_running_sessions()
    if running_sessions:
        logger.info(f"Cancelling {len(running_sessions)} running workflows")
        for session_id in running_sessions:
            try:
                await executor.cancel_workflow(session_id)
            except Exception as e:
                logger.error(f"Failed to cancel workflow {session_id}: {e}")

    logger.info("Shutdown complete")


@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint.

    Returns:
        Service information
    """
    return {
        "service": "AgentMesh Orchestrator",
        "version": "1.0.0",
        "status": "healthy",
        "description": "Production-scale multi-agent orchestration platform",
        "documentation": "/docs",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.get("/health", response_model=HealthCheckResponse, tags=["health"])
async def health_check():
    """
    Health check endpoint.

    Returns:
        Health status with registries check

    Demonstrates:
    - System health monitoring
    - Dependency checks
    """
    try:
        # Check if registries are loaded
        registry = get_registry_manager()
        registries_loaded = True

        # Get stats
        stats = registry.get_stats()

        return HealthCheckResponse(
            status="healthy",
            timestamp=datetime.utcnow().isoformat() + "Z",
            version="1.0.0",
            registries_loaded=registries_loaded
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)

        return HealthCheckResponse(
            status="unhealthy",
            timestamp=datetime.utcnow().isoformat() + "Z",
            version="1.0.0",
            registries_loaded=False
        )


@app.get("/stats", tags=["monitoring"])
async def get_stats():
    """
    Get system statistics.

    Returns:
        Comprehensive system stats

    Demonstrates:
    - Observability endpoint
    - System metrics
    """
    from .services.workflow_executor import get_workflow_executor
    from .services.sse_broadcaster import get_broadcaster

    try:
        registry = get_registry_manager()
        executor = get_workflow_executor()
        broadcaster = get_broadcaster()

        return {
            "registries": registry.get_stats(),
            "executor": executor.get_stats(),
            "broadcaster": broadcaster.get_stats(),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    except Exception as e:
        logger.error(f"Failed to get stats: {e}", exc_info=True)
        return {
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
