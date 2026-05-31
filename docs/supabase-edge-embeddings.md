# Supabase Edge Embeddings

Study Buddy now uses a Supabase Edge Function for embeddings instead of an OpenAI embeddings API key.

## Why

Supabase Postgres with pgvector stores and searches vectors, but raw text still needs to be converted into vectors. The `supabase/functions/embed` function uses Supabase Edge Runtime's built-in `gte-small` model to generate those vectors.

## Files

- `supabase/functions/embed/index.ts`: Edge Function that accepts `input` or `inputs` and returns embeddings.
- `supabase/migrations/002_use_gte_small_embeddings.sql`: Updates `document_chunks.embedding` and `match_document_chunks` to `vector(384)`.
- `backend/app/rag/embeddings.py`: Calls the Edge Function from FastAPI.

## Deploy

```bash
supabase login
supabase link --project-ref your-project-ref
supabase functions deploy embed
```

Then run `002_use_gte_small_embeddings.sql` in Supabase SQL Editor if you had already run the first migration.

## Local Environment

```env
SUPABASE_EMBEDDING_FUNCTION=embed
EMBEDDING_DIMENSIONS=384
EMBEDDING_BATCH_SIZE=1
```

No `OPENAI_API_KEY` is required for embeddings anymore.

`EMBEDDING_BATCH_SIZE=1` is intentional for development. It keeps each Edge Function invocation small enough to avoid worker resource limits when processing PDFs with many chunks.
