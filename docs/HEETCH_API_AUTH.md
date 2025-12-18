# Authentification Heetch via API

D'après les informations fournies, Heetch utilise une API d'authentification :
- **Base URL** : `https://auth-gw.heetch.com`
- **Endpoint session** : `GET /session`
- **Token** : Dans le header `authorization: Token ...` ou dans les cookies `heetch_auth_token`

## Flux d'authentification

1. **Vérifier l'état de la session** : `GET /session`
   - Retourne : `{"state": "authentication_required", "phone_number": "...", "authentication_provider": "phone_number-password"}`

2. **S'authentifier** : Endpoint à déterminer (probablement `POST /authenticate` ou `/login`)
   - Payload : `{"phone_number": "...", "password": "...", "authentication_provider": "phone_number-password"}`
   - Retourne : Token dans les headers ou le body

3. **Utiliser le token** : 
   - Header : `authorization: Token <token>`
   - Ou cookies : `heetch_auth_token=<token>`

## Note importante

Le flux complet nécessite toujours :
- Téléphone → SMS → Code SMS → Mot de passe

Mais une fois connecté, le token peut être réutilisé directement.

## Prochaines étapes

Pour utiliser l'API au lieu de Playwright, il faut :
1. Trouver l'endpoint exact d'authentification (`POST /authenticate` ou similaire)
2. Comprendre comment obtenir le code SMS via l'API (ou garder Playwright juste pour cette étape)
3. Utiliser le token pour toutes les requêtes suivantes

Pour l'instant, le système utilise Playwright pour le flux complet, mais on pourrait améliorer en utilisant l'API une fois le token obtenu.

