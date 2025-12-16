# Migration des utilisateurs de auth.users vers users

Ce document explique comment migrer automatiquement les utilisateurs de Supabase Auth (`auth.users`) vers la table `users`.

## Fonctions disponibles

### 1. `migrate_users_from_auth(default_org_id)`
Migre **tous** les utilisateurs de `auth.users` vers la table `users`.

**Paramètres:**
- `default_org_id` (optionnel, défaut: `'default_org'`): ID d'organisation à utiliser si non spécifié dans les metadata

**Retour:**
- `migrated_count`: Nombre d'utilisateurs migrés
- `skipped_count`: Nombre d'utilisateurs ignorés (actuellement toujours 0)
- `error_count`: Nombre d'erreurs rencontrées

**Usage:**
```sql
-- Migration avec org_id par défaut
SELECT * FROM migrate_users_from_auth();

-- Migration avec un org_id spécifique
SELECT * FROM migrate_users_from_auth('your_org_id');
```

### 2. `sync_users_from_auth(default_org_id)`
Synchronise uniquement les **nouveaux** utilisateurs (ceux qui n'existent pas encore dans `users`).

**Paramètres:**
- `default_org_id` (optionnel, défaut: `'default_org'`): ID d'organisation par défaut

**Retour:**
- Nombre d'utilisateurs synchronisés

**Usage:**
```sql
-- Synchronisation avec org_id par défaut
SELECT sync_users_from_auth();

-- Synchronisation avec un org_id spécifique
SELECT sync_users_from_auth('your_org_id');
```

## Processus de migration

### Étape 1: Migration initiale

Exécutez la migration complète pour migrer tous les utilisateurs existants:

```sql
SELECT * FROM migrate_users_from_auth('votre_org_id');
```

Cette commande va:
1. Parcourir tous les utilisateurs de `auth.users`
2. Extraire l'`org_id` depuis `raw_user_meta_data->>'org_id'` ou `raw_app_meta_data->>'org_id'`
3. Extraire le `role` depuis les metadata (défaut: `'user'`)
4. Extraire `first_name` et `last_name` depuis les metadata
5. Insérer dans `users` avec `ON CONFLICT (email) DO UPDATE` pour éviter les doublons

### Étape 2: Synchronisation périodique (optionnel)

Pour maintenir la synchronisation avec les nouveaux utilisateurs, vous pouvez:

#### Option A: Job Cron dans Supabase

1. Allez dans Database → Cron Jobs
2. Créez un nouveau job:
   - **Schedule**: `*/5 * * * *` (toutes les 5 minutes) ou `0 * * * *` (toutes les heures)
   - **SQL**: `SELECT sync_users_from_auth('votre_org_id');`

#### Option B: Appeler depuis le backend

Dans votre backend Python, créez un endpoint ou une tâche périodique:

```python
from app.core.supabase_client import get_supabase_client

def sync_users():
    supabase = get_supabase_client()
    result = supabase.rpc('sync_users_from_auth', {
        'default_org_id': 'votre_org_id'
    }).execute()
    print(f"Synchronisé {result.data} utilisateurs")
```

## Mapping des champs

| auth.users | users | Notes |
|------------|-------|-------|
| `id` | `id` | UUID identique |
| `email` | `email` | Email unique |
| `raw_user_meta_data->>'org_id'` | `org_id` | Ou depuis `raw_app_meta_data`, sinon `default_org_id` |
| `raw_user_meta_data->>'role'` | `role` | Défaut: `'user'` |
| `raw_user_meta_data->>'first_name'` | `first_name` | Ou extrait de `name` |
| `raw_user_meta_data->>'last_name'` | `last_name` | Ou extrait de `name` |
| `created_at` | `created_at` | Date de création |
| `updated_at` | `updated_at` | Date de mise à jour |
| - | `auth_provider` | Toujours `'supabase_auth'` |
| `id` | `auth_provider_id` | ID dans auth.users |
| - | `password_hash` | `null` (géré par Supabase Auth) |
| - | `is_active` | Toujours `true` par défaut |

## Vérification

Après la migration, vérifiez les résultats:

```sql
-- Compter les utilisateurs migrés
SELECT COUNT(*) FROM users;

-- Comparer avec auth.users
SELECT COUNT(*) FROM auth.users;

-- Voir les utilisateurs sans org_id
SELECT email, org_id FROM users WHERE org_id = 'default_org';

-- Voir les utilisateurs par rôle
SELECT role, COUNT(*) FROM users GROUP BY role;
```

## Résolution de problèmes

### Les utilisateurs n'ont pas d'org_id dans les metadata

Si vos utilisateurs n'ont pas `org_id` dans leurs metadata, ils seront créés avec `default_org_id`. Vous pouvez ensuite les mettre à jour manuellement:

```sql
-- Mettre à jour un utilisateur spécifique
UPDATE users SET org_id = 'votre_org_id' WHERE email = 'user@example.com';

-- Mettre à jour plusieurs utilisateurs
UPDATE users SET org_id = 'votre_org_id' WHERE org_id = 'default_org';
```

### Gestion des doublons

La fonction utilise `ON CONFLICT (email) DO UPDATE`, donc:
- Si un utilisateur existe déjà avec le même email, il sera mis à jour
- Si un utilisateur existe déjà avec le même `auth_provider_id`, il sera créé avec un email différent (rare)

### Erreurs de migration

Les erreurs sont loggées avec `RAISE NOTICE`. Pour voir les erreurs:

```sql
-- Les erreurs apparaîtront dans les logs Supabase
-- Vous pouvez aussi vérifier si des utilisateurs n'ont pas été migrés:

SELECT au.email, au.id
FROM auth.users au
LEFT JOIN users u ON u.email = au.email OR u.auth_provider_id = au.id::text
WHERE u.id IS NULL;
```

## Sécurité

- Les fonctions utilisent `SECURITY DEFINER` pour accéder à `auth.users`
- Seul le service role peut exécuter ces fonctions par défaut
- Les utilisateurs authentifiés normaux ne peuvent pas accéder à `auth.users`

## Mise à jour manuelle des metadata

Pour ajouter `org_id` dans les metadata des utilisateurs existants:

```sql
-- Via Supabase Dashboard ou API
-- Dans Supabase Dashboard: Authentication → Users → Edit user → Metadata

-- Ou via SQL (nécessite service role):
UPDATE auth.users 
SET raw_user_meta_data = jsonb_set(
    coalesce(raw_user_meta_data, '{}'::jsonb),
    '{org_id}',
    '"votre_org_id"'::jsonb
)
WHERE id = 'user-uuid-here';
```

