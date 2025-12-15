# Configuration de Supabase comme base de données

## Problème : Les données ne sont pas sauvegardées dans Supabase

Si tes tables sont vides dans Supabase, c'est probablement parce que le backend se connecte à la base PostgreSQL locale (Docker) au lieu de Supabase.

## Solution : Configurer Supabase comme base de données

### 1. Récupérer les informations de connexion Supabase

1. Va sur https://supabase.com/dashboard
2. Sélectionne ton projet
3. Va dans **Settings** → **Database**
4. Trouve la section **Connection string** → **URI**
5. Copie l'URI (format : `postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres`)

### 2. Configurer le `.env`

Dans `backend/.env`, configure les variables pour pointer vers Supabase :

```env
# Supabase Database (remplace les valeurs par les tiennes)
DB_HOST=db.xxxxx.supabase.co
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=ton_mot_de_passe_supabase

# Supabase Auth (pour l'authentification)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=ton_anon_key
SUPABASE_SERVICE_ROLE_KEY=ton_service_role_key
```

**⚠️ Important** : 
- `DB_HOST` doit être l'hostname Supabase (ex: `db.xxxxx.supabase.co`)
- `DB_PASSWORD` est le mot de passe que tu as défini lors de la création du projet Supabase
- Tu peux trouver le mot de passe dans **Settings** → **Database** → **Database password**

### 3. Appliquer le schéma SQL

Assure-toi que le schéma est appliqué dans Supabase :

1. Va sur **SQL Editor** dans Supabase
2. Ouvre `supabase/schema.sql`
3. Copie-colle tout le contenu
4. Clique sur **Run**

Ou utilise le script :

```bash
# Depuis Windows PowerShell
python scripts\push_schema_to_supabase.py
```

### 4. Vérifier la connexion

Teste la connexion :

```bash
# Depuis le container backend
docker compose exec backend python scripts/test_supabase_connection.py
```

Ou depuis ton terminal :

```bash
cd backend
python ../scripts/test_supabase_connection.py
```

### 5. Redémarrer le backend

```bash
docker compose restart backend
```

## Vérification

### 1. Vérifier que les tables existent

Dans Supabase Dashboard → **Table Editor**, tu devrais voir :
- `bolt_drivers`
- `bolt_vehicles`
- `bolt_trips`
- `bolt_earnings`
- `uber_drivers`
- etc.

### 2. Tester l'insertion

```bash
GET http://localhost:8000/bolt/debug/stats
Authorization: Bearer <ton_jwt>
```

### 3. Synchroniser des données

Une fois que tu as ton `company_id` Bolt :

```bash
POST http://localhost:8000/bolt/sync/drivers?company_id=ton_company_id
Authorization: Bearer <ton_jwt>
```

Puis vérifie dans Supabase Dashboard → **Table Editor** → `bolt_drivers` que les données sont là.

## Problème : Conflit entre PostgreSQL local et Supabase

Si tu as les deux configurés :

- **PostgreSQL local (Docker)** : `DB_HOST=db` (nom du service Docker)
- **Supabase** : `DB_HOST=db.xxxxx.supabase.co`

Le backend utilise celui défini dans `backend/.env`. Pour utiliser Supabase, assure-toi que `DB_HOST` pointe vers Supabase, pas vers `db`.

## Trouver le company_id Bolt

Si tu n'as pas ton `company_id` Bolt :

```bash
python scripts/find_bolt_company_id.py
```

Ce script teste différents `company_id` et te dit lequel fonctionne.

## Structure attendue

Une fois configuré, quand tu synchronises :

1. Les données sont récupérées depuis l'API Bolt
2. Elles sont sauvegardées dans Supabase avec `org_id`
3. Les endpoints lisent depuis Supabase filtré par `org_id`

Vérifie que tout fonctionne avec `/bolt/debug/stats` !

