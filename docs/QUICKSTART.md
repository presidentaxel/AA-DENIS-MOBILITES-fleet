# Guide de démarrage rapide

## 1. Prérequis

- Docker et Docker Compose installés
- Fichier `.env` configuré dans `backend/.env`

## 2. Démarrer tous les services

```bash
# Depuis la racine du projet
docker compose up --build
```

Cela démarre :
- **Backend** : http://localhost:8000
- **Frontend** : http://localhost:5173
- **Prometheus** : http://localhost:9090
- **Grafana** : http://localhost:3000
- **PostgreSQL** : localhost:5432

## 3. Vérifier que tout fonctionne

### Backend
```bash
# Healthcheck
curl http://localhost:8000/health

# Devrait retourner: {"status":"ok"}

# Metrics (pour Prometheus)
curl http://localhost:8000/metrics
```

### Prometheus
- Ouvre http://localhost:9090
- Va dans **Status** → **Targets**
- Vérifie que `backend:8000` est **UP** (vert)

### Grafana
- Ouvre http://localhost:3000
- Login : `admin` / `admin` (changera au premier login)
- Va dans **Configuration** → **Data Sources**
- Vérifie que **Prometheus** est configuré avec l'URL `http://prometheus:9090`

## 4. Problèmes courants

### "Connection refused" sur localhost:8000

**Cause** : Le backend n'est pas démarré ou crash au démarrage.

**Solution** :
```bash
# Voir les logs du backend
docker compose logs backend

# Redémarrer le backend
docker compose restart backend

# Ou tout redémarrer
docker compose down
docker compose up --build
```

### Grafana ne peut pas se connecter à Prometheus

**Cause** : Prometheus n'est pas démarré ou la datasource pointe vers `localhost` au lieu de `prometheus`.

**Solution** :
1. Vérifie que Prometheus tourne :
   ```bash
   docker compose ps
   # prometheus doit être "Up"
   ```

2. Vérifie la datasource Grafana :
   - Va dans Grafana → Configuration → Data Sources
   - L'URL doit être `http://prometheus:9090` (pas `localhost`)

3. Si tu as ajouté la datasource manuellement, supprime-la et laisse le provisioning automatique la créer.

### Prometheus ne scrape pas le backend

**Cause** : Le backend n'expose pas `/metrics` ou n'est pas accessible.

**Solution** :
1. Vérifie que le backend expose `/metrics` :
   ```bash
   curl http://localhost:8000/metrics
   ```

2. Vérifie dans Prometheus (http://localhost:9090) :
   - **Status** → **Targets** → `backend:8000` doit être **UP**

3. Vérifie les logs :
   ```bash
   docker compose logs prometheus
   ```

## 5. Commandes utiles

```bash
# Voir les logs de tous les services
docker compose logs -f

# Voir les logs d'un service spécifique
docker compose logs -f backend
docker compose logs -f prometheus
docker compose logs -f grafana

# Arrêter tous les services
docker compose down

# Arrêter et supprimer les volumes (⚠️ supprime les données)
docker compose down -v

# Redémarrer un service spécifique
docker compose restart backend

# Voir l'état des services
docker compose ps
```

## 6. Accès aux services

| Service | URL | Credentials |
|---------|-----|-------------|
| Backend API | http://localhost:8000 | - |
| Backend Docs | http://localhost:8000/docs | - |
| Frontend | http://localhost:5173 | - |
| Prometheus | http://localhost:9090 | - |
| Grafana | http://localhost:3000 | admin / admin |

## 7. Premier démarrage

1. **Configure ton `.env`** :
   ```bash
   cp backend/.env.example backend/.env
   # Édite backend/.env avec tes vraies valeurs
   ```

2. **Applique le schéma Supabase** (si tu utilises Supabase) :
   - Voir [docs/SUPABASE_SETUP.md](SUPABASE_SETUP.md)

3. **Démarre les services** :
   ```bash
   docker compose up --build
   ```

4. **Vérifie que tout fonctionne** :
   - Backend : http://localhost:8000/health
   - Frontend : http://localhost:5173
   - Grafana : http://localhost:3000

