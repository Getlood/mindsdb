"""Workflows Router - Visual workflow management"""
from fastapi import APIRouter, Depends
from api.routers.auth import get_current_user, User

router = APIRouter()

@router.get("")
async def list_workflows(current_user: User = Depends(get_current_user)):
    """List workflows"""
    return []

@router.post("/{workflow_id}/execute")
async def execute_workflow(workflow_id: str, current_user: User = Depends(get_current_user)):
    """Execute workflow"""
    return {"execution_id": "exec_123", "status": "running"}
