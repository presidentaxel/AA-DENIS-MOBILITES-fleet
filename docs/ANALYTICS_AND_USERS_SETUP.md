# Configuration des tables Analytics et Users

Ce document explique comment installer les tables nécessaires pour les analytics et la gestion des utilisateurs.

## Fichiers SQL

Le fichier `supabase/analytics_and_users.sql` contient toutes les tables et fonctions nécessaires.

## Tables créées

### 1. `users`
Table pour la gestion des utilisateurs de la plateforme (admins, gestionnaires, etc.)

**Colonnes principales:**
- `id`: UUID unique
- `org_id`: ID de l'organisation
- `email`: Email unique de l'utilisateur
- `password_hash`: Hash du mot de passe (si authentification locale)
- `role`: Rôle de l'utilisateur ('admin', 'manager', 'user')
- `is_active`: Statut actif/inactif
- `auth_provider`: Provider d'authentification ('supabase_auth', 'local', etc.)
- `auth_provider_id`: ID dans le système d'auth externe

**Index créés:**
- `ix_users_org_id`
- `ix_users_email`
- `ix_users_role`
- `ix_users_is_active`

### 2. `daily_analytics`
Agrégation quotidienne des données pour les analytics et graphiques d'évolution temporelle.

**Colonnes principales:**
- `org_id`: ID de l'organisation
- `date`: Date de l'agrégation
- `total_drivers`: Nombre total de drivers
- `connected_drivers`: Nombre de drivers connectés (30 derniers jours)
- `working_drivers`: Nombre de drivers actifs (ce jour)
- `total_vehicles`: Nombre total de véhicules
- `active_vehicles`: Nombre de véhicules actifs (ce jour)
- `total_orders`: Nombre total de commandes
- `completed_orders`: Nombre de commandes complétées
- `cancelled_orders`: Nombre de commandes annulées
- `total_gross_earnings`: Revenus bruts (en centimes)
- `total_net_earnings`: Revenus nets (en centimes)
- `total_commission`: Commission totale (en centimes)
- `total_tips`: Pourboires totaux (en centimes)
- `total_distance_km`: Distance totale (km)
- `total_time_hours`: Temps total (heures)
- `platform_breakdown`: Détails par plateforme (JSONB)

**Index créés:**
- `ix_daily_analytics_org_id`
- `ix_daily_analytics_date`
- `ix_daily_analytics_org_date`
- `ix_daily_analytics_date_range` (pour les 365 derniers jours)
- `ix_daily_analytics_platform_breakdown` (GIN pour JSONB)

### 3. `user_analytics`
Analytics quotidiennes par utilisateur (driver) pour calculs de performance.

**Colonnes principales:**
- `org_id`: ID de l'organisation
- `driver_uuid`: UUID du driver
- `date`: Date de l'agrégation
- Métriques quotidiennes (orders, earnings, distance, etc.)
- Scores de performance (income_score, efficiency_score, etc.)

**Index créés:**
- `ix_user_analytics_org_id`
- `ix_user_analytics_driver_uuid`
- `ix_user_analytics_date`
- `ix_user_analytics_org_driver_date`

## Fonctions SQL

### `compute_daily_analytics(target_date)`
Calcule et insère/met à jour les analytics quotidiennes pour une date donnée.

**Usage:**
```sql
-- Calculer pour aujourd'hui
SELECT compute_daily_analytics();

-- Calculer pour une date spécifique
SELECT compute_daily_analytics('2025-01-15'::date);

-- Calculer pour les 30 derniers jours
SELECT compute_daily_analytics(date) 
FROM generate_series(current_date - interval '30 days', current_date, '1 day'::interval) as date;
```

### `compute_user_analytics(target_date)`
Calcule et insère/met à jour les analytics quotidiennes par utilisateur pour une date donnée.

**Usage:**
```sql
-- Calculer pour aujourd'hui
SELECT compute_user_analytics();

-- Calculer pour une date spécifique
SELECT compute_user_analytics('2025-01-15'::date);
```

## Installation

### Étape 1: Exécuter le script SQL

1. Ouvrez Supabase Dashboard
2. Allez dans SQL Editor
3. Créez une nouvelle requête
4. Copiez le contenu de `supabase/analytics_and_users.sql`
5. Exécutez le script

### Étape 2: Vérifier les tables

Vérifiez que les tables ont été créées:
```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('users', 'daily_analytics', 'user_analytics');
```

### Étape 3: Calculer les analytics historiques (optionnel)

Pour calculer les analytics pour les données existantes:

```sql
-- Calculer pour les 90 derniers jours
SELECT compute_daily_analytics(date) 
FROM generate_series(current_date - interval '90 days', current_date, '1 day'::interval) as date;

-- Calculer les analytics utilisateurs pour les 90 derniers jours
SELECT compute_user_analytics(date) 
FROM generate_series(current_date - interval '90 days', current_date, '1 day'::interval) as date;
```

## Configuration d'un job cron (recommandé)

Pour calculer automatiquement les analytics chaque jour, configurez un job cron dans Supabase:

1. Allez dans Database → Cron Jobs
2. Créez un nouveau job:
   - **Schedule**: `0 2 * * *` (2h du matin chaque jour)
   - **SQL**: `SELECT compute_daily_analytics(); SELECT compute_user_analytics();`

## RLS (Row Level Security)

Toutes les tables ont RLS activé avec les policies suivantes:

- **Service role**: Accès complet
- **Authenticated users**: Lecture uniquement pour leur `org_id`

Les policies utilisent `current_setting('app.org_id', true)` pour filtrer par organisation.

## Utilisation dans le backend

Pour utiliser ces tables dans le backend Python:

```python
from app.core.supabase_db import SupabaseDB
from app.core.supabase_client import get_supabase_client

# Obtenir les analytics quotidiennes
supabase = get_supabase_client()
db = SupabaseDB(supabase)

# Récupérer les analytics pour une période
result = supabase.table("daily_analytics") \
    .select("*") \
    .eq("org_id", "your_org_id") \
    .gte("date", "2025-01-01") \
    .lte("date", "2025-01-31") \
    .order("date") \
    .execute()

# Récupérer les analytics par utilisateur
user_analytics = supabase.table("user_analytics") \
    .select("*") \
    .eq("org_id", "your_org_id") \
    .eq("driver_uuid", "driver_id") \
    .gte("date", "2025-01-01") \
    .lte("date", "2025-01-31") \
    .order("date") \
    .execute()
```

## Notes importantes

1. **Précision financière**: Les montants sont stockés en centimes (bigint) pour éviter les problèmes de précision avec les floats.

2. **Conversion en euros**: Pour convertir en euros dans le frontend:
   ```javascript
   const earningsInEuros = analytics.total_net_earnings / 100;
   ```

3. **Performance**: Les index sont optimisés pour les requêtes temporelles sur les 365 derniers jours.

4. **RLS**: Assurez-vous que `app.org_id` est correctement configuré dans les requêtes pour que le filtrage RLS fonctionne.

