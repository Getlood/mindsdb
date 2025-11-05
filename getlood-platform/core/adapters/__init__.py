"""
MindsDB Adapters - High-level interfaces for MindsDB operations
"""

from .mindsdb_client import MindsDBClient, MindsDBConfig, create_client
from .agent_adapter import AgentAdapter, Agent, AgentSpec, AgentResponse
from .knowledge_base_adapter import (
    KnowledgeBaseAdapter,
    KnowledgeBase,
    KnowledgeBaseSpec,
    Document,
    SearchResult
)

__all__ = [
    "MindsDBClient",
    "MindsDBConfig",
    "create_client",
    "AgentAdapter",
    "Agent",
    "AgentSpec",
    "AgentResponse",
    "KnowledgeBaseAdapter",
    "KnowledgeBase",
    "KnowledgeBaseSpec",
    "Document",
    "SearchResult",
]
