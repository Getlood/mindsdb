"""
Agents Router
CRUD operations for MindsDB agents
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from api.routers.auth import get_current_user, User
from core.adapters.agent_adapter import AgentAdapter, Agent, AgentSpec

router = APIRouter()


# Models
class AgentCreate(BaseModel):
    name: str
    model: str
    provider: Optional[str] = None
    skills: List[str] = []
    prompt: Optional[str] = None
    metadata: Dict[str, Any] = {}


class AgentUpdate(BaseModel):
    model: Optional[str] = None
    skills: Optional[List[str]] = None
    prompt: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AgentResponse(BaseModel):
    id: str
    name: str
    model: str
    provider: str
    skills: List[str]
    prompt: Optional[str]
    metadata: Dict[str, Any]
    created_at: Optional[datetime]


class AgentQueryRequest(BaseModel):
    message: str
    session_id: str
    stream: bool = False


class AgentQueryResponse(BaseModel):
    agent_id: str
    agent_name: str
    message: str
    session_id: str
    duration_ms: float
    tokens_used: Optional[int] = None


# Routes
@router.get("", response_model=List[AgentResponse])
async def list_agents(
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """
    List all agents

    Returns list of agents accessible to the current user
    """
    from api.main import get_app_state

    app_state = get_app_state()
    agent_adapter: AgentAdapter = app_state['agent_adapter']

    project = f"user_{current_user.id}"

    agents = await agent_adapter.list_agents(project=project)

    # Convert to response model
    response = [
        AgentResponse(
            id=agent.id,
            name=agent.name,
            model=agent.model,
            provider=agent.provider,
            skills=agent.skills,
            prompt=agent.prompt,
            metadata=agent.metadata,
            created_at=agent.created_at
        )
        for agent in agents
    ]

    return response[skip:skip + limit]


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_data: AgentCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new agent

    Creates an agent in the user's project
    """
    from api.main import get_app_state

    app_state = get_app_state()
    agent_adapter: AgentAdapter = app_state['agent_adapter']

    project = f"user_{current_user.id}"

    # Create agent spec
    spec = AgentSpec(
        name=agent_data.name,
        model=agent_data.model,
        provider=agent_data.provider,
        project=project,
        skills=agent_data.skills,
        prompt=agent_data.prompt,
        metadata={
            **agent_data.metadata,
            "created_by": current_user.id
        }
    )

    # Create agent
    agent = await agent_adapter.create_agent(spec)

    return AgentResponse(
        id=agent.id,
        name=agent.name,
        model=agent.model,
        provider=agent.provider,
        skills=agent.skills,
        prompt=agent.prompt,
        metadata=agent.metadata,
        created_at=agent.created_at
    )


@router.get("/{agent_name}", response_model=AgentResponse)
async def get_agent(
    agent_name: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get agent by name

    Returns agent details
    """
    from api.main import get_app_state

    app_state = get_app_state()
    agent_adapter: AgentAdapter = app_state['agent_adapter']

    project = f"user_{current_user.id}"

    agent = await agent_adapter.get_agent(agent_name, project=project)

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_name}' not found"
        )

    return AgentResponse(
        id=agent.id,
        name=agent.name,
        model=agent.model,
        provider=agent.provider,
        skills=agent.skills,
        prompt=agent.prompt,
        metadata=agent.metadata,
        created_at=agent.created_at
    )


@router.put("/{agent_name}", response_model=AgentResponse)
async def update_agent(
    agent_name: str,
    updates: AgentUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Update agent

    Updates agent configuration
    """
    from api.main import get_app_state

    app_state = get_app_state()
    agent_adapter: AgentAdapter = app_state['agent_adapter']

    project = f"user_{current_user.id}"

    # Build updates dict (only non-None values)
    update_data = {}
    if updates.model is not None:
        update_data['model'] = updates.model
    if updates.skills is not None:
        update_data['skills'] = updates.skills
    if updates.prompt is not None:
        update_data['prompt'] = updates.prompt
    if updates.metadata is not None:
        update_data['metadata'] = updates.metadata

    agent = await agent_adapter.update_agent(
        agent_name=agent_name,
        project=project,
        **update_data
    )

    return AgentResponse(
        id=agent.id,
        name=agent.name,
        model=agent.model,
        provider=agent.provider,
        skills=agent.skills,
        prompt=agent.prompt,
        metadata=agent.metadata,
        created_at=agent.created_at
    )


@router.delete("/{agent_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_name: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete agent

    Removes agent from user's project
    """
    from api.main import get_app_state

    app_state = get_app_state()
    agent_adapter: AgentAdapter = app_state['agent_adapter']

    project = f"user_{current_user.id}"

    success = await agent_adapter.delete_agent(agent_name, project=project)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_name}' not found"
        )

    return None


@router.post("/{agent_name}/query", response_model=AgentQueryResponse)
async def query_agent(
    agent_name: str,
    query: AgentQueryRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Query agent

    Sends message to agent and gets response
    """
    from api.main import get_app_state

    app_state = get_app_state()
    agent_adapter: AgentAdapter = app_state['agent_adapter']

    project = f"user_{current_user.id}"

    # Query agent
    response = await agent_adapter.query_agent(
        agent_name=agent_name,
        message=query.message,
        session_id=query.session_id,
        project=project,
        stream=query.stream
    )

    return AgentQueryResponse(
        agent_id=response.agent_id,
        agent_name=response.agent_name,
        message=response.message,
        session_id=response.session_id,
        duration_ms=response.duration_ms,
        tokens_used=response.tokens_used
    )
