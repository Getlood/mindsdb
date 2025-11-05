"""
GETLOOD Core - Business logic and MindsDB integration
"""

__version__ = "3.0.0"
__author__ = "GETLOOD Team"
__license__ = "MIT"

from .adapters.mindsdb_client import MindsDBClient, MindsDBConfig, create_client
from .adapters.agent_adapter import AgentAdapter, Agent, AgentSpec
from .adapters.knowledge_base_adapter import (
    KnowledgeBaseAdapter,
    KnowledgeBase,
    KnowledgeBaseSpec,
    Document,
    SearchResult
)

__all__ = [
    # Client
    "MindsDBClient",
    "MindsDBConfig",
    "create_client",
    # Agents
    "AgentAdapter",
    "Agent",
    "AgentSpec",
    # Knowledge Bases
    "KnowledgeBaseAdapter",
    "KnowledgeBase",
    "KnowledgeBaseSpec",
    "Document",
    "SearchResult",
]
