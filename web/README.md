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
