# Trouver le Company ID Bolt dans l'URL du portail

## 🎯 Méthode la plus simple

Le `company_id` Bolt est visible dans l'URL du portail Bolt Fleet !

### Comment le trouver

1. Connecte-toi au **Bolt Fleet Portal** : https://fleets.bolt.eu
2. Navigue vers n'importe quelle page de settings
3. Regarde l'URL dans la barre d'adresse

**Exemple d'URL** :
```
https://fleets.bolt.eu/218016/settings/companySettings?tab=contacts
```

Le nombre **`218016`** dans l'URL est ton **`company_id`** ! ✅

### Format de l'URL

```
https://fleets.bolt.eu/[COMPANY_ID]/[page]
```

Où `[COMPANY_ID]` est le `company_id` que tu cherches.

## Configuration

Une fois que tu as trouvé le `company_id` dans l'URL :

```env
BOLT_DEFAULT_FLEET_ID=218016
```

## Vérification

Teste avec l'endpoint de sync :

```bash
POST http://localhost:8000/bolt/sync/drivers?company_id=218016
Authorization: Bearer <ton_jwt>
```

Si ça fonctionne, c'est le bon ! ✅

## Note importante

⚠️ **Ne confonds pas avec le "Registration code"** :
- Le **Registration code** (`98961628900017` dans l'exemple) est un code d'enregistrement légal
- Le **Company ID** (`218016` dans l'URL) est l'ID utilisé par l'API

Utilise toujours le nombre dans l'URL, pas le registration code.

