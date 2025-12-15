# Correction du payload Bolt API

## Problème : INVALID_REQUEST

Si tu obtiens `INVALID_REQUEST` (code 702), c'est probablement parce que le payload ne correspond pas exactement à ce que l'API Bolt attend.

## Solution : Format exact du payload

Selon la documentation Bolt, le payload doit inclure **tous ces champs** dans cet ordre :

```json
{
  "offset": 0,
  "limit": 0,
  "company_id": 218016,
  "start_ts": 0,
  "end_ts": 0,
  "portal_status": "active",
  "search": ""
}
```

### Détails des champs

- **`offset`** : Nombre de résultats à sauter (pour pagination)
- **`limit`** : Nombre maximum de résultats (0 = pas de limite, max 1000 pour drivers, 100 pour vehicles)
- **`company_id`** : ID de la compagnie (obligatoire)
- **`start_ts`** : Timestamp de début (0 = pas de filtre de date)
- **`end_ts`** : Timestamp de fin (0 = pas de filtre de date)
- **`portal_status`** : Statut dans le portail (`"active"`, `"inactive"`, etc.)
- **`search`** : Recherche textuelle (chaîne vide = pas de filtre)

## Exemple de requête complète

```bash
curl -X 'POST' \
  'https://node.bolt.eu/fleet-integration-gateway/fleetIntegration/v1/getDrivers' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer TON_TOKEN_BOLT' \
  -d '{
    "offset": 0,
    "limit": 100,
    "company_id": 218016,
    "start_ts": 0,
    "end_ts": 0,
    "portal_status": "active",
    "search": ""
  }'
```

## Vérification

Après avoir mis à jour le code, teste :

```bash
POST http://localhost:8000/bolt/sync/drivers?company_id=218016
Authorization: Bearer <ton_jwt>
```

Si ça fonctionne, tu devrais voir :
```json
{
  "status": "success",
  "message": "Drivers synchronized",
  "total_drivers_in_db": X,
  "org_id_used": "default_org"
}
```

## Notes importantes

1. **Ordre des champs** : L'ordre peut être important pour certaines APIs, même si JSON est normalement insensible à l'ordre
2. **Types de données** : 
   - `company_id`, `offset`, `limit`, `start_ts`, `end_ts` sont des **nombres** (int)
   - `portal_status` et `search` sont des **chaînes** (string)
3. **Valeurs par défaut** : 
   - `limit: 0` signifie "pas de limite" (mais l'API peut avoir un max)
   - `start_ts: 0` et `end_ts: 0` signifient "pas de filtre de date"
   - `search: ""` signifie "pas de recherche textuelle"

