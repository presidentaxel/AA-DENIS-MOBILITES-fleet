-- Schema for AA Denis Mobilités Fleet (Supabase / Postgres)
-- RLS is enabled on every table; policies are permissive by default for authenticated users.
-- Adjust policies to enforce tenant/org segregation as soon as org_id fields are added.

create table if not exists uber_organizations (
    id text primary key,
    org_id text not null,
    name text not null
);

create table if not exists uber_drivers (
    uuid text primary key,
    org_id text not null,
    name text not null,
    email text
);

create table if not exists uber_vehicles (
    uuid text primary key,
    org_id text not null,
    plate text not null,
    model text
);

create table if not exists driver_daily_metrics (
    id text primary key,
    org_id text not null,
    driver_uuid text not null references uber_drivers(uuid),
    day date not null,
    trips double precision default 0,
    online_hours double precision default 0,
    on_trip_hours double precision default 0,
    earnings double precision default 0
);

create table if not exists driver_payments (
    id text primary key,
    org_id text not null,
    driver_uuid text not null references uber_drivers(uuid),
    occurred_at timestamptz not null,
    amount double precision not null,
    currency text default 'EUR',
    description text
);

-- Bolt tables
create table if not exists bolt_drivers (
    id text primary key,
    org_id text not null,
    first_name text not null default '',
    last_name text not null default '',
    phone text,
    email text,
    active boolean default true
);

create index if not exists ix_bolt_drivers_id on bolt_drivers(id);
create index if not exists ix_bolt_drivers_org_id on bolt_drivers(org_id);

create table if not exists bolt_vehicles (
    id text primary key,
    org_id text not null,
    provider_vehicle_id text,
    plate text not null,
    model text
);

create index if not exists ix_bolt_vehicles_id on bolt_vehicles(id);
create index if not exists ix_bolt_vehicles_org_id on bolt_vehicles(org_id);

create table if not exists bolt_trips (
    id text primary key,
    org_id text not null,
    driver_id text,
    start_time timestamptz not null,
    end_time timestamptz not null,
    price double precision default 0,
    distance double precision default 0,
    currency text default 'EUR',
    status text
);

create index if not exists ix_bolt_trips_id on bolt_trips(id);
create index if not exists ix_bolt_trips_org_id on bolt_trips(org_id);
create index if not exists ix_bolt_trips_driver_id on bolt_trips(driver_id);
create index if not exists ix_bolt_trips_start_time on bolt_trips(start_time);

create table if not exists bolt_earnings (
    id text primary key,
    org_id text not null,
    driver_id text,
    payout_date timestamptz not null,
    amount double precision default 0,
    type text,
    currency text default 'EUR'
);

create index if not exists ix_bolt_earnings_id on bolt_earnings(id);
create index if not exists ix_bolt_earnings_org_id on bolt_earnings(org_id);
create index if not exists ix_bolt_earnings_driver_id on bolt_earnings(driver_id);
create index if not exists ix_bolt_earnings_payout_date on bolt_earnings(payout_date);

-- Enable RLS on all tables
alter table uber_organizations enable row level security;
alter table uber_drivers enable row level security;
alter table uber_vehicles enable row level security;
alter table driver_daily_metrics enable row level security;
alter table driver_payments enable row level security;
alter table bolt_drivers enable row level security;
alter table bolt_vehicles enable row level security;
alter table bolt_trips enable row level security;
alter table bolt_earnings enable row level security;

-- Service role: full access
do $$
declare
  t text;
  policy_name text;
begin
  for t in select tablename from pg_tables where schemaname = 'public' loop
    policy_name := t || '_service_all';
    -- Drop policy if exists, then create
    execute format('drop policy if exists %I on %I', policy_name, t);
    execute format('create policy %I on %I for all using (auth.role() = ''service_role'') with check (auth.role() = ''service_role'')', policy_name, t);
  end loop;
end$$;

-- Authenticated users: org-scoped read only (expect org_id claim in JWT)
do $$
declare
  t text;
  policy_name text;
begin
  for t in select tablename from pg_tables where schemaname = 'public' loop
    policy_name := t || '_auth_read_org';
    -- Drop policy if exists, then create
    execute format('drop policy if exists %I on %I', policy_name, t);
    execute format(
      'create policy %I on %I for select using (org_id = coalesce(current_setting(''request.jwt.claims'', true)::json->>''org_id'', ''''))',
      policy_name,
      t
    );
  end loop;
end$$;

