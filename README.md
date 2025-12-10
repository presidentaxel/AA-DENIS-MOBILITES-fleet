# AA DENIS MOBILITES – Fleet Manager API

## 1. Objectif du projet

Cette application fournit une **API REST sécurisée** pour exploiter les données de la flotte
AA DENIS MOBILITES à partir des APIs Uber (Supplier / Fleet).

L'objectif principal :

- récupérer et agréger les infos Uber (chauffeurs, véhicules, performance, paiements)
- les stocker dans une base interne
- exposer ces données via une API REST sécurisée pour un frontend (dashboard interne).

Le frontend n'est **pas prioritaire** : la priorité est d'avoir une **API propre et stable**,
avec une bonne séparation entre :

- **authentification front → backend** (JWT interne)
- **intégration Uber** (OAuth2 client credentials côté serveur uniquement).

Le frontend ne voit **jamais** les identifiants Uber ni les tokens Uber.

---

## 2. Architecture générale

### 2.1 Vue d’ensemble

- **backend/**
  - Framework web (FastAPI par défaut, mais remplaçable par équivalent)
  - Gestion de l’auth interne (login, JWT)
  - Client HTTP Uber + services d’intégration
  - Persistance des données (PostgreSQL / Supabase recommandé)
  - Tâches planifiées pour synchroniser les données Uber
  - API REST `/fleet/...` consommable par un frontend

- **frontend/**
  - Client web léger (React/Vue/…)
  - Authentification via JWT
  - Appel des endpoints `/fleet/...` pour afficher les données

---

## 3. Sécurité & Authentification

Il y a **deux niveaux d’auth** :

1. **Utilisateur interne (front → backend)**  
   - Auth via `/auth/login` (email + mot de passe, ou autre mécanisme interne).  
   - Le backend renvoie un **JWT**.  
   - Toutes les routes `/fleet/...` exigent un `Authorization: Bearer <token>` valide.

2. **Intégration Uber (backend → API Uber)**  
   - Le backend utilise les credentials Uber :
     - `UBER_CLIENT_ID`
     - `UBER_CLIENT_SECRET`
   - Il génère un **access_token Uber** via OAuth2 `client_credentials`
     avec les scopes appropriés (ex.: `vehicle_suppliers.organizations.read`,
     `solutions.suppliers.metrics.read`, `supplier.partner.payments`, etc.).
   - Le token est stocké en mémoire/cache avec sa durée de vie,
     et régénéré automatiquement à l’expiration.
   - Les credentials Uber ne doivent **jamais** sortir du backend.

---

## 4. Organisation du code (backend)

### 4.1 Dossier `core/`

- `config.py`  
  Centralise la configuration (lecture des variables d’environnement) :
  - paramètres DB
  - `UBER_CLIENT_ID`, `UBER_CLIENT_SECRET`
  - URL des endpoints Uber
  - secrets pour les JWT internes

- `db.py`  
  Initialise la connexion à la base de données.

- `security.py`  
  Gère l’auth interne :
  - génération/validation des tokens JWT
  - fonction utilitaire `get_current_user` utilisée par les routes protégées

- `logging.py`  
  Configuration des logs appli.

### 4.2 Dossier `auth/`

- `routes_auth.py`  
  - `/auth/login` : authentification utilisateur interne → renvoie un JWT  
  - `/auth/refresh` (optionnel)  
  - `/auth/me` (optionnel)

- `service_auth.py`  
  Regroupe la logique métier : vérifier mot de passe, créer utilisateur, etc.
  (implémentation libre selon les besoins).

### 4.3 Dossier `uber_integration/`

C’est le cœur de la connexion avec Uber.

- `uber_client.py`  
  - gère :
    - récupération du token Uber via OAuth2 client_credentials
    - appels HTTP génériques (GET/POST) avec le Bearer token Uber
  - expose des méthodes internes type `get()`, `post()` utilisées par les services.

- `uber_scopes.py`  
  Liste les scopes nécessaires, de manière centralisée.

- `services_orgs.py`  
  - Récupération des organisations Uber (orgs) pour AA DENIS MOBILITES
  - Sauvegarde/maj dans la table `uber_organizations`

- `services_drivers.py`  
  - Récupération des chauffeurs rattachés à l’org  
  - Gestion de la pagination  
  - Sauvegarde/maj dans `uber_drivers`

- `services_vehicles.py`  
  - Récupération des véhicules rattachés à l’org  
  - Sauvegarde/maj dans `uber_vehicles`

- `services_metrics.py`  
  - Appelle l’endpoint Uber "Supplier Performance Data"  
  - Agrège les données par chauffeur (trips, heures online, heures en course, earnings)  
  - Remplit la table `driver_daily_metrics` (une ligne par chauffeur et par jour).

- `services_payments.py`  
  - Appelle l’endpoint Uber "Driver Payments"  
  - Récupère les transactions (24h glissantes)  
  - Alimente la table `driver_payments`.

- `services_reports.py`  
  - Permet de demander/gérer les gros reports (CSV) fournis par Uber
    si besoin de data plus détaillée (historique long, qualité, etc.).

### 4.4 Dossier `models/`

Représentation des tables DB :

- `org.py` → `uber_organizations`  
- `driver.py` → `uber_drivers`  
- `vehicle.py` → `uber_vehicles`  
- `driver_metrics.py` → `driver_daily_metrics`  
- `driver_payments.py` → `driver_payments`

### 4.5 Dossier `schemas/`

Schémas utilisés pour exposer les objets via l’API (inputs/outputs):

- `auth.py` → `LoginRequest`, `TokenResponse`  
- `org.py` → modèle retourné par `/fleet/orgs`  
- `driver.py` → listes et détails de chauffeurs  
- `vehicle.py` → listes et détails de véhicules  
- `metrics.py` → format retourné par `/fleet/drivers/{id}/metrics`  
- `payments.py` → format retourné par `/fleet/drivers/{id}/payments`

### 4.6 Dossier `api/`

- `deps.py`  
  - fonctions communes pour les routes, par ex :
    - `get_current_user` (utilise `security.py`)
    - éventuellement `get_org_id` si l’org Uber est unique et stockée en config/DB.

- `router_fleet.py`  
  - assemble tous les endpoints `/fleet/...` sous un même router.

- `endpoints/`  
  - `fleet_orgs.py`
    - `GET /fleet/orgs` : liste des orgs connues (souvent une seule)
  - `fleet_drivers.py`
    - `GET /fleet/drivers` : liste paginée des chauffeurs
    - `GET /fleet/drivers/{driver_uuid}` : détail d’un chauffeur
  - `fleet_vehicles.py`
    - `GET /fleet/vehicles`
    - `GET /fleet/vehicles/{vehicle_uuid}`
  - `fleet_metrics.py`
    - `GET /fleet/drivers/{driver_uuid}/metrics?from=YYYY-MM-DD&to=YYYY-MM-DD`
  - `fleet_payments.py`
    - `GET /fleet/drivers/{driver_uuid}/payments?from=...&to=...`
  - `sync.py`
    - endpoints admin pour déclencher manuellement les tâches de sync
      (par exemple `POST /fleet/sync/drivers`, `POST /fleet/sync/metrics`).

Toutes ces routes sont **protégées** : elles exigent un JWT interne.

### 4.7 Dossier `jobs/`

- `scheduler.py`  
  - configure le système de tâches planifiées (cron, APScheduler, autre).

- `job_sync_orgs.py`, `job_sync_drivers.py`, etc.  
  - utilisent les services de `uber_integration/` pour :
    - sync l’org (rarement)
    - sync les chauffeurs / véhicules (quotidien ou quand besoin)
    - récupérer les paiements des dernières 24h plusieurs fois par jour
    - produire les metrics journalières.

L’idée : même si Uber est indisponible, le frontend lit la **base locale**,
pas directement Uber.

### 4.8 Dossier `webhooks/` (optionnel pour plus tard)

- `routes_webhooks.py`  
  - endpoints pour recevoir les webhooks Uber (status chauffeurs, etc.)

- `handlers.py`  
  - logique métier pour traiter ces événements.

---

## 5. Organisation du frontend (optionnel mais structuré)

Le frontend est là pour :

- se connecter (`/auth/login`)
- appeler les endpoints `/fleet/...` avec un JWT
- afficher la data.

Exemple minimal :

- `src/api/fleetApi.ts`  
  - fonctions utilitaires :
    - `login(credentials)`
    - `getDrivers(params)`
    - `getDriverMetrics(driverUuid, filters)`
    - `getDriverPayments(driverUuid, filters)`

Ces fonctions :
- lisent le JWT stocké (localStorage, cookie, etc.)
- ajoutent `Authorization: Bearer <token>`
- appellent la bonne route du backend.

---

## 6. Variables d’environnement

Un fichier `.env.example` doit lister :

```text
# Backend
APP_ENV=dev

# DB
DB_HOST=
DB_PORT=
DB_NAME=
DB_USER=
DB_PASSWORD=

# JWT
JWT_SECRET=
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# Uber API
UBER_CLIENT_ID=
UBER_CLIENT_SECRET=
UBER_BASE_URL=https://api.uber.com
UBER_AUTH_URL=https://auth.uber.com/oauth/v2/token

# Optionnel: organisation Uber forcée
UBER_DEFAULT_ORG_ID=
