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
begin
  for t in select tablename from pg_tables where schemaname = 'public' loop
    execute format('create policy if not exists "%I_service_all" on %I for all using (auth.role() = ''service_role'') with check (auth.role() = ''service_role'')', t, t);
  end loop;
end$$;

-- Authenticated users: org-scoped read only (expect org_id claim in JWT)
do $$
declare
  t text;
begin
  for t in select tablename from pg_tables where schemaname = 'public' loop
    execute format(
      'create policy if not exists "%I_auth_read_org" on %I for select using (org_id = coalesce(current_setting(''request.jwt.claims'', true)::json->>''org_id'', ''''))',
      t,
      t
    );
  end loop;
end$$;

