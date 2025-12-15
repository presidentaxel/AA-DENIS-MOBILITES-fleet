# Créer les tables Bolt dans Supabase

## 🚨 Problème
L'erreur `Could not find the table 'public.bolt_organizations'` signifie que les tables Bolt n'ont pas encore été créées dans Supabase.

## ✅ Solution : Exécuter le schéma SQL

### Option 1 : Via le SQL Editor Supabase (RECOMMANDÉ)

1. **Ouvre le Dashboard Supabase**
   - Va sur https://supabase.com/dashboard
   - Sélectionne ton projet

2. **Ouvre le SQL Editor**
   - Menu de gauche → **SQL Editor**
   - Clique sur **New query**

3. **Exécute le schéma SQL**
   - Ouvre le fichier `supabase/schema.sql` dans ton éditeur
   - **Sélectionne TOUT le contenu** (Ctrl+A) et copie (Ctrl+C)
   - Colle dans l'éditeur SQL de Supabase (Ctrl+V)
   - Clique sur **Run** (ou appuie sur `Ctrl+Enter`)

✅ Les tables seront créées immédiatement !

### Option 2 : Via psql (si installé localement)

```bash
# Depuis la racine du projet
psql "postgresql://[DB_USER]:[DB_PASSWORD]@[DB_HOST]:5432/[DB_NAME]" -f supabase/schema.sql
```

**Pour obtenir la connection string :**
- Supabase Dashboard → Settings → Database
- Copie la connection string "Connection string" (URI mode)
- Remplace `[YOUR-PASSWORD]` par ton mot de passe de base de données

### Option 3 : Via Supabase CLI

```bash
# Si tu as installé Supabase CLI
supabase db push
```

## 📋 Tables qui seront créées

Le schéma SQL crée les tables suivantes :

- ✅ `bolt_organizations` - Organizations Bolt (company_ids)
- ✅ `bolt_drivers` - Chauffeurs Bolt
- ✅ `bolt_vehicles` - Véhicules Bolt
- ✅ `bolt_trips` - Trajets Bolt
- ✅ `bolt_earnings` - Revenus Bolt

Avec tous les index nécessaires et Row Level Security (RLS) activé.

## 🔍 Vérifier que les tables sont créées

Après avoir exécuté le schéma :

1. Va dans **Table Editor** dans Supabase
2. Tu devrais voir toutes les tables listées
3. Clique sur `bolt_organizations` pour vérifier qu'elle existe

Ou utilise le script de test :

```bash
cd backend
python -c "from app.core.supabase_db import SupabaseDB; from app.core.supabase_client import get_supabase_client; from app.models.bolt_org import BoltOrganization; db = SupabaseDB(get_supabase_client()); result = db.query(BoltOrganization).count(); print(f'✅ Table bolt_organizations existe, {result} lignes')"
```

## ⚠️ Important

- Les tables doivent être créées **avant** de lancer la synchronisation automatique
- Si tu vois encore l'erreur après avoir créé les tables, redémarre le backend :
  ```bash
  docker compose restart backend
  ```

