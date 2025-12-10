# Correction de la configuration Bolt

## Problème : Erreur 404 sur l'authentification

Si tu vois cette erreur :
```
Client error '404 Not Found' for url 'https://auth.bolt.com/oauth/token'
```

C'est parce que l'URL d'authentification Bolt dans ton `.env` est incorrecte.

## Solution

### 1. Vérifie ton fichier `backend/.env`

Ouvre `backend/.env` et vérifie la ligne `BOLT_AUTH_URL`. Elle doit être :

```env
BOLT_AUTH_URL=https://oidc.bolt.eu/token
```

**❌ Ne pas utiliser :**
```env
BOLT_AUTH_URL=https://auth.bolt.com/oauth/token  # ❌ INCORRECT
```

### 2. Vérifie aussi `BOLT_BASE_URL`

L'URL de base de l'API Bolt doit être :

```env
BOLT_BASE_URL=https://api.bolt.eu
```

### 3. Configuration complète recommandée

```env
# Bolt API Credentials
BOLT_CLIENT_ID=ton_client_id
BOLT_CLIENT_SECRET=ton_secret

# Bolt API URLs (IMPORTANT : utiliser les bonnes URLs)
BOLT_BASE_URL=https://api.bolt.eu
BOLT_AUTH_URL=https://oidc.bolt.eu/token

# Optionnel
BOLT_DEFAULT_FLEET_ID=ton_company_id
```

### 4. Redémarrer le backend

Après avoir modifié le `.env`, redémarre le backend :

```bash
docker compose restart backend
```

Ou si tu développes localement, redémarre simplement le serveur.

## Vérification

Pour vérifier que ça fonctionne, teste l'authentification :

```bash
curl --location --request POST 'https://oidc.bolt.eu/token' \
--header 'Content-Type: application/x-www-form-urlencoded' \
--data-urlencode 'client_id=TON_CLIENT_ID' \
--data-urlencode 'client_secret=TON_SECRET' \
--data-urlencode 'grant_type=client_credentials' \
--data-urlencode 'scope=fleet-integration:api'
```

Tu devrais recevoir un token :

```json
{
  "access_token": "YOUR_TOKEN",
  "expires_in": 600,
  "token_type": "Bearer",
  "scope": "fleet-integration:api"
}
```

## Endpoints Bolt mis à jour

Les services ont été mis à jour pour utiliser les bons endpoints Bolt :

- **Drivers** : `POST /fleetIntegration/v1/getDrivers` (au lieu de `GET /drivers`)
- **Vehicles** : `POST /fleetIntegration/v1/getVehicles` (au lieu de `GET /vehicles`)

Ces endpoints nécessitent un `company_id` dans le body de la requête. Si tu as un `company_id`, ajoute-le dans `BOLT_DEFAULT_FLEET_ID` dans ton `.env`.

## Note importante

L'API Bolt utilise des endpoints **POST** avec un **body JSON**, pas des GET simples. La structure de réponse est aussi différente :

```json
{
  "code": 0,
  "message": "string",
  "data": {
    "drivers": [...],
    "vehicles": [...]
  }
}
```

Les services ont été mis à jour pour gérer cette structure.

