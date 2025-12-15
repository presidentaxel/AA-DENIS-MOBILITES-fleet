# Correction des scripts de diagnostic

## Problème 1 : Script non trouvé dans Docker

**Erreur** : `python: can't open file '/app/scripts/test_supabase_connection.py'`

**Solution** : Utilise le script dans `backend/scripts/` :

```bash
docker compose exec backend python scripts/test_db_connection.py
```

## Problème 2 : Quel mot de passe Supabase utiliser ?

**Réponse** : Utilise le **mot de passe de la base de données PostgreSQL**, pas les keys !

### Où le trouver ?

1. Supabase Dashboard → **Settings** → **Database**
2. Section **Database password**
3. Si tu ne le connais pas, clique sur **Reset database password**
4. Copie le mot de passe

### Configuration dans `.env`

```env
DB_HOST=db.xxxxx.supabase.co
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=ton_mot_de_passe_postgresql  # ← Celui-ci !
```

**⚠️ Ne pas utiliser** :
- ❌ `SUPABASE_SERVICE_ROLE_KEY` (c'est pour l'auth)
- ❌ `SUPABASE_ANON_KEY` (c'est pour le frontend)

Voir `docs/SUPABASE_PASSWORD.md` pour plus de détails.

## Problème 3 : Script find_bolt_company_id.py ne fonctionne pas

**Erreur** : `ModuleNotFoundError: No module named 'app'`

**Solution** : Utilise le script depuis Docker :

```bash
docker compose exec backend python scripts/find_bolt_company_id.py
```

Ou depuis Windows, change de répertoire :

```bash
cd backend
python scripts/find_bolt_company_id.py
```

## Commandes corrigées

### Tester la connexion Supabase

```bash
docker compose exec backend python scripts/test_db_connection.py
```

### Trouver le company_id Bolt

```bash
docker compose exec backend python scripts/find_bolt_company_id.py
```

### Rebuild l'image Docker (si les scripts ne sont pas copiés)

```bash
docker compose build backend
docker compose up -d backend
```

## Configuration complète pour Supabase

Dans `backend/.env` :

```env
# Connexion PostgreSQL Supabase
DB_HOST=db.xxxxx.supabase.co  # Remplace par ton host Supabase
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=ton_mot_de_passe_postgresql  # Settings → Database → Database password

# Supabase Auth
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # Optionnel

# Bolt (si tu l'as)
BOLT_DEFAULT_FLEET_ID=ton_company_id
```

## Vérification

1. **Teste la connexion** :
   ```bash
   docker compose exec backend python scripts/test_db_connection.py
   ```

2. **Vérifie dans Supabase Dashboard** :
   - Table Editor → Tu devrais voir les tables
   - SQL Editor → Tu peux exécuter des requêtes

3. **Redémarre le backend** :
   ```bash
   docker compose restart backend
   ```

