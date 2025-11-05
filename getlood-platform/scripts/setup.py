#!/usr/bin/env python3
"""
GETLOOD Platform Setup Script
Initializes MindsDB with system agents, knowledge bases, and configurations
"""

import asyncio
import sys
import os
import yaml
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.adapters.mindsdb_client import create_client, MindsDBConfig
from core.adapters.agent_adapter import AgentAdapter, AgentSpec
from core.adapters.knowledge_base_adapter import KnowledgeBaseAdapter, KnowledgeBaseSpec

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GetloodSetup:
    """Setup orchestrator for GETLOOD platform"""

    def __init__(self, config_path: str = "config/getlood_config.yaml"):
        self.config_path = config_path
        self.config = None
        self.client = None
        self.agent_adapter = None
        self.kb_adapter = None

    async def load_config(self):
        """Load configuration file"""
        logger.info(f"Loading configuration from {self.config_path}")

        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        logger.info(f"Configuration loaded (version: {self.config['version']})")

    async def connect_mindsdb(self):
        """Connect to MindsDB"""
        logger.info("Connecting to MindsDB...")

        mindsdb_config = self.config['mindsdb']

        self.client = create_client(
            http_url=mindsdb_config['http_url'],
            sql_url=mindsdb_config['sql_url'],
            a2a_url=mindsdb_config['a2a_url'],
            api_key=mindsdb_config.get('api_key')
        )

        # Health check
        health = await self.client.health_check()

        if not health['sql']:
            raise Exception("MindsDB SQL connection failed")

        logger.info("✓ Connected to MindsDB successfully")

        self.agent_adapter = AgentAdapter(self.client)
        self.kb_adapter = KnowledgeBaseAdapter(self.client)

    async def create_system_project(self):
        """Create system project for system agents"""
        logger.info("Creating system project...")

        try:
            await self.client.execute("CREATE PROJECT system")
            logger.info("✓ System project created")
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.info("✓ System project already exists")
            else:
                logger.error(f"Failed to create system project: {str(e)}")
                raise

    async def setup_system_agents(self):
        """Create pre-configured system agents"""
        logger.info("Setting up system agents...")

        system_agents = self.config['agents']['system_agents']

        for agent_config in system_agents:
            try:
                # Check if agent exists
                existing = await self.agent_adapter.get_agent(
                    agent_name=agent_config['name'],
                    project=agent_config['project']
                )

                if existing:
                    logger.info(f"  ✓ Agent '{agent_config['name']}' already exists")
                    continue

                # Create agent
                spec = AgentSpec(
                    name=agent_config['name'],
                    project=agent_config['project'],
                    model=agent_config['model'],
                    skills=agent_config.get('skills', []),
                    prompt=agent_config.get('prompt', ''),
                    metadata={
                        "system": True,
                        "description": f"System agent for {agent_config['name']}"
                    }
                )

                agent = await self.agent_adapter.create_agent(spec)
                logger.info(f"  ✓ Created agent: {agent.name} (ID: {agent.id})")

            except Exception as e:
                logger.error(f"  ✗ Failed to create agent '{agent_config['name']}': {str(e)}")
                # Continue with other agents

    async def setup_knowledge_bases(self):
        """Create pre-configured knowledge bases"""
        logger.info("Setting up knowledge bases...")

        knowledge_bases = self.config.get('knowledge_bases', [])

        for kb_config in knowledge_bases:
            try:
                # Check if KB exists
                existing = await self.kb_adapter.get_knowledge_base(
                    name=kb_config['name'],
                    project=kb_config['project']
                )

                if existing:
                    logger.info(f"  ✓ Knowledge base '{kb_config['name']}' already exists")
                    continue

                # Create KB
                spec = KnowledgeBaseSpec(
                    name=kb_config['name'],
                    project=kb_config['project'],
                    storage=kb_config['storage'],
                    model=kb_config['model'],
                    description=kb_config.get('description', ''),
                    metadata={"system": True}
                )

                kb = await self.kb_adapter.create_knowledge_base(spec)
                logger.info(f"  ✓ Created knowledge base: {kb.name} (ID: {kb.id})")

            except Exception as e:
                logger.error(f"  ✗ Failed to create KB '{kb_config['name']}': {str(e)}")
                # Continue with other KBs

    async def setup_database_tables(self):
        """Create database tables for metadata storage"""
        logger.info("Setting up database tables...")

        tables = [
            # Agent metadata
            """
            CREATE TABLE IF NOT EXISTS agent_metadata (
                agent_id VARCHAR(36) PRIMARY KEY,
                project VARCHAR(100) NOT NULL,
                agent_name VARCHAR(100) NOT NULL,
                metadata JSONB NOT NULL,
                updated_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(project, agent_name)
            )
            """,

            # Knowledge base metadata
            """
            CREATE TABLE IF NOT EXISTS kb_metadata (
                kb_id VARCHAR(36) PRIMARY KEY,
                project VARCHAR(100) NOT NULL,
                kb_name VARCHAR(100) NOT NULL,
                metadata JSONB NOT NULL,
                updated_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(project, kb_name)
            )
            """,

            # Desktop windows state
            """
            CREATE TABLE IF NOT EXISTS windows_state (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36) NOT NULL,
                desktop_id INTEGER NOT NULL CHECK (desktop_id BETWEEN 1 AND 3),
                app_id VARCHAR(100) NOT NULL,
                position JSONB NOT NULL,
                state JSONB NOT NULL,
                metadata JSONB,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                INDEX idx_windows_user_desktop (user_id, desktop_id)
            )
            """,

            # Conversation history
            """
            CREATE TABLE IF NOT EXISTS conversation_history (
                id VARCHAR(36) PRIMARY KEY,
                session_id VARCHAR(36) NOT NULL,
                user_id VARCHAR(36) NOT NULL,
                role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
                content TEXT NOT NULL,
                metadata JSONB,
                created_at TIMESTAMP DEFAULT NOW(),
                INDEX idx_conversation_session (session_id, created_at),
                INDEX idx_conversation_user (user_id, created_at)
            )
            """,

            # Pipeline execution logs
            """
            CREATE TABLE IF NOT EXISTS pipeline_logs (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36) NOT NULL,
                session_id VARCHAR(36) NOT NULL,
                message TEXT NOT NULL,
                intent_type VARCHAR(50),
                routing_mode VARCHAR(50),
                agent_used VARCHAR(100),
                execution_time_ms INTEGER,
                tokens_used INTEGER,
                cost_usd DECIMAL(10, 6),
                created_at TIMESTAMP DEFAULT NOW(),
                INDEX idx_pipeline_user (user_id, created_at),
                INDEX idx_pipeline_session (session_id, created_at)
            )
            """
        ]

        for i, table_sql in enumerate(tables, 1):
            try:
                await self.client.execute(table_sql)
                logger.info(f"  ✓ Table {i}/{len(tables)} created")
            except Exception as e:
                logger.warning(f"  ! Table {i}/{len(tables)}: {str(e)}")

    async def verify_setup(self):
        """Verify that setup was successful"""
        logger.info("\nVerifying setup...")

        checks = []

        # Check agents
        try:
            agents = await self.agent_adapter.list_agents(project="system")
            checks.append(("System agents", len(agents) > 0, f"{len(agents)} agents found"))
        except Exception as e:
            checks.append(("System agents", False, str(e)))

        # Check knowledge bases
        try:
            kbs = await self.kb_adapter.list_knowledge_bases(project="system")
            checks.append(("Knowledge bases", len(kbs) > 0, f"{len(kbs)} KBs found"))
        except Exception as e:
            checks.append(("Knowledge bases", False, str(e)))

        # Check database tables
        try:
            result = await self.client.execute("""
                SELECT COUNT(*) as count FROM information_schema.tables
                WHERE table_name IN ('agent_metadata', 'kb_metadata', 'windows_state', 'conversation_history', 'pipeline_logs')
            """)
            table_count = int(result.iloc[0]['count'])
            checks.append(("Database tables", table_count == 5, f"{table_count}/5 tables created"))
        except Exception as e:
            checks.append(("Database tables", False, str(e)))

        # Print results
        logger.info("\n" + "="*60)
        logger.info("SETUP VERIFICATION")
        logger.info("="*60)

        all_passed = True
        for check_name, passed, details in checks:
            status = "✓" if passed else "✗"
            logger.info(f"{status} {check_name}: {details}")
            if not passed:
                all_passed = False

        logger.info("="*60)

        return all_passed

    async def run(self):
        """Run complete setup"""
        logger.info("\n" + "="*60)
        logger.info("GETLOOD PLATFORM SETUP")
        logger.info("="*60 + "\n")

        try:
            # 1. Load configuration
            await self.load_config()

            # 2. Connect to MindsDB
            await self.connect_mindsdb()

            # 3. Create system project
            await self.create_system_project()

            # 4. Setup system agents
            await self.setup_system_agents()

            # 5. Setup knowledge bases
            await self.setup_knowledge_bases()

            # 6. Setup database tables
            await self.setup_database_tables()

            # 7. Verify setup
            success = await self.verify_setup()

            if success:
                logger.info("\n✓ Setup completed successfully!")
                logger.info("\nNext steps:")
                logger.info("  1. Start the API: cd api && python -m uvicorn main:app --reload")
                logger.info("  2. Start the frontend: cd frontend && npm run dev")
                logger.info("  3. Open http://localhost:5173 in your browser")
                return 0
            else:
                logger.warning("\n! Setup completed with warnings. Please check the logs.")
                return 1

        except Exception as e:
            logger.error(f"\n✗ Setup failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return 1

        finally:
            if self.client:
                await self.client.close()


async def main():
    setup = GetloodSetup()
    exit_code = await setup.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
