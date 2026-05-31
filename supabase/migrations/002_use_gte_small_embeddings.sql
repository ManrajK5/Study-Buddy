drop function if exists public.match_document_chunks(vector(1536), int, uuid, uuid);
drop function if exists public.match_document_chunks(vector(384), int, uuid, uuid);

drop index if exists public.document_chunks_embedding_idx;

alter table public.document_chunks
  alter column embedding type vector(384)
  using null;

create index document_chunks_embedding_idx
  on public.document_chunks using ivfflat (embedding vector_cosine_ops) with (lists = 100);

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
