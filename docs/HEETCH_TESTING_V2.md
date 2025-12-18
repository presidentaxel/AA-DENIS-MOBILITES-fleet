# Guide de test Heetch - Version avec flux en 2 étapes

## Problèmes corrigés

1. ✅ **Playwright dans un thread séparé** - Résout l'erreur `NotImplementedError`
2. ✅ **Flux de connexion en 2 étapes** - Téléphone → SMS → Code SMS → Mot de passe

## Nouveau flux de connexion

Le flux Heetch fonctionne maintenant en **2 étapes** :

1. **Étape 1** : Envoyer le numéro de téléphone → SMS envoyé
2. **Étape 2** : Valider le code SMS + entrer le mot de passe → Connexion réussie

## Tests étape par étape

### Étape 1 : Démarrer le serveur
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### Étape 2 : Obtenir un token d'authentification
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=votre_email@example.com&password=votre_mot_de_passe"
```

Copier le `access_token` de la réponse.

### Étape 3 : Envoyer le SMS (Étape 1 de connexion)
```bash
curl -X POST "http://localhost:8000/heetch/auth/start" \
  -H "Authorization: Bearer VOTRE_ACCESS_TOKEN"
```

**Réponse attendue** :
```json
{
  "status": "success",
  "message": "SMS envoyé avec succès. Vérifiez votre téléphone pour le code.",
  "next_step": "Appelez /heetch/auth/complete avec le code SMS et le mot de passe"
}
```

**⚠️ Important** : Vérifiez votre téléphone pour le code SMS !

### Étape 4 : Finaliser la connexion (Étape 2)
```bash
curl -X POST "http://localhost:8000/heetch/auth/complete?sms_code=123456&password=votre_mot_de_passe" \
  -H "Authorization: Bearer VOTRE_ACCESS_TOKEN"
```

**Réponse attendue** :
```json
{
  "status": "success",
  "message": "Connexion réussie. Vous pouvez maintenant utiliser les endpoints de synchronisation."
}
```

### Étape 5 : Synchroniser les drivers
```bash
curl -X POST "http://localhost:8000/heetch/sync/drivers" \
  -H "Authorization: Bearer VOTRE_ACCESS_TOKEN"
```

**Réponse attendue** :
```json
{
  "status": "success",
  "message": "Drivers synchronized",
  "count_before": 0,
  "count_after": 10,
  "total_drivers_in_db": 10,
  "org_id_used": "votre_org_id"
}
```

### Étape 6 : Synchroniser les earnings
```bash
curl -X POST "http://localhost:8000/heetch/sync/earnings?from=2025-12-15&to=2025-12-21&period=weekly" \
  -H "Authorization: Bearer VOTRE_ACCESS_TOKEN"
```

### Étape 7 : Lister les données
```bash
# Drivers
curl -X GET "http://localhost:8000/heetch/drivers" \
  -H "Authorization: Bearer VOTRE_ACCESS_TOKEN"

# Earnings
curl -X GET "http://localhost:8000/heetch/earnings?from=2025-12-15&to=2025-12-21&period=weekly" \
  -H "Authorization: Bearer VOTRE_ACCESS_TOKEN"
```

## Test via Swagger

1. Ouvrir `http://localhost:8000/docs`
2. Se connecter et obtenir un token (voir étape 2)
3. Cliquer sur **"Authorize"** et coller le token
4. Tester dans l'ordre :
   - `POST /heetch/auth/start` - Envoyer le SMS
   - Attendre le SMS sur votre téléphone
   - `POST /heetch/auth/complete` - Finaliser la connexion (avec `sms_code` et `password`)
   - `POST /heetch/sync/drivers` - Synchroniser les drivers
   - `POST /heetch/sync/earnings` - Synchroniser les earnings

## Gestion de la session

- La session est valide pendant **24 heures**
- Après expiration, il faut refaire les étapes 3 et 4
- Les endpoints de synchronisation vérifient automatiquement la validité de la session

## Dépannage

### Erreur "Session expirée"
Refaire les étapes 3 et 4 (`/heetch/auth/start` puis `/heetch/auth/complete`).

### Erreur Playwright
Le problème devrait être résolu avec le thread séparé. Si vous avez encore des problèmes :
```bash
playwright install chromium
```

### Le SMS n'arrive pas
- Vérifier que le numéro dans `HEETCH_LOGIN` est correct
- Attendre quelques secondes (le SMS peut prendre du temps)
- Vérifier les logs du backend pour voir si l'envoi a réussi

### Erreur "Impossible de trouver le champ..."
Le site Heetch a peut-être changé. Vérifier les logs pour voir quels sélecteurs ont été essayés. Vous pouvez aussi prendre une capture d'écran (le code le fait automatiquement en cas d'erreur).

## Notes importantes

1. **Le client garde l'état** : Une fois connecté via `/heetch/auth/complete`, la session est valide pour tous les endpoints suivants
2. **Thread séparé** : Playwright s'exécute maintenant dans un thread séparé pour éviter les problèmes d'event loop
3. **Flux en 2 étapes** : C'est maintenant obligatoire car Heetch demande d'abord le téléphone, puis le SMS, puis le mot de passe

