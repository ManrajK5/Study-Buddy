# Deployment Guide

This guide deploys Study Buddy as a recruiter-friendly production demo:

- Supabase: auth, PostgreSQL, pgvector, storage, and the embedding Edge Function.
- Render: FastAPI backend.
- Vercel: React frontend.

## 1. Prepare The Repository

This folder is not currently initialized as a Git repository. From the project root:

```bash
cd /Users/manrajkalra/Documents/Codex/2026-05-28/Study-Buddy
git init
git add .
git commit -m "Prepare Study Buddy for deployment"
```

Create a GitHub repository named `study-buddy`, then push:

```bash
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/study-buddy.git
git push -u origin main
```

Before pushing, make sure local secret files are ignored:

```bash
git check-ignore backend/.env frontend/.env
```

Both files should print back in the terminal. Do not commit `.env` files.

## 2. Supabase Production Checklist

Use your existing hosted Supabase project.

1. Run the migrations from `supabase/migrations` in Supabase SQL Editor.
2. Confirm the `vector` extension exists.
3. Confirm the `course-documents` storage bucket exists.
4. Deploy the embedding Edge Function:

```bash
supabase functions deploy embed --project-ref YOUR_PROJECT_REF
```

5. In Supabase Dashboard, go to Authentication > URL Configuration:
   - Site URL: your final Vercel production URL, for example `https://study-buddy.vercel.app`
   - Additional Redirect URLs:
     - `https://study-buddy.vercel.app/**`
     - `http://localhost:5173/**`
     - `http://127.0.0.1:5173/**`
     - `http://localhost:5174/**`
     - `http://127.0.0.1:5174/**`

Supabase requires redirect URLs to be allow-listed for auth flows. The production URL should be the default site URL, while localhost stays available for development.

## 3. Google OAuth Checklist

In Google Cloud Console, keep your existing OAuth client and add production URLs.

Authorized JavaScript origins:

```text
https://study-buddy.vercel.app
http://localhost:5173
http://127.0.0.1:5173
http://localhost:5174
http://127.0.0.1:5174
```

Authorized redirect URI:

```text
https://YOUR_PROJECT_REF.supabase.co/auth/v1/callback
```

If the app is still in Testing mode, add recruiter emails as test users. For a public portfolio link, publish the OAuth consent screen when you are ready.

## 4. Deploy The Backend On Render

Create a new Render Web Service from the GitHub repo.

Settings:

```text
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
Health Check Path: /api/v1/health
```

Environment variables:

```text
APP_NAME=Study Buddy API
APP_ENV=production
API_V1_PREFIX=/api/v1
BACKEND_CORS_ORIGINS=https://study-buddy.vercel.app,http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174

SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
SUPABASE_ANON_KEY=YOUR_SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY=YOUR_SUPABASE_SERVICE_ROLE_KEY
SUPABASE_STORAGE_BUCKET=course-documents
SUPABASE_EMBEDDING_FUNCTION=embed
EMBEDDING_DIMENSIONS=384
EMBEDDING_BATCH_SIZE=1

GOOGLE_API_KEY=YOUR_GEMINI_API_KEY
GEMINI_MODEL=gemini-2.5-flash

MAX_UPLOAD_MB=25
RAG_CHUNK_SIZE=1200
RAG_CHUNK_OVERLAP=180
```

The same variable list is available in `backend/.env.production.example`.

After deploy, verify:

```text
https://YOUR_RENDER_SERVICE.onrender.com/api/v1/health
https://YOUR_RENDER_SERVICE.onrender.com/docs
```

## 5. Deploy The Frontend On Vercel

Create a new Vercel project from the same GitHub repo.

Settings:

```text
Framework Preset: Vite
Root Directory: frontend
Build Command: npm run build
Output Directory: dist
Install Command: npm install
```

Environment variables:

```text
VITE_API_BASE_URL=https://YOUR_RENDER_SERVICE.onrender.com/api/v1
VITE_SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
VITE_SUPABASE_ANON_KEY=YOUR_SUPABASE_ANON_KEY
```

The same variable list is available in `frontend/.env.production.example`.

Redeploy after adding environment variables.

## 6. Final Smoke Test

Open the Vercel URL and test this recruiter demo path:

1. Sign in with Google.
2. Create a course.
3. Upload a syllabus PDF.
4. Confirm duplicate file detection.
5. Preview extracted events.
6. Edit one extracted event before saving.
7. Confirm upcoming events only.
8. Ask the chatbot: `What assignments are due next week?`
9. Open Analytics and verify course labels, event editing, and charts.
10. Sync selected upcoming events to Google Calendar.

## 7. Portfolio Notes

For a resume or GitHub README, describe this as:

> Built a full-stack AI academic assistant with FastAPI, React, Supabase/PostgreSQL/pgvector, LangGraph agent orchestration, Gemini, and a complete RAG pipeline for syllabus and lecture PDF analysis.

Show the deployed frontend link, the GitHub repo, and 3-5 screenshots or a short walkthrough video.
