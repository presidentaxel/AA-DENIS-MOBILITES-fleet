# Configuration de l'authentification

## Comment ça fonctionne

L'application utilise **Supabase Auth** pour l'authentification. Tu dois créer un compte utilisateur dans Supabase pour te connecter.

## 1. Créer un utilisateur dans Supabase

### Option 1 : Via le Dashboard Supabase (recommandé pour le premier utilisateur)

1. Va sur https://supabase.com/dashboard
2. Sélectionne ton projet
3. Va dans **Authentication** → **Users**
4. Clique sur **Add user** → **Create new user**
5. Remplis :
   - **Email** : ton email (ex: `admin@example.com`)
   - **Password** : un mot de passe sécurisé
   - **Auto Confirm User** : ✅ coche cette case (sinon tu devras confirmer l'email)
6. Clique sur **Create user**

✅ Ton utilisateur est créé !

### Option 2 : Via l'API Supabase (pour créer plusieurs utilisateurs)

```bash
# Utilise le service_role_key pour créer un utilisateur
curl -X POST 'https://TON_PROJECT.supabase.co/auth/v1/admin/users' \
  -H "apikey: TON_SERVICE_ROLE_KEY" \
  -H "Authorization: Bearer TON_SERVICE_ROLE_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "ton_mot_de_passe",
    "email_confirm": true
  }'
```

### Option 3 : Via l'interface d'inscription (si tu l'ajoutes au frontend)

Tu peux aussi permettre aux utilisateurs de s'inscrire directement via le frontend en utilisant le client Supabase.

## 2. Se connecter via l'API

### Via curl

```bash
POST http://localhost:8000/auth/login
Content-Type: application/x-www-form-urlencoded

username=ton_email@example.com&password=ton_mot_de_passe
```

**Exemple :**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=ton_mot_de_passe"
```

**Réponse :**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Via le frontend

Le frontend a déjà une page de login (`frontend/src/pages/Login.tsx`) qui appelle `/auth/login`.

1. Ouvre http://localhost:5173
2. Tu verras la page de login
3. Entre ton email et mot de passe
4. Clique sur "Login"

## 3. Utiliser le token

Une fois connecté, tu reçois un **JWT interne** que tu dois utiliser pour toutes les requêtes protégées :

```bash
GET http://localhost:8000/fleet/drivers
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## 4. Vérifier ta session

```bash
GET http://localhost:8000/auth/me
Authorization: Bearer ton_token
```

**Réponse :**
```json
{
  "user": {
    "sub": "admin@example.com"
  }
}
```

## 5. Configuration requise

Assure-toi que ces variables sont définies dans `backend/.env` :

```env
SUPABASE_URL=https://ton_projet.supabase.co
SUPABASE_ANON_KEY=ton_anon_key
SUPABASE_SERVICE_ROLE_KEY=ton_service_role_key
```

⚠️ **Important** : Le `SUPABASE_SERVICE_ROLE_KEY` est utilisé pour créer/gérer les utilisateurs. Ne le partage jamais publiquement !

## 6. Créer plusieurs utilisateurs

### Via le Dashboard Supabase

1. **Authentication** → **Users** → **Add user**
2. Répète pour chaque utilisateur

### Via un script Python

Crée un fichier `scripts/create_user.py` :

```python
from supabase import create_client
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Créer un utilisateur
response = supabase.auth.admin.create_user({
    "email": "nouvel_utilisateur@example.com",
    "password": "mot_de_passe_securise",
    "email_confirm": True
})

print(f"Utilisateur créé : {response.user.email}")
```

Exécute :
```bash
cd backend
python ../scripts/create_user.py
```

## 7. Gérer les utilisateurs

### Voir tous les utilisateurs

1. Dashboard Supabase → **Authentication** → **Users**
2. Tu verras la liste de tous les utilisateurs

### Modifier un utilisateur

1. Dashboard Supabase → **Authentication** → **Users**
2. Clique sur l'utilisateur
3. Modifie les informations (email, mot de passe, etc.)

### Supprimer un utilisateur

1. Dashboard Supabase → **Authentication** → **Users**
2. Clique sur l'utilisateur
3. Clique sur **Delete user**

## 8. Problèmes courants

### "Invalid credentials"

**Cause** : Email ou mot de passe incorrect, ou utilisateur n'existe pas.

**Solution** :
1. Vérifie que l'utilisateur existe dans Supabase Dashboard
2. Vérifie l'email et le mot de passe
3. Si l'utilisateur n'est pas confirmé, coche "Auto Confirm User" lors de la création

### "Supabase configuration missing"

**Cause** : Les variables Supabase ne sont pas définies dans `.env`.

**Solution** :
1. Vérifie que `SUPABASE_URL` et `SUPABASE_SERVICE_ROLE_KEY` sont dans `backend/.env`
2. Redémarre le backend : `docker compose restart backend`

### "Connection refused" sur Supabase

**Cause** : URL Supabase incorrecte ou réseau bloqué.

**Solution** :
1. Vérifie que `SUPABASE_URL` est correct (format : `https://xxxxx.supabase.co`)
2. Vérifie ta connexion internet
3. Vérifie les logs : `docker compose logs backend`

## 9. Sécurité

- ✅ Les mots de passe sont hashés par Supabase (bcrypt)
- ✅ Les tokens JWT expirent après 60 minutes
- ✅ Le `SUPABASE_SERVICE_ROLE_KEY` ne doit jamais être exposé au frontend
- ✅ Utilise HTTPS en production
- ✅ Active MFA (Multi-Factor Authentication) pour les comptes sensibles dans Supabase

## 10. Test rapide

```bash
# 1. Créer un utilisateur dans Supabase Dashboard
# Email: test@example.com
# Password: test123456

# 2. Se connecter
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=test123456"

# 3. Utiliser le token reçu
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer TON_TOKEN_ICI"
```

