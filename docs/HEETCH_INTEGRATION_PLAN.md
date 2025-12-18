# Plan d'intégration Heetch

## Objectif
Intégrer Heetch dans le système existant qui fonctionne déjà avec Bolt. Heetch n'a pas d'API officielle, donc on va utiliser du scraping web pour récupérer les données.

## État actuel
- ✅ Système fonctionne avec Bolt via API officielle
- ✅ Modèles SQL pour Bolt (bolt_orders, bolt_drivers, bolt_earnings, etc.)
- ✅ Services de synchronisation Bolt
- ✅ Endpoints API pour Bolt

## Plan d'implémentation

### Phase 1: Modèles de données SQL ✅
- [x] Créer `heetch_driver` (similaire à `bolt_driver`)
  - id (email comme clé primaire)
  - org_id
  - first_name
  - last_name
  - email
  - image_url
  - active
- [x] Créer `heetch_earnings` (similaire à `bolt_earning`)
  - id (composite: driver_id + date + period)
  - org_id
  - driver_id (email)
  - date (date de la période)
  - period (weekly, monthly, etc.)
  - gross_earnings
  - net_earnings
  - cash_collected
  - card_gross_earnings
  - cash_commission_fees
  - card_commission_fees
  - cancellation_fees
  - bonuses
  - terminated_rides
  - cancelled_rides
  - currency

### Phase 2: Client de scraping Heetch ✅
- [x] Créer `heetch_client.py` avec Playwright
  - Gestion de session avec cookies
  - Connexion avec login/mdp
  - Gestion 2FA par SMS (demande code à l'utilisateur)
  - Récupération des cookies de session
  - Méthode pour récupérer les earnings via `/api/earnings`
- [x] Ajouter Playwright dans requirements.txt

### Phase 3: Services de synchronisation ✅
- [x] Créer `services_drivers.py` pour synchroniser les drivers depuis les données earnings
- [x] Créer `services_earnings.py` pour synchroniser les earnings
- [x] Gérer la pagination et les différentes périodes (weekly, monthly)

### Phase 4: Endpoints API ✅
- [x] Créer endpoints pour Heetch (similaires à Bolt)
  - `/heetch/sync/drivers` - Synchroniser les drivers
  - `/heetch/sync/earnings` - Synchroniser les earnings
  - `/heetch/drivers` - Lister les drivers
  - `/heetch/earnings` - Récupérer les earnings
- [x] Ajouter router pour Heetch

### Phase 5: Configuration ✅
- [x] Ajouter variables d'environnement pour Heetch
  - HEETCH_LOGIN (numéro de téléphone, format international recommandé)
  - HEETCH_PASSWORD
  - HEETCH_2FA_CODE (optionnel, pour automatisation future)

### Phase 6: Migration Alembic ✅
- [x] Créer migration pour créer les tables heetch_driver et heetch_earnings

## Détails techniques

### Authentification Heetch
1. Connexion sur https://driver.heetch.com/login
2. Entrer numéro de téléphone et mot de passe
3. Si 2FA demandé, attendre le code SMS et le fournir
4. Récupérer les cookies de session (notamment `heetch_auth_token` et `heetch_driver_session`)
5. Utiliser ces cookies pour les requêtes API suivantes

### Endpoint Earnings
- URL: `https://driver.heetch.com/api/earnings?date=YYYY-MM-DD&period=weekly`
- Méthode: GET
- Headers: Cookies de session
- Réponse: JSON avec summary et liste de drivers avec leurs earnings

### Mapping des données
Les données Heetch sont différentes de Bolt:
- Heetch fournit des earnings par période (weekly/monthly) avec un résumé global
- Bolt fournit des orders individuels avec détails
- On va mapper les earnings Heetch vers notre modèle SQL standardisé

## Notes importantes
- ⚠️ Le scraping peut être fragile si Heetch change leur interface
- ⚠️ La gestion de session doit être robuste (expiration, refresh)
- ⚠️ Le 2FA nécessite une intervention manuelle pour l'instant
- ⚠️ Les cookies de session peuvent expirer, il faut prévoir un refresh automatique

## Prochaines étapes
1. ✅ Créer les modèles SQL (heetch_driver, heetch_earnings)
2. ✅ Créer le client Heetch avec Playwright
3. ✅ Créer les services de synchronisation
4. ✅ Créer les endpoints API
5. ✅ Créer la migration Alembic
6. ⏳ Tester la connexion et récupération des données
7. ⏳ Ajouter gestion automatique du refresh de session
8. ⏳ Ajouter support pour d'autres endpoints Heetch si nécessaire
9. ⏳ Intégrer dans le frontend (si nécessaire)

## Notes importantes pour l'utilisation

### Installation de Playwright
Après avoir installé les dépendances Python, il faut installer les navigateurs Playwright :
```bash
playwright install chromium
```

### Variables d'environnement
Ajouter dans `.env` :
```
HEETCH_LOGIN=+33612345678
HEETCH_PASSWORD=votre_mot_de_passe
HEETCH_2FA_CODE=  # Optionnel, pour automatisation future
```

**Note** : `HEETCH_LOGIN` doit être un numéro de téléphone (format international recommandé, ex: +33612345678)

### Gestion du 2FA
Lors de la première connexion ou si la session expire, Heetch peut demander un code SMS.
Dans ce cas :
1. L'endpoint retournera `requires_2fa: true`
2. Il faut appeler à nouveau l'endpoint avec le paramètre `sms_code` contenant le code reçu

### Endpoints disponibles
- `POST /heetch/sync/drivers` - Synchroniser les drivers
- `POST /heetch/sync/earnings` - Synchroniser les earnings
- `GET /heetch/drivers` - Lister les drivers
- `GET /heetch/drivers/{driver_id}` - Obtenir un driver
- `GET /heetch/drivers/{driver_id}/earnings` - Obtenir les earnings d'un driver
- `GET /heetch/earnings` - Obtenir tous les earnings

