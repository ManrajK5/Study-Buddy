alter table public.documents
  add column if not exists content_sha256 text;

create unique index if not exists documents_user_course_hash_unique
  on public.documents(user_id, coalesce(course_id, '00000000-0000-0000-0000-000000000000'::uuid), content_sha256)
  where content_sha256 is not null;

create index if not exists documents_user_course_filename_idx
  on public.documents(user_id, course_id, file_name);
