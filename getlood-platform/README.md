# GETLOOD Platform - Powered by MindsDB

> Le premier OS agentique qui pense comme vous travaillez

<div align="center">

[![Version](https://img.shields.io/badge/version-3.0.0-blue.svg)](https://github.com/getlood/platform)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![MindsDB](https://img.shields.io/badge/powered%20by-MindsDB-orange.svg)](https://mindsdb.com)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![React](https://img.shields.io/badge/react-18.3-61dafb.svg)](https://react.dev)

</div>

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [Features](#-features)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Reference](#-api-reference)
- [Development](#-development)
- [Deployment](#-deployment)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

GETLOOD est une **plateforme agentique multi-tenant** qui fusionne l'ergonomie d'un système d'exploitation desktop avec la puissance d'une orchestration IA distribuée. En utilisant **MindsDB comme backend composable**, GETLOOD offre :

- 🖥️ **Desktop System** : Interface desktop-first avec window manager, multi-desktop navigation
- 🤖 **AI Orchestration** : Pipeline 5-stages avec intent detection, routing, et enhancement
- 🔄 **Visual Workflows** : Création et exécution de workflows complexes avec agents
- 🧠 **Knowledge Bases** : Recherche sémantique et RAG sur vos données
- 💬 **Multi-Universe** : 5 interfaces (Desktop, Console, Chat, Workflow, Security)
- 🚀 **Real-time Sync** : WebSocket pour synchronisation multi-clients

### Why MindsDB?

MindsDB fournit une **abstraction unifiée** pour :
- **200+ data sources** : PostgreSQL, MySQL, Snowflake, BigQuery, APIs...
- **Multi-provider AI** : OpenAI, Anthropic, Google Gemini, Llama, etc.
- **Native agents** : Langchain-based avec tools et mémoire
- **Vector search** : ChromaDB, Pinecone, Weaviate intégrés
- **SQL interface** : Requêtes IA via SQL standard

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         GETLOOD Frontend                │
│   React + TypeScript + XState + Jotai  │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│         GETLOOD API Gateway             │
│   FastAPI + WebSocket + GraphQL        │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│      GETLOOD Core Orchestration         │
│  Pipeline · Desktop · Workflows · KB    │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│      MindsDB Adapter Layer              │
│  Agent · Model · KB · Job Adapters      │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│           MindsDB Core                  │
│  Agents · Models · KB · Jobs · A2A      │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│         Data Sources & AI Providers     │
│  Databases · APIs · OpenAI · Gemini     │
└─────────────────────────────────────────┘
```

Voir [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) pour l'architecture détaillée.

---

## ✨ Features

### Core Features

✅ **Desktop System**
- 3 desktops virtuels avec personnalité distincte
- Window manager XState-powered (60fps drag & drop)
- Snap system intelligent avec magnetisme
- Mission Control et Launchpad
- Spotlight search universel

✅ **AI Pipeline (5 Stages)**
1. **Intent Detection** : Classification intelligente avec ambiguïté handling
2. **Routing** : Sélection du mode optimal (Workflow, Reasoning, Chat, Direct)
3. **Agent Selection** : Choix de l'agent spécialisé optimal
4. **Execution** : Exécution avec streaming temps réel
5. **Enhancement** : Theory of Mind + Neural UI + Context Awareness

✅ **Visual Workflows**
- Drag & drop node editor (React Flow)
- 8 types de nodes (start, end, agent, condition, llm, human_input, parallel, merge)
- Export XState machines
- Monitoring et analytics en temps réel

✅ **Knowledge Bases**
- Recherche sémantique avec embeddings
- Multi-vector-DB support (ChromaDB, Pinecone, Weaviate)
- RAG (Retrieval Augmented Generation)
- Document management CRUD

✅ **Multi-Universe**
- **Desktop Universe** : Interface traditionnelle
- **Console Universe** : Terminal interactif avec AI
- **Chat Universe** : Conversation multimodale
- **Workflow Universe** : Visual workflow builder
- **Security Universe** : Admin dashboard (admin-only)

### AI Capabilities

🤖 **Agents**
- Intent detection agent
- Chat agent (conversational)
- Data analyzer agent
- UI generator agent
- Workflow builder agent
- Custom agents support

🧠 **Reasoning Methods**
- **CoT** (Chain of Thought) : Raisonnement linéaire
- **ToT** (Tree of Thoughts) : Exploration de branches
- **ReAct** (Reasoning + Acting) : Itératif avec feedback

💡 **Theory of Mind**
- Détection du goal utilisateur
- Analyse du contexte émotionnel
- Prédiction de la prochaine intention
- Adaptation au niveau d'expertise

🎨 **Neural UI**
- Génération automatique d'action buttons
- Quick replies contextuels
- Suggestions d'interaction patterns

---

## 🚀 Quick Start

### Prerequisites

- **Docker** & **Docker Compose** (recommended)
- OR:
  - Python 3.10+
  - Node.js 18+
  - PostgreSQL 15+
  - Redis 7+

### Option 1: Docker Compose (Recommended)

```bash
# Clone repository
git clone https://github.com/getlood/platform.git
cd platform/getlood-platform

# Configure environment
cp .env.example .env
# Edit .env with your API keys (OpenAI, Anthropic, etc.)

# Start all services
docker-compose up -d

# Wait for services to be ready (~2 minutes)
docker-compose logs -f mindsdb

# Run setup script
docker-compose exec getlood-api python scripts/setup.py

# Access platform
# Frontend: http://localhost:5173
# API: http://localhost:8000
# MindsDB: http://localhost:47334
# Grafana: http://localhost:3000 (admin/admin)
```

### Option 2: Local Development

```bash
# 1. Start MindsDB
docker run -d --name mindsdb \
  -p 47334:47334 \
  -p 47335:47335 \
  mindsdb/mindsdb:latest

# 2. Install Python dependencies
cd getlood-platform
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Setup database
createdb getlood
python scripts/setup.py

# 4. Start API
cd api
uvicorn main:app --reload --port 8000

# 5. Start Frontend (new terminal)
cd frontend
npm install
npm run dev
```

---

## 📦 Installation

### System Requirements

**Minimum:**
- CPU: 2 cores
- RAM: 4GB
- Storage: 10GB
- OS: Linux, macOS, Windows (WSL2)

**Recommended:**
- CPU: 4 cores
- RAM: 8GB
- Storage: 20GB SSD
- OS: Linux (Ubuntu 22.04+)

### Dependencies

**Backend:**
```bash
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

### Environment Variables

Create `.env` file:

```env
# MindsDB
MINDSDB_HTTP_URL=http://localhost:47334
MINDSDB_SQL_URL=postgresql://mindsdb:mindsdb@localhost:47334/mindsdb
MINDSDB_A2A_URL=http://localhost:47334/a2a

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/getlood

# Redis
REDIS_URL=redis://localhost:6379/0

# Authentication
JWT_SECRET=your-secret-key-change-in-production

# AI Providers (optional, for custom models)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...

# Monitoring (optional)
SENTRY_DSN=https://...

# Environment
ENVIRONMENT=development
```

---

## ⚙️ Configuration

La configuration principale se trouve dans `config/getlood_config.yaml`.

### Key Configuration Sections

**MindsDB Connection:**
```yaml
mindsdb:
  http_url: "http://localhost:47334"
  sql_url: "postgresql://mindsdb:mindsdb@localhost:47334/mindsdb"
  a2a_url: "http://localhost:47334/a2a"
  timeout: 30
  max_retries: 3
```

**AI Models:**
```yaml
ai_models:
  intent_detector:
    model: "google/gemini-2.5-flash"
    temperature: 0.3

  chat_agent:
    model: "google/gemini-2.5-flash"
    temperature: 0.7
```

**Pipeline:**
```yaml
pipeline:
  timeouts:
    intent_detection: 5000
    execution: 30000

  confidence_thresholds:
    high: 0.85
    clarification_needed: 0.40
```

**Rate Limiting:**
```yaml
api:
  rate_limit:
    enabled: true
    requests_per_minute: 100
```

Voir [docs/CONFIGURATION.md](docs/CONFIGURATION.md) pour la documentation complète.

---

## 📚 Usage

### 1. Using the Desktop UI

```typescript
// Open the platform
// Navigate to http://localhost:5173

// Use keyboard shortcuts
Ctrl+1/2/3        // Switch desktops
Ctrl+M            // Mission Control
Cmd+Space         // Spotlight search
Cmd+Tab           // Window switcher
```

### 2. Using the Python API

```python
import asyncio
from core.adapters.mindsdb_client import create_client
from core.adapters.agent_adapter import AgentAdapter
from core.pipeline.pipeline_executor import PipelineExecutor, ExecutionContext

async def main():
    # Initialize
    client = create_client()
    executor = PipelineExecutor(client)

    # Create context
    context = ExecutionContext(
        user_id="user_123",
        session_id="session_abc",
        project="user_123"
    )

    # Execute pipeline
    result = await executor.execute(
        user_message="Create a dashboard for sales analytics",
        context=context
    )

    # Get results
    print(f"Intent: {result.intent.intent_type}")
    print(f"Response: {result.enhanced_response}")

    # Access enhancement data
    if result.enhancement:
        for btn in result.enhancement.neural_ui.action_buttons:
            print(f"Action: {btn['label']}")

    await client.close()

asyncio.run(main())
```

### 3. Using the REST API

```bash
# Health check
curl http://localhost:8000/health

# Chat completion
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "message": "Create a workflow to analyze customer feedback",
    "user_id": "user_123",
    "session_id": "session_abc"
  }'

# List agents
curl http://localhost:8000/api/v1/agents \
  -H "Authorization: Bearer YOUR_TOKEN"

# Create agent
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "my_agent",
    "model": "gpt-4",
    "skills": ["web_search", "sql_query"],
    "prompt": "You are a helpful assistant"
  }'
```

### 4. Using WebSocket

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/desktop/1');

ws.onopen = () => {
  console.log('Connected to desktop 1');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Desktop update:', data);

  // Handle window events
  if (data.type === 'WINDOW_OPENED') {
    console.log(`Window opened: ${data.payload.appId}`);
  }
};

// Send window update
ws.send(JSON.stringify({
  type: 'UPDATE_WINDOW',
  payload: {
    windowId: 'window_123',
    x: 100,
    y: 100
  }
}));
```

---

## 🔌 API Reference

### REST Endpoints

#### Chat

```
POST /api/v1/chat/completions
```

Request:
```json
{
  "message": "Create a dashboard",
  "user_id": "user_123",
  "session_id": "session_abc",
  "stream": false
}
```

Response:
```json
{
  "id": "pipeline_abc_123",
  "intent": {
    "intent_type": "GENERATE_UI",
    "confidence": 0.94
  },
  "enhanced_response": "I've created a dashboard...",
  "actions": [
    {
      "label": "Open Dashboard",
      "action": "OPEN_WINDOW",
      "payload": {"appId": "dashboard-abc"}
    }
  ],
  "quick_replies": ["Customize", "Export", "Share"]
}
```

#### Agents

```
GET    /api/v1/agents              # List agents
POST   /api/v1/agents              # Create agent
GET    /api/v1/agents/{id}         # Get agent
PUT    /api/v1/agents/{id}         # Update agent
DELETE /api/v1/agents/{id}         # Delete agent
POST   /api/v1/agents/{id}/query   # Query agent
```

#### Knowledge Bases

```
GET    /api/v1/kb                  # List KBs
POST   /api/v1/kb                  # Create KB
GET    /api/v1/kb/{id}             # Get KB
DELETE /api/v1/kb/{id}             # Delete KB
POST   /api/v1/kb/{id}/documents   # Insert documents
POST   /api/v1/kb/{id}/search      # Semantic search
```

#### Desktop

```
GET    /api/v1/desktop/state/{id}  # Get desktop state
POST   /api/v1/desktop/state       # Save desktop state
POST   /api/v1/desktop/windows     # Create window
PUT    /api/v1/desktop/windows/{id}# Update window
DELETE /api/v1/desktop/windows/{id}# Delete window
```

Voir [docs/API.md](docs/API.md) pour l'API complète.

---

## 🛠️ Development

### Project Structure

```
getlood-platform/
├── core/                   # Core business logic
│   ├── adapters/          # MindsDB adapters
│   ├── orchestration/     # Desktop manager, etc.
│   └── pipeline/          # AI pipeline executor
├── api/                   # FastAPI backend
│   ├── gateway/           # API Gateway
│   ├── websocket/         # WebSocket handlers
│   └── graphql/           # GraphQL schema
├── frontend/              # React frontend
│   ├── src/
│   │   ├── components/    # UI components
│   │   ├── state/         # XState + Jotai
│   │   └── apps/          # Native applications
├── config/                # Configuration files
├── database/              # Database migrations
├── docs/                  # Documentation
├── scripts/               # Setup & maintenance scripts
└── tests/                 # Tests
    ├── unit/
    ├── integration/
    └── e2e/
```

### Running Tests

```bash
# Unit tests
pytest tests/unit -v

# Integration tests
pytest tests/integration -v

# E2E tests (requires running services)
playwright test

# Coverage
pytest --cov=core --cov=api tests/
```

### Code Quality

```bash
# Linting
flake8 core/ api/
eslint frontend/src

# Type checking
mypy core/ api/
tsc --noEmit

# Formatting
black core/ api/
prettier --write frontend/src
```

### Adding a New Agent

1. **Define agent in config:**

```yaml
# config/getlood_config.yaml
agents:
  system_agents:
    - name: "my_custom_agent"
      project: "system"
      model: "gpt-4"
      skills: ["custom_skill"]
      prompt: "You are a custom agent..."
```

2. **Create agent:**

```python
from core.adapters.agent_adapter import AgentAdapter, AgentSpec

spec = AgentSpec(
    name="my_custom_agent",
    model="gpt-4",
    skills=["custom_skill"],
    prompt="You are a custom agent..."
)

agent = await agent_adapter.create_agent(spec)
```

3. **Use agent:**

```python
response = await agent_adapter.query_agent(
    agent_name="my_custom_agent",
    message="Hello!",
    session_id="session_123"
)
```

---

## 🚢 Deployment

### Docker Compose (Production)

```bash
# Build images
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Check logs
docker-compose -f docker-compose.prod.yml logs -f

# Scale API
docker-compose -f docker-compose.prod.yml up -d --scale getlood-api=5
```

### Kubernetes

```bash
# Apply manifests
kubectl apply -f k8s/namespace.yml
kubectl apply -f k8s/configmap.yml
kubectl apply -f k8s/secrets.yml
kubectl apply -f k8s/mindsdb.yml
kubectl apply -f k8s/postgres.yml
kubectl apply -f k8s/redis.yml
kubectl apply -f k8s/api.yml
kubectl apply -f k8s/frontend.yml
kubectl apply -f k8s/ingress.yml

# Check status
kubectl get pods -n getlood-prod

# Scale API
kubectl scale deployment getlood-api --replicas=10 -n getlood-prod
```

### Performance Tuning

**Database:**
```yaml
# docker-compose.yml
postgres:
  environment:
    - shared_buffers=256MB
    - max_connections=200
    - effective_cache_size=1GB
```

**API:**
```yaml
# config/getlood_config.yaml
api:
  workers: 4
  worker_class: "uvicorn.workers.UvicornWorker"
  max_requests: 1000
  timeout: 30
```

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Workflow

1. **Fork & Clone**
```bash
git clone https://github.com/YOUR_USERNAME/getlood-platform.git
cd getlood-platform
```

2. **Create Branch**
```bash
git checkout -b feature/my-awesome-feature
```

3. **Make Changes & Test**
```bash
pytest tests/
npm run test
```

4. **Commit (Conventional Commits)**
```bash
git commit -m "feat(agents): add custom skill support"
```

5. **Push & PR**
```bash
git push origin feature/my-awesome-feature
```

### Commit Convention

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `test`: Tests
- `chore`: Maintenance

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **MindsDB** - For the amazing AI orchestration platform
- **Lovable** - For the development platform
- **React** - For the UI framework
- **XState** - For state machine management
- **Tailwind CSS** - For styling

---

## 📞 Support

- 📧 Email: support@getlood.com
- 💬 Discord: [discord.gg/getlood](https://discord.gg/getlood)
- 🐛 Issues: [github.com/getlood/platform/issues](https://github.com/getlood/platform/issues)
- 📖 Docs: [docs.getlood.com](https://docs.getlood.com)

---

<div align="center">

**Made with ❤️ by the GETLOOD Team**

[Website](https://getlood.com) · [Documentation](https://docs.getlood.com) · [Blog](https://blog.getlood.com)

</div>
