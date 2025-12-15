# Guide complet de l'API Fleet Manager

## Vue d'ensemble

L'API Fleet Manager est une API REST sécurisée qui agrège et synchronise les données de flotte depuis les plateformes Uber (Supplier/Fleet) et Bolt Fleet Integration. Les données sont stockées dans une base de données interne (PostgreSQL/Supabase) et exposées via une API unifiée pour consommation par un frontend ou d'autres applications.

### Objectifs principaux

- Synchroniser automatiquement les données Uber et Bolt (chauffeurs, véhicules, trajets, métriques, paiements)
- Stocker les données localement avec sécurité au niveau des lignes (RLS) par organisation
- Exposer une API REST unifiée avec endpoints séparés pour Uber (`/fleet/...`) et Bolt (`/bolt/...`)
- Fournir une authentification interne via JWT pour sécuriser l'accès à l'API

## Architecture

### Composants principaux

**Backend (FastAPI)**
- Framework web FastAPI avec authentification JWT interne
- Intégrations OAuth2 avec Uber et Bolt (client credentials)
- Système de tâches planifiées (APScheduler) pour synchronisations automatiques
- Migrations de base de données via Alembic
- Instrumentation Prometheus pour métriques
- Stockage des données dans PostgreSQL/Supabase avec RLS activé

**Frontend (React + Vite + TypeScript)**
- Interface utilisateur pour visualiser les données
- Authentification via JWT
- Affichage des chauffeurs, véhicules, métriques et paiements
- Support pour les données Uber et Bolt

**Monitoring**
- Prometheus pour collecte de métriques
- Grafana pour visualisation avec dashboards provisionnés

**Base de données**
- PostgreSQL ou Supabase
- Row Level Security (RLS) activé sur toutes les tables
- Isolation des données par organisation via `org_id`

## Authentification

L'API utilise un système d'authentification à deux niveaux :

### 1. Authentification interne (Frontend vers Backend)

Les utilisateurs doivent s'authentifier pour accéder à l'API :

**Endpoint de connexion :**
```
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=email@example.com&password=mot_de_passe
```

**Réponse :**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Utilisation du token :**
Toutes les requêtes vers les endpoints protégés doivent inclure le token dans l'en-tête :
```
Authorization: Bearer <access_token>
```

**Durée de validité :** Le token JWT est valide pendant 60 minutes. Après expiration, il faut se reconnecter.

**Vérification de session :**
```
GET /auth/me
Authorization: Bearer <access_token>
```

### 2. Authentification avec Uber et Bolt (Backend vers APIs externes)

Le backend gère automatiquement l'authentification avec Uber et Bolt :
- Les credentials Uber/Bolt sont stockés uniquement côté backend (variables d'environnement)
- Le backend génère et renouvelle automatiquement les tokens d'accès
- Les tokens sont mis en cache et régénérés à l'expiration
- Les credentials ne sont jamais exposés au frontend

## Endpoints disponibles

### Authentification

- `POST /auth/login` - Connexion utilisateur (retourne un JWT)
- `GET /auth/me` - Informations sur l'utilisateur connecté

### Endpoints Uber (Fleet)

- `GET /fleet/orgs` - Liste des organisations Uber
- `GET /fleet/drivers` - Liste paginée des chauffeurs
- `GET /fleet/drivers/{driver_uuid}` - Détails d'un chauffeur
- `GET /fleet/vehicles` - Liste des véhicules
- `GET /fleet/vehicles/{vehicle_uuid}` - Détails d'un véhicule
- `GET /fleet/drivers/{driver_uuid}/metrics?from=YYYY-MM-DD&to=YYYY-MM-DD` - Métriques d'un chauffeur
- `GET /fleet/drivers/{driver_uuid}/payments?from=YYYY-MM-DD&to=YYYY-MM-DD` - Paiements d'un chauffeur
- `POST /fleet/sync/orgs` - Synchronisation manuelle des organisations
- `POST /fleet/sync/drivers` - Synchronisation manuelle des chauffeurs
- `POST /fleet/sync/vehicles` - Synchronisation manuelle des véhicules
- `POST /fleet/sync/metrics` - Synchronisation manuelle des métriques
- `POST /fleet/sync/payments` - Synchronisation manuelle des paiements

### Endpoints Bolt

- `GET /bolt/drivers` - Liste des chauffeurs Bolt
- `GET /bolt/drivers/{driver_id}` - Détails d'un chauffeur Bolt
- `GET /bolt/vehicles` - Liste des véhicules Bolt
- `GET /bolt/drivers/{driver_id}/trips?from=YYYY-MM-DD&to=YYYY-MM-DD` - Trajets d'un chauffeur
- `GET /bolt/drivers/{driver_id}/earnings?from=YYYY-MM-DD&to=YYYY-MM-DD` - Gains d'un chauffeur

### Autres endpoints

- `GET /health` - Vérification de santé de l'API
- `GET /metrics` - Métriques Prometheus
- `GET /docs` - Documentation Swagger UI
- `GET /redoc` - Documentation ReDoc
- `GET /openapi.json` - Schéma OpenAPI

## Utilisation de l'API

### Étape 1 : Authentification

Obtenez un token d'accès en vous connectant :

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=votre_mot_de_passe"
```

Conservez le `access_token` retourné.

### Étape 2 : Utiliser le token

Incluez le token dans toutes les requêtes protégées :

```bash
curl http://localhost:8000/fleet/drivers \
  -H "Authorization: Bearer VOTRE_ACCESS_TOKEN"
```

### Étape 3 : Utilisation avec Swagger UI

1. Accédez à http://localhost:8000/docs
2. Cliquez sur le bouton "Authorize" en haut à droite
3. Entrez votre `access_token` dans le champ "Value"
4. Cliquez sur "Authorize" puis "Close"
5. Tous les endpoints protégés utiliseront automatiquement ce token

### Exemples de requêtes

**Liste des chauffeurs Uber :**
```bash
curl http://localhost:8000/fleet/drivers \
  -H "Authorization: Bearer VOTRE_TOKEN"
```

**Métriques d'un chauffeur :**
```bash
curl "http://localhost:8000/fleet/drivers/{driver_uuid}/metrics?from=2024-01-01&to=2024-01-31" \
  -H "Authorization: Bearer VOTRE_TOKEN"
```

**Liste des chauffeurs Bolt :**
```bash
curl http://localhost:8000/bolt/drivers \
  -H "Authorization: Bearer VOTRE_TOKEN"
```

## Configuration

### Variables d'environnement Backend

Créez un fichier `backend/.env` à partir de `backend/.env.example` :

```env
# Environnement
APP_ENV=dev

# Base de données
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fleet_db
DB_USER=postgres
DB_PASSWORD=votre_mot_de_passe

# JWT interne
JWT_SECRET=votre_secret_jwt
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# Supabase (recommandé pour production)
SUPABASE_URL=https://votre_projet.supabase.co
SUPABASE_ANON_KEY=votre_anon_key
SUPABASE_SERVICE_ROLE_KEY=votre_service_role_key
SUPABASE_JWT_SECRET=votre_jwt_secret

# Uber API
UBER_CLIENT_ID=votre_uber_client_id
UBER_CLIENT_SECRET=votre_uber_client_secret
UBER_BASE_URL=https://api.uber.com
UBER_AUTH_URL=https://auth.uber.com/oauth/v2/token
UBER_DEFAULT_ORG_ID=votre_org_id_uber

# Bolt API
BOLT_CLIENT_ID=votre_bolt_client_id
BOLT_CLIENT_SECRET=votre_bolt_client_secret
BOLT_BASE_URL=https://node.bolt.eu/fleet-integration-gateway
BOLT_AUTH_URL=https://oidc.bolt.eu/token
BOLT_DEFAULT_FLEET_ID=votre_fleet_id_bolt
```

### Variables d'environnement Frontend

Créez un fichier `frontend/.env` à partir de `frontend/.env.example` :

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Synchronisation automatique

L'API synchronise automatiquement les données via des tâches planifiées (APScheduler) :

### Synchronisation Uber

- **Organisations** : Quotidienne
- **Chauffeurs** : Toutes les 6 heures
- **Véhicules** : Toutes les 6 heures
- **Métriques** : Toutes les 12 heures
- **Paiements** : Toutes les 30 minutes

### Synchronisation Bolt

- **Chauffeurs** : Toutes les 15 minutes
- **Véhicules** : Toutes les 15 minutes
- **Trajets** : Toutes les 6 heures
- **Gains** : Toutes les heures

### Synchronisation manuelle

Vous pouvez déclencher manuellement une synchronisation via les endpoints `/fleet/sync/...` ou `/bolt/sync/...` (si disponibles).

## Base de données et migrations

### Schéma de base de données

Le schéma SQL est défini dans `supabase/schema.sql`. Il inclut :
- Tables pour les organisations Uber
- Tables pour les chauffeurs, véhicules, métriques et paiements
- Tables pour les données Bolt (chauffeurs, véhicules, trajets, gains)
- Activation de Row Level Security (RLS) sur toutes les tables
- Politiques de sécurité par organisation

### Migrations Alembic

Les migrations sont gérées via Alembic :

```bash
cd backend
alembic upgrade head
```

Migrations disponibles :
- `0001_init.py` - Schéma initial Uber
- `0002_backfill_org_id.py` - Remplissage des org_id avec UBER_DEFAULT_ORG_ID
- `0003_bolt_tables.py` - Ajout des tables Bolt

Créer une nouvelle migration :
```bash
alembic revision --autogenerate -m "description"
```

## Démarrage et installation

### Démarrage rapide avec Docker

```bash
# Depuis la racine du projet
docker compose up --build
```

Cela démarre :
- Backend : http://localhost:8000
- Frontend : http://localhost:5173
- Prometheus : http://localhost:9090
- Grafana : http://localhost:3000
- PostgreSQL : localhost:5432

### Démarrage manuel

**Backend :**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Éditer .env avec vos valeurs
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend :**
```bash
cd frontend
npm install
cp .env.example .env
# Éditer .env avec VITE_API_BASE_URL
npm run dev
```

## Monitoring

### Prometheus

Les métriques sont exposées sur `/metrics` et collectées par Prometheus :
- Requêtes HTTP (nombre, durée, codes de statut)
- Erreurs et exceptions
- Temps de réponse des endpoints
- Utilisation des ressources

Accès : http://localhost:9090

### Grafana

Dashboards provisionnés :
- Vue d'ensemble du backend
- Métriques par endpoint
- Métriques de base de données

Accès : http://localhost:3000 (admin/admin par défaut)

## Sécurité

### Row Level Security (RLS)

Toutes les tables utilisent RLS pour isoler les données par organisation :
- Chaque table a un champ `org_id`
- Les politiques RLS limitent l'accès aux données de l'organisation de l'utilisateur
- La clé service role est utilisée uniquement côté backend

### Bonnes pratiques

- Ne jamais exposer `SUPABASE_SERVICE_ROLE_KEY` au frontend
- Utiliser HTTPS en production
- Valider et sanitizer toutes les entrées utilisateur
- Limiter les permissions des tokens JWT
- Activer MFA pour les comptes sensibles dans Supabase
- Surveiller les logs et métriques pour détecter les anomalies

## Création d'utilisateurs

### Via le Dashboard Supabase

1. Accédez à https://supabase.com/dashboard
2. Sélectionnez votre projet
3. Allez dans Authentication → Users
4. Cliquez sur Add user → Create new user
5. Remplissez l'email et le mot de passe
6. Cochez "Auto Confirm User" pour éviter la confirmation par email
7. Cliquez sur Create user

### Via l'API Supabase

```bash
curl -X POST 'https://VOTRE_PROJECT.supabase.co/auth/v1/admin/users' \
  -H "apikey: VOTRE_SERVICE_ROLE_KEY" \
  -H "Authorization: Bearer VOTRE_SERVICE_ROLE_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "mot_de_passe_securise",
    "email_confirm": true
  }'
```

## Tests

### Tests unitaires

```bash
cd backend
pytest app/tests
```

### Vérifications locales

- Healthcheck : `GET http://localhost:8000/health`
- Métriques : `GET http://localhost:8000/metrics`
- Documentation : http://localhost:8000/docs

## Déploiement

### Déploiement OVH

Voir `docs/DEPLOY-OVH.md` pour un guide complet de déploiement sur OVH.

### Étapes générales

1. Configurer les variables d'environnement
2. Builder les images Docker
3. Pousser les images vers un registre
4. Déployer sur le serveur avec Docker Compose
5. Configurer le reverse proxy (Traefik/Nginx) pour TLS
6. Vérifier que RLS est activé sur toutes les tables

## Structure des données

### Modèles principaux

**Uber :**
- `uber_organizations` - Organisations Uber
- `uber_drivers` - Chauffeurs Uber
- `uber_vehicles` - Véhicules Uber
- `driver_daily_metrics` - Métriques journalières par chauffeur
- `driver_payments` - Paiements des chauffeurs

**Bolt :**
- `bolt_drivers` - Chauffeurs Bolt
- `bolt_vehicles` - Véhicules Bolt
- `bolt_trips` - Trajets Bolt
- `bolt_earnings` - Gains Bolt

Toutes les tables incluent :
- `org_id` pour l'isolation par organisation
- `created_at` et `updated_at` pour le suivi des modifications
- Index pour optimiser les requêtes

## Support et dépannage

### Problèmes courants

**Erreur 401 Unauthorized :**
- Vérifiez que le token est valide et non expiré
- Vérifiez que le token est inclus dans l'en-tête Authorization

**Erreur de connexion à la base de données :**
- Vérifiez les variables d'environnement DB_*
- Vérifiez que la base de données est accessible
- Vérifiez les logs : `docker compose logs backend`

**Synchronisation ne fonctionne pas :**
- Vérifiez les credentials Uber/Bolt dans `.env`
- Vérifiez les logs des jobs : `docker compose logs backend`
- Déclenchez une synchronisation manuelle via les endpoints `/sync/...`

**Grafana ne peut pas se connecter à Prometheus :**
- Vérifiez que Prometheus est démarré
- Vérifiez que la datasource pointe vers `http://prometheus:9090` (pas localhost)

## Documentation supplémentaire

- `docs/QUICKSTART.md` - Guide de démarrage rapide
- `docs/AUTH_SETUP.md` - Configuration de l'authentification
- `docs/SUPABASE_SETUP.md` - Configuration Supabase
- `docs/TESTING.md` - Tests et vérifications
- `docs/BOLT_API_TESTING.md` - Guide de test de l'API Bolt
- `docs/DEPLOY-OVH.md` - Déploiement sur OVH

