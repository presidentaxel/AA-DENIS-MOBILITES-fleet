# Guide d'installation et d'utilisation Heetch

## Installation

### 1. Installer les dépendances Python
```bash
cd backend
pip install -r requirements.txt
```

### 2. Installer les navigateurs Playwright
Playwright nécessite l'installation des navigateurs :
```bash
playwright install chromium
```

### 3. Configuration des variables d'environnement
Ajouter dans `backend/.env` :
```env
HEETCH_LOGIN=+33612345678
HEETCH_PASSWORD=votre_mot_de_passe
# Optionnel pour automatisation future :
# HEETCH_2FA_CODE=code_sms
```

**Note** : `HEETCH_LOGIN` doit être un numéro de téléphone (format international recommandé, ex: +33612345678)

### 4. Créer les tables dans la base de données
Exécuter la migration Alembic :
```bash
cd backend
alembic upgrade head
```

## Utilisation

### Synchronisation des drivers
```bash
POST /heetch/sync/drivers
```

Si le 2FA est requis, l'endpoint retournera :
```json
{
  "status": "error",
  "message": "Code SMS requis pour la connexion...",
  "requires_2fa": true
}
```

Dans ce cas, rappeler l'endpoint avec le code SMS :
```bash
POST /heetch/sync/drivers?sms_code=123456
```

### Synchronisation des earnings
```bash
POST /heetch/sync/earnings?from=2025-12-15&to=2025-12-21&period=weekly
```

Paramètres :
- `from` : Date de début (YYYY-MM-DD)
- `to` : Date de fin (YYYY-MM-DD)
- `period` : `weekly` ou `monthly` (défaut: `weekly`)
- `sms_code` : Code SMS si nécessaire

### Récupération des données

#### Lister les drivers
```bash
GET /heetch/drivers?limit=50&offset=0
```

#### Obtenir un driver spécifique
```bash
GET /heetch/drivers/{driver_email}
```

#### Obtenir les earnings d'un driver
```bash
GET /heetch/drivers/{driver_email}/earnings?from=2025-12-15&to=2025-12-21&period=weekly
```

#### Obtenir tous les earnings
```bash
GET /heetch/earnings?from=2025-12-15&to=2025-12-21&period=weekly
```

## Notes importantes

1. **Gestion de session** : Le client Heetch gère automatiquement les cookies de session. La session expire après 24h par sécurité.

2. **2FA** : Lors de la première connexion ou si la session expire, Heetch peut demander un code SMS. Il faut alors fournir le code via le paramètre `sms_code`.

3. **Performance** : Le scraping avec Playwright est plus lent qu'une API directe. Les requêtes peuvent prendre quelques secondes.

4. **Stabilité** : Le scraping peut être fragile si Heetch change leur interface. Surveiller les logs en cas d'erreur.

## Dépannage

### Erreur "Playwright not installed"
```bash
playwright install chromium
```

### Erreur "Code SMS requis"
C'est normal lors de la première connexion. Fournir le code SMS reçu par téléphone via le paramètre `sms_code`.

### Erreur de connexion
Vérifier que :
- Les credentials sont corrects dans `.env`
- Le site Heetch est accessible
- Aucun VPN ou firewall ne bloque l'accès

### Session expirée
Si la session expire, le client se reconnectera automatiquement. Si le 2FA est requis, il faudra fournir le code SMS.

