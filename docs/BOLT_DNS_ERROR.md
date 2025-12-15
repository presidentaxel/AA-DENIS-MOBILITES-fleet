# Erreur "[Errno -2] Name or service not known" - Diagnostic

## Problème

Si tu vois cette erreur lors de la synchronisation Bolt :
```json
{
  "status": "error",
  "message": "[Errno -2] Name or service not known"
}
```

Cela signifie que le système ne peut pas résoudre le nom de domaine de l'API Bolt.

## Causes possibles

### 1. URL incorrecte dans `.env` (le plus probable)

Vérifie ton fichier `backend/.env` :

**❌ INCORRECT :**
```env
BOLT_BASE_URL=https://api.bolt.com
BOLT_AUTH_URL=https://auth.bolt.com/oauth/token
```

**✅ CORRECT :**
```env
BOLT_BASE_URL=https://node.bolt.eu/fleet-integration-gateway
BOLT_AUTH_URL=https://oidc.bolt.eu/token
```

**⚠️ Important** : L'URL de base est `https://node.bolt.eu/fleet-integration-gateway`, pas `https://api.bolt.eu` !

**⚠️ Note importante :** Les URLs Bolt utilisent `.bolt.eu` (Europe), pas `.bolt.com` !

### 2. Problème de réseau depuis Docker

Si tu utilises Docker, le container peut avoir des problèmes de résolution DNS.

**Solution :**
```bash
# Vérifie que le container peut résoudre les DNS
docker compose exec backend nslookup api.bolt.eu

# Si ça échoue, vérifie la configuration réseau Docker
docker compose exec backend ping -c 3 api.bolt.eu
```

### 3. Variables d'environnement non chargées

Vérifie que les variables sont bien chargées :

```bash
# Dans le container backend
docker compose exec backend env | grep BOLT
```

Tu devrais voir :
```
BOLT_CLIENT_ID=...
BOLT_CLIENT_SECRET=...
BOLT_BASE_URL=https://api.bolt.eu
BOLT_AUTH_URL=https://oidc.bolt.eu/token
```

## Solution étape par étape

### Étape 1 : Vérifier le `.env`

Ouvre `backend/.env` et assure-toi d'avoir :

```env
# Bolt API Credentials
BOLT_CLIENT_ID=ton_client_id
BOLT_CLIENT_SECRET=ton_secret

# URLs Bolt (IMPORTANT : .bolt.eu, pas .bolt.com)
BOLT_BASE_URL=https://api.bolt.eu
BOLT_AUTH_URL=https://oidc.bolt.eu/token

# Optionnel
BOLT_DEFAULT_FLEET_ID=ton_company_id
```

### Étape 2 : Redémarrer le backend

```bash
docker compose restart backend
```

### Étape 3 : Tester la connexion depuis le container

```bash
# Test DNS
docker compose exec backend nslookup api.bolt.eu

# Test HTTP
docker compose exec backend curl -I https://api.bolt.eu
```

### Étape 4 : Tester l'authentification manuellement

```bash
# Depuis ton terminal (pas dans Docker)
curl --location --request POST 'https://oidc.bolt.eu/token' \
--header 'Content-Type: application/x-www-form-urlencoded' \
--data-urlencode 'client_id=TON_CLIENT_ID' \
--data-urlencode 'client_secret=TON_SECRET' \
--data-urlencode 'grant_type=client_credentials' \
--data-urlencode 'scope=fleet-integration:api'
```

Si ça fonctionne depuis ton terminal mais pas depuis Docker, c'est un problème de réseau Docker.

### Étape 5 : Vérifier les logs

```bash
docker compose logs backend | grep -i bolt
```

## Configuration Docker pour DNS

Si le problème persiste, ajoute des serveurs DNS dans `docker-compose.yml` :

```yaml
services:
  backend:
    # ... autres configs
    dns:
      - 8.8.8.8
      - 8.8.4.4
```

## Vérification finale

Après correction, teste la synchronisation :

```bash
POST http://localhost:8000/bolt/sync/drivers
Authorization: Bearer <ton_token>
```

Tu devrais maintenant voir un message de succès ou une erreur plus explicite qui t'indiquera exactement quel problème il reste.

## Messages d'erreur améliorés

Le code a été mis à jour pour afficher des messages d'erreur plus clairs. Si tu vois maintenant :

```
Impossible de se connecter à https://api.bolt.com/... Vérifie que BOLT_BASE_URL est correct (doit être https://api.bolt.eu)
```

Cela confirme que l'URL dans ton `.env` est incorrecte.

