# Guide de test Heetch

## Prérequis

### 1. Installer les dépendances Python
```bash
cd backend
pip install -r requirements.txt
```

### 2. Installer Playwright et les navigateurs
```bash
# Installer Playwright
pip install playwright

# Installer le navigateur Chromium
playwright install chromium
```

### 3. Créer les tables dans la base de données
Exécuter le SQL dans Supabase ou votre base PostgreSQL :
```bash
# Via psql
psql -h votre-host -U votre-user -d votre-db -f supabase/heetch_tables.sql

# Ou copier-coller le contenu de supabase/heetch_tables.sql dans le SQL Editor de Supabase
```

### 4. Configurer les variables d'environnement
Dans `backend/.env`, ajouter :
```env
HEETCH_LOGIN=+33612345678  # Votre numéro de téléphone Heetch
HEETCH_PASSWORD=votre_mot_de_passe
```

## Tests étape par étape

### Étape 1 : Démarrer le serveur backend
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Le serveur devrait démarrer sur `http://localhost:8000`

### Étape 2 : Se connecter pour obtenir un token
```bash
# Remplacer les credentials par les vôtres
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=votre_email@example.com&password=votre_mot_de_passe"
```

Récupérer le `access_token` de la réponse.

### Étape 3 : Tester la synchronisation des drivers

#### Test sans 2FA (si la session existe déjà)
```bash
curl -X POST "http://localhost:8000/heetch/sync/drivers" \
  -H "Authorization: Bearer VOTRE_ACCESS_TOKEN"
```

#### Test avec 2FA (première connexion)
Si vous recevez une réponse avec `requires_2fa: true` :
```bash
curl -X POST "http://localhost:8000/heetch/sync/drivers?sms_code=123456" \
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

### Étape 4 : Tester la synchronisation des earnings
```bash
curl -X POST "http://localhost:8000/heetch/sync/earnings?from=2025-12-15&to=2025-12-21&period=weekly" \
  -H "Authorization: Bearer VOTRE_ACCESS_TOKEN"
```

Si 2FA requis :
```bash
curl -X POST "http://localhost:8000/heetch/sync/earnings?from=2025-12-15&to=2025-12-21&period=weekly&sms_code=123456" \
  -H "Authorization: Bearer VOTRE_ACCESS_TOKEN"
```

**Réponse attendue** :
```json
{
  "status": "success",
  "message": "Earnings synchronized",
  "count_before": 0,
  "count_after": 50,
  "total_earnings_in_db": 50,
  "org_id_used": "votre_org_id"
}
```

### Étape 5 : Lister les drivers
```bash
curl -X GET "http://localhost:8000/heetch/drivers?limit=50&offset=0" \
  -H "Authorization: Bearer VOTRE_ACCESS_TOKEN"
```

**Réponse attendue** :
```json
[
  {
    "id": "email@example.com",
    "org_id": "votre_org_id",
    "first_name": "Nicolas",
    "last_name": "VEDOVATO",
    "email": "email@example.com",
    "image_url": "https://...",
    "active": true
  },
  ...
]
```

### Étape 6 : Obtenir un driver spécifique
```bash
curl -X GET "http://localhost:8000/heetch/drivers/email@example.com" \
  -H "Authorization: Bearer VOTRE_ACCESS_TOKEN"
```

### Étape 7 : Obtenir les earnings d'un driver
```bash
curl -X GET "http://localhost:8000/heetch/drivers/email@example.com/earnings?from=2025-12-15&to=2025-12-21&period=weekly" \
  -H "Authorization: Bearer VOTRE_ACCESS_TOKEN"
```

### Étape 8 : Obtenir tous les earnings
```bash
curl -X GET "http://localhost:8000/heetch/earnings?from=2025-12-15&to=2025-12-21&period=weekly" \
  -H "Authorization: Bearer VOTRE_ACCESS_TOKEN"
```

## Tests via l'interface Swagger

1. Ouvrir `http://localhost:8000/docs` dans votre navigateur
2. Cliquer sur **"Authorize"** en haut à droite
3. Entrer votre `access_token` obtenu à l'étape 2
4. Tester les endpoints `/heetch/*` directement depuis l'interface

## Vérification dans la base de données

### Vérifier les drivers
```sql
SELECT * FROM heetch_drivers LIMIT 10;
```

### Vérifier les earnings
```sql
SELECT * FROM heetch_earnings ORDER BY date DESC LIMIT 10;
```

### Compter les données
```sql
SELECT 
  (SELECT COUNT(*) FROM heetch_drivers) as drivers_count,
  (SELECT COUNT(*) FROM heetch_earnings) as earnings_count;
```

## Dépannage

### Erreur "Playwright not installed"
```bash
playwright install chromium
```

### Erreur "Code SMS requis"
C'est normal lors de la première connexion. Le système détecte automatiquement le besoin de 2FA. Il faut :
1. Vérifier votre téléphone pour le code SMS
2. Rappeler l'endpoint avec le paramètre `sms_code`

### Erreur de connexion / Timeout
- Vérifier que les credentials sont corrects dans `.env`
- Vérifier que le site `driver.heetch.com` est accessible
- Vérifier les logs du backend pour plus de détails

### Erreur "Table does not exist"
Exécuter le SQL de création des tables :
```bash
psql -h votre-host -U votre-user -d votre-db -f supabase/heetch_tables.sql
```

### Vérifier les logs
Les logs du backend affichent les détails de la connexion :
```
[HEETCH] Connexion en cours pour +33612345678
[HEETCH] Numéro de téléphone rempli avec sélecteur: input[type="tel"]
[HEETCH] Mot de passe rempli avec sélecteur: input[type="password"]
[HEETCH] Connexion réussie, URL actuelle: https://driver.heetch.com/earnings
[HEETCH] 15 cookies récupérés
```

## Test complet automatisé (optionnel)

Créer un script de test `test_heetch.py` :
```python
import requests
import os
from datetime import date, timedelta

BASE_URL = "http://localhost:8000"
TOKEN = "VOTRE_ACCESS_TOKEN"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# 1. Sync drivers
print("1. Synchronisation des drivers...")
response = requests.post(f"{BASE_URL}/heetch/sync/drivers", headers=HEADERS)
print(response.json())

# 2. Lister les drivers
print("\n2. Liste des drivers...")
response = requests.get(f"{BASE_URL}/heetch/drivers", headers=HEADERS)
drivers = response.json()
print(f"Nombre de drivers: {len(drivers)}")
if drivers:
    print(f"Premier driver: {drivers[0]}")

# 3. Sync earnings
print("\n3. Synchronisation des earnings...")
today = date.today()
monday = today - timedelta(days=today.weekday())
response = requests.post(
    f"{BASE_URL}/heetch/sync/earnings",
    params={"from": monday.isoformat(), "to": today.isoformat(), "period": "weekly"},
    headers=HEADERS
)
print(response.json())

# 4. Lister les earnings
print("\n4. Liste des earnings...")
response = requests.get(
    f"{BASE_URL}/heetch/earnings",
    params={"from": monday.isoformat(), "to": today.isoformat(), "period": "weekly"},
    headers=HEADERS
)
earnings = response.json()
print(f"Nombre d'earnings: {len(earnings)}")
if earnings:
    print(f"Premier earning: {earnings[0]}")
```

Exécuter :
```bash
python test_heetch.py
```

