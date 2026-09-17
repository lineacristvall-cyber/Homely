-- Homely additive preparation for bbwmwwupvqajidqznsly. No data import or deletion.
-- Run as project database administrator; changes are atomic. Re-runnable for this
-- schema version, but does not repair incompatible pre-existing table definitions.
begin;

create table if not exists public.homely_projects (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null default auth.uid() references auth.users(id),
  name text not null check (char_length(name) between 1 and 200),
  mode text not null default 'designer' check (mode in ('designer', 'diy')),
  version bigint not null default 1 check (version > 0),
  data jsonb not null default '{}'::jsonb check (jsonb_typeof(data) = 'object'),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (id, owner_id)
);
create index if not exists homely_projects_owner_idx on public.homely_projects(owner_id, updated_at desc);

create table if not exists public.homely_jobs (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null default auth.uid() references auth.users(id),
  project_id uuid not null,
  project_version bigint not null check (project_version > 0),
  kind text not null check (kind in ('research', 'visualization', 'import')),
  status text not null default 'queued' check (status in ('queued','running','completed','failed','cancelled')),
  progress integer not null default 0 check (progress between 0 and 100),
  result jsonb,
  error text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  foreign key (project_id, owner_id) references public.homely_projects(id, owner_id)
);
create index if not exists homely_jobs_owner_project_idx on public.homely_jobs(owner_id, project_id, created_at desc);

create table if not exists public.homely_assets (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null default auth.uid() references auth.users(id),
  project_id uuid not null,
  kind text not null check (kind in ('room_original','product_source','illustrative_render')),
  object_path text not null unique,
  mime_type text not null check (mime_type in ('image/jpeg','image/png','image/webp')),
  byte_size bigint not null check (byte_size between 1 and 10485760),
  consent jsonb not null default '{}'::jsonb check (jsonb_typeof(consent) = 'object'),
  lineage jsonb not null default '{}'::jsonb check (jsonb_typeof(lineage) = 'object'),
  created_at timestamptz not null default now(),
  foreign key (project_id, owner_id) references public.homely_projects(id, owner_id),
  check (object_path = owner_id::text || '/' || project_id::text || '/' || id::text)
);
create index if not exists homely_assets_owner_project_idx on public.homely_assets(owner_id, project_id);

create or replace function public.homely_project_version() returns trigger
language plpgsql set search_path = '' as $$
begin
  new.version := old.version + 1;
  new.updated_at := now();
  return new;
end;
$$;
revoke all on function public.homely_project_version() from public, anon, authenticated;
drop trigger if exists homely_project_version on public.homely_projects;
create trigger homely_project_version before update on public.homely_projects
for each row execute function public.homely_project_version();

alter table public.homely_projects enable row level security;
alter table public.homely_projects force row level security;
alter table public.homely_jobs enable row level security;
alter table public.homely_jobs force row level security;
alter table public.homely_assets enable row level security;
alter table public.homely_assets force row level security;

-- Explicit grants avoid inheriting permissive project defaults.
revoke all on public.homely_projects, public.homely_jobs, public.homely_assets from public, anon, authenticated;
grant select, insert on public.homely_projects to authenticated;
grant update (name, mode, data) on public.homely_projects to authenticated;
-- Job result/status writes belong to trusted backend workers, not browser users.
grant select on public.homely_jobs to authenticated;
grant select, insert on public.homely_assets to authenticated;
grant select, insert, update, delete on public.homely_projects, public.homely_jobs, public.homely_assets to service_role;

-- Replace only Homely-owned policies; no unrelated policies or tables are changed.
drop policy if exists homely_project_owner_select on public.homely_projects;
create policy homely_project_owner_select on public.homely_projects for select to authenticated
using ((select auth.uid()) is not null and owner_id = (select auth.uid()));
drop policy if exists homely_project_owner_insert on public.homely_projects;
create policy homely_project_owner_insert on public.homely_projects for insert to authenticated
with check ((select auth.uid()) is not null and owner_id = (select auth.uid()));
drop policy if exists homely_project_owner_update on public.homely_projects;
create policy homely_project_owner_update on public.homely_projects for update to authenticated
using ((select auth.uid()) is not null and owner_id = (select auth.uid()))
with check ((select auth.uid()) is not null and owner_id = (select auth.uid()));
drop policy if exists homely_job_owner_select on public.homely_jobs;
create policy homely_job_owner_select on public.homely_jobs for select to authenticated
using ((select auth.uid()) is not null and owner_id = (select auth.uid()));
drop policy if exists homely_asset_owner_select on public.homely_assets;
create policy homely_asset_owner_select on public.homely_assets for select to authenticated
using ((select auth.uid()) is not null and owner_id = (select auth.uid()));
drop policy if exists homely_asset_owner_insert on public.homely_assets;
create policy homely_asset_owner_insert on public.homely_assets for insert to authenticated
with check ((select auth.uid()) is not null and owner_id = (select auth.uid())
  and exists (select 1 from public.homely_projects p where p.id = project_id and p.owner_id = (select auth.uid())));

-- Restrictive fences prevent unrelated permissive policies from widening owner access.
drop policy if exists homely_projects_owner_fence on public.homely_projects;
create policy homely_projects_owner_fence on public.homely_projects as restrictive for all to authenticated
using ((select auth.uid()) is not null and owner_id = (select auth.uid()))
with check ((select auth.uid()) is not null and owner_id = (select auth.uid()));
drop policy if exists homely_jobs_owner_fence on public.homely_jobs;
create policy homely_jobs_owner_fence on public.homely_jobs as restrictive for all to authenticated
using ((select auth.uid()) is not null and owner_id = (select auth.uid()))
with check ((select auth.uid()) is not null and owner_id = (select auth.uid()));
drop policy if exists homely_assets_owner_fence on public.homely_assets;
create policy homely_assets_owner_fence on public.homely_assets as restrictive for all to authenticated
using ((select auth.uid()) is not null and owner_id = (select auth.uid()))
with check ((select auth.uid()) is not null and owner_id = (select auth.uid()));

-- A new private bucket; never changes an existing bucket to public or overwrites
-- an existing configuration. If a same-name bucket exists public, abort atomically.
insert into storage.buckets(id, name, public, file_size_limit, allowed_mime_types)
values ('homely-private-assets', 'homely-private-assets', false, 10485760,
        array['image/jpeg','image/png','image/webp'])
on conflict (id) do nothing;
do $$ begin
  if exists (select 1 from storage.buckets where id = 'homely-private-assets' and (public or file_size_limit is distinct from 10485760
      or allowed_mime_types is distinct from array['image/jpeg','image/png','image/webp'])) then
    raise exception 'Existing Homely bucket configuration differs; review its privacy, MIME and size limits before applying.';
  end if;
end $$;

-- Restrictive fence protects this bucket even if another bucket's broad permissive
-- policies exist. Non-Homely bucket access is unaffected by this fence.
drop policy if exists homely_storage_owner_fence on storage.objects;
create policy homely_storage_owner_fence on storage.objects as restrictive for all to authenticated
using (bucket_id <> 'homely-private-assets' or (
  (select auth.uid()) is not null and (storage.foldername(name))[1] = (select auth.uid())::text
  and exists (select 1 from public.homely_assets a where a.object_path = name and a.owner_id = (select auth.uid()))))
with check (bucket_id <> 'homely-private-assets' or (
  (select auth.uid()) is not null and (storage.foldername(name))[1] = (select auth.uid())::text
  and exists (select 1 from public.homely_assets a where a.object_path = name and a.owner_id = (select auth.uid())
              and a.consent @> '{"upload":true}'::jsonb)));
drop policy if exists homely_storage_anon_fence on storage.objects;
create policy homely_storage_anon_fence on storage.objects as restrictive for all to anon
using (bucket_id <> 'homely-private-assets') with check (bucket_id <> 'homely-private-assets');
drop policy if exists homely_storage_owner_read on storage.objects;
create policy homely_storage_owner_read on storage.objects for select to authenticated
using (bucket_id = 'homely-private-assets' and (storage.foldername(name))[1] = (select auth.uid())::text);
drop policy if exists homely_storage_owner_insert on storage.objects;
create policy homely_storage_owner_insert on storage.objects for insert to authenticated
with check (bucket_id = 'homely-private-assets' and (storage.foldername(name))[1] = (select auth.uid())::text);
-- Original bytes are immutable to clients: no Homely UPDATE or DELETE grant/policy.
-- Additional restrictive policy stops broad pre-existing policies granting overwrite.
drop policy if exists homely_storage_no_client_update on storage.objects;
create policy homely_storage_no_client_update on storage.objects as restrictive for update to authenticated
using (bucket_id <> 'homely-private-assets') with check (bucket_id <> 'homely-private-assets');
drop policy if exists homely_storage_no_client_delete on storage.objects;
create policy homely_storage_no_client_delete on storage.objects as restrictive for delete to authenticated
using (bucket_id <> 'homely-private-assets');

commit;
