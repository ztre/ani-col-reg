# 番剧收藏登记系统

SQLite-first full-stack MVP for searching YourAnimes season data, caching source covers locally, and keeping anime collection records.

## Stack

- Backend: FastAPI, SQLAlchemy, SQLite, HTTPX, BeautifulSoup
- Frontend: Vue 3, Vite, Element Plus
- Tests: Pytest

## Docker Quick Start

The project targets Linux container deployment.

```bash
cp .env.example .env
docker compose up --build
```

Then open:

- App: `http://localhost:8060`
- Health check: `http://localhost:8060/health`
- API docs: `http://localhost:8060/docs`

Container runtime data is persisted under `${ANI_COL_ROOT_DIR}/data` and mounted to `/app/data`.

## Local Linux Development

Copy the shared development defaults once:

```bash
cp .env.example .env
```

Default local ports:

- Backend: `http://localhost:8060`
- Frontend dev server: `http://localhost:5173`
- Vite proxy target: `http://localhost:8060`

Docker-related root `.env` fields:

- `PUID` / `PGID`: container runtime user mapping
- `ANI_COL_ROOT_DIR`: host-side runtime directory root, default `./runtime`
- `ANI_COL_PORT`: shared app port used by local backend and Docker publish rules

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

The default database is created at `backend/data/ani_col_reg.sqlite3`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend dev server port is controlled by `VITE_DEV_SERVER_PORT` and defaults to `5173`.
Its `/api` and `/health` proxy target follows `VITE_API_BASE_URL`, or falls back to `http://localhost:${ANI_COL_PORT}`.


## API

- `GET /api/anime`
- `POST /api/anime/search`
- `GET /api/anime/{id}`
- `POST /api/collection`
- `PATCH /api/collection/{id}`
- `POST /api/mapping/mgr-ani-ml`

More details are in `doc/api.md` and `doc/database.md`.
