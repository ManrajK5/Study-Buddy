# Study Buddy Development Roadmap

## Phase 1: Foundation

1. Create backend and frontend project structure.
2. Configure FastAPI, Pydantic settings, CORS, logging, and health checks.
3. Add Supabase environment configuration.
4. Create initial PostgreSQL and pgvector schema.
5. Add typed API schemas for courses, documents, deadlines, chat, and analytics.

## Phase 2: PDF Upload And Storage

1. Build authenticated upload endpoint.
2. Validate PDF MIME type, extension, and size.
3. Store files in Supabase Storage.
4. Persist `documents` metadata.
5. Add extraction status tracking.

## Phase 3: RAG Pipeline

1. Extract PDF text with PyPDFLoader and pdfplumber fallback.
2. Chunk text with page and document metadata.
3. Generate embeddings through the Supabase `embed` Edge Function using `gte-small`.
4. Store chunks in Supabase `document_chunks`.
5. Implement vector search RPC using pgvector.
6. Build grounded chat endpoint with source citations.

## Phase 4: LangGraph Workflow

1. Implement PDF extraction agent.
2. Implement deadline parsing agent.
3. Implement validation agent with confidence scoring.
4. Implement retry behavior for low-confidence extractions.
5. Implement study planner agent.
6. Add workflow tracing and structured logs.

## Phase 5: React Application

1. Initialize React, Tailwind CSS, and routing.
2. Add Supabase auth pages and protected app shell.
3. Build upload page with progress and extraction status.
4. Build chat page with source-aware answers.
5. Build dashboard, calendar, course, and analytics pages.
6. Add Recharts visualizations for workload and deadlines.

## Phase 6: Production Readiness

1. Add integration tests for API routes and services.
2. Add frontend component and flow tests.
3. Add background job processing for extraction.
4. Add rate limiting and request size limits.
5. Add observability, error tracking, and structured audit logs.
6. Add deployment docs for Render/Fly.io/Vercel plus Supabase.
