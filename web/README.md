# SmartHire ATS Frontend

Complete React + JavaScript frontend for the existing SmartHire FastAPI backend.

## Stack

- React
- JavaScript
- Vite
- React Router
- Supabase Auth
- Recharts
- Lucide React
- Native Fetch API

## Pages

- `/login`
- `/signup`
- `/dashboard`
- `/analyze`
- `/history`
- `/analysis/:id`
- `/resources`

## Existing backend remains unchanged

The frontend uses these existing FastAPI endpoints:

- `POST /api/v1/analyze-resume`
- `GET /api/v1/history`
- `DELETE /api/v1/history/{id}`
- `POST /api/v1/generate-pdf`
- `GET /api/v1/history/{id}/pdf`
- `GET /api/v1/health`

Vite proxies `/api/*` to `http://localhost:8000/api/*` during development.

## Setup

1. Open this folder in VS Code.
2. Run:

```bash
npm install
```

3. Create `.env` from `.env.example`:

```env
VITE_SUPABASE_URL=your_existing_supabase_url
VITE_SUPABASE_ANON_KEY=your_existing_supabase_anon_key
VITE_API_BASE_URL=/api
```

4. Start FastAPI from the SmartHire project root:

```bash
venv\Scripts\activate
uvicorn backend.main:app --reload
```

5. In this frontend folder:

```bash
npm run dev
```

6. Open:

`http://localhost:5173`

## Important

The PDF frontend code correctly treats PDF responses as binary blobs. If the backend PDF endpoint itself fails, the UI will display the backend error.

## Current integration behavior

- Login/signup use Supabase Auth.
- Protected pages require a Supabase session.
- API requests send `Authorization: Bearer <access token>`.
- Analyze page uploads the actual resume to FastAPI.
- Analysis page renders the actual `AnalysisResponse`.
- History loads from FastAPI.
- History PDF downloads as a browser file.
- New analysis results can be viewed immediately without waiting for a history refresh.

## Link previews (Open Graph / Twitter)

Crawlers for WhatsApp, LinkedIn, Telegram, Discord, Facebook and X do not run
JavaScript, so the metadata is written into **static HTML at build time**.

- `src/seo/routes.js` - all titles, descriptions and the share-image settings.
- `vite-plugin-seo.js` - injects the homepage tags into `index.html`, then emits
  `dist/<route>/index.html` for each known route and `dist/spa-fallback.html`
  for everything else. `vercel.json` rewrites unknown URLs to the fallback, so
  the homepage metadata is never served for other pages.
- `src/components/RouteMeta.jsx` - keeps `<head>` correct on client-side
  navigation and restores the homepage values when returning to `/`.
- `public/og-image.png` - 1200x630 share image.

### Required build setting

`VITE_SITE_URL` = your production origin (https, no path, no trailing slash).
On Vercel it falls back to `VERCEL_PROJECT_PRODUCTION_URL` if unset. The build
fails with a clear message if neither is available.

### Deploy

1. Vercel -> Project -> Settings -> Environment Variables: add `VITE_SITE_URL`
   (Production). Redeploy; keep existing Supabase / API variables as they are.
2. Push to the branch Vercel deploys from.

### Verify

```bash
# against a local build (set VITE_SITE_URL first)
npm run build
npm run verify:seo -- --dist dist --site https://your-domain.tld

# against the live site (acts as WhatsApp/LinkedIn/Telegram/Discord/X/Facebook)
npm run verify:seo -- --url https://your-domain.tld
```

After deploying, refresh each platform's cached preview: LinkedIn Post
Inspector, Facebook Sharing Debugger, and the X card validator. WhatsApp,
Telegram and Discord cache per URL, so test with a fresh link
(`https://your-domain.tld/?v=2`) if you shared the old one before.
