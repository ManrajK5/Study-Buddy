# Google Sign-In And Calendar Export

Study Buddy uses Supabase Auth for Google sign-in. Calendar sharing is handled with a downloadable iCalendar (`.ics`) file so any signed-in user can export deadlines without granting sensitive Google Calendar permissions.

## 1. Google Cloud Setup

1. Open Google Cloud Console.
2. Create or select a project.
3. Configure the OAuth consent screen.
4. Create an OAuth Client ID with application type `Web application`.
5. Add authorized JavaScript origins for local development:

```text
http://localhost:5174
http://127.0.0.1:5174
http://localhost:5173
http://127.0.0.1:5173
```

6. Add the Supabase Auth callback URL as an authorized redirect URI:

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
openid email profile
```

After sign-in, Supabase returns a Supabase access token. The token authenticates Study Buddy API requests.

When the user clicks `Download .ics`, the frontend calls:

```text
GET /api/v1/calendar/export.ics
```

The backend loads upcoming extracted deadlines for the signed-in user and returns a standards-compatible iCalendar file. The user can import that file into Google Calendar, Apple Calendar, Outlook, or other calendar apps.

## 5. Test Flow

1. Start FastAPI on `http://127.0.0.1:8000`.
2. Start React on `http://localhost:5174` or `http://127.0.0.1:5174`.
3. Click `Sign in with Google`.
4. Upload a PDF and extract deadlines.
5. Open Analytics.
6. Click `Download .ics`.
7. Import the downloaded file into Google Calendar, Apple Calendar, or Outlook.
