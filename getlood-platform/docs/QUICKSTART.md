# GETLOOD Platform - Quick Start Guide

This guide will get you up and running with GETLOOD in **under 10 minutes**.

---

## Prerequisites

You need **ONE** of the following:

### Option A: Docker (Recommended)
- Docker Desktop installed
- 8GB RAM available
- 10GB disk space

### Option B: Local Development
- Python 3.10+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

---

## 🚀 Quick Start with Docker

### Step 1: Clone & Configure

```bash
# Clone repository
git clone https://github.com/getlood/platform.git
cd platform/getlood-platform

# Create environment file
cat > .env << EOF
# MindsDB (default values, no changes needed)
MINDSDB_HTTP_URL=http://mindsdb:47334
MINDSDB_SQL_URL=postgresql://mindsdb:mindsdb@mindsdb:47334/mindsdb
MINDSDB_A2A_URL=http://mindsdb:47334/a2a

# Database
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/getlood

# Redis
REDIS_URL=redis://redis:6379/0

# Security (CHANGE THIS in production!)
JWT_SECRET=$(openssl rand -hex 32)

# AI Providers (optional - for custom models)
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
# GOOGLE_API_KEY=...

# Environment
ENVIRONMENT=development
EOF
```

### Step 2: Start Services

```bash
# Start all services in background
docker-compose up -d

# Watch logs (Ctrl+C to exit, services keep running)
docker-compose logs -f
```

**Wait for services to be ready** (~2 minutes). You'll see:
```
mindsdb     | MindsDB server started on http://0.0.0.0:47334
getlood-api | Application startup complete
```

### Step 3: Initialize Platform

```bash
# Run setup script
docker-compose exec getlood-api python scripts/setup.py
```

Expected output:
```
============================================================
GETLOOD PLATFORM SETUP
============================================================

✓ Configuration loaded (version: 3.0.0)
✓ Connected to MindsDB successfully
✓ System project created
✓ Created agent: intent_detector (ID: agent_abc123...)
✓ Created agent: chat (ID: agent_def456...)
...
✓ Setup completed successfully!
```

### Step 4: Access Platform

**Frontend**: http://localhost:5173
- Login with demo account or create new user

**API Documentation**: http://localhost:8000/docs
- Interactive Swagger UI

**MindsDB UI**: http://localhost:47334
- Direct access to MindsDB

**Grafana**: http://localhost:3000
- Username: `admin`
- Password: `admin`

---

## 🎯 Your First Agent Interaction

### Via Web UI

1. Open http://localhost:5173
2. Click **Chat Universe** (or press `Ctrl+Shift+3`)
3. Type: **"Create a dashboard for sales analytics"**
4. Watch the 5-stage pipeline execute:
   - Stage 1: Intent detected → `GENERATE_UI`
   - Stage 2: Routed to → `WORKFLOW_MODE`
   - Stage 3: Agent selected → `ui_generator`
   - Stage 4: Execution → Dashboard generated
   - Stage 5: Enhancement → Action buttons added
5. Click **"Open Dashboard"** button

### Via Python

```python
import asyncio
from core import create_client
from core.pipeline import PipelineExecutor, ExecutionContext

async def demo():
    # Initialize
    client = create_client()
    executor = PipelineExecutor(client)

    # Context
    context = ExecutionContext(
        user_id="demo_user",
        session_id="demo_session_001",
        project="mindsdb"
    )

    # Execute
    result = await executor.execute(
        user_message="Analyze last month's sales data",
        context=context
    )

    # Results
    print(f"Intent: {result.intent.intent_type}")
    print(f"Confidence: {result.intent.confidence:.2f}")
    print(f"Agent: {result.selected_agent.agent_name}")
    print(f"Response: {result.enhanced_response}")

    await client.close()

asyncio.run(demo())
```

Run it:
```bash
docker-compose exec getlood-api python -c "
import asyncio
from core import create_client
from core.pipeline import PipelineExecutor, ExecutionContext

async def demo():
    client = create_client()
    executor = PipelineExecutor(client)
    context = ExecutionContext(
        user_id='demo_user',
        session_id='demo_001',
        project='mindsdb'
    )
    result = await executor.execute(
        'Create a workflow to analyze data',
        context
    )
    print(f'Intent: {result.intent.intent_type}')
    print(f'Agent: {result.selected_agent.agent_name}')
    await client.close()

asyncio.run(demo())
"
```

### Via REST API

```bash
# Get JWT token (create user first or use demo token)
export TOKEN="your-jwt-token"

# Chat completion
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "message": "What agents are available?",
    "user_id": "demo_user",
    "session_id": "demo_001"
  }' | jq '.'

# List agents
curl http://localhost:8000/api/v1/agents \
  -H "Authorization: Bearer $TOKEN" | jq '.'

# Create custom agent
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "my_assistant",
    "model": "google/gemini-2.5-flash",
    "skills": ["chat", "search"],
    "prompt": "You are my personal assistant"
  }' | jq '.'
```

---

## 🧪 Testing the Pipeline

Test all 5 stages with different intents:

```bash
# Stage 1: Intent Detection
curl -X POST http://localhost:8000/api/v1/pipeline/test \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Create a workflow to send daily reports",
    "stage": "intent_detection"
  }' | jq '.intent'

# Full pipeline
curl -X POST http://localhost:8000/api/v1/pipeline/test \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Analyze customer feedback from last week",
    "user_id": "test_user"
  }' | jq '.'
```

---

## 🎨 Exploring the Desktop

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+1` / `Ctrl+2` / `Ctrl+3` | Switch desktops |
| `Ctrl+M` | Mission Control (overview) |
| `Cmd+Space` | Spotlight search |
| `Cmd+Tab` | Window switcher |
| `Cmd+W` | Close active window |
| `Cmd+Q` | Quit application |

### Open Native Apps

```javascript
// In browser console (http://localhost:5173)

// Open calculator
window.postMessage({
  type: 'OPEN_APP',
  payload: { appId: 'calculator' }
}, '*');

// Open terminal
window.postMessage({
  type: 'OPEN_APP',
  payload: { appId: 'terminal' }
}, '*');

// Open AI Intelligence Hub
window.postMessage({
  type: 'OPEN_APP',
  payload: { appId: 'ai-intelligence-hub' }
}, '*');
```

---

## 🔧 Customization

### Add Custom Agent

Edit `config/getlood_config.yaml`:

```yaml
agents:
  system_agents:
    # ... existing agents ...

    - name: "code_reviewer"
      project: "system"
      model: "anthropic/claude-3-5-sonnet"
      skills: ["code_review", "security", "best_practices"]
      prompt: |
        You are an expert code reviewer. Analyze code for:
        - Security vulnerabilities
        - Performance issues
        - Best practices
        - Code quality

        Provide constructive feedback with examples.
```

Re-run setup:
```bash
docker-compose exec getlood-api python scripts/setup.py
```

### Change AI Models

Edit `config/getlood_config.yaml`:

```yaml
ai_models:
  intent_detector:
    model: "anthropic/claude-3-5-sonnet"  # Instead of Gemini
    temperature: 0.3

  chat_agent:
    model: "openai/gpt-4"  # Instead of Gemini
    temperature: 0.7
```

Restart API:
```bash
docker-compose restart getlood-api
```

---

## 📊 Monitoring

### Health Check

```bash
# Overall health
curl http://localhost:8000/health | jq '.'

# MindsDB health
curl http://localhost:47334/api/status | jq '.'

# Database health
docker-compose exec postgres pg_isready

# Redis health
docker-compose exec redis redis-cli ping
```

### Metrics

**Prometheus**: http://localhost:9090
- Query: `getlood_pipeline_execution_time_seconds`
- Query: `getlood_agent_requests_total`

**Grafana**: http://localhost:3000
- Dashboard: "GETLOOD Overview"
- Dashboard: "Pipeline Performance"

### Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f getlood-api
docker-compose logs -f mindsdb

# Filter by level
docker-compose logs -f | grep ERROR
```

---

## 🛑 Stopping & Cleaning

### Stop Services

```bash
# Stop all services
docker-compose stop

# Stop specific service
docker-compose stop getlood-api

# Remove containers (keeps data)
docker-compose down

# Remove everything (including data)
docker-compose down -v
```

### Clean Restart

```bash
# Stop and remove everything
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Start fresh
docker-compose up -d
docker-compose exec getlood-api python scripts/setup.py
```

---

## 🐛 Troubleshooting

### MindsDB won't start

```bash
# Check logs
docker-compose logs mindsdb

# Common issue: Port already in use
lsof -i :47334  # Find process using port
kill -9 <PID>   # Kill process

# Restart
docker-compose restart mindsdb
```

### API returns 500 errors

```bash
# Check API logs
docker-compose logs getlood-api

# Common issue: MindsDB not ready
docker-compose restart getlood-api

# Check MindsDB connection
docker-compose exec getlood-api python -c "
import asyncio
from core import create_client

async def test():
    client = create_client()
    health = await client.health_check()
    print(health)
    await client.close()

asyncio.run(test())
"
```

### Frontend can't connect to API

```bash
# Check if API is running
curl http://localhost:8000/health

# Check CORS settings in config/getlood_config.yaml
# Ensure frontend URL is in allowed origins

# Restart API
docker-compose restart getlood-api
```

### Database connection errors

```bash
# Check PostgreSQL
docker-compose exec postgres psql -U postgres -c "SELECT version();"

# Recreate database
docker-compose exec postgres psql -U postgres -c "DROP DATABASE getlood; CREATE DATABASE getlood;"

# Re-run setup
docker-compose exec getlood-api python scripts/setup.py
```

---

## 📚 Next Steps

Now that you have GETLOOD running:

1. **Read the Architecture**: [docs/ARCHITECTURE.md](ARCHITECTURE.md)
2. **API Reference**: [docs/API.md](API.md)
3. **Create Custom Agents**: [docs/guides/CREATING_AGENTS.md](guides/CREATING_AGENTS.md)
4. **Build Workflows**: [docs/guides/WORKFLOWS.md](guides/WORKFLOWS.md)
5. **Deploy to Production**: [docs/DEPLOYMENT.md](DEPLOYMENT.md)

---

## 💬 Get Help

- **Discord**: https://discord.gg/getlood
- **GitHub Issues**: https://github.com/getlood/platform/issues
- **Email**: support@getlood.com
- **Documentation**: https://docs.getlood.com

---

**Happy building with GETLOOD! 🚀**
