"""
Knowledge Base Adapter - Vector search and RAG operations
Provides interface for MindsDB Knowledge Bases
"""

import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from datetime import datetime
from uuid import uuid4
import logging

from .mindsdb_client import MindsDBClient, MindsDBQueryError

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """Represents a document in knowledge base"""
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Document':
        """Create from dictionary"""
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


@dataclass
class SearchResult:
    """Represents a search result"""
    document: Document
    score: float  # Similarity score (0-1)
    rank: int  # Result rank (1-based)


@dataclass
class KnowledgeBase:
    """Represents a MindsDB Knowledge Base"""
    id: str
    name: str
    project: str
    model: str  # Embedding model
    storage: str  # Vector DB (chromadb, pinecone, weaviate, etc.)
    table_name: Optional[str] = None  # Source data table
    content_columns: List[str] = field(default_factory=list)
    metadata_columns: List[str] = field(default_factory=list)
    document_count: int = 0
    created_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        return data


@dataclass
class KnowledgeBaseSpec:
    """Specification for creating a knowledge base"""
    name: str
    project: str = "mindsdb"
    model: str = "sentence-transformers/all-MiniLM-L6-v2"  # Default embedding model
    storage: str = "chromadb"  # Default vector DB
    table_name: Optional[str] = None
    content_columns: List[str] = field(default_factory=list)
    metadata_columns: List[str] = field(default_factory=list)
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class KnowledgeBaseAdapter:
    """
    Adapter for MindsDB Knowledge Base operations

    Provides high-level interface for creating, querying, and managing
    knowledge bases with vector search capabilities.

    Example usage:
        >>> adapter = KnowledgeBaseAdapter(mindsdb_client)
        >>>
        >>> # Create knowledge base
        >>> spec = KnowledgeBaseSpec(
        ...     name="docs_kb",
        ...     storage="chromadb",
        ...     table_name="documents",
        ...     content_columns=["title", "content"],
        ...     metadata_columns=["author", "created_at"]
        ... )
        >>> kb = await adapter.create_knowledge_base(spec)
        >>>
        >>> # Insert documents
        >>> docs = [
        ...     Document(id="doc1", content="MindsDB is awesome", metadata={"author": "Alice"}),
        ...     Document(id="doc2", content="AI agents are powerful", metadata={"author": "Bob"})
        ... ]
        >>> await adapter.insert_documents(kb.id, docs)
        >>>
        >>> # Semantic search
        >>> results = await adapter.search(kb.id, "What is MindsDB?", top_k=5)
        >>> for result in results:
        ...     print(f"Score: {result.score:.3f} - {result.document.content}")
    """

    def __init__(self, mindsdb_client: MindsDBClient):
        self.client = mindsdb_client

    async def create_knowledge_base(self, spec: KnowledgeBaseSpec) -> KnowledgeBase:
        """
        Create a new knowledge base

        Args:
            spec: Knowledge base specification

        Returns:
            Created KnowledgeBase instance

        Raises:
            MindsDBQueryError: If creation fails
        """
        kb_id = f"kb_{uuid4().hex[:12]}"

        try:
            # Build CREATE KNOWLEDGE BASE SQL
            query_parts = [
                f"CREATE KNOWLEDGE BASE {spec.project}.{spec.name}",
                "USING"
            ]

            using_parts = [
                f"model = '{spec.model}'",
                f"storage = '{spec.storage}'"
            ]

            if spec.table_name:
                using_parts.append(f"table = '{spec.table_name}'")

            if spec.content_columns:
                columns_str = ', '.join([f"'{col}'" for col in spec.content_columns])
                using_parts.append(f"content_columns = [{columns_str}]")

            if spec.metadata_columns:
                columns_str = ', '.join([f"'{col}'" for col in spec.metadata_columns])
                using_parts.append(f"metadata_columns = [{columns_str}]")

            query_parts.append(",\n    ".join(using_parts))
            query = "\n".join(query_parts)

            await self.client.execute(query)

            # Store metadata
            metadata = {
                **spec.metadata,
                "id": kb_id,
                "description": spec.description,
                "created_at": datetime.now().isoformat()
            }
            await self._store_kb_metadata(kb_id, spec.project, spec.name, metadata)

            return KnowledgeBase(
                id=kb_id,
                name=spec.name,
                project=spec.project,
                model=spec.model,
                storage=spec.storage,
                table_name=spec.table_name,
                content_columns=spec.content_columns,
                metadata_columns=spec.metadata_columns,
                created_at=datetime.now(),
                metadata=metadata
            )

        except Exception as e:
            logger.error(f"Failed to create knowledge base {spec.name}: {str(e)}")
            raise MindsDBQueryError(f"Knowledge base creation failed: {str(e)}")

    async def get_knowledge_base(
        self,
        name: str,
        project: str = "mindsdb"
    ) -> Optional[KnowledgeBase]:
        """
        Get knowledge base by name

        Args:
            name: Name of the knowledge base
            project: Project name

        Returns:
            KnowledgeBase instance or None if not found
        """
        try:
            # Query knowledge base info
            query = f"""
                SELECT * FROM information_schema.knowledge_bases
                WHERE knowledge_base_name = '{name}'
                AND project = '{project}'
            """
            result = await self.client.execute(query)

            if result.empty:
                return None

            row = result.iloc[0]
            metadata = await self._get_kb_metadata(name, project)

            return KnowledgeBase(
                id=metadata.get("id", f"kb_{uuid4().hex[:12]}"),
                name=name,
                project=project,
                model=row.get("model", "unknown"),
                storage=row.get("storage", "unknown"),
                table_name=row.get("table_name"),
                content_columns=json.loads(row.get("content_columns", "[]")),
                metadata_columns=json.loads(row.get("metadata_columns", "[]")),
                created_at=row.get("created_at"),
                metadata=metadata
            )

        except Exception as e:
            logger.error(f"Failed to get knowledge base {name}: {str(e)}")
            return None

    async def delete_knowledge_base(
        self,
        name: str,
        project: str = "mindsdb"
    ) -> bool:
        """
        Delete knowledge base

        Args:
            name: Name of the knowledge base
            project: Project name

        Returns:
            True if deleted successfully
        """
        try:
            await self.client.execute(f"DROP KNOWLEDGE BASE {project}.{name}")
            await self._delete_kb_metadata(name, project)
            return True

        except Exception as e:
            logger.error(f"Failed to delete knowledge base {name}: {str(e)}")
            return False

    async def list_knowledge_bases(
        self,
        project: str = "mindsdb"
    ) -> List[KnowledgeBase]:
        """
        List all knowledge bases in project

        Args:
            project: Project name

        Returns:
            List of KnowledgeBase instances
        """
        try:
            query = f"""
                SELECT * FROM information_schema.knowledge_bases
                WHERE project = '{project}'
            """
            result = await self.client.execute(query)

            kbs = []
            for _, row in result.iterrows():
                metadata = await self._get_kb_metadata(row["knowledge_base_name"], project)

                kb = KnowledgeBase(
                    id=metadata.get("id", f"kb_{uuid4().hex[:12]}"),
                    name=row["knowledge_base_name"],
                    project=project,
                    model=row.get("model", "unknown"),
                    storage=row.get("storage", "unknown"),
                    table_name=row.get("table_name"),
                    content_columns=json.loads(row.get("content_columns", "[]")),
                    metadata_columns=json.loads(row.get("metadata_columns", "[]")),
                    created_at=row.get("created_at"),
                    metadata=metadata
                )
                kbs.append(kb)

            return kbs

        except Exception as e:
            logger.error(f"Failed to list knowledge bases: {str(e)}")
            return []

    async def insert_documents(
        self,
        kb_name: str,
        documents: List[Document],
        project: str = "mindsdb"
    ) -> int:
        """
        Insert documents into knowledge base

        Args:
            kb_name: Name of the knowledge base
            documents: List of documents to insert
            project: Project name

        Returns:
            Number of documents inserted

        Raises:
            MindsDBQueryError: If insertion fails
        """
        try:
            # Get KB to find table name
            kb = await self.get_knowledge_base(kb_name, project)
            if not kb or not kb.table_name:
                raise MindsDBQueryError(f"Knowledge base {kb_name} not found or has no table")

            # Insert documents into source table
            for doc in documents:
                # Build INSERT query
                content_values = []
                metadata_values = []

                # Map document content to content columns
                if len(kb.content_columns) == 1:
                    content_values.append(f"'{doc.content.replace(chr(39), chr(39)*2)}'")
                else:
                    # If multiple content columns, try to split content or use metadata
                    content_values.append(f"'{doc.content.replace(chr(39), chr(39)*2)}'")

                # Map document metadata to metadata columns
                for col in kb.metadata_columns:
                    value = doc.metadata.get(col, '')
                    if isinstance(value, str):
                        metadata_values.append(f"'{value.replace(chr(39), chr(39)*2)}'")
                    else:
                        metadata_values.append(f"'{json.dumps(value)}'")

                # Build INSERT
                all_columns = kb.content_columns + kb.metadata_columns + ['id']
                all_values = content_values + metadata_values + [f"'{doc.id}'"]

                query = f"""
                    INSERT INTO {project}.{kb.table_name} ({', '.join(all_columns)})
                    VALUES ({', '.join(all_values)})
                """

                await self.client.execute(query)

            return len(documents)

        except Exception as e:
            logger.error(f"Failed to insert documents into {kb_name}: {str(e)}")
            raise MindsDBQueryError(f"Document insertion failed: {str(e)}")

    async def search(
        self,
        kb_name: str,
        query: str,
        top_k: int = 5,
        project: str = "mindsdb",
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Perform semantic search in knowledge base

        Args:
            kb_name: Name of the knowledge base
            query: Search query
            top_k: Number of results to return
            project: Project name
            filters: Optional metadata filters

        Returns:
            List of SearchResult instances

        Raises:
            MindsDBQueryError: If search fails
        """
        try:
            # Build search query
            sql_query = f"""
                SELECT *,
                       DISTANCE(embedding, EMBEDDING('{query}')) as distance
                FROM {project}.{kb_name}
            """

            # Add filters
            if filters:
                conditions = []
                for key, value in filters.items():
                    if isinstance(value, str):
                        conditions.append(f"{key} = '{value}'")
                    else:
                        conditions.append(f"{key} = {value}")

                if conditions:
                    sql_query += f"\nWHERE {' AND '.join(conditions)}"

            # Order by relevance and limit
            sql_query += f"\nORDER BY distance ASC\nLIMIT {top_k}"

            result = await self.client.execute(sql_query)

            # Parse results
            search_results = []
            for idx, row in result.iterrows():
                # Extract content (combine all content columns)
                kb = await self.get_knowledge_base(kb_name, project)
                content = ' '.join([str(row.get(col, '')) for col in kb.content_columns])

                # Extract metadata
                metadata = {}
                for col in kb.metadata_columns:
                    if col in row:
                        metadata[col] = row[col]

                # Create document
                doc = Document(
                    id=row.get('id', f"doc_{idx}"),
                    content=content,
                    metadata=metadata
                )

                # Calculate similarity score (1 - normalized distance)
                distance = row.get('distance', 1.0)
                score = max(0, 1 - distance)

                search_results.append(SearchResult(
                    document=doc,
                    score=score,
                    rank=idx + 1
                ))

            return search_results

        except Exception as e:
            logger.error(f"Search failed in {kb_name}: {str(e)}")
            raise MindsDBQueryError(f"Search failed: {str(e)}")

    async def get_document_count(
        self,
        kb_name: str,
        project: str = "mindsdb"
    ) -> int:
        """
        Get number of documents in knowledge base

        Args:
            kb_name: Name of the knowledge base
            project: Project name

        Returns:
            Number of documents
        """
        try:
            kb = await self.get_knowledge_base(kb_name, project)
            if not kb or not kb.table_name:
                return 0

            query = f"SELECT COUNT(*) as count FROM {project}.{kb.table_name}"
            result = await self.client.execute(query)

            return int(result.iloc[0]['count']) if not result.empty else 0

        except Exception as e:
            logger.error(f"Failed to get document count for {kb_name}: {str(e)}")
            return 0

    async def update_document(
        self,
        kb_name: str,
        document_id: str,
        updates: Dict[str, Any],
        project: str = "mindsdb"
    ) -> bool:
        """
        Update document in knowledge base

        Args:
            kb_name: Name of the knowledge base
            document_id: ID of document to update
            updates: Dictionary of fields to update
            project: Project name

        Returns:
            True if updated successfully
        """
        try:
            kb = await self.get_knowledge_base(kb_name, project)
            if not kb or not kb.table_name:
                return False

            # Build UPDATE query
            set_parts = []
            for key, value in updates.items():
                if isinstance(value, str):
                    set_parts.append(f"{key} = '{value.replace(chr(39), chr(39)*2)}'")
                else:
                    set_parts.append(f"{key} = '{json.dumps(value)}'")

            query = f"""
                UPDATE {project}.{kb.table_name}
                SET {', '.join(set_parts)}
                WHERE id = '{document_id}'
            """

            await self.client.execute(query)
            return True

        except Exception as e:
            logger.error(f"Failed to update document {document_id}: {str(e)}")
            return False

    async def delete_document(
        self,
        kb_name: str,
        document_id: str,
        project: str = "mindsdb"
    ) -> bool:
        """
        Delete document from knowledge base

        Args:
            kb_name: Name of the knowledge base
            document_id: ID of document to delete
            project: Project name

        Returns:
            True if deleted successfully
        """
        try:
            kb = await self.get_knowledge_base(kb_name, project)
            if not kb or not kb.table_name:
                return False

            query = f"""
                DELETE FROM {project}.{kb.table_name}
                WHERE id = '{document_id}'
            """

            await self.client.execute(query)
            return True

        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {str(e)}")
            return False

    # Helper methods for metadata management

    async def _store_kb_metadata(
        self,
        kb_id: str,
        project: str,
        kb_name: str,
        metadata: Dict[str, Any]
    ):
        """Store KB metadata"""
        try:
            await self.client.execute("""
                CREATE TABLE IF NOT EXISTS kb_metadata (
                    kb_id VARCHAR(36) PRIMARY KEY,
                    project VARCHAR(100),
                    kb_name VARCHAR(100),
                    metadata JSON,
                    updated_at TIMESTAMP
                )
            """)

            metadata_json = json.dumps(metadata).replace("'", "''")
            await self.client.execute(f"""
                INSERT INTO kb_metadata (kb_id, project, kb_name, metadata, updated_at)
                VALUES ('{kb_id}', '{project}', '{kb_name}', '{metadata_json}', NOW())
                ON CONFLICT (kb_id) DO UPDATE SET
                    metadata = '{metadata_json}',
                    updated_at = NOW()
            """)

        except Exception as e:
            logger.warning(f"Failed to store KB metadata: {str(e)}")

    async def _get_kb_metadata(self, kb_name: str, project: str) -> Dict[str, Any]:
        """Get KB metadata"""
        try:
            result = await self.client.execute(f"""
                SELECT metadata FROM kb_metadata
                WHERE kb_name = '{kb_name}' AND project = '{project}'
            """)

            if not result.empty:
                metadata_str = result.iloc[0]["metadata"]
                return json.loads(metadata_str) if isinstance(metadata_str, str) else metadata_str

        except Exception as e:
            logger.warning(f"Failed to get KB metadata: {str(e)}")

        return {}

    async def _delete_kb_metadata(self, kb_name: str, project: str):
        """Delete KB metadata"""
        try:
            await self.client.execute(f"""
                DELETE FROM kb_metadata
                WHERE kb_name = '{kb_name}' AND project = '{project}'
            """)
        except Exception as e:
            logger.warning(f"Failed to delete KB metadata: {str(e)}")


if __name__ == "__main__":
    import asyncio
    from .mindsdb_client import create_client

    async def main():
        client = create_client()
        adapter = KnowledgeBaseAdapter(client)

        # Create knowledge base
        spec = KnowledgeBaseSpec(
            name="test_kb",
            storage="chromadb",
            description="Test knowledge base for demo"
        )

        kb = await adapter.create_knowledge_base(spec)
        print(f"Created KB: {kb.name} (ID: {kb.id})")

        # Insert documents
        docs = [
            Document(
                id="doc1",
                content="MindsDB enables AI to query and understand data from multiple sources",
                metadata={"category": "introduction", "author": "Alice"}
            ),
            Document(
                id="doc2",
                content="Agents in MindsDB can be configured with custom skills and tools",
                metadata={"category": "agents", "author": "Bob"}
            ),
            Document(
                id="doc3",
                content="Knowledge bases support semantic search using vector embeddings",
                metadata={"category": "search", "author": "Charlie"}
            )
        ]

        count = await adapter.insert_documents(kb.name, docs)
        print(f"\nInserted {count} documents")

        # Search
        print("\n" + "="*50)
        print("Search Results for: 'How do agents work?'")
        print("="*50)

        results = await adapter.search(kb.name, "How do agents work?", top_k=3)
        for result in results:
            print(f"\nRank {result.rank} (Score: {result.score:.3f})")
            print(f"Content: {result.document.content}")
            print(f"Metadata: {result.document.metadata}")

        await client.close()

    asyncio.run(main())
