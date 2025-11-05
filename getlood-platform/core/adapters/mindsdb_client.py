"""
MindsDB Client - Unified client for MindsDB interactions
Supports SQL, HTTP, and A2A protocols
"""

import asyncio
import json
import aiohttp
import pandas as pd
from typing import Dict, Any, Optional, AsyncIterator, List
from dataclasses import dataclass
from urllib.parse import urljoin
import logging

logger = logging.getLogger(__name__)


@dataclass
class MindsDBConfig:
    """MindsDB connection configuration"""
    http_url: str = "http://localhost:47334"
    sql_url: str = "postgresql://mindsdb:mindsdb@localhost:47334/mindsdb"
    a2a_url: str = "http://localhost:47334/a2a"
    api_key: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3


class MindsDBException(Exception):
    """Base exception for MindsDB operations"""
    pass


class MindsDBConnectionError(MindsDBException):
    """Connection-related errors"""
    pass


class MindsDBQueryError(MindsDBException):
    """Query execution errors"""
    pass


class SQLClient:
    """SQL protocol client for MindsDB"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self._engine = None

    async def connect(self):
        """Initialize database connection pool"""
        from sqlalchemy.ext.asyncio import create_async_engine

        self._engine = create_async_engine(
            self.connection_string,
            echo=False,
            pool_size=20,
            max_overflow=40,
            pool_pre_ping=True
        )

    async def execute(self, query: str, params: Optional[Dict] = None) -> pd.DataFrame:
        """
        Execute SQL query and return results as DataFrame

        Args:
            query: SQL query string
            params: Optional query parameters

        Returns:
            DataFrame with query results

        Raises:
            MindsDBQueryError: If query execution fails
        """
        if not self._engine:
            await self.connect()

        try:
            async with self._engine.begin() as conn:
                result = await conn.execute(query, params or {})

                if result.returns_rows:
                    rows = result.fetchall()
                    columns = result.keys()
                    return pd.DataFrame(rows, columns=columns)
                else:
                    # For INSERT/UPDATE/DELETE, return affected rows
                    return pd.DataFrame({'affected_rows': [result.rowcount]})

        except Exception as e:
            logger.error(f"SQL query failed: {query[:100]}... Error: {str(e)}")
            raise MindsDBQueryError(f"Query execution failed: {str(e)}")

    async def close(self):
        """Close database connection"""
        if self._engine:
            await self._engine.dispose()


class HTTPClient:
    """HTTP REST API client for MindsDB"""

    def __init__(self, base_url: str, api_key: Optional[str] = None, timeout: int = 30):
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if not self._session:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            self._session = aiohttp.ClientSession(
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self._session

    async def request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to MindsDB API

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters

        Returns:
            Response JSON

        Raises:
            MindsDBConnectionError: If request fails
        """
        session = await self._get_session()
        url = urljoin(self.base_url, endpoint)

        try:
            async with session.request(
                method=method,
                url=url,
                json=data,
                params=params
            ) as response:
                response.raise_for_status()
                return await response.json()

        except aiohttp.ClientError as e:
            logger.error(f"HTTP request failed: {method} {url} - Error: {str(e)}")
            raise MindsDBConnectionError(f"HTTP request failed: {str(e)}")

    async def close(self):
        """Close HTTP session"""
        if self._session:
            await self._session.close()


class A2AClient:
    """Agent-to-Agent protocol client for MindsDB"""

    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url
        self.api_key = api_key

    async def stream(
        self,
        agent_name: str,
        message: str,
        session_id: str,
        task_id: Optional[str] = None,
        accepted_output_modes: List[str] = None
    ) -> AsyncIterator[str]:
        """
        Stream agent response via A2A protocol

        Args:
            agent_name: Name of the agent to query
            message: User message
            session_id: Session identifier
            task_id: Optional task identifier
            accepted_output_modes: List of accepted output modes

        Yields:
            Streamed response chunks

        Raises:
            MindsDBConnectionError: If streaming fails
        """
        task_id = task_id or f"task_{session_id}"
        accepted_output_modes = accepted_output_modes or ["text/plain"]

        payload = {
            "jsonrpc": "2.0",
            "id": task_id,
            "method": "tasks/sendSubscribe",
            "params": {
                "id": task_id,
                "sessionId": session_id,
                "message": {
                    "role": "user",
                    "parts": [{"type": "text", "text": message}],
                    "metadata": {"agentName": agent_name}
                },
                "acceptedOutputModes": accepted_output_modes
            }
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url,
                    json=payload,
                    headers=headers
                ) as response:
                    response.raise_for_status()

                    # Parse SSE (Server-Sent Events)
                    async for line in response.content:
                        decoded = line.decode('utf-8').strip()

                        if decoded.startswith('data: '):
                            data = decoded[6:]  # Remove 'data: ' prefix

                            if data == '[DONE]':
                                break

                            try:
                                chunk = json.loads(data)

                                # Extract text from chunk
                                if 'result' in chunk and 'parts' in chunk['result']:
                                    for part in chunk['result']['parts']:
                                        if part.get('type') == 'text':
                                            yield part.get('text', '')

                            except json.JSONDecodeError:
                                logger.warning(f"Failed to parse SSE chunk: {data}")
                                continue

        except aiohttp.ClientError as e:
            logger.error(f"A2A streaming failed: {str(e)}")
            raise MindsDBConnectionError(f"A2A streaming failed: {str(e)}")

    async def send(
        self,
        agent_name: str,
        message: str,
        session_id: str,
        task_id: Optional[str] = None
    ) -> str:
        """
        Send message to agent and get complete response (non-streaming)

        Args:
            agent_name: Name of the agent to query
            message: User message
            session_id: Session identifier
            task_id: Optional task identifier

        Returns:
            Complete agent response
        """
        chunks = []
        async for chunk in self.stream(agent_name, message, session_id, task_id):
            chunks.append(chunk)

        return ''.join(chunks)


class MindsDBClient:
    """
    Unified MindsDB client supporting SQL, HTTP, and A2A protocols

    Example usage:
        >>> config = MindsDBConfig(http_url="http://localhost:47334")
        >>> client = MindsDBClient(config)
        >>>
        >>> # SQL query
        >>> result = await client.execute("SELECT * FROM models")
        >>>
        >>> # HTTP request
        >>> agents = await client.http.request("GET", "/api/agents")
        >>>
        >>> # A2A streaming
        >>> async for chunk in client.a2a_stream("my_agent", "Hello!", "session_123"):
        >>>     print(chunk, end='', flush=True)
    """

    def __init__(self, config: MindsDBConfig):
        self.config = config

        # Initialize protocol clients
        self.sql = SQLClient(config.sql_url)
        self.http = HTTPClient(config.http_url, config.api_key, config.timeout)
        self.a2a = A2AClient(config.a2a_url, config.api_key)

    async def execute(self, query: str, params: Optional[Dict] = None) -> pd.DataFrame:
        """Execute SQL query (convenience method)"""
        return await self.sql.execute(query, params)

    async def a2a_stream(
        self,
        agent_name: str,
        message: str,
        session_id: str
    ) -> AsyncIterator[str]:
        """Stream agent response (convenience method)"""
        async for chunk in self.a2a.stream(agent_name, message, session_id):
            yield chunk

    async def a2a_send(
        self,
        agent_name: str,
        message: str,
        session_id: str
    ) -> str:
        """Send agent message and get complete response (convenience method)"""
        return await self.a2a.send(agent_name, message, session_id)

    async def health_check(self) -> Dict[str, bool]:
        """
        Check health of all MindsDB endpoints

        Returns:
            Dictionary with health status for each protocol
        """
        health = {
            "sql": False,
            "http": False,
            "a2a": False
        }

        # Check SQL
        try:
            await self.execute("SELECT 1")
            health["sql"] = True
        except Exception as e:
            logger.error(f"SQL health check failed: {str(e)}")

        # Check HTTP
        try:
            await self.http.request("GET", "/api/status")
            health["http"] = True
        except Exception as e:
            logger.error(f"HTTP health check failed: {str(e)}")

        # Check A2A (we can't easily test without an agent, so mark as True if HTTP works)
        health["a2a"] = health["http"]

        return health

    async def close(self):
        """Close all connections"""
        await self.sql.close()
        await self.http.close()


# Convenience function for quick initialization
def create_client(
    http_url: str = "http://localhost:47334",
    sql_url: str = "postgresql://mindsdb:mindsdb@localhost:47334/mindsdb",
    a2a_url: str = "http://localhost:47334/a2a",
    api_key: Optional[str] = None
) -> MindsDBClient:
    """
    Create MindsDB client with default or custom configuration

    Args:
        http_url: MindsDB HTTP API URL
        sql_url: MindsDB SQL connection string
        a2a_url: MindsDB A2A endpoint URL
        api_key: Optional API key for authentication

    Returns:
        Configured MindsDBClient instance
    """
    config = MindsDBConfig(
        http_url=http_url,
        sql_url=sql_url,
        a2a_url=a2a_url,
        api_key=api_key
    )
    return MindsDBClient(config)


if __name__ == "__main__":
    # Example usage
    async def main():
        client = create_client()

        # Test health
        health = await client.health_check()
        print(f"Health check: {health}")

        # Execute SQL query
        result = await client.execute("SHOW DATABASES")
        print(f"\nDatabases:\n{result}")

        await client.close()

    asyncio.run(main())
