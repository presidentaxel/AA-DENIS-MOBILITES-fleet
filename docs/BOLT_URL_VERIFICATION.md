# Vérification de l'URL de l'API Bolt

## Problème : Erreur DNS "[Errno -2] Name or service not known"

Cette erreur signifie que le système ne peut pas résoudre le nom de domaine `api.bolt.eu`.

## Étapes de diagnostic

### 1. Tester depuis Windows (hôte)

Ouvre PowerShell et teste :

```powershell
# Test DNS
nslookup api.bolt.eu

# Test HTTP
curl -I https://api.bolt.eu
curl -I https://oidc.bolt.eu/token
```

**Si ça fonctionne depuis Windows mais pas depuis Docker**, c'est un problème de réseau Docker.

**Si ça ne fonctionne pas depuis Windows non plus**, l'URL est peut-être incorrecte.

### 2. Vérifier l'URL de base dans la documentation Bolt

Dans la documentation Bolt que tu as (Fleet Owner Portal → API Documentation), vérifie :

1. **Quelle est l'URL de base exacte ?**
   - Est-ce vraiment `https://api.bolt.eu` ?
   - Ou peut-être `https://fleet-api.bolt.eu` ?
   - Ou une autre URL selon ta région ?

2. **Exemple d'URL complète dans la doc :**
   - Si la doc montre `https://api.bolt.eu/fleetIntegration/v1/getDrivers`, alors `https://api.bolt.eu` est correct
   - Si la doc montre une autre URL, utilise celle-là

### 3. Tester depuis Docker avec Python

```bash
# Copier le script dans le container
docker compose cp scripts/test_bolt_dns.py backend:/tmp/test_bolt_dns.py

# Exécuter le test
docker compose exec backend python /tmp/test_bolt_dns.py
```

### 4. Vérifier les variables d'environnement

```bash
docker compose exec backend env | grep BOLT
```

Tu devrais voir :
```
BOLT_BASE_URL=https://api.bolt.eu
BOLT_AUTH_URL=https://oidc.bolt.eu/token
```

## Solutions possibles

### Solution 1 : URL incorrecte

Si l'URL de base dans la documentation Bolt est différente, mets à jour `backend/.env` :

```env
BOLT_BASE_URL=https://la-vraie-url-de-la-doc
```

### Solution 2 : Problème DNS Docker

Si le DNS fonctionne depuis Windows mais pas depuis Docker :

1. **Vérifie que les DNS sont bien configurés dans docker-compose.yml** (déjà fait)

2. **Redémarre complètement Docker Compose :**
   ```bash
   docker compose down
   docker compose up -d
   ```

3. **Vérifie la configuration réseau Docker :**
   ```powershell
   docker network inspect api-uber_appnet
   ```

### Solution 3 : Utiliser l'IP directement (temporaire)

Si tu connais l'IP de l'API Bolt, tu peux temporairement utiliser l'IP au lieu du domaine :

```env
BOLT_BASE_URL=https://<IP_DE_L_API_BOLT>
```

Mais ce n'est pas recommandé pour la production.

## Vérification rapide

**Depuis ton terminal Windows, teste :**

```powershell
# 1. DNS
nslookup api.bolt.eu

# 2. HTTP
curl https://api.bolt.eu

# 3. Auth endpoint
curl https://oidc.bolt.eu/token
```

**Partage les résultats** pour qu'on puisse identifier le problème exact.

## Note importante

L'URL de l'API Bolt peut varier selon :
- La région (Europe, US, etc.)
- Le type de compte
- La version de l'API

**Vérifie toujours dans ta documentation Bolt officielle quelle est l'URL de base exacte.**

