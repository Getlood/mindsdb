"""
Health Check Router
Provides health and readiness endpoints
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
import time
from datetime import datetime

router = APIRouter()


@router.get("")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint

    Returns service status and uptime
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "getlood-api",
        "version": "3.0.0"
    }


@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check endpoint

    Checks if all dependencies are available
    """
    from api.main import get_app_state

    app_state = get_app_state()

    checks = {
        "mindsdb": False,
        "agent_adapter": False,
        "kb_adapter": False,
        "pipeline": False
    }

    # Check MindsDB
    if 'mindsdb_client' in app_state:
        try:
            health = await app_state['mindsdb_client'].health_check()
            checks['mindsdb'] = health.get('sql', False)
        except:
            pass

    # Check adapters
    checks['agent_adapter'] = 'agent_adapter' in app_state
    checks['kb_adapter'] = 'kb_adapter' in app_state
    checks['pipeline'] = 'pipeline_executor' in app_state

    all_ready = all(checks.values())

    return {
        "ready": all_ready,
        "checks": checks,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/live")
async def liveness_check() -> Dict[str, str]:
    """
    Liveness check endpoint

    Simple endpoint to verify the service is running
    """
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat()
    }
