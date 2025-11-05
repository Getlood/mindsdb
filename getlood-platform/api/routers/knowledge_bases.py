"""Knowledge Bases Router - CRUD for vector search"""
from fastapi import APIRouter, Depends
from typing import List
from api.routers.auth import get_current_user, User

router = APIRouter()

@router.get("")
async def list_knowledge_bases(current_user: User = Depends(get_current_user)):
    """List all knowledge bases"""
    return []

@router.post("")
async def create_knowledge_base(current_user: User = Depends(get_current_user)):
    """Create knowledge base"""
    return {"message": "KB created"}
