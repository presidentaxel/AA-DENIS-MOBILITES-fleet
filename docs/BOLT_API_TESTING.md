# Guide de test de l'API Bolt

## Configuration

### Variables d'environnement requises

Dans `backend/.env`, ajoute :

```env
# Bolt API Credentials (obtenus depuis le Fleet Owner Portal)
BOLT_CLIENT_ID=ton_client_id
BOLT_CLIENT_SECRET=ton_client_secret

# URLs Bolt (déjà configurées par défaut)
BOLT_BASE_URL=https://api.bolt.eu
BOLT_AUTH_URL=https://oidc.bolt.eu/token

# Optionnel : Fleet ID par défaut
# Si tu as plusieurs flottes, tu peux spécifier laquelle utiliser
# Sinon, laisse vide et utilise "default_org"
BOLT_DEFAULT_FLEET_ID=
```

### Où trouver les credentials

1. Va sur le **Fleet Owner Portal** de Bolt
2. Va dans **Settings** → **Data API connections**
3. Tu verras ton **Client ID** et **Secret**
4. ⚠️ **Important** : Sauvegarde le Secret immédiatement, tu ne pourras le voir qu'une seule fois !

### BOLT_DEFAULT_FLEET_ID

**C'est optionnel** mais peut être utile si :
- Tu gères plusieurs flottes Bolt
- Tu veux filtrer les données par flotte spécifique

**Où le trouver :**
- Dans l'API Bolt, certains endpoints peuvent retourner un `fleet_id` ou `organization_id`
- Tu peux aussi le laisser vide et utiliser `"default_org"` comme identifiant par défaut
- Si tu n'as qu'une seule flotte, tu n'en as pas besoin

## Endpoints Bolt disponibles

### 1. Authentification (automatique)

Le client Bolt gère automatiquement l'authentification :
- Token obtenu via OAuth2 Client Credentials
- Scope : `fleet-integration:api`
- Token expire en **10 minutes** (auto-renouvellement)

**Test manuel :**
```bash
curl --location --request POST 'https://oidc.bolt.eu/token' \
--header 'Content-Type: application/x-www-form-urlencoded' \
--data-urlencode 'client_id=TON_CLIENT_ID' \
--data-urlencode 'client_secret=TON_SECRET' \
--data-urlencode 'grant_type=client_credentials' \
--data-urlencode 'scope=fleet-integration:api'
```

**Réponse attendue :**
```json
{
  "access_token": "YOUR_TOKEN",
  "expires_in": 600,
  "token_type": "Bearer",
  "scope": "fleet-integration:api"
}
```

### 2. Drivers (Chauffeurs)

**Endpoint API Bolt :** `GET /drivers`

**Via notre API :**
```bash
# Liste tous les chauffeurs
GET http://localhost:8000/bolt/drivers
Authorization: Bearer <ton_jwt_interne>

# Détail d'un chauffeur
GET http://localhost:8000/bolt/drivers/{driver_id}
Authorization: Bearer <ton_jwt_interne>
```

**Réponse attendue de Bolt :**
```json
{
  "data": [
    {
      "id": "driver_123",
      "first_name": "Jean",
      "last_name": "Dupont",
      "email": "jean.dupont@example.com",
      "phone": "+33612345678",
      "active": true
    }
  ]
}
```

**Test direct Bolt (avec token) :**
```bash
curl --location 'https://api.bolt.eu/drivers' \
--header 'Authorization: Bearer TON_ACCESS_TOKEN'
```

### 3. Vehicles (Véhicules)

**Endpoint API Bolt :** `GET /vehicles`

**Via notre API :**
```bash
# Liste tous les véhicules
GET http://localhost:8000/bolt/vehicles
Authorization: Bearer <ton_jwt_interne>

# Détail d'un véhicule
GET http://localhost:8000/bolt/vehicles/{vehicle_id}
Authorization: Bearer <ton_jwt_interne>
```

**Réponse attendue de Bolt :**
```json
{
  "data": [
    {
      "id": "vehicle_456",
      "license_plate": "AB-123-CD",
      "model": "Toyota Corolla",
      "make": "Toyota",
      "year": 2020
    }
  ]
}
```

**Test direct Bolt :**
```bash
curl --location 'https://api.bolt.eu/vehicles' \
--header 'Authorization: Bearer TON_ACCESS_TOKEN'
```

### 4. Trips (Trajets)

**Endpoint API Bolt :** `GET /trips`

**Paramètres optionnels :**
- `driver_id` : Filtrer par chauffeur
- `from` : Date de début (ISO 8601)
- `to` : Date de fin (ISO 8601)

**Via notre API :**
```bash
# Tous les trajets
GET http://localhost:8000/bolt/drivers/{driver_id}/trips
Authorization: Bearer <ton_jwt_interne>

# Trajets avec filtres de date
GET http://localhost:8000/bolt/drivers/{driver_id}/trips?from=2024-01-01T00:00:00Z&to=2024-01-31T23:59:59Z
Authorization: Bearer <ton_jwt_interne>
```

**Réponse attendue de Bolt :**
```json
{
  "data": [
    {
      "id": "trip_789",
      "driver_id": "driver_123",
      "start_time": "2024-01-15T10:30:00Z",
      "end_time": "2024-01-15T11:15:00Z",
      "price": 25.50,
      "distance": 12.5,
      "currency": "EUR",
      "status": "completed"
    }
  ]
}
```

**Test direct Bolt :**
```bash
# Tous les trajets
curl --location 'https://api.bolt.eu/trips' \
--header 'Authorization: Bearer TON_ACCESS_TOKEN'

# Avec filtres
curl --location 'https://api.bolt.eu/trips?driver_id=driver_123&from=2024-01-01T00:00:00Z&to=2024-01-31T23:59:59Z' \
--header 'Authorization: Bearer TON_ACCESS_TOKEN'
```

### 5. Earnings (Revenus)

**Endpoint API Bolt :** `GET /earnings`

**Paramètres optionnels :**
- `driver_id` : Filtrer par chauffeur
- `from` : Date de début (ISO 8601)
- `to` : Date de fin (ISO 8601)

**Via notre API :**
```bash
# Tous les revenus d'un chauffeur
GET http://localhost:8000/bolt/drivers/{driver_id}/earnings
Authorization: Bearer <ton_jwt_interne>

# Revenus avec filtres de date
GET http://localhost:8000/bolt/drivers/{driver_id}/earnings?from=2024-01-01T00:00:00Z&to=2024-01-31T23:59:59Z
Authorization: Bearer <ton_jwt_interne>
```

**Réponse attendue de Bolt :**
```json
{
  "data": [
    {
      "id": "earning_101",
      "driver_id": "driver_123",
      "payout_date": "2024-01-15T00:00:00Z",
      "amount": 1500.00,
      "type": "weekly_payout",
      "currency": "EUR"
    }
  ]
}
```

**Test direct Bolt :**
```bash
# Tous les revenus
curl --location 'https://api.bolt.eu/earnings' \
--header 'Authorization: Bearer TON_ACCESS_TOKEN'

# Avec filtres
curl --location 'https://api.bolt.eu/earnings?driver_id=driver_123&from=2024-01-01T00:00:00Z&to=2024-01-31T23:59:59Z' \
--header 'Authorization: Bearer TON_ACCESS_TOKEN'
```

## Tests via notre API (recommandé)

### 1. Se connecter pour obtenir un JWT interne

```bash
POST http://localhost:8000/auth/login
Content-Type: application/json

{
  "email": "demo@example.com",
  "password": "demo"
}
```

**Réponse :**
```json
{
  "access_token": "ton_jwt_interne",
  "token_type": "bearer"
}
```

### 2. Tester les endpoints Bolt via notre API

```bash
# Drivers
curl http://localhost:8000/bolt/drivers \
  -H "Authorization: Bearer ton_jwt_interne"

# Vehicles
curl http://localhost:8000/bolt/vehicles \
  -H "Authorization: Bearer ton_jwt_interne"

# Trips d'un chauffeur
curl "http://localhost:8000/bolt/drivers/driver_123/trips?from=2024-01-01&to=2024-01-31" \
  -H "Authorization: Bearer ton_jwt_interne"

# Earnings d'un chauffeur
curl "http://localhost:8000/bolt/drivers/driver_123/earnings?from=2024-01-01&to=2024-01-31" \
  -H "Authorization: Bearer ton_jwt_interne"
```

## Synchronisation automatique

Les jobs de synchronisation appellent automatiquement Bolt :

```bash
# Déclencher une sync manuelle
POST http://localhost:8000/bolt/sync/drivers
Authorization: Bearer <ton_jwt_interne>

POST http://localhost:8000/bolt/sync/vehicles
Authorization: Bearer <ton_jwt_interne>

POST http://localhost:8000/bolt/sync/trips
Authorization: Bearer <ton_jwt_interne>

POST http://localhost:8000/bolt/sync/earnings
Authorization: Bearer <ton_jwt_interne>
```

## Structure des réponses

Tous les endpoints Bolt retournent généralement :

```json
{
  "data": [...],  // Array d'objets
  "pagination": { // Si pagination disponible
    "page": 1,
    "per_page": 50,
    "total": 100
  }
}
```

## Gestion des erreurs

### Token expiré
- Le client Bolt renouvelle automatiquement le token
- Si erreur 401, vérifie tes credentials

### Rate limiting
- Bolt peut limiter le nombre de requêtes
- En cas d'erreur 429, attends quelques secondes

### Erreurs courantes

| Code | Signification | Solution |
|------|---------------|----------|
| 401 | Non autorisé | Vérifie CLIENT_ID et CLIENT_SECRET |
| 403 | Accès refusé | Vérifie les permissions de ton compte |
| 404 | Non trouvé | L'endpoint ou la ressource n'existe pas |
| 429 | Trop de requêtes | Attends avant de réessayer |
| 500 | Erreur serveur | Problème côté Bolt, réessaye plus tard |

## Notes importantes

1. **Tokens expirent en 10 minutes** : Le client gère automatiquement le renouvellement
2. **Scope requis** : `fleet-integration:api` (déjà configuré)
3. **Format des dates** : ISO 8601 (ex: `2024-01-15T10:30:00Z`)
4. **Pagination** : Certains endpoints peuvent retourner beaucoup de données, vérifie la pagination
5. **BOLT_DEFAULT_FLEET_ID** : Optionnel, utile seulement si tu gères plusieurs flottes

## Documentation officielle Bolt

Pour plus de détails, consulte la documentation officielle Bolt dans le Fleet Owner Portal :
- **Settings** → **Data API connections** → **API documentation**

