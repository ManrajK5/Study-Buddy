# Study Buddy

- Study Buddy is a production-style AI academic assistant for uploading syllabi and lecture PDFs, extracting academic deadlines, chatting with course documents through RAG, and generating personalized study plans.

- Link: https://study-buddy-tan-seven.vercel.app/

- Demo: https://youtu.be/LEAjihpyL4c

## Stack

- Frontend: React, Tailwind CSS, Recharts
- Backend: FastAPI, Python async services
- Database/Auth/Storage: Supabase, PostgreSQL, pgvector
- AI: LangChain, LangGraph, Gemini 3.5 Flash, Supabase Edge Runtime embeddings with `gte-small`
- PDF Processing: PyPDFLoader, pdfplumber

## Current Slice

This repository starts with the production architecture, Supabase schema, backend service boundaries, FastAPI app, RAG pipeline interfaces, and LangGraph multi-agent workflow scaffold.

## Quick Start

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

API docs will be available at `http://localhost:8000/docs`.

## Project Docs

- [Architecture](docs/architecture.md)
- [Folder Structure](docs/folder-structure.md)
- [Roadmap](docs/roadmap.md)
- [Deployment Guide](docs/deployment.md)
- [Supabase Schema](supabase/migrations/001_initial_schema.sql)
- [Supabase Embed Function](supabase/functions/embed/index.ts)
- [Google Sign-In And Calendar Export](docs/google-auth-calendar.md)
