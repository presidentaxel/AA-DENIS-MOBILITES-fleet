# Comment trouver le Company ID Bolt

## Problème : Liste vide après synchronisation

Si après avoir synchronisé les drivers/véhicules Bolt, tu obtiens une liste vide `[]` lors de la lecture, c'est probablement parce que le `company_id` n'est pas configuré ou est incorrect.

## Solution : Trouver ton Company ID

### Méthode 1 : Via l'API Bolt (recommandé)

1. **Teste l'endpoint `/fleetIntegration/v1/getDrivers` directement** avec différents `company_id` :

```bash
# Avec ton token Bolt (obtenu via /auth/login puis utilisé pour appeler Bolt)
curl -X POST 'https://node.bolt.eu/fleet-integration-gateway/fleetIntegration/v1/getDrivers' \
  -H 'Authorization: Bearer TON_TOKEN_BOLT' \
  -H 'Content-Type: application/json' \
  -d '{
    "company_id": 0,
    "limit": 10,
    "offset": 0
  }'
```

Si ça retourne une erreur `COMPANY_NOT_FOUND`, essaie avec d'autres valeurs (1, 2, etc.) ou contacte le support Bolt.

### Méthode 2 : Via la documentation Bolt

Dans la documentation Bolt (Fleet Owner Portal → API Documentation), regarde les exemples de requêtes. Le `company_id` peut être mentionné dans les exemples.

### Méthode 3 : Via le support Bolt

Contacte le support Bolt et demande ton `company_id` pour l'API Fleet Integration.

### Méthode 4 : Via les réponses de l'API

Certaines réponses de l'API Bolt peuvent contenir le `company_id`. Regarde dans les réponses des endpoints que tu appelles.

## Configuration

Une fois que tu as ton `company_id`, ajoute-le dans `backend/.env` :

```env
BOLT_DEFAULT_FLEET_ID=ton_company_id
```

**Important** : Le `company_id` doit être un **nombre entier** (ex: `12345`), pas une chaîne.

## Vérification

### 1. Endpoint de debug

Utilise l'endpoint de debug pour voir ce qui est dans la base :

```bash
GET http://localhost:8000/bolt/debug/stats
Authorization: Bearer <ton_jwt>
```

Cela te montrera :
- Combien de drivers/véhicules sont dans la DB
- Pour quel `org_id` ils sont sauvegardés
- Quel `org_id` ton utilisateur utilise

### 2. Synchroniser avec company_id explicite

Tu peux aussi passer le `company_id` directement dans l'endpoint de sync :

```bash
POST http://localhost:8000/bolt/sync/drivers?company_id=12345
Authorization: Bearer <ton_jwt>
```

### 3. Vérifier les logs

Les logs du backend affichent maintenant :
- Combien de drivers/véhicules ont été récupérés depuis Bolt
- Combien ont été sauvegardés
- Avec quel `org_id`

```bash
docker compose logs backend | grep -i bolt
```

## Problème : org_id ne correspond pas

Si les données sont sauvegardées mais que tu ne les vois pas, c'est probablement un problème de `org_id` :

1. **Vérifie ton `org_id` utilisateur** :
   ```bash
   GET http://localhost:8000/auth/me
   Authorization: Bearer <ton_jwt>
   ```

2. **Vérifie l'`org_id` des données** :
   ```bash
   GET http://localhost:8000/bolt/debug/stats
   Authorization: Bearer <ton_jwt>
   ```

3. **Si les `org_id` ne correspondent pas**, assure-toi que :
   - `BOLT_DEFAULT_FLEET_ID` dans `.env` correspond à ton `org_id` utilisateur
   - Ou que ton JWT contient le bon `org_id` (si tu utilises Supabase Auth avec des claims personnalisés)

## Exemple de réponse de debug

```json
{
  "user_org_id": "default_org",
  "bolt_default_fleet_id": null,
  "uber_default_org_id": null,
  "drivers": {
    "total_in_db": 5,
    "for_your_org_id": 5,
    "unique_org_ids": ["default_org"]
  },
  "vehicles": {
    "total_in_db": 3,
    "for_your_org_id": 3,
    "unique_org_ids": ["default_org"]
  }
}
```

Si `for_your_org_id` est 0 mais `total_in_db` > 0, c'est que les données sont sauvegardées avec un `org_id` différent.

