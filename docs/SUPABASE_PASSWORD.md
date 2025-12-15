# Quel mot de passe utiliser pour Supabase ?

## ⚠️ Confusion courante

Il y a **3 types de credentials** dans Supabase, et c'est facile de les confondre :

## 1. 🔑 Mot de passe de la base de données PostgreSQL (`DB_PASSWORD`)

**C'est celui que tu utilises pour `DB_PASSWORD` dans `.env`**

### Où le trouver ?

1. Va sur https://supabase.com/dashboard
2. Sélectionne ton projet
3. Va dans **Settings** → **Database**
4. Section **Database password**
5. Clique sur **Reset database password** si tu ne le connais pas
6. **Copie le mot de passe** (tu ne pourras plus le voir après)

### Format

C'est un **mot de passe aléatoire** généré par Supabase, par exemple :
```
your-super-secret-password-12345
```

### Utilisation dans `.env`

```env
DB_HOST=db.xxxxx.supabase.co
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your-super-secret-password-12345  # ← C'est celui-ci !
```

---

## 2. 🔐 Service Role Key (`SUPABASE_SERVICE_ROLE_KEY`)

**C'est une clé API pour l'authentification Supabase (Auth)**

### Où le trouver ?

1. Supabase Dashboard → **Settings** → **API**
2. Section **Project API keys**
3. **`service_role`** key (⚠️ **secret**, ne jamais exposer au frontend)

### Format

C'est une **JWT token**, par exemple :
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh4eHh4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTYzODk4NzY1MCwiZXhwIjoxOTU0NTYzNjUwfQ.xxxxx
```

### Utilisation dans `.env`

```env
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # ← Pour l'auth
```

**⚠️ Ne pas confondre avec `DB_PASSWORD` !**

---

## 3. 🔓 Anon Key (`SUPABASE_ANON_KEY`)

**C'est une clé API publique pour le frontend (optionnel pour ce projet)**

### Où le trouver ?

1. Supabase Dashboard → **Settings** → **API**
2. Section **Project API keys**
3. **`anon`** `public` key

### Format

C'est aussi une **JWT token**, mais publique.

### Utilisation dans `.env`

```env
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # ← Pour le frontend (optionnel)
```

---

## 📋 Résumé

| Variable | Type | Usage | Où trouver |
|----------|------|-------|------------|
| `DB_PASSWORD` | Mot de passe | Connexion PostgreSQL | Settings → Database → Database password |
| `SUPABASE_SERVICE_ROLE_KEY` | JWT token | Auth backend | Settings → API → service_role key |
| `SUPABASE_ANON_KEY` | JWT token | Frontend (optionnel) | Settings → API → anon public key |

## ✅ Configuration complète pour `.env`

```env
# Connexion PostgreSQL (pour SQLAlchemy)
DB_HOST=db.xxxxx.supabase.co
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=ton_mot_de_passe_postgresql  # ← Settings → Database → Database password

# Supabase Auth (pour l'authentification)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # ← Settings → API → service_role
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # ← Settings → API → anon (optionnel)
```

## 🔍 Comment vérifier que c'est le bon mot de passe ?

1. Va sur Supabase Dashboard → **Settings** → **Database**
2. Section **Connection string** → **URI**
3. L'URI contient le mot de passe : `postgresql://postgres:[PASSWORD]@db.xxxxx.supabase.co:5432/postgres`
4. Extrais le `[PASSWORD]` de cette URI

Ou utilise le script de test :

```bash
docker compose exec backend python scripts/test_db_connection.py
```

Si ça fonctionne, c'est le bon mot de passe ! ✅

