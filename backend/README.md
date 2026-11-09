# Backend

FastAPI application source lives in `app/`; SQL migration scripts live in the sibling `migrations/` directory. Run locally from this directory with `uvicorn app.main:app --reload` after installing `requirements.txt` and setting `DATABASE_URL` and `SECRET_KEY`.
