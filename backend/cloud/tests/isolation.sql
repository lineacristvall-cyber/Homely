-- Execute AFTER migration as database administrator in SQL Editor or psql.
-- Real database isolation tests; all fixtures are transaction-local and rolled back.
-- NOT executed by the Python unit tests. Abort-on-error in SQL Editor; with psql:
-- psql "$HOMELY_TEST_DATABASE_URL" -v ON_ERROR_STOP=1 -f backend/cloud/tests/isolation.sql
begin;
insert into auth.users(id, aud, role, email) values
('aaaaaaaa-1111-4111-8111-111111111111', 'authenticated', 'authenticated', 'homely-rls-a@example.invalid'),
('bbbbbbbb-2222-4222-8222-222222222222', 'authenticated', 'authenticated', 'homely-rls-b@example.invalid');
insert into public.homely_projects(id, owner_id, name) values
('cccccccc-3333-4333-8333-333333333333','aaaaaaaa-1111-4111-8111-111111111111','Isolation A'),
('dddddddd-4444-4444-8444-444444444444','bbbbbbbb-2222-4222-8222-222222222222','Isolation B');
insert into public.homely_jobs(owner_id, project_id, project_version, kind) values
('aaaaaaaa-1111-4111-8111-111111111111','cccccccc-3333-4333-8333-333333333333',1,'research'),
('bbbbbbbb-2222-4222-8222-222222222222','dddddddd-4444-4444-8444-444444444444',1,'research');

set local role authenticated;
select set_config('request.jwt.claims', '{"sub":"aaaaaaaa-1111-4111-8111-111111111111","role":"authenticated"}', true);
do $$ declare n integer; begin
  select count(*) into n from public.homely_projects where id in ('cccccccc-3333-4333-8333-333333333333','dddddddd-4444-4444-8444-444444444444');
  if n <> 1 then raise exception 'FAIL: project SELECT isolation'; end if;
  select count(*) into n from public.homely_jobs where project_id in ('cccccccc-3333-4333-8333-333333333333','dddddddd-4444-4444-8444-444444444444');
  if n <> 1 then raise exception 'FAIL: job SELECT isolation'; end if;
  update public.homely_projects set name = 'forbidden' where id = 'dddddddd-4444-4444-8444-444444444444';
  get diagnostics n = row_count;
  if n <> 0 then raise exception 'FAIL: cross-owner UPDATE'; end if;
  update public.homely_projects set name = 'Allowed' where id = 'cccccccc-3333-4333-8333-333333333333' and version = 1;
  get diagnostics n = row_count;
  if n <> 1 then raise exception 'FAIL: own UPDATE'; end if;
  select version into n from public.homely_projects where id = 'cccccccc-3333-4333-8333-333333333333';
  if n <> 2 then raise exception 'FAIL: version increment'; end if;
  begin
    insert into public.homely_projects(owner_id,name) values ('bbbbbbbb-2222-4222-8222-222222222222','forbidden');
    raise exception 'FAIL: foreign owner INSERT permitted';
  exception when insufficient_privilege then null; end;
  begin
    update public.homely_jobs set status = 'completed';
    raise exception 'FAIL: browser can forge job completion';
  exception when insufficient_privilege then null; end;
  begin
    delete from public.homely_projects where id = 'cccccccc-3333-4333-8333-333333333333';
    raise exception 'FAIL: client can delete project';
  exception when insufficient_privilege then null; end;
end $$;

insert into public.homely_assets(id,owner_id,project_id,kind,object_path,mime_type,byte_size,consent) values
('eeeeeeee-5555-4555-8555-555555555555','aaaaaaaa-1111-4111-8111-111111111111','cccccccc-3333-4333-8333-333333333333','room_original',
'aaaaaaaa-1111-4111-8111-111111111111/cccccccc-3333-4333-8333-333333333333/eeeeeeee-5555-4555-8555-555555555555','image/png',100,'{"upload":true}');
-- Storage metadata rows only, no actual file is uploaded; transaction rolls back.
insert into storage.objects(bucket_id,name) values ('homely-private-assets',
'aaaaaaaa-1111-4111-8111-111111111111/cccccccc-3333-4333-8333-333333333333/eeeeeeee-5555-4555-8555-555555555555');
select set_config('request.jwt.claims', '{"sub":"bbbbbbbb-2222-4222-8222-222222222222","role":"authenticated"}', true);
do $$ declare n integer; begin
  select count(*) into n from public.homely_assets where id = 'eeeeeeee-5555-4555-8555-555555555555';
  if n <> 0 then raise exception 'FAIL: cross-owner asset metadata read'; end if;
  select count(*) into n from storage.objects where bucket_id = 'homely-private-assets' and name like 'aaaaaaaa-1111-4111-8111-111111111111/%';
  if n <> 0 then raise exception 'FAIL: cross-owner storage read'; end if;
  begin
    insert into storage.objects(bucket_id,name) values ('homely-private-assets','aaaaaaaa-1111-4111-8111-111111111111/forbidden');
    raise exception 'FAIL: cross-owner storage INSERT';
  exception when insufficient_privilege then null; end;
end $$;
reset role;
set local role anon;
select set_config('request.jwt.claims', '{}', true);
do $$ begin
  begin
    perform 1 from public.homely_projects;
    raise exception 'FAIL: anonymous project read permitted';
  exception when insufficient_privilege then null; end;
end $$;
reset role;
rollback;
