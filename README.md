# Chap Chap Africa HRMS

HR management system with a React/Vite frontend, FastAPI backend, and PostgreSQL database.

## Run with Docker Compose

1. Copy `.env.example` to `.env` and set a unique database password and secret key.
2. Start the application with `docker compose up --build`.
3. Open the frontend at <http://localhost:3000> and the API docs at <http://localhost:8000/docs>.

The compose file persists PostgreSQL data in a named volume and candidate CV uploads in `uploads/`.

## Run locally

Set `DATABASE_URL` and `SECRET_KEY` in the environment, then install the backend dependencies from `backend/requirements.txt`. Start the API from `backend/` with `uvicorn app.main:app --reload`.

In another terminal, install the frontend dependencies from `frontend/` and run `npm run dev`. Set `VITE_API_BASE_URL` when the API is not available at `http://localhost:8000/api`.

## Project layout

- `backend/app/main.py` registers the API routers and startup migrations.
- `backend/app/routers/` contains FastAPI route modules.
- `backend/app/models/` contains SQLAlchemy models.
- `backend/migrations/` contains SQL migration files.
- `frontend/src/` contains the React application.
