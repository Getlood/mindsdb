# Configuration Serveur Distant - GETLOOD Platform

Guide pour déployer GETLOOD sur un serveur distant (srv818698.hstgr.cloud).

---

## 🌐 Architecture Réseau

```
Internet → srv818698.hstgr.cloud:8081 (nginx) → Services Docker internes
                                              ├─→ frontend:5173
                                              ├─→ api:8000
                                              └─→ mindsdb:47334
```

**Point d'entrée unique:** Nginx sur le port **8081**

---

## 📋 Checklist de Configuration

### 1. Variables d'Environnement

Créer le fichier `.env` depuis `.env.example`:

```bash
cp .env.example .env
nano .env
```

Vérifiez que ces variables utilisent le bon domaine:

```env
# CORS - Autoriser les requêtes depuis votre domaine
CORS_ORIGINS=http://srv818698.hstgr.cloud:8081,http://srv818698.hstgr.cloud:5173

# Frontend - API accessible via nginx
VITE_API_URL=http://srv818698.hstgr.cloud:8081/api
VITE_WS_URL=ws://srv818698.hstgr.cloud:8081/ws

# JWT Secret (générez-en un nouveau)
JWT_SECRET=$(openssl rand -hex 32)
```

### 2. Firewall - Ouvrir les Ports

Vérifiez que les ports sont ouverts:

```bash
# Vérifier l'état du firewall
sudo firewall-cmd --state
# ou
sudo ufw status

# Ouvrir le port nginx (8081)
sudo firewall-cmd --permanent --add-port=8081/tcp
sudo firewall-cmd --reload

# ou avec ufw
sudo ufw allow 8081/tcp
```

**Ports à ouvrir:**
- ✅ **8081** (nginx - OBLIGATOIRE)
- ⚠️ **5173** (frontend dev - optionnel, pour debug)
- ⚠️ **8000** (API - optionnel, pour debug)
- ⚠️ **47334** (MindsDB - optionnel, pour admin)

### 3. Rebuild avec la Nouvelle Configuration

```bash
# Arrêter les services
docker compose down

# Rebuild le frontend avec les nouvelles URLs
docker compose build --no-cache getlood-frontend

# Redémarrer tout
docker compose up -d

# Vérifier l'état
docker compose ps
```

### 4. Vérifier la Configuration Nginx

```bash
# Tester la config nginx
docker compose exec nginx nginx -t

# Voir les logs nginx
docker compose logs nginx

# Recharger nginx si besoin
docker compose restart nginx
```

---

## 🔗 URLs d'Accès

Une fois configuré, accédez aux services via:

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://srv818698.hstgr.cloud:8081 | Application principale |
| **API Docs** | http://srv818698.hstgr.cloud:8081/api/docs | Documentation API |
| **Health Check** | http://srv818698.hstgr.cloud:8081/health | Vérification nginx |
| **Grafana** | http://srv818698.hstgr.cloud:3000 | Monitoring |
| **MindsDB** | http://srv818698.hstgr.cloud:47334 | Console MindsDB |

---

## 🧪 Tests de Connectivité

### Test 1: Nginx Health Check

```bash
curl http://srv818698.hstgr.cloud:8081/health
# Attendu: healthy
```

### Test 2: API Health

```bash
curl http://srv818698.hstgr.cloud:8081/api/health
# Attendu: {"status":"healthy"}
```

### Test 3: Frontend

```bash
curl -I http://srv818698.hstgr.cloud:8081/
# Attendu: HTTP/1.1 200 OK
```

### Test 4: Depuis le Navigateur

```
http://srv818698.hstgr.cloud:8081
```

Si vous voyez l'interface GETLOOD → ✅ Succès !

---

## ⚠️ Problèmes Courants

### Erreur 404 Not Found

**Cause:** Accès direct au port du service au lieu de passer par nginx

```bash
# ❌ INCORRECT
http://srv818698.hstgr.cloud:5173  # Accès direct frontend
http://srv818698.hstgr.cloud:8000  # Accès direct API

# ✅ CORRECT
http://srv818698.hstgr.cloud:8081  # Via nginx
```

**Solution:**
- Utilisez toujours le port **8081** (nginx)
- Nginx route automatiquement vers les bons services

### Connexion Refusée

**Diagnostic:**

```bash
# Vérifier que nginx écoute
sudo netstat -tlnp | grep 8081

# Vérifier que le conteneur est up
docker ps | grep getlood-nginx

# Tester depuis le serveur
curl localhost:8081/health
```

**Causes possibles:**
1. Port 8081 fermé dans le firewall
2. Nginx pas démarré
3. docker-compose.yml mapping de port incorrect

### ERR_CONNECTION_REFUSED

**Cause:** Firewall bloque le port 8081

**Solution:**

```bash
# Vérifier les ports ouverts
sudo ss -tlnp | grep 8081

# Ouvrir le port
sudo firewall-cmd --permanent --add-port=8081/tcp
sudo firewall-cmd --reload

# Tester à nouveau
curl http://srv818698.hstgr.cloud:8081/health
```

### CORS Error dans la Console

**Symptôme:**
```
Access to fetch at 'http://srv818698.hstgr.cloud:8081/api/...' from origin
'http://srv818698.hstgr.cloud:8081' has been blocked by CORS policy
```

**Solution:**

Vérifier `.env`:
```env
CORS_ORIGINS=http://srv818698.hstgr.cloud:8081,http://srv818698.hstgr.cloud:5173
```

Redémarrer l'API:
```bash
docker compose restart getlood-api
```

---

## 🔒 Configuration SSL/HTTPS (Optionnel)

Pour production, configurez HTTPS:

### 1. Obtenir un Certificat SSL

```bash
# Avec Let's Encrypt (certbot)
sudo certbot certonly --standalone -d srv818698.hstgr.cloud
```

### 2. Copier les Certificats

```bash
sudo cp /etc/letsencrypt/live/srv818698.hstgr.cloud/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/srv818698.hstgr.cloud/privkey.pem nginx/ssl/
```

### 3. Mettre à Jour nginx.conf

```nginx
server {
    listen 443 ssl http2;
    server_name srv818698.hstgr.cloud;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    # ... reste de la config
}

# Redirection HTTP → HTTPS
server {
    listen 80;
    server_name srv818698.hstgr.cloud;
    return 301 https://$server_name$request_uri;
}
```

### 4. Mettre à Jour docker-compose.yml

```yaml
nginx:
  ports:
    - "80:80"    # HTTP
    - "443:443"  # HTTPS
```

### 5. Mettre à Jour .env

```env
VITE_API_URL=https://srv818698.hstgr.cloud/api
VITE_WS_URL=wss://srv818698.hstgr.cloud/ws
CORS_ORIGINS=https://srv818698.hstgr.cloud
```

---

## 📊 Monitoring

### Logs en Temps Réel

```bash
# Tous les services
docker compose logs -f

# Service spécifique
docker compose logs -f nginx
docker compose logs -f getlood-api
docker compose logs -f getlood-frontend
```

### Ressources Utilisées

```bash
docker stats
```

### Espace Disque

```bash
docker system df
```

---

## 🚀 Commandes Rapides

```bash
# Redémarrer tout
docker compose restart

# Rebuild frontend avec nouvelles URLs
docker compose up -d --build getlood-frontend

# Voir l'état
docker compose ps

# Nettoyer et relancer
docker compose down && docker compose up -d

# Accéder aux logs nginx
docker compose logs nginx | grep error
```

---

## ✅ Validation Finale

Checklist avant mise en production:

- [ ] Port 8081 ouvert dans le firewall
- [ ] `.env` créé avec les bonnes URLs (srv818698.hstgr.cloud:8081)
- [ ] JWT_SECRET généré (32 caractères hex)
- [ ] CORS_ORIGINS configuré
- [ ] Tous les services `Up (healthy)`
- [ ] `curl http://srv818698.hstgr.cloud:8081/health` retourne `healthy`
- [ ] Interface accessible dans le navigateur
- [ ] API docs accessible: `/api/docs`
- [ ] WebSocket fonctionne (tester le chat en temps réel)

---

## 📞 Support

Si problème, collectez ces informations:

```bash
# État des services
docker compose ps > debug.txt

# Logs nginx
docker compose logs nginx >> debug.txt

# Logs API
docker compose logs getlood-api >> debug.txt

# Test de connectivité
curl -v http://srv818698.hstgr.cloud:8081/health >> debug.txt
```

Envoyez `debug.txt` avec votre demande de support.
