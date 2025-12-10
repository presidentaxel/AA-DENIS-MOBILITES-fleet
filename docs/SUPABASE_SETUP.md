# Configuration Supabase

## 1. Variables d'environnement Supabase

### Où trouver les clés Supabase

1. **SUPABASE_URL** et **SUPABASE_ANON_KEY**
   - Va sur https://supabase.com/dashboard
   - Sélectionne ton projet
   - Va dans **Settings** → **API**
   - Tu trouveras :
     - **Project URL** → `SUPABASE_URL`
     - **anon public** key → `SUPABASE_ANON_KEY`

2. **SUPABASE_SERVICE_ROLE_KEY**
   - Même page (Settings → API)
   - **service_role secret** key → `SUPABASE_SERVICE_ROLE_KEY`
   - ⚠️ **Important** : Cette clé a des permissions admin, ne la partage jamais publiquement !

3. **SUPABASE_JWT_SECRET** (optionnel)
   - Va dans **Settings** → **API** → **JWT Settings**
   - **JWT Secret** → `SUPABASE_JWT_SECRET`
   - ⚠️ **Note** : Cette clé est généralement utilisée pour valider les tokens JWT générés par Supabase Auth.
   - Si tu utilises l'auth Supabase directement (via le client Supabase), tu n'as pas forcément besoin de cette variable.
   - Elle est utile si tu veux valider manuellement les tokens JWT dans ton backend.

### Exemple de .env

```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_JWT_SECRET=your-jwt-secret-here  # Optionnel
```

## 2. Appliquer le schéma SQL

### Option 1 : Via le SQL Editor Supabase (Recommandé)

1. Va sur https://supabase.com/dashboard
2. Sélectionne ton projet
3. Va dans **SQL Editor** (menu de gauche)
4. Clique sur **New query**
5. Ouvre le fichier `supabase/schema.sql` dans ton éditeur
6. Copie-colle tout le contenu dans l'éditeur SQL
7. Clique sur **Run** (ou `Ctrl+Enter`)

✅ Le schéma sera appliqué immédiatement.

### Option 2 : Via psql (ligne de commande)

Si tu as `psql` installé localement :

```bash
# Depuis la racine du projet
psql "postgresql://[DB_USER]:[DB_PASSWORD]@[DB_HOST]:5432/[DB_NAME]" -f supabase/schema.sql
```

Ou utilise le script fourni :

```bash
chmod +x scripts/push_schema_psql.sh
./scripts/push_schema_psql.sh
```

### Option 3 : Via le script Python

```bash
cd backend
python ../scripts/push_schema_to_supabase.py
```

⚠️ **Note** : Le script Python affiche les instructions car le client Supabase Python ne permet pas d'exécuter du SQL arbitraire directement. Utilise plutôt l'Option 1.

## 3. Vérifier que RLS est activé

Après avoir appliqué le schéma :

1. Va dans **Table Editor** (menu de gauche)
2. Sélectionne une table (ex: `uber_drivers`)
3. Clique sur l'onglet **Policies**
4. Vérifie que **Row Level Security** est activé (toggle vert)

Si ce n'est pas le cas, active-le manuellement ou ré-exécute les commandes `ALTER TABLE ... ENABLE ROW LEVEL SECURITY;` du schéma.

## 4. Tester la connexion

```bash
cd backend
python -c "from app.core.supabase_client import get_supabase; print('✅ Connexion OK')"
```

## 5. Problèmes courants

### "relation does not exist"
- Le schéma n'a pas été appliqué. Utilise l'Option 1 ci-dessus.

### "permission denied"
- Vérifie que tu utilises `SUPABASE_SERVICE_ROLE_KEY` (pas `SUPABASE_ANON_KEY`) pour les opérations admin.

### "JWT secret not found"
- `SUPABASE_JWT_SECRET` est optionnel si tu utilises l'auth Supabase directement.
- Si tu veux la trouver : Settings → API → JWT Settings → JWT Secret

