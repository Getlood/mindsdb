"""
Agent Adapter - CRUD operations for MindsDB Agents
Provides high-level interface for agent management
"""

import json
from typing import Dict, Any, Optional, List, AsyncIterator
from dataclasses import dataclass, field, asdict
from datetime import datetime
from uuid import uuid4
import logging

from .mindsdb_client import MindsDBClient, MindsDBQueryError

logger = logging.getLogger(__name__)


@dataclass
class AgentSkill:
    """Represents an agent skill (tool)"""
    name: str
    description: str
    type: str  # 'database', 'api', 'custom'
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Agent:
    """Represents a MindsDB Agent"""
    id: str
    name: str
    project: str
    model: str
    provider: str
    skills: List[str] = field(default_factory=list)
    prompt: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary"""
        data = asdict(self)
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        if self.updated_at:
            data['updated_at'] = self.updated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Agent':
        """Create agent from dictionary"""
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)


@dataclass
class AgentMessage:
    """Represents a message in agent conversation"""
    role: str  # 'user', 'assistant', 'system'
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AgentResponse:
    """Represents agent response"""
    agent_id: str
    agent_name: str
    message: str
    session_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    tokens_used: Optional[int] = None
    duration_ms: Optional[float] = None
    model_used: Optional[str] = None


@dataclass
class AgentSpec:
    """Specification for creating an agent"""
    name: str
    model: str
    project: str = "mindsdb"
    provider: Optional[str] = None
    skills: List[str] = field(default_factory=list)
    prompt: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentAdapter:
    """
    Adapter for MindsDB Agent operations

    Provides high-level CRUD operations and query capabilities for agents.

    Example usage:
        >>> adapter = AgentAdapter(mindsdb_client)
        >>>
        >>> # Create agent
        >>> spec = AgentSpec(
        ...     name="my_agent",
        ...     model="gpt-4",
        ...     skills=["web_search", "sql_query"],
        ...     prompt="You are a helpful assistant"
        ... )
        >>> agent = await adapter.create_agent(spec)
        >>>
        >>> # Query agent with streaming
        >>> async for chunk in adapter.query_agent_stream(
        ...     agent_id=agent.id,
        ...     message="What is the weather today?",
        ...     session_id="session_123"
        ... ):
        ...     print(chunk, end='', flush=True)
    """

    def __init__(self, mindsdb_client: MindsDBClient):
        self.client = mindsdb_client

    async def create_agent(self, spec: AgentSpec) -> Agent:
        """
        Create a new agent in MindsDB

        Args:
            spec: Agent specification

        Returns:
            Created Agent instance

        Raises:
            MindsDBQueryError: If agent creation fails
        """
        # Generate unique ID
        agent_id = f"agent_{uuid4().hex[:12]}"

        # Build CREATE AGENT SQL
        skills_sql = f"[{','.join([f'{s}' for s in spec.skills])}]" if spec.skills else "[]"

        # Escape single quotes in prompt
        prompt_escaped = spec.prompt.replace("'", "''") if spec.prompt else ""

        # Build metadata JSON
        metadata = {
            **spec.metadata,
            "id": agent_id,
            "created_at": datetime.now().isoformat()
        }
        metadata_json = json.dumps(metadata).replace("'", "''")

        query = f"""
            CREATE AGENT {spec.project}.{spec.name}
            USING
                model = '{spec.model}'
        """

        if spec.provider:
            query += f",\n                provider = '{spec.provider}'"

        if spec.skills:
            query += f",\n                skills = {skills_sql}"

        if spec.prompt:
            query += f",\n                prompt = '{prompt_escaped}'"

        # Note: MindsDB doesn't natively support custom metadata in CREATE AGENT
        # We'll store it separately in a metadata table

        try:
            await self.client.execute(query)

            # Store metadata separately
            await self._store_agent_metadata(agent_id, spec.project, spec.name, metadata)

            # Return created agent
            return Agent(
                id=agent_id,
                name=spec.name,
                project=spec.project,
                model=spec.model,
                provider=spec.provider or "mindsdb",
                skills=spec.skills,
                prompt=spec.prompt,
                metadata=metadata,
                created_at=datetime.now()
            )

        except Exception as e:
            logger.error(f"Failed to create agent {spec.name}: {str(e)}")
            raise MindsDBQueryError(f"Agent creation failed: {str(e)}")

    async def get_agent(self, agent_name: str, project: str = "mindsdb") -> Optional[Agent]:
        """
        Get agent by name

        Args:
            agent_name: Name of the agent
            project: Project name (default: "mindsdb")

        Returns:
            Agent instance or None if not found
        """
        try:
            # Query agent from MindsDB
            query = f"""
                SELECT * FROM {project}.agents
                WHERE name = '{agent_name}'
            """
            result = await self.client.execute(query)

            if result.empty:
                return None

            row = result.iloc[0]

            # Get metadata
            metadata = await self._get_agent_metadata(agent_name, project)

            return Agent(
                id=metadata.get("id", f"agent_{uuid4().hex[:12]}"),
                name=row.get("name", agent_name),
                project=project,
                model=row.get("model", "unknown"),
                provider=row.get("provider", "mindsdb"),
                skills=json.loads(row.get("skills", "[]")) if isinstance(row.get("skills"), str) else row.get("skills", []),
                prompt=row.get("prompt"),
                metadata=metadata,
                created_at=row.get("created_at")
            )

        except Exception as e:
            logger.error(f"Failed to get agent {agent_name}: {str(e)}")
            return None

    async def update_agent(
        self,
        agent_name: str,
        project: str = "mindsdb",
        **updates
    ) -> Agent:
        """
        Update agent properties

        Args:
            agent_name: Name of the agent
            project: Project name
            **updates: Properties to update (model, skills, prompt, metadata)

        Returns:
            Updated Agent instance

        Raises:
            MindsDBQueryError: If update fails
        """
        # Get current agent
        agent = await self.get_agent(agent_name, project)
        if not agent:
            raise MindsDBQueryError(f"Agent {agent_name} not found in project {project}")

        # MindsDB doesn't support ALTER AGENT, so we need to drop and recreate
        # First, save conversation history if any
        # Then drop and recreate with new config

        # Build update parts
        update_parts = []

        if "model" in updates:
            update_parts.append(f"model = '{updates['model']}'")
            agent.model = updates["model"]

        if "skills" in updates:
            skills_sql = f"[{','.join([f'{s}' for s in updates['skills']])}]"
            update_parts.append(f"skills = {skills_sql}")
            agent.skills = updates["skills"]

        if "prompt" in updates:
            prompt_escaped = updates["prompt"].replace("'", "''")
            update_parts.append(f"prompt = '{prompt_escaped}'")
            agent.prompt = updates["prompt"]

        if "metadata" in updates:
            agent.metadata.update(updates["metadata"])
            agent.metadata["updated_at"] = datetime.now().isoformat()

        if update_parts:
            try:
                # Drop existing agent
                await self.client.execute(f"DROP AGENT {project}.{agent_name}")

                # Recreate with new config
                query = f"""
                    CREATE AGENT {project}.{agent_name}
                    USING
                        {', '.join(update_parts)}
                """
                await self.client.execute(query)

                # Update metadata
                await self._store_agent_metadata(agent.id, project, agent_name, agent.metadata)

                agent.updated_at = datetime.now()
                return agent

            except Exception as e:
                logger.error(f"Failed to update agent {agent_name}: {str(e)}")
                raise MindsDBQueryError(f"Agent update failed: {str(e)}")

        return agent

    async def delete_agent(self, agent_name: str, project: str = "mindsdb") -> bool:
        """
        Delete agent

        Args:
            agent_name: Name of the agent
            project: Project name

        Returns:
            True if deleted successfully
        """
        try:
            await self.client.execute(f"DROP AGENT {project}.{agent_name}")

            # Delete metadata
            await self._delete_agent_metadata(agent_name, project)

            return True

        except Exception as e:
            logger.error(f"Failed to delete agent {agent_name}: {str(e)}")
            return False

    async def list_agents(
        self,
        project: str = "mindsdb",
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Agent]:
        """
        List all agents in project

        Args:
            project: Project name
            filters: Optional filters (e.g., {"model": "gpt-4"})

        Returns:
            List of Agent instances
        """
        try:
            query = f"SELECT * FROM {project}.agents"

            # Add filters if provided
            if filters:
                conditions = []
                for key, value in filters.items():
                    if isinstance(value, str):
                        conditions.append(f"{key} = '{value}'")
                    else:
                        conditions.append(f"{key} = {value}")

                if conditions:
                    query += f" WHERE {' AND '.join(conditions)}"

            result = await self.client.execute(query)

            agents = []
            for _, row in result.iterrows():
                metadata = await self._get_agent_metadata(row["name"], project)

                agent = Agent(
                    id=metadata.get("id", f"agent_{uuid4().hex[:12]}"),
                    name=row["name"],
                    project=project,
                    model=row.get("model", "unknown"),
                    provider=row.get("provider", "mindsdb"),
                    skills=json.loads(row.get("skills", "[]")) if isinstance(row.get("skills"), str) else row.get("skills", []),
                    prompt=row.get("prompt"),
                    metadata=metadata,
                    created_at=row.get("created_at")
                )
                agents.append(agent)

            return agents

        except Exception as e:
            logger.error(f"Failed to list agents in project {project}: {str(e)}")
            return []

    async def query_agent(
        self,
        agent_name: str,
        message: str,
        session_id: str,
        project: str = "mindsdb",
        stream: bool = False
    ) -> AgentResponse:
        """
        Query agent and get response (non-streaming)

        Args:
            agent_name: Name of the agent
            message: User message
            session_id: Session identifier
            project: Project name
            stream: Whether to use streaming (for compatibility)

        Returns:
            AgentResponse with complete response
        """
        start_time = datetime.now()

        try:
            # Use A2A protocol for querying
            full_agent_name = f"{project}.{agent_name}" if project != "mindsdb" else agent_name

            response_text = await self.client.a2a_send(
                agent_name=full_agent_name,
                message=message,
                session_id=session_id
            )

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            # Get agent details
            agent = await self.get_agent(agent_name, project)

            return AgentResponse(
                agent_id=agent.id if agent else "unknown",
                agent_name=agent_name,
                message=response_text,
                session_id=session_id,
                duration_ms=duration_ms,
                model_used=agent.model if agent else None
            )

        except Exception as e:
            logger.error(f"Failed to query agent {agent_name}: {str(e)}")
            raise MindsDBQueryError(f"Agent query failed: {str(e)}")

    async def query_agent_stream(
        self,
        agent_name: str,
        message: str,
        session_id: str,
        project: str = "mindsdb"
    ) -> AsyncIterator[str]:
        """
        Query agent with streaming response

        Args:
            agent_name: Name of the agent
            message: User message
            session_id: Session identifier
            project: Project name

        Yields:
            Response chunks as they arrive
        """
        try:
            full_agent_name = f"{project}.{agent_name}" if project != "mindsdb" else agent_name

            async for chunk in self.client.a2a_stream(
                agent_name=full_agent_name,
                message=message,
                session_id=session_id
            ):
                yield chunk

        except Exception as e:
            logger.error(f"Failed to stream agent {agent_name}: {str(e)}")
            raise MindsDBQueryError(f"Agent streaming failed: {str(e)}")

    # Helper methods for metadata management

    async def _store_agent_metadata(
        self,
        agent_id: str,
        project: str,
        agent_name: str,
        metadata: Dict[str, Any]
    ):
        """Store agent metadata in a separate table"""
        try:
            # Create metadata table if not exists
            await self.client.execute("""
                CREATE TABLE IF NOT EXISTS agent_metadata (
                    agent_id VARCHAR(36) PRIMARY KEY,
                    project VARCHAR(100),
                    agent_name VARCHAR(100),
                    metadata JSON,
                    updated_at TIMESTAMP
                )
            """)

            # Insert or update metadata
            metadata_json = json.dumps(metadata).replace("'", "''")
            await self.client.execute(f"""
                INSERT INTO agent_metadata (agent_id, project, agent_name, metadata, updated_at)
                VALUES ('{agent_id}', '{project}', '{agent_name}', '{metadata_json}', NOW())
                ON CONFLICT (agent_id) DO UPDATE SET
                    metadata = '{metadata_json}',
                    updated_at = NOW()
            """)

        except Exception as e:
            logger.warning(f"Failed to store agent metadata: {str(e)}")

    async def _get_agent_metadata(self, agent_name: str, project: str) -> Dict[str, Any]:
        """Get agent metadata from table"""
        try:
            result = await self.client.execute(f"""
                SELECT metadata FROM agent_metadata
                WHERE agent_name = '{agent_name}' AND project = '{project}'
            """)

            if not result.empty:
                metadata_str = result.iloc[0]["metadata"]
                return json.loads(metadata_str) if isinstance(metadata_str, str) else metadata_str

        except Exception as e:
            logger.warning(f"Failed to get agent metadata: {str(e)}")

        return {}

    async def _delete_agent_metadata(self, agent_name: str, project: str):
        """Delete agent metadata"""
        try:
            await self.client.execute(f"""
                DELETE FROM agent_metadata
                WHERE agent_name = '{agent_name}' AND project = '{project}'
            """)
        except Exception as e:
            logger.warning(f"Failed to delete agent metadata: {str(e)}")


if __name__ == "__main__":
    import asyncio
    from .mindsdb_client import create_client

    async def main():
        client = create_client()
        adapter = AgentAdapter(client)

        # Create agent
        spec = AgentSpec(
            name="test_agent",
            model="gpt-4",
            skills=["web_search"],
            prompt="You are a helpful assistant",
            metadata={"version": "1.0"}
        )

        agent = await adapter.create_agent(spec)
        print(f"Created agent: {agent.name} (ID: {agent.id})")

        # List agents
        agents = await adapter.list_agents()
        print(f"\nFound {len(agents)} agents")

        # Query agent with streaming
        print("\n" + "="*50)
        print("Streaming response:")
        print("="*50)

        async for chunk in adapter.query_agent_stream(
            agent_name="test_agent",
            message="Hello! What can you do?",
            session_id="test_session_123"
        ):
            print(chunk, end='', flush=True)

        print("\n" + "="*50)

        await client.close()

    asyncio.run(main())
