# Tests et vérifications locales

## Backend
- Dépendances : `pip install -r backend/requirements.txt`
- Variables d'env : copier `backend/.env.example` vers `backend/.env` et compléter (Supabase ou Postgres local).
- Lancer l'API : `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` (dans `backend/`).
- Migrations Alembic :
  - `cd backend`
  - `alembic upgrade head` (applique `backend/alembic/versions/0001_init.py`)
  - Générer une migration : `alembic revision --autogenerate -m "message"`
- Tests unitaires (placeholders à enrichir) : `pytest backend/app/tests`.
- Metrics Prometheus : `GET http://localhost:8000/metrics`.
- Healthcheck : `GET http://localhost:8000/health`.

## Frontend (React + Vite + TS)
- Dépendances : `npm install` (dans `frontend/`).
- Variables d'env : copier `frontend/.env.example` vers `frontend/.env` et renseigner `VITE_API_BASE_URL`.
- Dev server : `npm run dev` (par défaut sur `http://localhost:5173`).
- Build : `npm run build`.
- Preview prod : `npm run preview`.

## Docker (frontend + backend + Postgres + Prometheus + Grafana)
- `docker compose up --build`
- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (user/pass par défaut `admin`/`admin`)

## Notes Supabase / RLS
- Si vous utilisez Supabase, configurez la chaîne Postgres dans `.env`.
- Activez toujours RLS sur chaque table créée et ajoutez des politiques adaptées (ex. accès par organisation/tenant). Conservez la clé service role uniquement côté backend.

