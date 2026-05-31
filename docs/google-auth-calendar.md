# Google Sign-In And Calendar Sync

Study Buddy uses Supabase Auth for Google sign-in and Google Calendar API for deadline sync.

## 1. Google Cloud Setup

1. Open Google Cloud Console.
2. Create or select a project.
3. Configure the OAuth consent screen.
4. Enable the Google Calendar API.
5. Create an OAuth Client ID with application type `Web application`.
6. Add authorized JavaScript origins for local development:

```text
http://localhost:5174
http://127.0.0.1:5174
http://localhost:5173
http://127.0.0.1:5173
```

7. Add the Supabase Auth callback URL as an authorized redirect URI:

```text
https://your-project-ref.supabase.co/auth/v1/callback
```

Use your real project ref.

## 2. Supabase Provider Setup

In Supabase Dashboard:

1. Go to Authentication -> Providers.
2. Enable Google.
3. Paste the Google OAuth client ID and client secret.
4. Save.

## 3. Frontend Environment

Create `frontend/.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
VITE_SUPABASE_URL=https://your-project-ref.supabase.co
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key
```

Restart the frontend dev server after editing `.env`.

## 4. How It Works

The frontend requests these Google scopes during Supabase OAuth:

```text
openid email profile https://www.googleapis.com/auth/calendar.events
```

After sign-in, Supabase returns a Supabase access token and a Google provider token. The Supabase token authenticates Study Buddy API requests. The Google provider token is sent to `POST /api/v1/calendar/sync` only when the user clicks sync.

Provider tokens are not stored in the Study Buddy database in this implementation.

## 5. Test Flow

1. Start FastAPI on `http://127.0.0.1:8000`.
2. Start React on `http://localhost:5174` or `http://127.0.0.1:5174`.
3. Click `Sign in with Google`.
4. Upload a PDF and extract deadlines.
5. Open Analytics.
6. Click `Sync deadlines`.
7. Check Google Calendar.
