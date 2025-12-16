-- Schema additionnel pour Analytics et Gestion des Utilisateurs
-- Exécuter ce fichier dans Supabase SQL Editor pour ajouter les tables nécessaires

-- ============================================================================
-- TABLE: users
-- Gestion des utilisateurs de la plateforme (admins, gestionnaires, etc.)
-- ============================================================================
-- Note: Le script est idempotent et peut être exécuté plusieurs fois

create table if not exists users (
    id uuid primary key default gen_random_uuid(),
    org_id text not null,
    email text not null unique,
    password_hash text, -- Si authentification locale, sinon null
    first_name text,
    last_name text,
    role text not null default 'user', -- 'admin', 'manager', 'user'
    is_active boolean default true,
    created_at timestamptz default now(),
    updated_at timestamptz default now(),
    
    -- Metadata pour intégration avec auth providers
    auth_provider text, -- 'supabase_auth', 'local', etc.
    auth_provider_id text, -- ID dans le système d'auth externe
    
    constraint users_email_check check (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

create index if not exists ix_users_org_id on users(org_id);
create index if not exists ix_users_email on users(email);
create index if not exists ix_users_role on users(role);
create index if not exists ix_users_is_active on users(is_active);

-- Trigger pour mettre à jour updated_at automatiquement
create or replace function update_updated_at_column()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

drop trigger if exists update_users_updated_at on users;
create trigger update_users_updated_at before update on users
    for each row execute function update_updated_at_column();

-- ============================================================================
-- TABLE: daily_analytics
-- Agrégation quotidienne des données pour les analytics
-- Permet les graphiques d'évolution temporelle avec groupement par jour
-- ============================================================================
create table if not exists daily_analytics (
    id uuid primary key default gen_random_uuid(),
    org_id text not null,
    date date not null,
    
    -- Métriques générales
    total_drivers integer default 0,
    connected_drivers integer default 0,
    working_drivers integer default 0, -- Drivers avec au moins une commande
    
    -- Métriques véhicules
    total_vehicles integer default 0,
    active_vehicles integer default 0,
    
    -- Métriques commandes
    total_orders integer default 0,
    completed_orders integer default 0,
    cancelled_orders integer default 0,
    
    -- Métriques financières (en centimes pour éviter les problèmes de précision float)
    total_gross_earnings bigint default 0, -- En centimes
    total_net_earnings bigint default 0, -- En centimes
    total_commission bigint default 0, -- En centimes
    total_tips bigint default 0, -- En centimes
    
    -- Métriques distance et temps
    total_distance_km double precision default 0,
    total_time_hours double precision default 0, -- Temps total en heures
    
    -- Métriques par plateforme (JSONB pour flexibilité)
    platform_breakdown jsonb, -- Ex: {"bolt": {"orders": 100, "earnings": 50000}, "uber": {...}}
    
    -- Métadonnées
    computed_at timestamptz default now(),
    
    -- Contrainte d'unicité : une seule ligne par org_id et date
    constraint daily_analytics_org_date_unique unique (org_id, date)
);

create index if not exists ix_daily_analytics_org_id on daily_analytics(org_id);
create index if not exists ix_daily_analytics_date on daily_analytics(date);
create index if not exists ix_daily_analytics_org_date on daily_analytics(org_id, date);
create index if not exists ix_daily_analytics_date_desc on daily_analytics(date desc);

-- Index GIN pour les requêtes JSONB
create index if not exists ix_daily_analytics_platform_breakdown on daily_analytics using gin(platform_breakdown);

-- ============================================================================
-- TABLE: user_analytics
-- Analytics spécifiques par utilisateur (driver) pour calculs de performance
-- ============================================================================
-- Note: Le script est idempotent et peut être exécuté plusieurs fois

create table if not exists user_analytics (
    id uuid primary key default gen_random_uuid(),
    org_id text not null,
    driver_uuid text not null, -- Référence vers bolt_drivers.id ou uber_drivers.uuid
    date date not null,
    
    -- Métriques quotidiennes
    total_orders integer default 0,
    completed_orders integer default 0,
    cancelled_orders integer default 0,
    
    -- Métriques financières (en centimes)
    gross_earnings bigint default 0,
    net_earnings bigint default 0,
    commission bigint default 0,
    tips bigint default 0,
    
    -- Métriques activité
    distance_km double precision default 0,
    time_hours double precision default 0,
    trips_per_hour double precision default 0,
    hourly_earning bigint default 0, -- En centimes
    
    -- Scores de performance (calculés)
    income_score integer, -- 0-100
    efficiency_score integer, -- 0-100
    sustainability_score integer, -- 0-100
    overall_score integer, -- 0-100
    
    -- Métadonnées
    computed_at timestamptz default now(),
    
    -- Contrainte d'unicité
    constraint user_analytics_driver_date_unique unique (org_id, driver_uuid, date)
);

create index if not exists ix_user_analytics_org_id on user_analytics(org_id);
create index if not exists ix_user_analytics_driver_uuid on user_analytics(driver_uuid);
create index if not exists ix_user_analytics_date on user_analytics(date);
create index if not exists ix_user_analytics_org_driver_date on user_analytics(org_id, driver_uuid, date);

-- ============================================================================
-- FUNCTION: compute_daily_analytics
-- Fonction pour calculer et insérer les analytics quotidiennes
-- Peut être appelée via un job cron ou manuellement
-- ============================================================================
create or replace function compute_daily_analytics(target_date date default current_date)
returns void as $$
declare
    target_org_id text;
begin
    -- Pour chaque org_id dans le système
    for target_org_id in select distinct org_id from bolt_organizations
    loop
        -- Insérer ou mettre à jour les analytics pour cette date et org
        insert into daily_analytics (
            org_id,
            date,
            total_drivers,
            connected_drivers,
            working_drivers,
            total_vehicles,
            active_vehicles,
            total_orders,
            completed_orders,
            cancelled_orders,
            total_gross_earnings,
            total_net_earnings,
            total_commission,
            total_tips,
            total_distance_km,
            total_time_hours,
            platform_breakdown,
            computed_at
        )
        select
            target_org_id,
            target_date,
            -- Total drivers
            (select count(*) from bolt_drivers where org_id = target_org_id),
            -- Connected drivers (avec au moins une commande dans les 30 derniers jours)
            (select count(distinct driver_uuid) 
             from bolt_orders 
             where org_id = target_org_id 
             and order_created_timestamp >= extract(epoch from (target_date - interval '30 days'))::bigint
             and order_created_timestamp < extract(epoch from (target_date + interval '1 day'))::bigint),
            -- Working drivers (avec commande ce jour)
            (select count(distinct driver_uuid)
             from bolt_orders
             where org_id = target_org_id
             and order_created_timestamp >= extract(epoch from target_date)::bigint
             and order_created_timestamp < extract(epoch from (target_date + interval '1 day'))::bigint),
            -- Total vehicles
            (select count(*) from bolt_vehicles where org_id = target_org_id),
            -- Active vehicles (avec commande ce jour)
            (select count(distinct vehicle_license_plate)
             from bolt_orders
             where org_id = target_org_id
             and order_created_timestamp >= extract(epoch from target_date)::bigint
             and order_created_timestamp < extract(epoch from (target_date + interval '1 day'))::bigint),
            -- Orders du jour
            count(*),
            count(*) filter (where order_status ilike '%finished%' or order_status ilike '%completed%'),
            count(*) filter (where order_status ilike '%cancel%'),
            -- Earnings (convertir en centimes)
            sum(coalesce(ride_price, 0) * 100)::bigint,
            sum(coalesce(net_earnings, 0) * 100)::bigint,
            sum(coalesce(commission, 0) * 100)::bigint,
            sum(coalesce(tip, 0) * 100)::bigint,
            -- Distance et temps
            sum(coalesce(ride_distance, 0)),
            sum(case 
                when order_pickup_timestamp is not null and order_drop_off_timestamp is not null
                then (order_drop_off_timestamp - order_pickup_timestamp) / 3600.0
                else 0
            end),
            -- Platform breakdown (pour l'instant juste Bolt)
            jsonb_build_object(
                'bolt', jsonb_build_object(
                    'orders', count(*) filter (where true), -- Toutes les commandes sont Bolt pour l'instant
                    'earnings', sum(coalesce(net_earnings, 0) * 100)::bigint
                )
            ),
            now()
        from bolt_orders
        where org_id = target_org_id
        and order_created_timestamp >= extract(epoch from target_date)::bigint
        and order_created_timestamp < extract(epoch from (target_date + interval '1 day'))::bigint
        group by org_id
        on conflict (org_id, date) do update set
            total_drivers = excluded.total_drivers,
            connected_drivers = excluded.connected_drivers,
            working_drivers = excluded.working_drivers,
            total_vehicles = excluded.total_vehicles,
            active_vehicles = excluded.active_vehicles,
            total_orders = excluded.total_orders,
            completed_orders = excluded.completed_orders,
            cancelled_orders = excluded.cancelled_orders,
            total_gross_earnings = excluded.total_gross_earnings,
            total_net_earnings = excluded.total_net_earnings,
            total_commission = excluded.total_commission,
            total_tips = excluded.total_tips,
            total_distance_km = excluded.total_distance_km,
            total_time_hours = excluded.total_time_hours,
            platform_breakdown = excluded.platform_breakdown,
            computed_at = now();
    end loop;
end;
$$ language plpgsql;

-- ============================================================================
-- FUNCTION: compute_user_analytics
-- Fonction pour calculer les analytics par utilisateur pour une date donnée
-- ============================================================================
create or replace function compute_user_analytics(target_date date default current_date)
returns void as $$
declare
    target_org_id text;
begin
    for target_org_id in select distinct org_id from bolt_organizations
    loop
        insert into user_analytics (
            org_id,
            driver_uuid,
            date,
            total_orders,
            completed_orders,
            cancelled_orders,
            gross_earnings,
            net_earnings,
            commission,
            tips,
            distance_km,
            time_hours,
            trips_per_hour,
            hourly_earning,
            computed_at
        )
        select
            org_id,
            driver_uuid,
            target_date,
            count(*) as total_orders,
            count(*) filter (where order_status ilike '%finished%' or order_status ilike '%completed%') as completed_orders,
            count(*) filter (where order_status ilike '%cancel%') as cancelled_orders,
            sum(coalesce(ride_price, 0) * 100)::bigint as gross_earnings,
            sum(coalesce(net_earnings, 0) * 100)::bigint as net_earnings,
            sum(coalesce(commission, 0) * 100)::bigint as commission,
            sum(coalesce(tip, 0) * 100)::bigint as tips,
            sum(coalesce(ride_distance, 0)) as distance_km,
            sum(case 
                when order_pickup_timestamp is not null and order_drop_off_timestamp is not null
                then (order_drop_off_timestamp - order_pickup_timestamp) / 3600.0
                else 0
            end) as time_hours,
            case 
                when sum(case 
                    when order_pickup_timestamp is not null and order_drop_off_timestamp is not null
                    then (order_drop_off_timestamp - order_pickup_timestamp) / 3600.0
                    else 0
                end) > 0
                then count(*)::double precision / sum(case 
                    when order_pickup_timestamp is not null and order_drop_off_timestamp is not null
                    then (order_drop_off_timestamp - order_pickup_timestamp) / 3600.0
                    else 0
                end)
                else 0
            end as trips_per_hour,
            case 
                when sum(case 
                    when order_pickup_timestamp is not null and order_drop_off_timestamp is not null
                    then (order_drop_off_timestamp - order_pickup_timestamp) / 3600.0
                    else 0
                end) > 0
                then (sum(coalesce(net_earnings, 0) * 100)::bigint / sum(case 
                    when order_pickup_timestamp is not null and order_drop_off_timestamp is not null
                    then (order_drop_off_timestamp - order_pickup_timestamp) / 3600.0
                    else 0
                end))::bigint
                else 0
            end as hourly_earning,
            now()
        from bolt_orders
        where org_id = target_org_id
        and driver_uuid is not null
        and order_created_timestamp >= extract(epoch from target_date)::bigint
        and order_created_timestamp < extract(epoch from (target_date + interval '1 day'))::bigint
        group by org_id, driver_uuid
        on conflict (org_id, driver_uuid, date) do update set
            total_orders = excluded.total_orders,
            completed_orders = excluded.completed_orders,
            cancelled_orders = excluded.cancelled_orders,
            gross_earnings = excluded.gross_earnings,
            net_earnings = excluded.net_earnings,
            commission = excluded.commission,
            tips = excluded.tips,
            distance_km = excluded.distance_km,
            time_hours = excluded.time_hours,
            trips_per_hour = excluded.trips_per_hour,
            hourly_earning = excluded.hourly_earning,
            computed_at = now();
    end loop;
end;
$$ language plpgsql;

-- ============================================================================
-- RLS Policies
-- ============================================================================
alter table users enable row level security;
alter table daily_analytics enable row level security;
alter table user_analytics enable row level security;

-- Policy pour users : les utilisateurs peuvent voir les autres utilisateurs de leur org
drop policy if exists "Users can view users in their org" on users;
create policy "Users can view users in their org" on users
    for select using (org_id = current_setting('app.org_id', true) or current_setting('app.org_id', true) is null);

-- Policy pour daily_analytics : lecture selon org_id
drop policy if exists "Users can view analytics for their org" on daily_analytics;
create policy "Users can view analytics for their org" on daily_analytics
    for select using (org_id = current_setting('app.org_id', true) or current_setting('app.org_id', true) is null);

-- Policy pour user_analytics : lecture selon org_id
drop policy if exists "Users can view user analytics for their org" on user_analytics;
create policy "Users can view user analytics for their org" on user_analytics
    for select using (org_id = current_setting('app.org_id', true) or current_setting('app.org_id', true) is null);

-- ============================================================================
-- FUNCTION: migrate_users_from_auth
-- Migre automatiquement les utilisateurs de auth.users vers la table users
-- ============================================================================
create or replace function migrate_users_from_auth(default_org_id text default 'default_org')
returns table(
    migrated_count integer,
    skipped_count integer,
    error_count integer
) as $$
declare
    auth_user_record record;
    migrated integer := 0;
    skipped integer := 0;
    errors integer := 0;
    user_org_id text;
    user_role text;
    user_email text;
begin
    -- Parcourir tous les utilisateurs de auth.users
    for auth_user_record in 
        select 
            id,
            email,
            raw_user_meta_data,
            raw_app_meta_data,
            created_at,
            updated_at
        from auth.users
    loop
        begin
            -- Extraire l'org_id depuis les metadata ou utiliser la valeur par défaut
            user_org_id := coalesce(
                auth_user_record.raw_user_meta_data->>'org_id',
                auth_user_record.raw_app_meta_data->>'org_id',
                default_org_id
            );
            
            -- Extraire le rôle depuis les metadata ou utiliser 'user' par défaut
            user_role := coalesce(
                auth_user_record.raw_user_meta_data->>'role',
                auth_user_record.raw_app_meta_data->>'role',
                'user'
            );
            
            user_email := auth_user_record.email;
            
            -- Insérer ou mettre à jour l'utilisateur
            insert into users (
                id,
                org_id,
                email,
                first_name,
                last_name,
                role,
                is_active,
                created_at,
                updated_at,
                auth_provider,
                auth_provider_id
            )
            values (
                auth_user_record.id,
                user_org_id,
                user_email,
                coalesce(auth_user_record.raw_user_meta_data->>'first_name', auth_user_record.raw_user_meta_data->>'name'),
                auth_user_record.raw_user_meta_data->>'last_name',
                user_role,
                true, -- Actif par défaut
                auth_user_record.created_at,
                auth_user_record.updated_at,
                'supabase_auth',
                auth_user_record.id::text
            )
            on conflict (email) do update set
                -- Mettre à jour les champs si l'utilisateur existe déjà
                org_id = excluded.org_id,
                first_name = coalesce(excluded.first_name, users.first_name),
                last_name = coalesce(excluded.last_name, users.last_name),
                role = excluded.role,
                updated_at = excluded.updated_at,
                auth_provider = excluded.auth_provider,
                auth_provider_id = excluded.auth_provider_id;
            
            migrated := migrated + 1;
            
        exception when others then
            errors := errors + 1;
            -- Log l'erreur (on pourrait aussi créer une table de logs)
            raise notice 'Erreur lors de la migration de l''utilisateur %: %', auth_user_record.email, sqlerrm;
        end;
    end loop;
    
    return query select migrated, skipped, errors;
end;
$$ language plpgsql security definer;

-- ============================================================================
-- FUNCTION: sync_users_from_auth (pour synchronisation continue)
-- Synchronise les nouveaux utilisateurs de auth.users vers users
-- À appeler périodiquement (via cron ou trigger)
-- ============================================================================
create or replace function sync_users_from_auth(default_org_id text default 'default_org')
returns integer as $$
declare
    sync_count integer := 0;
    auth_user_record record;
    user_org_id text;
    user_role text;
begin
    -- Parcourir les utilisateurs de auth.users qui n'existent pas encore dans users
    for auth_user_record in 
        select 
            au.id,
            au.email,
            au.raw_user_meta_data,
            au.raw_app_meta_data,
            au.created_at,
            au.updated_at
        from auth.users au
        left join users u on u.email = au.email or u.auth_provider_id = au.id::text
        where u.id is null
    loop
        begin
            -- Extraire l'org_id depuis les metadata ou utiliser la valeur par défaut
            user_org_id := coalesce(
                auth_user_record.raw_user_meta_data->>'org_id',
                auth_user_record.raw_app_meta_data->>'org_id',
                default_org_id
            );
            
            -- Extraire le rôle depuis les metadata ou utiliser 'user' par défaut
            user_role := coalesce(
                auth_user_record.raw_user_meta_data->>'role',
                auth_user_record.raw_app_meta_data->>'role',
                'user'
            );
            
            -- Insérer l'utilisateur
            insert into users (
                id,
                org_id,
                email,
                first_name,
                last_name,
                role,
                is_active,
                created_at,
                updated_at,
                auth_provider,
                auth_provider_id
            )
            values (
                auth_user_record.id,
                user_org_id,
                auth_user_record.email,
                coalesce(
                    auth_user_record.raw_user_meta_data->>'first_name', 
                    split_part(auth_user_record.raw_user_meta_data->>'name', ' ', 1)
                ),
                coalesce(
                    auth_user_record.raw_user_meta_data->>'last_name',
                    split_part(auth_user_record.raw_user_meta_data->>'name', ' ', 2)
                ),
                user_role,
                true,
                auth_user_record.created_at,
                auth_user_record.updated_at,
                'supabase_auth',
                auth_user_record.id::text
            )
            on conflict (email) do nothing; -- Ignorer les doublons
            
            sync_count := sync_count + 1;
            
        exception when others then
            raise notice 'Erreur lors de la synchronisation de l''utilisateur %: %', auth_user_record.email, sqlerrm;
        end;
    end loop;
    
    return sync_count;
end;
$$ language plpgsql security definer;

-- ============================================================================
-- TRIGGER: auto_sync_users_on_auth_insert (optionnel)
-- Synchronise automatiquement quand un nouvel utilisateur est créé dans auth.users
-- ============================================================================
-- Note: Ce trigger nécessite que la fonction soit appelée depuis le service role
-- car auth.users est dans le schéma auth, pas public
-- Alternative: Utiliser un webhook Supabase ou appeler sync_users_from_auth() via cron

-- ============================================================================
-- COMMENTAIRES
-- ============================================================================
comment on table users is 'Utilisateurs de la plateforme (admins, gestionnaires)';
comment on table daily_analytics is 'Agrégation quotidienne des données pour analytics et graphiques d''évolution temporelle';
comment on table user_analytics is 'Analytics quotidiennes par utilisateur (driver) pour calculs de performance';

comment on function compute_daily_analytics is 'Calcule et insère/met à jour les analytics quotidiennes pour une date donnée';
comment on function compute_user_analytics is 'Calcule et insère/met à jour les analytics quotidiennes par utilisateur pour une date donnée';
comment on function migrate_users_from_auth is 'Migre tous les utilisateurs de auth.users vers la table users. Paramètre: default_org_id (défaut: ''default_org'')';
comment on function sync_users_from_auth is 'Synchronise les nouveaux utilisateurs de auth.users vers users (uniquement les nouveaux). À appeler périodiquement.';

