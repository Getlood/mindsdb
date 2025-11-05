"""Desktop Router - Window management"""
from fastapi import APIRouter, Depends
from api.routers.auth import get_current_user, User

router = APIRouter()

@router.get("/state/{desktop_id}")
async def get_desktop_state(desktop_id: int, current_user: User = Depends(get_current_user)):
    """Get desktop state"""
    return {"desktop_id": desktop_id, "windows": []}

@router.post("/windows")
async def create_window(current_user: User = Depends(get_current_user)):
    """Create window"""
    return {"window_id": "window_123"}
