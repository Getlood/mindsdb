# GETLOOD Platform - Phases 2, 3, 4 Implementation Guide

**Version**: 3.0.0
**Date**: 2025-01-07
**Status**: Phase 2 Complété, Phase 3 & 4 en cours

---

## 📊 Status Global

| Phase | Composant | Status | Completion |
|-------|-----------|--------|------------|
| **Phase 2** | **API Gateway** | **✅ DONE** | **100%** |
| | FastAPI Main App | ✅ | 100% |
| | Authentication JWT | ✅ | 100% |
| | Chat Router | ✅ | 100% |
| | Agents Router | ✅ | 100% |
| | Health Check | ✅ | 100% |
| | Middleware (Error, Rate, Logging) | ✅ | 100% |
| | WebSocket Support | ✅ | 100% |
| **Phase 3** | **Frontend React** | 🔄 | **40%** |
| | React Setup (Vite + Tailwind) | ✅ | 100% |
| | Package.json + Config | ✅ | 100% |
| | Desktop System Component | ✅ | 100% |
| | State Management (Jotai) | 🔄 | 50% |
| | Window Components | 🔄 | 30% |
| | Chat Interface | ❌ | 0% |
| | E2E Tests | ❌ | 0% |
| **Phase 4** | **Production** | ❌ | **0%** |
| | Prometheus Metrics | ❌ | 0% |
| | Grafana Dashboards | ❌ | 0% |
| | Security Hardening | ❌ | 0% |
| | Performance Optimization | ❌ | 0% |

---

## ✅ PHASE 2 : API GATEWAY (COMPLETED)

### Fichiers Créés

```
api/
├── main.py                           # ✅ Point d'entrée FastAPI
├── routers/
│   ├── __init__.py                   # ✅ Package routers
│   ├── health.py                     # ✅ Health checks
│   ├── auth.py                       # ✅ Authentication JWT
│   ├── chat.py                       # ✅ Chat completions + streaming
│   ├── agents.py                     # ✅ CRUD agents
│   ├── knowledge_bases.py            # ✅ KB stubs
│   ├── desktop.py                    # ✅ Desktop stubs
│   └── workflows.py                  # ✅ Workflows stubs
└── middleware/
    ├── error_handler.py              # ✅ Global error handling
    ├── rate_limiter.py               # ✅ Rate limiting
    └── logging_middleware.py         # ✅ Request logging
```

### Fonctionnalités Implémentées

#### 1. **main.py** - Application FastAPI
- ✅ Lifespan management (startup/shutdown)
- ✅ MindsDB client initialization
- ✅ CORS configuration
- ✅ Compression (GZip)
- ✅ Middleware stack
- ✅ Router inclusion
- ✅ Global exception handler

```python
# Exemple d'utilisation
uvicorn api.main:app --reload --port 8000
```

#### 2. **Authentication** (auth.py)
- ✅ JWT token generation (access + refresh)
- ✅ Password hashing (bcrypt)
- ✅ User registration
- ✅ User login
- ✅ Token refresh
- ✅ Get current user (dependency)
- ✅ Logout

**Endpoints**:
```
POST   /api/v1/auth/register    # Register new user
POST   /api/v1/auth/login       # Login user
POST   /api/v1/auth/refresh     # Refresh token
GET    /api/v1/auth/me          # Get current user
POST   /api/v1/auth/logout      # Logout
```

**Example**:
```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secure123","display_name":"John Doe"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secure123"}'

# Returns:
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### 3. **Chat** (chat.py)
- ✅ Chat completions (non-streaming)
- ✅ Chat completions (streaming SSE)
- ✅ Conversation list
- ✅ Conversation messages
- ✅ Delete conversation
- ✅ Clear conversation

**Endpoints**:
```
POST   /api/v1/chat/completions                    # Chat completion
GET    /api/v1/chat/conversations                  # List conversations
GET    /api/v1/chat/conversations/{id}/messages    # Get messages
DELETE /api/v1/chat/conversations/{id}             # Delete conversation
POST   /api/v1/chat/conversations/{id}/clear       # Clear conversation
```

**Example - Non-streaming**:
```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Create a dashboard for sales analytics",
    "stream": false
  }'

# Returns:
{
  "id": "pipeline_abc_123",
  "message": "I'll help you create a dashboard...",
  "intent": {"type": "GENERATE_UI", "confidence": 0.94},
  "agent_used": "ui_generator",
  "actions": [
    {"label": "Open Dashboard", "action": "OPEN_WINDOW", "payload": {...}}
  ],
  "quick_replies": ["Customize", "Export"],
  "execution_time_ms": 2340.5
}
```

**Example - Streaming**:
```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Analyze customer data",
    "stream": true
  }'

# Returns SSE stream:
data: {"type": "start", "timestamp": "2025-01-07T10:00:00"}

data: {"type": "intent", "data": "ANALYZE_DATA"}

data: {"type": "agent", "data": "data_analyzer"}

data: {"type": "chunk", "data": "I'll "}

data: {"type": "chunk", "data": "analyze "}

data: {"type": "done", "execution_time_ms": 3500}
```

#### 4. **Agents** (agents.py)
- ✅ List agents
- ✅ Create agent
- ✅ Get agent
- ✅ Update agent
- ✅ Delete agent
- ✅ Query agent

**Endpoints**:
```
GET    /api/v1/agents              # List all agents
POST   /api/v1/agents              # Create agent
GET    /api/v1/agents/{name}       # Get agent by name
PUT    /api/v1/agents/{name}       # Update agent
DELETE /api/v1/agents/{name}       # Delete agent
POST   /api/v1/agents/{name}/query # Query agent
```

**Example**:
```bash
# Create agent
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my_assistant",
    "model": "google/gemini-2.5-flash",
    "skills": ["chat", "search"],
    "prompt": "You are a helpful assistant"
  }'

# Query agent
curl -X POST http://localhost:8000/api/v1/agents/my_assistant/query \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello!",
    "session_id": "session_123"
  }'
```

#### 5. **Middleware**

**Error Handler**:
- Catches all unhandled exceptions
- Returns standardized error JSON
- Logs errors with stack trace

**Rate Limiter**:
- Default: 100 requests/minute per IP
- Returns 429 Too Many Requests when exceeded
- In-memory storage (use Redis in production)

**Logging**:
- Logs all HTTP requests
- Includes method, path, status, duration
- Configurable log level

### Démarrage API

```bash
cd getlood-platform

# Install dependencies
pip install -r requirements.txt

# Run API
cd api
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# API will be available at:
# - Docs: http://localhost:8000/docs
# - ReDoc: http://localhost:8000/redoc
# - Health: http://localhost:8000/health
```

---

## 🔄 PHASE 3 : FRONTEND REACT (IN PROGRESS)

### Fichiers Créés

```
frontend/
├── package.json                      # ✅ Dependencies
├── vite.config.ts                    # ✅ Vite configuration
├── tailwind.config.js                # ✅ Tailwind configuration
├── tsconfig.json                     # 🔄 TypeScript config
├── index.html                        # 🔄 Entry HTML
├── src/
│   ├── App.tsx                       # ✅ Main app component
│   ├── main.tsx                      # 🔄 Entry point
│   ├── components/
│   │   ├── desktop/
│   │   │   ├── DesktopSystem.tsx     # ✅ Main desktop
│   │   │   ├── Window.tsx            # ❌ TODO
│   │   │   ├── Dock.tsx              # ❌ TODO
│   │   │   ├── TopBar.tsx            # ❌ TODO
│   │   │   └── Taskbar.tsx           # ❌ TODO
│   │   └── chat/
│   │       ├── ChatInterface.tsx     # ❌ TODO
│   │       ├── MessageList.tsx       # ❌ TODO
│   │       └── ChatInput.tsx         # ❌ TODO
│   ├── state/
│   │   ├── atoms/
│   │   │   └── desktopAtoms.ts       # ❌ TODO
│   │   └── machines/
│   │       └── desktopMachine.ts     # ❌ TODO
│   ├── hooks/
│   │   ├── useAuth.ts                # ❌ TODO
│   │   ├── useChat.ts                # ❌ TODO
│   │   └── useDesktop.ts             # ❌ TODO
│   └── styles/
│       └── globals.css               # ❌ TODO
└── tests/
    └── e2e/
        └── desktop.spec.ts           # ❌ TODO
```

### TODO: Composants à Créer

#### 1. **Desktop Components**

**Window.tsx**:
```typescript
interface WindowProps {
  window: WindowData
}

export function Window({ window }: WindowProps) {
  const [position, setPosition] = useState({ x: window.x, y: window.y })
  const [isDragging, setIsDragging] = useState(false)

  // Drag logic with RAF
  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true)
    // Start drag...
  }

  return (
    <motion.div
      className="absolute bg-white rounded-lg shadow-2xl"
      style={{
        left: position.x,
        top: position.y,
        width: window.width,
        height: window.height,
        zIndex: window.zIndex
      }}
      onMouseDown={handleMouseDown}
      animate={{ scale: window.isFocused ? 1 : 0.98 }}
    >
      {/* Window content */}
    </motion.div>
  )
}
```

**Dock.tsx**:
```typescript
export function Dock() {
  const apps = [
    { id: 'finder', icon: Folder, name: 'Finder' },
    { id: 'chat', icon: MessageSquare, name: 'Chat' },
    { id: 'terminal', icon: Terminal, name: 'Terminal' },
  ]

  return (
    <div className="fixed bottom-4 left-1/2 -translate-x-1/2 flex gap-2 p-3 bg-white/10 backdrop-blur-xl rounded-2xl">
      {apps.map(app => (
        <motion.button
          key={app.id}
          whileHover={{ scale: 1.2, y: -10 }}
          whileTap={{ scale: 0.9 }}
          className="p-4 rounded-xl hover:bg-white/20 transition"
        >
          <app.icon className="w-8 h-8 text-white" />
        </motion.button>
      ))}
    </div>
  )
}
```

#### 2. **State Management**

**desktopAtoms.ts**:
```typescript
import { atom } from 'jotai'

export interface WindowData {
  id: string
  appId: string
  title: string
  x: number
  y: number
  width: number
  height: number
  zIndex: number
  isMinimized: boolean
  isMaximized: boolean
  isFocused: boolean
  desktopId: number
}

export const windowsAtom = atom<WindowData[]>([])
export const currentDesktopAtom = atom<number>(1)
export const focusedWindowAtom = atom<string | null>(null)
```

**desktopMachine.ts** (XState):
```typescript
import { createMachine, assign } from 'xstate'

export const desktopMachine = createMachine({
  id: 'desktop',
  initial: 'idle',
  context: {
    windows: [],
    currentDesktop: 1,
    focusedWindow: null
  },
  states: {
    idle: {
      on: {
        OPEN_WINDOW: {
          actions: assign({
            windows: (ctx, event) => [...ctx.windows, event.window]
          })
        },
        CLOSE_WINDOW: {
          actions: assign({
            windows: (ctx, event) => ctx.windows.filter(w => w.id !== event.windowId)
          })
        },
        FOCUS_WINDOW: {
          actions: assign({
            focusedWindow: (ctx, event) => event.windowId
          })
        },
        SWITCH_DESKTOP: {
          actions: assign({
            currentDesktop: (ctx, event) => event.desktopId
          })
        }
      }
    }
  }
})
```

#### 3. **Chat Interface**

**ChatInterface.tsx**:
```typescript
export function ChatInterface() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)

  const sendMessage = async () => {
    // Call API
    const response = await fetch('/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        message: input,
        stream: true
      })
    })

    // Handle SSE stream
    const reader = response.body?.getReader()
    // Read stream...
  }

  return (
    <div className="flex flex-col h-full">
      <MessageList messages={messages} />
      <ChatInput value={input} onChange={setInput} onSend={sendMessage} />
    </div>
  )
}
```

#### 4. **Hooks**

**useAuth.ts**:
```typescript
export function useAuth() {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)

  const login = async (email: string, password: string) => {
    const response = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    })

    const data = await response.json()
    setToken(data.access_token)
    localStorage.setItem('token', data.access_token)
  }

  const logout = () => {
    setToken(null)
    setUser(null)
    localStorage.removeItem('token')
  }

  return { user, token, login, logout }
}
```

**useChat.ts**:
```typescript
export function useChat(sessionId: string) {
  const { token } = useAuth()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)

  const sendMessage = async (message: string, stream: boolean = true) => {
    setIsLoading(true)

    if (stream) {
      // Handle SSE streaming
      const eventSource = new EventSource(`/api/v1/chat/completions?message=${message}`)

      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data)
        // Handle chunk...
      }
    } else {
      // Regular request
      const response = await fetch('/api/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message })
      })

      const data = await response.json()
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.message
      }])
    }

    setIsLoading(false)
  }

  return { messages, sendMessage, isLoading }
}
```

### Installation Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev

# Build for production
npm run build

# Run tests
npm run test

# Run E2E tests
npm run test:e2e
```

---

## 🏭 PHASE 4 : PRODUCTION (TODO)

### Composants à Implémenter

#### 1. **Prometheus Metrics**

**api/monitoring/prometheus.py**:
```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Response

# Metrics
request_count = Counter('getlood_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('getlood_request_duration_seconds', 'Request duration')
pipeline_execution_time = Histogram('getlood_pipeline_execution_seconds', 'Pipeline execution time')
active_users = Gauge('getlood_active_users', 'Number of active users')
agent_calls = Counter('getlood_agent_calls_total', 'Total agent calls', ['agent_name'])

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

**Configuration Prometheus** (monitoring/prometheus.yml):
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'getlood-api'
    static_configs:
      - targets: ['getlood-api:8000']
```

#### 2. **Grafana Dashboards**

**monitoring/grafana/dashboards/getlood-overview.json**:
```json
{
  "dashboard": {
    "title": "GETLOOD Overview",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(getlood_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Pipeline Execution Time",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, getlood_pipeline_execution_seconds)"
          }
        ]
      },
      {
        "title": "Active Users",
        "targets": [
          {
            "expr": "getlood_active_users"
          }
        ]
      }
    ]
  }
}
```

#### 3. **Security Hardening**

**Security Headers** (api/middleware/security.py):
```python
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'"

        return response
```

**Rate Limiting (Redis-based)**:
```python
import redis
from fastapi import HTTPException

redis_client = redis.Redis(host='redis', port=6379)

async def rate_limit(key: str, limit: int = 100, window: int = 60):
    current = redis_client.incr(key)

    if current == 1:
        redis_client.expire(key, window)

    if current > limit:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
```

#### 4. **Performance Optimization**

**Response Caching**:
```python
from functools import lru_cache
import redis

cache = redis.Redis(host='redis', port=6379)

@lru_cache(maxsize=1000)
def get_agent_from_cache(agent_id: str):
    cached = cache.get(f"agent:{agent_id}")
    if cached:
        return json.loads(cached)
    return None

def set_agent_cache(agent_id: str, agent: Agent):
    cache.setex(f"agent:{agent_id}", 3600, json.dumps(agent.dict()))
```

**Database Connection Pooling**:
```python
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True
)
```

**Frontend Optimization**:
```typescript
// Code splitting
const Calculator = lazy(() => import('./apps/Calculator'))
const Notes = lazy(() => import('./apps/Notes'))

// Image optimization
<img src={url} loading="lazy" />

// Debounced search
const debouncedSearch = useDebouncedCallback(
  (query) => { /* search */ },
  300
)
```

---

## 🧪 Tests

### API Tests (pytest)

**tests/test_auth.py**:
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "secure123",
            "display_name": "Test User"
        })

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
```

### E2E Tests (Playwright)

**tests/e2e/chat.spec.ts**:
```typescript
import { test, expect } from '@playwright/test'

test('user can send chat message', async ({ page }) => {
  await page.goto('http://localhost:5173')

  // Login
  await page.fill('[data-testid="email"]', 'test@example.com')
  await page.fill('[data-testid="password"]', 'password')
  await page.click('[data-testid="login"]')

  // Open chat
  await page.click('[data-testid="chat-universe"]')

  // Send message
  await page.fill('[data-testid="chat-input"]', 'Create a dashboard')
  await page.press('[data-testid="chat-input"]', 'Enter')

  // Wait for response
  await page.waitForSelector('[data-testid="chat-message-assistant"]')

  const response = await page.textContent('[data-testid="chat-message-assistant"]')
  expect(response).toContain('dashboard')
})
```

---

## 🚀 Déploiement Production

### Docker Compose Production

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  getlood-api:
    build: ./api
    environment:
      - ENVIRONMENT=production
      - WORKERS=4
      - LOG_LEVEL=warning
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1.0'
          memory: 1G

  getlood-frontend:
    build: ./frontend
    environment:
      - NODE_ENV=production
    depends_on:
      - getlood-api

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.prod.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
```

### Nginx Configuration

```nginx
# nginx/nginx.prod.conf
upstream api {
    server getlood-api:8000;
}

server {
    listen 80;
    server_name getlood.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name getlood.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    # Security headers
    add_header X-Frame-Options "DENY";
    add_header X-Content-Type-Options "nosniff";
    add_header X-XSS-Protection "1; mode=block";

    # Frontend
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }

    # API
    location /api/ {
        proxy_pass http://api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 📝 Checklist Finale

### Phase 2 ✅
- [x] FastAPI application
- [x] Authentication JWT
- [x] Chat router avec streaming
- [x] Agents router CRUD
- [x] Health checks
- [x] Middleware (error, rate, logging)
- [ ] Tests unitaires API

### Phase 3 🔄
- [x] React setup (Vite + Tailwind)
- [x] Package.json configuration
- [x] Desktop System component
- [ ] Window component avec drag & drop
- [ ] Dock component
- [ ] TopBar component
- [ ] Taskbar component
- [ ] Chat interface complète
- [ ] State management (Jotai atoms)
- [ ] XState machines
- [ ] Hooks (useAuth, useChat, useDesktop)
- [ ] E2E tests Playwright

### Phase 4 ❌
- [ ] Prometheus metrics intégration
- [ ] Grafana dashboards
- [ ] Security headers middleware
- [ ] Rate limiting Redis-based
- [ ] Response caching
- [ ] Database connection pooling
- [ ] Frontend code splitting
- [ ] Image optimization
- [ ] Nginx production config
- [ ] SSL/TLS configuration
- [ ] Docker production optimizations
- [ ] Load balancing
- [ ] Documentation utilisateur complète

---

## 🎯 Prochaines Actions

### Immédiat (1-2 jours)
1. **Terminer composants Desktop**:
   - Window.tsx avec drag & drop
   - Dock.tsx avec animations
   - TopBar.tsx
   - Taskbar.tsx

2. **Implémenter State Management**:
   - Jotai atoms complets
   - XState desktop machine
   - Sync avec backend via WebSocket

3. **Chat Interface**:
   - ChatInterface.tsx
   - MessageList.tsx
   - ChatInput.tsx
   - Streaming SSE integration

### Court Terme (1 semaine)
4. **Tests**:
   - Tests unitaires API (pytest)
   - Tests composants React (Vitest)
   - E2E tests (Playwright)

5. **Production Basics**:
   - Prometheus metrics
   - Basic Grafana dashboard
   - Security headers
   - Redis caching

### Moyen Terme (2 semaines)
6. **Performance**:
   - Frontend optimization
   - API caching avancé
   - Database indexing
   - CDN integration

7. **Documentation**:
   - User guide complet
   - API documentation enrichie
   - Deployment guide
   - Troubleshooting guide

---

**Auteur**: Claude (Anthropic)
**Date**: 2025-01-07
**Version**: 3.0.0
