# GETLOOD Platform - Quick Start Guide

This guide will help you get the GETLOOD platform up and running in minutes.

## Prerequisites

- Docker 20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- Docker Compose V2+ ([Install Docker Compose](https://docs.docker.com/compose/install/))
- 8GB+ RAM available
- 20GB+ disk space

## Quick Start (Recommended)

### 1. Clone the Repository

```bash
git clone https://github.com/Getlood/mindsdb.git
cd mindsdb/getlood-platform
```

### 2. Run the Setup Script

```bash
chmod +x quickstart.sh
./quickstart.sh setup
```

This single command will:
- ✅ Check dependencies
- ✅ Create `.env` from `.env.example` with a secure JWT secret
- ✅ Create required directories
- ✅ Generate configuration files
- ✅ Pull and build Docker images
- ✅ Start all services
- ✅ Wait for services to be healthy
- ✅ Display access URLs

### 3. Access the Platform

Once setup completes, you'll see:

```
Access URLs:
Frontend:    http://localhost:80
API Docs:    http://localhost:8000/docs
MindsDB:     http://localhost:47334
Grafana:     http://localhost:3000 (admin/admin)
Prometheus:  http://localhost:9090
```

**Demo Account:**
- Email: `demo@getlood.com`
- Password: `demo123`

---

## Manual Setup

If you prefer manual setup or need more control:

### 1. Create Environment File

```bash
cp .env.example .env
```

### 2. Generate JWT Secret

```bash
openssl rand -hex 32
```

Update `JWT_SECRET` in `.env` with the generated value.

### 3. Configure API Keys

Edit `.env` and add your AI provider API keys:

```env
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 4. Start Services

```bash
docker compose up -d
```

### 5. Check Status

```bash
docker compose ps
```

Wait until all services show `healthy` status (may take 2-3 minutes).

---

## Available Commands

The `quickstart.sh` script provides several commands:

```bash
./quickstart.sh setup      # Initial setup (first time only)
./quickstart.sh start      # Start all services
./quickstart.sh stop       # Stop all services
./quickstart.sh restart    # Restart all services
./quickstart.sh logs       # Show logs (all services)
./quickstart.sh logs api   # Show logs for specific service
./quickstart.sh status     # Show service status and URLs
./quickstart.sh build      # Rebuild Docker images
./quickstart.sh clean      # Remove all containers and volumes
```

---

## Troubleshooting

### Services Won't Start

**Check Docker resources:**
```bash
docker system info | grep -i memory
```

Ensure Docker has at least 8GB RAM allocated.

**View logs:**
```bash
./quickstart.sh logs
```

### Port Conflicts

If ports 80, 8000, or 5173 are in use, edit `docker-compose.yml` to change port mappings:

```yaml
ports:
  - "8080:80"  # Change 80 to 8080
```

### Database Connection Errors

**Reset database:**
```bash
./quickstart.sh stop
docker volume rm getlood-platform_postgres_data
./quickstart.sh start
```

### MindsDB Not Responding

MindsDB takes 60-90 seconds to start. Wait for the health check:

```bash
watch -n 2 'docker compose ps'
```

Wait until `getlood-mindsdb` shows `healthy`.

---

## Service Ports

| Service | Port | Purpose |
|---------|------|---------|
| Nginx (Frontend) | 80 | Main application |
| API Gateway | 8000 | REST API & WebSocket |
| MindsDB HTTP | 47334 | AI orchestration |
| MindsDB MySQL | 47335 | MySQL protocol |
| PostgreSQL | 5432 | Primary database |
| Redis | 6379 | Cache & pub/sub |
| ChromaDB | 8100 | Vector database |
| Prometheus | 9090 | Metrics |
| Grafana | 3000 | Monitoring |
| Frontend Dev | 5173 | Vite dev server |

---

## Next Steps

1. **Configure AI Models:**
   - Visit MindsDB at http://localhost:47334
   - Create agents using the UI or API

2. **Explore API Documentation:**
   - Visit http://localhost:8000/docs
   - Try the interactive API examples

3. **Monitor Performance:**
   - Grafana: http://localhost:3000 (admin/admin)
   - Prometheus: http://localhost:9090

4. **Read Full Documentation:**
   - [Architecture Guide](docs/ARCHITECTURE.md)
   - [API Reference](docs/API_REFERENCE.md)
   - [Development Guide](docs/DEVELOPMENT.md)

---

## Production Deployment

For production deployment:

1. **Update Security Settings:**
   ```bash
   # .env
   ENVIRONMENT=production
   DEBUG=false
   ```

2. **Use Strong Passwords:**
   - Change all default passwords in `.env`
   - Use unique JWT_SECRET

3. **Enable SSL/TLS:**
   - Configure SSL certificates in `nginx/ssl/`
   - Update nginx configuration

4. **Configure Monitoring:**
   - Set up Sentry for error tracking
   - Configure alert rules in Prometheus

5. **Backup Strategy:**
   ```bash
   # Backup volumes
   docker run --rm -v getlood-platform_postgres_data:/data -v $(pwd):/backup ubuntu tar czf /backup/postgres-backup.tar.gz /data
   ```

---

## Support

- **Issues:** https://github.com/Getlood/mindsdb/issues
- **Documentation:** https://docs.getlood.com
- **Community:** https://discord.gg/getlood

---

## License

MIT License - see [LICENSE](LICENSE) for details
