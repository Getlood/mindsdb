# GETLOOD Platform Architecture
## MindsDB as Composable Backend

> **Version**: 3.0.0
> **Last Updated**: 2025-01-07
> **Architecture**: Multi-tier, Event-driven, Real-time

---

## 🎯 Executive Summary

GETLOOD est une plateforme agentique multi-tenant qui utilise **MindsDB comme backend composable universel**. Cette architecture tire parti des capacités natives de MindsDB (agents, knowledge bases, multi-provider AI) tout en ajoutant une couche d'orchestration sophistiquée et une interface desktop-first.

### Tagline
**"Le premier OS agentique qui pense comme vous travaillez - Powered by MindsDB"**

---

## 🏗️ Architecture en Couches

```
┌─────────────────────────────────────────────────────────────┐
│                    GETLOOD FRONTEND                         │
│  React 18 + TypeScript + XState + Jotai + Tailwind         │
│                                                             │
│  [Desktop UI] [Chat UI] [Workflow UI] [Console] [Security] │
└─────────────────────────────────────────────────────────────┘
                            ↓ WebSocket/REST/GraphQL
┌─────────────────────────────────────────────────────────────┐
│                   GETLOOD API GATEWAY                       │
│  Unified API · Rate Limiting · Auth · Cache · Transform    │
│                                                             │
│  [REST] [GraphQL] [WebSocket] [SSE] [gRPC]                 │
└─────────────────────────────────────────────────────────────┘
                            ↓ Internal APIs
┌─────────────────────────────────────────────────────────────┐
│              GETLOOD CORE ORCHESTRATION                     │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Pipeline   │  │   Desktop    │  │   Workflow   │    │
│  │  Executor    │  │   Manager    │  │   Engine     │    │
│  │  (5 Stages)  │  │   (XState)   │  │ (React Flow) │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Agent      │  │   Knowledge  │  │    Event     │    │
│  │  Registry    │  │     Base     │  │  Dispatcher  │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            ↓ Adapter Layer
┌─────────────────────────────────────────────────────────────┐
│              GETLOOD MINDSDB ADAPTERS                       │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │    Agent     │  │  Knowledge   │  │    Model     │    │
│  │   Adapter    │  │     Base     │  │   Adapter    │    │
│  │              │  │   Adapter    │  │              │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Project    │  │    Skills    │  │     Job      │    │
│  │   Adapter    │  │   Adapter    │  │   Adapter    │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            ↓ SQL/HTTP/A2A
┌─────────────────────────────────────────────────────────────┐
│                     MINDSDB CORE                            │
│                                                             │
│  ├─ Agents (Langchain-based)                               │
│  ├─ Knowledge Bases (Vector Search)                        │
│  ├─ Models (Multi-provider: OpenAI, Anthropic, Gemini...)  │
│  ├─ Projects (Multi-tenant isolation)                      │
│  ├─ Skills (Tool execution)                                │
│  ├─ Jobs (Scheduled tasks)                                 │
│  ├─ Views (Unified data access)                            │
│  └─ A2A Protocol (Agent-to-Agent communication)            │
└─────────────────────────────────────────────────────────────┘
                            ↓ Integrations
┌─────────────────────────────────────────────────────────────┐
│                  DATA SOURCES & SERVICES                    │
│                                                             │
│  [PostgreSQL] [MySQL] [MongoDB] [Snowflake] [BigQuery]    │
│  [Slack] [Gmail] [GitHub] [Jira] [Notion] [Google Drive]  │
│  [S3] [Azure Blob] [GCS] [OpenAI] [Anthropic] [Gemini]    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔑 Concepts Clés

### 1. MindsDB comme Backend Universel

MindsDB n'est pas juste une base de données - c'est une **plateforme d'orchestration IA** qui :

- **Unifie les sources de données** : 200+ connecteurs natifs
- **Orchestre les modèles IA** : Multi-provider (OpenAI, Anthropic, Gemini, Llama, etc.)
- **Gère les agents** : Langchain-based avec tools et mémoire
- **Stocke les connaissances** : Vector databases intégrées (ChromaDB, Pinecone, Weaviate)
- **Schedule les tâches** : Jobs automatiques avec cron-like scheduling
- **Expose les APIs** : SQL, HTTP, A2A, MCP

### 2. Adapter Pattern

Chaque fonctionnalité MindsDB est encapsulée dans un **adapter** :

```python
# Example: AgentAdapter
class MindsDBAgentAdapter:
    def __init__(self, mindsdb_client: MindsDBClient):
        self.client = mindsdb_client

    async def create_agent(
        self,
        name: str,
        model: str,
        skills: List[str],
        prompt: str,
        metadata: Dict[str, Any]
    ) -> Agent:
        """Create agent via MindsDB SQL API"""
        result = await self.client.execute(f"""
            CREATE AGENT {name}
            USING
                model = '{model}',
                skills = {skills},
                prompt = '{prompt}',
                metadata = '{json.dumps(metadata)}'
        """)
        return self._parse_agent(result)

    async def query_agent(
        self,
        agent_name: str,
        message: str,
        session_id: str,
        stream: bool = True
    ) -> AsyncIterator[str]:
        """Query agent via A2A API with streaming"""
        async for chunk in self.client.a2a_stream(
            agent_name=agent_name,
            message=message,
            session_id=session_id
        ):
            yield chunk
```

### 3. Pipeline d'Orchestration (5 Stages)

Le pipeline GETLOOD enrichit MindsDB avec intelligence contextuelle :

```
User Input
    ↓
[Stage 1] Intent Detection (MindsDB LLM)
    ↓
[Stage 2] Routing (Rule-based + ML)
    ↓
[Stage 3] Agent Selection (MindsDB Agent Registry)
    ↓
[Stage 4] Execution (MindsDB Agent + Skills)
    ↓
[Stage 5] Enhancement (ToM + Neural UI + Context)
    ↓
Enhanced Response + Actions
```

**Nouveauté** : Les stages 1-4 utilisent directement MindsDB, stage 5 ajoute intelligence GETLOOD.

### 4. Multi-Tenancy via Projects

MindsDB supporte nativement le multi-tenancy via **Projects** :

```sql
-- Create tenant workspace
CREATE PROJECT workspace_user123;

-- All resources are scoped to project
CREATE AGENT workspace_user123.my_agent ...;
CREATE MODEL workspace_user123.my_model ...;
CREATE TABLE workspace_user123.my_data ...;
```

GETLOOD mappe :
- **User** → MindsDB Project
- **Desktop** → MindsDB Database
- **Window** → MindsDB Table (windows_state)
- **Agent** → MindsDB Agent
- **Workflow** → MindsDB Job + Agents chain

---

## 📦 Composants Principaux

### 1. Core Adapters (`core/adapters/`)

#### `mindsdb_client.py`
Client Python unifié pour MindsDB (SQL + HTTP + A2A).

```python
class MindsDBClient:
    def __init__(self, config: MindsDBConfig):
        self.http_client = HttpClient(config.http_url)
        self.sql_client = SQLClient(config.sql_url)
        self.a2a_client = A2AClient(config.a2a_url)

    async def execute(self, query: str) -> pd.DataFrame:
        """Execute SQL query"""
        return await self.sql_client.execute(query)

    async def a2a_stream(self, agent_name: str, message: str, session_id: str):
        """Stream agent response via A2A"""
        async for chunk in self.a2a_client.stream(
            agent_name=agent_name,
            message=message,
            session_id=session_id
        ):
            yield chunk
```

#### `agent_adapter.py`
CRUD operations for agents.

```python
class AgentAdapter:
    async def create_agent(self, spec: AgentSpec) -> Agent
    async def get_agent(self, agent_id: str) -> Agent
    async def update_agent(self, agent_id: str, updates: Dict) -> Agent
    async def delete_agent(self, agent_id: str) -> bool
    async def list_agents(self, filters: Dict) -> List[Agent]
    async def query_agent(self, agent_id: str, message: str, stream: bool) -> AsyncIterator[str]
```

#### `knowledge_base_adapter.py`
Vector search and RAG operations.

```python
class KnowledgeBaseAdapter:
    async def create_kb(self, name: str, vector_db: str, embedding_model: str) -> KB
    async def insert_documents(self, kb_id: str, docs: List[Document]) -> None
    async def semantic_search(self, kb_id: str, query: str, top_k: int) -> List[Document]
    async def delete_kb(self, kb_id: str) -> bool
```

#### `model_adapter.py`
Multi-provider model management.

```python
class ModelAdapter:
    async def create_model(self, name: str, provider: str, config: Dict) -> Model
    async def predict(self, model_id: str, input_data: Dict) -> Dict
    async def fine_tune(self, model_id: str, training_data: pd.DataFrame) -> Job
```

#### `job_adapter.py`
Scheduled workflows and automation.

```python
class JobAdapter:
    async def create_job(self, name: str, query: str, schedule: str) -> Job
    async def trigger_job(self, job_id: str) -> Execution
    async def get_job_history(self, job_id: str, limit: int) -> List[Execution]
```

### 2. Core Orchestration (`core/orchestration/`)

#### `pipeline_executor.py`
5-stage AI pipeline orchestrator.

```python
class PipelineExecutor:
    def __init__(
        self,
        mindsdb_client: MindsDBClient,
        agent_adapter: AgentAdapter,
        kb_adapter: KnowledgeBaseAdapter
    ):
        self.mindsdb = mindsdb_client
        self.agents = agent_adapter
        self.kb = kb_adapter

        # Stage handlers
        self.stages = [
            IntentDetectionStage(mindsdb_client),
            RoutingStage(),
            AgentSelectionStage(agent_adapter),
            ExecutionStage(agent_adapter),
            EnhancementStage(kb_adapter)
        ]

    async def execute(
        self,
        user_message: str,
        context: ExecutionContext
    ) -> PipelineResult:
        """Execute full pipeline"""
        result = PipelineResult(message=user_message)

        for stage in self.stages:
            result = await stage.process(result, context)

            # Early exit if clarification needed
            if result.needs_clarification:
                return result

        return result
```

#### `desktop_manager.py`
Window management state machine (XState → MindsDB).

```python
class DesktopManager:
    async def create_window(self, app_id: str, desktop_id: int) -> Window
    async def update_window_position(self, window_id: str, x: int, y: int) -> None
    async def focus_window(self, window_id: str) -> None
    async def close_window(self, window_id: str) -> None
    async def save_desktop_state(self, desktop_id: int) -> None
    async def restore_desktop_state(self, desktop_id: int) -> DesktopState
```

State persisted in MindsDB:
```sql
CREATE TABLE windows_state (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36),
    desktop_id INT,
    app_id VARCHAR(100),
    position JSON,
    state JSON,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### `workflow_engine.py`
Visual workflow execution engine.

```python
class WorkflowEngine:
    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: Dict
    ) -> WorkflowExecution:
        """Execute workflow as MindsDB agent chain"""
        workflow = await self.get_workflow(workflow_id)

        # Convert workflow to MindsDB job
        job_query = self._workflow_to_sql(workflow)

        # Create temporary job
        job = await self.job_adapter.create_job(
            name=f"workflow_{workflow_id}_{uuid4()}",
            query=job_query,
            schedule="manual"
        )

        # Execute and stream results
        execution = await self.job_adapter.trigger_job(job.id)

        return WorkflowExecution(
            workflow_id=workflow_id,
            job_id=job.id,
            execution_id=execution.id,
            status=execution.status
        )
```

### 3. API Gateway (`api/gateway/`)

#### `unified_gateway.py`
Single entry point for all APIs.

```python
from fastapi import FastAPI, WebSocket
from graphql import GraphQLSchema

app = FastAPI(title="GETLOOD API Gateway")

# REST endpoints
@app.post("/api/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    """OpenAI-compatible chat endpoint"""
    result = await pipeline_executor.execute(
        user_message=request.message,
        context=ExecutionContext(user_id=request.user_id)
    )
    return ChatResponse(
        id=result.id,
        choices=[{"message": {"content": result.enhanced_response}}]
    )

# WebSocket for real-time
@app.websocket("/ws/desktop/{desktop_id}")
async def desktop_ws(websocket: WebSocket, desktop_id: int):
    """Real-time desktop state sync"""
    await websocket.accept()

    # Subscribe to MindsDB realtime
    async for event in mindsdb_client.subscribe(f"desktop_{desktop_id}"):
        await websocket.send_json(event)

# GraphQL endpoint
@app.post("/graphql")
async def graphql_endpoint(query: str):
    """GraphQL API for complex queries"""
    result = await graphql_schema.execute(query)
    return result.data
```

### 4. Frontend Integration (`frontend/`)

#### State Management Architecture

```
React Components (UI)
    ↓ props/context
React Context (stable global state)
    ↓ computed atoms
Jotai Atoms (reactive state)
    ↓ useDesktopBridge
XState Machine (deterministic FSM)
    ↓ WebSocket/REST
GETLOOD API Gateway
    ↓ Adapters
MindsDB Core
```

#### `useDesktopBridge.ts`
Hook for XState ↔ MindsDB sync.

```typescript
export const useDesktopBridge = (desktopId: number) => {
  const [state, send] = useMachine(desktopSystemMachine);

  // Sync to MindsDB on state change
  useEffect(() => {
    const debouncedSync = debounce(async () => {
      await fetch('/api/v1/desktop/state', {
        method: 'POST',
        body: JSON.stringify({
          desktop_id: desktopId,
          windows: state.context.windows,
          focus_stack: state.context.focusStack
        })
      });
    }, 500);

    debouncedSync();

    return () => debouncedSync.cancel();
  }, [state.context]);

  // Restore from MindsDB on mount
  useEffect(() => {
    const restore = async () => {
      const response = await fetch(`/api/v1/desktop/state/${desktopId}`);
      const savedState = await response.json();

      send({ type: 'RESTORE_STATE', data: savedState });
    };

    restore();
  }, [desktopId]);

  return { state, send };
};
```

---

## 🔐 Security & Multi-Tenancy

### Row-Level Security (RLS)

MindsDB Projects provide natural tenant isolation:

```python
# User authentication creates/links to project
async def authenticate_user(email: str, password: str) -> User:
    user = await auth_service.verify(email, password)

    # Ensure user has MindsDB project
    project_name = f"user_{user.id}"

    try:
        await mindsdb_client.execute(f"CREATE PROJECT {project_name}")
    except ProjectExistsError:
        pass  # Already exists

    # All subsequent queries scoped to project
    user.mindsdb_project = project_name

    return user

# Usage
async def query_user_agents(user: User) -> List[Agent]:
    # Automatic project scoping
    result = await mindsdb_client.execute(f"""
        SELECT * FROM {user.mindsdb_project}.agents
    """)
    return [Agent.from_row(row) for row in result.itertuples()]
```

### API Authentication

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    user = await auth_service.verify_token(token)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    return user

# Protected endpoint
@app.post("/api/v1/agents")
async def create_agent(
    spec: AgentSpec,
    user: User = Depends(get_current_user)
):
    # Agent automatically created in user's project
    agent = await agent_adapter.create_agent(
        name=spec.name,
        model=spec.model,
        skills=spec.skills,
        project=user.mindsdb_project  # Automatic tenant isolation
    )
    return agent
```

---

## 📊 Data Flow Examples

### Example 1: User sends chat message

```
1. User types: "Crée-moi un dashboard analytics"
   ↓
2. Frontend sends to /api/v1/chat/completions
   ↓
3. API Gateway validates auth, extracts user context
   ↓
4. PipelineExecutor.execute() starts:

   Stage 1 (Intent Detection):
   - Calls MindsDB agent "intent_detector"
   - Result: { intent: "GENERATE_UI", confidence: 0.94 }

   Stage 2 (Routing):
   - Routes to "WORKFLOW_MODE" (complex task)

   Stage 3 (Agent Selection):
   - Queries user's project agents: "SELECT * FROM user_123.agents WHERE 'ui-generation' IN skills"
   - Selects: agent "ui_generator_v2"

   Stage 4 (Execution):
   - Calls MindsDB A2A API with streaming
   - Agent returns: React component code + instructions

   Stage 5 (Enhancement):
   - Theory of Mind: Detects user wants quick action
   - Neural UI: Generates action button "Ouvrir le dashboard"
   - Context: Saves to conversation history in MindsDB KB

5. Returns enhanced response with actions
   ↓
6. Frontend renders response + action buttons
   ↓
7. User clicks "Ouvrir le dashboard"
   ↓
8. Frontend calls /api/v1/desktop/windows (create window)
   ↓
9. DesktopManager saves window state to MindsDB
   ↓
10. Window opens with dashboard component
```

### Example 2: Execute visual workflow

```
1. User designs workflow in Workflow Universe:
   [Start] → [Analyze Data] → [Generate Report] → [Send Email] → [End]
   ↓
2. User clicks "Execute"
   ↓
3. Frontend calls /api/v1/workflows/{id}/execute
   ↓
4. WorkflowEngine converts nodes to MindsDB job:

   CREATE JOB workflow_abc123
   AS (
       -- Node 1: Analyze Data
       CREATE TABLE analysis_result AS
       SELECT * FROM agent_query(
           agent='data_analyzer',
           message='Analyze sales data from last month'
       );

       -- Node 2: Generate Report
       CREATE TABLE report AS
       SELECT * FROM agent_query(
           agent='report_generator',
           message='Create executive summary',
           context=(SELECT * FROM analysis_result)
       );

       -- Node 3: Send Email
       INSERT INTO email_integration.send
       SELECT
           'exec@company.com' as to,
           'Monthly Report' as subject,
           content as body
       FROM report;
   )
   ↓
5. Job executes in MindsDB, logs to execution_logs table
   ↓
6. Frontend subscribes to WebSocket for real-time updates
   ↓
7. Each node completion triggers event:
   { type: 'NODE_COMPLETED', node_id: 'analyze_data', duration_ms: 2340 }
   ↓
8. Workflow completes, final result returned
```

---

## 🚀 Deployment Architecture

### Development
```
docker-compose up
  ├─ mindsdb (port 47334)
  ├─ postgres (port 5432)
  ├─ redis (port 6379)
  ├─ getlood-api (port 8000)
  └─ getlood-frontend (port 5173)
```

### Production (Kubernetes)
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: getlood-prod

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mindsdb
  namespace: getlood-prod
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mindsdb
  template:
    metadata:
      labels:
        app: mindsdb
    spec:
      containers:
      - name: mindsdb
        image: mindsdb/mindsdb:latest
        ports:
        - containerPort: 47334
        env:
        - name: MINDSDB_DB_URL
          value: postgresql://postgres:5432/mindsdb
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: getlood-api
  namespace: getlood-prod
spec:
  replicas: 5
  selector:
    matchLabels:
      app: getlood-api
  template:
    metadata:
      labels:
        app: getlood-api
    spec:
      containers:
      - name: api
        image: getlood/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: MINDSDB_URL
          value: http://mindsdb:47334
        - name: REDIS_URL
          value: redis://redis:6379
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
```

---

## 📈 Performance Considerations

### Caching Strategy

```python
from functools import lru_cache
import redis

redis_client = redis.Redis(host='redis', port=6379)

class CachedMindsDBClient:
    @lru_cache(maxsize=1000)
    async def get_agent(self, agent_id: str) -> Agent:
        """Cache agent metadata (rarely changes)"""
        cache_key = f"agent:{agent_id}"

        # Check Redis first
        cached = redis_client.get(cache_key)
        if cached:
            return Agent.parse_raw(cached)

        # Fetch from MindsDB
        agent = await self.mindsdb_client.execute(f"""
            SELECT * FROM agents WHERE id = '{agent_id}'
        """)

        # Cache for 1 hour
        redis_client.setex(cache_key, 3600, agent.json())

        return agent
```

### Connection Pooling

```python
from sqlalchemy.pool import QueuePool

engine = create_engine(
    MINDSDB_SQL_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True
)
```

### Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/chat/completions")
@limiter.limit("100/minute")  # 100 requests per minute
async def chat_completions(request: ChatRequest):
    ...
```

---

## 🧪 Testing Strategy

### Unit Tests
```python
# tests/unit/test_agent_adapter.py
import pytest
from getlood.core.adapters import AgentAdapter

@pytest.mark.asyncio
async def test_create_agent(mock_mindsdb_client):
    adapter = AgentAdapter(mock_mindsdb_client)

    agent = await adapter.create_agent(
        name="test_agent",
        model="gpt-4",
        skills=["web_search"],
        prompt="You are a helpful assistant"
    )

    assert agent.name == "test_agent"
    assert agent.model == "gpt-4"
    assert "web_search" in agent.skills
```

### Integration Tests
```python
# tests/integration/test_pipeline.py
@pytest.mark.asyncio
async def test_full_pipeline(real_mindsdb_client):
    executor = PipelineExecutor(real_mindsdb_client)

    result = await executor.execute(
        user_message="Crée un rapport de ventes",
        context=ExecutionContext(user_id="test_user")
    )

    assert result.intent == "GENERATE_REPORT"
    assert result.agent_used is not None
    assert len(result.enhanced_response) > 0
```

### E2E Tests (Playwright)
```typescript
// tests/e2e/chat-to-dashboard.spec.ts
test('user creates dashboard via chat', async ({ page }) => {
  await page.goto('http://localhost:5173');

  // Login
  await page.fill('[data-testid="email"]', 'test@example.com');
  await page.fill('[data-testid="password"]', 'password');
  await page.click('[data-testid="login"]');

  // Send chat message
  await page.click('[data-testid="chat-universe"]');
  await page.fill('[data-testid="chat-input"]', 'Crée un dashboard analytics');
  await page.press('[data-testid="chat-input"]', 'Enter');

  // Wait for response
  await page.waitForSelector('[data-testid="action-button"]');

  // Click action button
  await page.click('[data-testid="action-button"]');

  // Verify window opened
  const window = await page.waitForSelector('[data-testid="window-dashboard"]');
  expect(window).toBeTruthy();
});
```

---

## 📚 Next Steps

1. **Phase 1 (Week 1-2)**: Implement core adapters
2. **Phase 2 (Week 3-4)**: Build orchestration layer
3. **Phase 3 (Week 5-6)**: Integrate API gateway
4. **Phase 4 (Week 7-8)**: Frontend integration
5. **Phase 5 (Week 9-10)**: Testing & optimization
6. **Phase 6 (Week 11-12)**: Documentation & launch

---

## 🤝 Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

---

**Architecture maintained by GETLOOD Core Team**
**Last review**: 2025-01-07
**Next review**: 2025-02-01
