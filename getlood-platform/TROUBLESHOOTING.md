# GETLOOD Platform - Troubleshooting Guide

Guide de dépannage pour les problèmes courants de déploiement.

---

## Erreurs de Build Docker

### ❌ Error: `npm ci` can only install with existing package-lock.json

**Symptôme:**
```
npm error The `npm ci` command can only install with an existing package-lock.json
```

**Cause:**
Le fichier `package-lock.json` est manquant dans le dossier frontend.

**Solution:**
Le Dockerfile a été mis à jour pour gérer ce cas automatiquement. Assurez-vous d'avoir la dernière version:
```bash
git pull origin claude/getlood-platform-setup-011CUobW5rr2LZwUVjTVWzuY
```

**Alternative manuelle:**
```bash
cd frontend
npm install  # Génère package-lock.json
cd ..
docker compose build getlood-frontend
```

---

### ❌ Error: open Dockerfile: no such file or directory

**Symptôme:**
```
failed to solve: failed to read dockerfile: open Dockerfile: no such file or directory
```

**Cause:**
Le Dockerfile est manquant pour un des services.

**Solution:**
Vérifiez que tous les Dockerfiles existent:
```bash
ls -la api/Dockerfile
ls -la frontend/Dockerfile
```

Si manquants, récupérez-les depuis le dépôt:
```bash
git pull
git checkout claude/getlood-platform-setup-011CUobW5rr2LZwUVjTVWzuY
```

---

### ❌ Error: Context canceled

**Symptôme:**
```
context canceled
```

**Cause:**
Build interrompu ou timeout.

**Solution:**
```bash
# Nettoyer le cache Docker
docker builder prune -a

# Rebuilder avec logs détaillés
docker compose build --no-cache --progress=plain
```

---

## Erreurs au Démarrage

### ❌ Error: Port already in use

**Symptôme:**
```
Error starting userland proxy: listen tcp 0.0.0.0:80: bind: address already in use
```

**Cause:**
Le port est déjà utilisé par un autre service.

**Solution Option 1:** Arrêter le service conflictuel
```bash
# Trouver le processus qui utilise le port
sudo lsof -i :80
sudo kill -9 <PID>
```

**Solution Option 2:** Changer le port dans docker-compose.yml
```yaml
ports:
  - "8080:80"  # Change external port to 8080
```

**Ports utilisés par GETLOOD:**
- 80 (Nginx)
- 8000 (API)
- 5173 (Frontend dev)
- 47334-47336 (MindsDB)
- 5432 (PostgreSQL)
- 6379 (Redis)
- 8100 (ChromaDB)
- 3000 (Grafana)
- 9090 (Prometheus)

---

### ❌ Services stay "unhealthy"

**Symptôme:**
```
getlood-mindsdb   unhealthy
getlood-api       unhealthy
```

**Diagnostic:**
```bash
# Voir les logs
./quickstart.sh logs mindsdb
./quickstart.sh logs getlood-api

# Vérifier l'état détaillé
docker inspect getlood-mindsdb | grep -A 10 Health
```

**Solutions:**

**Pour MindsDB:**
- MindsDB prend 60-90 secondes au premier démarrage
- Attendez et vérifiez à nouveau: `docker compose ps`

**Pour API:**
```bash
# Vérifier si la base de données est accessible
docker compose exec getlood-api ping postgres

# Vérifier les variables d'environnement
docker compose exec getlood-api env | grep -i db
```

---

### ❌ Database connection refused

**Symptôme:**
```
FATAL: database "getlood" does not exist
connection refused to postgres:5432
```

**Solution:**
```bash
# Recréer la base de données
docker compose down
docker volume rm getlood-platform_postgres_data
docker compose up -d postgres

# Attendre que postgres soit healthy
watch -n 2 'docker compose ps postgres'

# Redémarrer tous les services
docker compose up -d
```

---

### ❌ MindsDB: Model provider API key missing

**Symptôme:**
```
Error: OpenAI API key not found
Error: Anthropic API key not found
```

**Solution:**
Configurez vos clés API dans `.env`:
```bash
nano .env

# Ajoutez:
OPENAI_API_KEY=sk-your-actual-key-here
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
```

Redémarrez:
```bash
docker compose restart getlood-api mindsdb
```

---

## Erreurs de Permissions

### ❌ Permission denied: './quickstart.sh'

**Symptôme:**
```
bash: ./quickstart.sh: Permission denied
```

**Solution:**
```bash
chmod +x quickstart.sh
./quickstart.sh start
```

---

### ❌ Cannot connect to Docker daemon

**Symptôme:**
```
Cannot connect to the Docker daemon at unix:///var/run/docker.sock
```

**Solution:**
```bash
# Démarrer le service Docker
sudo systemctl start docker

# Ajouter votre user au groupe docker
sudo usermod -aG docker $USER
newgrp docker

# Ou utiliser sudo
sudo docker compose up -d
```

---

## Erreurs de Performance

### ⚠️ Services running slow

**Diagnostic:**
```bash
# Vérifier l'utilisation des ressources
docker stats

# Vérifier l'espace disque
docker system df
```

**Solutions:**

**Augmenter la RAM Docker:**
- Docker Desktop → Settings → Resources
- Allouer au minimum 8GB RAM

**Nettoyer l'espace disque:**
```bash
# Nettoyer les images inutilisées
docker image prune -a

# Nettoyer tout
docker system prune -a --volumes
```

---

## Erreurs de Réseau

### ❌ Frontend can't reach API

**Symptôme:**
Console browser:
```
Failed to fetch http://localhost:8000/api/...
```

**Solution:**

**Vérifier que l'API est accessible:**
```bash
curl http://localhost:8000/health
```

**Vérifier la configuration CORS dans .env:**
```env
CORS_ORIGINS=http://localhost:5173,http://localhost:80
```

**Redémarrer nginx:**
```bash
docker compose restart nginx
```

---

### ❌ WebSocket connection failed

**Symptôme:**
```
WebSocket connection to 'ws://localhost:8000/ws/desktop/1' failed
```

**Solution:**

**Vérifier nginx WebSocket proxy:**
```bash
# Voir les logs nginx
docker compose logs nginx

# Tester manuellement
wscat -c ws://localhost:8000/ws/desktop/1?token=YOUR_TOKEN
```

**Vérifier le timeout nginx:**
Le fichier `nginx/nginx.conf` doit avoir:
```nginx
location /ws {
    proxy_read_timeout 86400;
    proxy_send_timeout 86400;
}
```

---

## Commandes de Debug Utiles

```bash
# Voir tous les logs
./quickstart.sh logs

# Logs d'un service spécifique
./quickstart.sh logs getlood-api

# Logs en temps réel
docker compose logs -f getlood-api

# Entrer dans un conteneur
docker compose exec getlood-api sh
docker compose exec postgres psql -U postgres -d getlood

# Vérifier les réseaux
docker network ls
docker network inspect getlood-platform_getlood-network

# Vérifier les volumes
docker volume ls
docker volume inspect getlood-platform_postgres_data

# Rebuild complet
./quickstart.sh clean
./quickstart.sh setup

# État détaillé d'un service
docker inspect getlood-api

# Ressources utilisées
docker stats

# Espace disque
docker system df -v
```

---

## Reset Complet

Si rien ne fonctionne, reset complet:

```bash
# 1. Arrêter tout
docker compose down

# 2. Supprimer tous les volumes
docker volume rm $(docker volume ls -q | grep getlood)

# 3. Supprimer toutes les images
docker rmi $(docker images | grep getlood | awk '{print $3}')

# 4. Nettoyer le cache de build
docker builder prune -a

# 5. Reconstruire depuis zéro
./quickstart.sh setup
```

---

## Obtenir de l'Aide

Si le problème persiste:

1. **Collecter les informations:**
```bash
# Créer un rapport de debug
./quickstart.sh status > debug-report.txt
docker compose logs >> debug-report.txt
docker system info >> debug-report.txt
```

2. **Créer une issue GitHub:**
   - URL: https://github.com/Getlood/mindsdb/issues
   - Inclure le rapport de debug
   - Description du problème
   - Étapes pour reproduire

3. **Contacter le support:**
   - Discord: https://discord.gg/getlood
   - Email: support@getlood.com

---

## Logs Importants

### Logs de l'API
```bash
docker compose logs getlood-api | tail -100
```

Erreurs communes:
- `Database connection failed` → Vérifier PostgreSQL
- `MindsDB not responding` → Attendre le démarrage de MindsDB
- `JWT token invalid` → Vérifier JWT_SECRET dans .env

### Logs de MindsDB
```bash
docker compose logs mindsdb | tail -100
```

Erreurs communes:
- `API key not found` → Configurer clés API
- `Model not available` → Vérifier les modèles activés
- `Database migration failed` → Reset le volume

### Logs de PostgreSQL
```bash
docker compose logs postgres | tail -50
```

Erreurs communes:
- `FATAL: database does not exist` → Recréer avec init script
- `too many connections` → Augmenter max_connections

---

## Checklist de Vérification

Avant de déployer, vérifiez:

- [ ] Docker version 20.10+
- [ ] Docker Compose V2+
- [ ] 8GB+ RAM disponible
- [ ] 20GB+ espace disque
- [ ] Ports 80, 8000, 5173 disponibles
- [ ] Fichier `.env` créé depuis `.env.example`
- [ ] JWT_SECRET généré (32 caractères hex)
- [ ] Clés API configurées (OpenAI/Anthropic)
- [ ] Pas de proxy/firewall bloquant

---

## Performance Tips

### Optimiser le Build

**Utiliser le cache de build:**
```bash
# Build avec cache (rapide)
docker compose build

# Build sans cache (clean)
docker compose build --no-cache
```

**Build parallèle:**
```bash
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
docker compose build --parallel
```

### Optimiser l'Exécution

**Limiter les logs:**
```yaml
# docker-compose.yml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

**Augmenter les ressources:**
```yaml
# docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
```

---

*Dernière mise à jour: 2025-11-05*
