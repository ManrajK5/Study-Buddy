create extension if not exists vector;
create extension if not exists pgcrypto;

create type document_status as enum ('uploaded', 'processing', 'processed', 'failed');
create type academic_event_type as enum ('assignment', 'quiz', 'exam', 'project', 'reading', 'lecture', 'other');
create type verification_status as enum ('pending', 'verified', 'flagged', 'rejected');

create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  full_name text,
  avatar_url text,
  timezone text default 'America/Toronto',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.courses (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  name text not null,
  code text,
  term text,
  instructor text,
  color text default '#2563eb',
  difficulty integer check (difficulty between 1 and 5),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.documents (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  course_id uuid references public.courses(id) on delete set null,
  title text not null,
  file_path text not null,
  file_name text not null,
  mime_type text not null,
  file_size bigint not null,
  status document_status not null default 'uploaded',
  extraction_error text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.document_chunks (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references public.documents(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  course_id uuid references public.courses(id) on delete set null,
  content text not null,
  page_number integer,
  chunk_index integer not null,
  token_count integer,
  metadata jsonb not null default '{}'::jsonb,
  embedding vector(384),
  created_at timestamptz not null default now()
);

create table public.academic_events (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  course_id uuid references public.courses(id) on delete cascade,
  document_id uuid references public.documents(id) on delete set null,
  title text not null,
  event_type academic_event_type not null default 'other',
  description text,
  due_at timestamptz,
  grading_weight numeric(5,2),
  estimated_hours numeric(5,2),
  confidence_score numeric(4,3) check (confidence_score >= 0 and confidence_score <= 1),
  verification_status verification_status not null default 'pending',
  source_chunk_ids uuid[] not null default '{}',
  raw_extraction jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.study_plans (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  course_id uuid references public.courses(id) on delete cascade,
  week_start date not null,
  plan jsonb not null,
  generated_reasoning text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.chat_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  course_id uuid references public.courses(id) on delete set null,
  title text not null default 'New chat',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.chat_messages (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.chat_sessions(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null check (role in ('user', 'assistant', 'system')),
  content text not null,
  citations jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create index courses_user_id_idx on public.courses(user_id);
create index documents_user_course_idx on public.documents(user_id, course_id);
create index document_chunks_document_idx on public.document_chunks(document_id, chunk_index);
create index academic_events_due_idx on public.academic_events(user_id, due_at);
create index academic_events_course_idx on public.academic_events(course_id);
create index document_chunks_embedding_idx on public.document_chunks using ivfflat (embedding vector_cosine_ops) with (lists = 100);

create or replace function public.match_document_chunks(
  query_embedding vector(384),
  match_count int,
  filter_user_id uuid,
  filter_course_id uuid default null
)
returns table (
  id uuid,
  document_id uuid,
  course_id uuid,
  content text,
  page_number integer,
  metadata jsonb,
  similarity float
)
language sql stable
as $$
  select
    dc.id,
    dc.document_id,
    dc.course_id,
    dc.content,
    dc.page_number,
    dc.metadata,
    1 - (dc.embedding <=> query_embedding) as similarity
  from public.document_chunks dc
  where dc.user_id = filter_user_id
    and (filter_course_id is null or dc.course_id = filter_course_id)
  order by dc.embedding <=> query_embedding
  limit match_count;
$$;

alter table public.profiles enable row level security;
alter table public.courses enable row level security;
alter table public.documents enable row level security;
alter table public.document_chunks enable row level security;
alter table public.academic_events enable row level security;
alter table public.study_plans enable row level security;
alter table public.chat_sessions enable row level security;
alter table public.chat_messages enable row level security;

create policy "Users manage own profile" on public.profiles for all using (auth.uid() = id);
create policy "Users manage own courses" on public.courses for all using (auth.uid() = user_id);
create policy "Users manage own documents" on public.documents for all using (auth.uid() = user_id);
create policy "Users manage own chunks" on public.document_chunks for all using (auth.uid() = user_id);
create policy "Users manage own events" on public.academic_events for all using (auth.uid() = user_id);
create policy "Users manage own plans" on public.study_plans for all using (auth.uid() = user_id);
create policy "Users manage own chat sessions" on public.chat_sessions for all using (auth.uid() = user_id);
create policy "Users manage own chat messages" on public.chat_messages for all using (auth.uid() = user_id);
