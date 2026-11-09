FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /srv/hrms
COPY backend/requirements.txt /srv/hrms/backend/requirements.txt
RUN pip install --no-cache-dir -r /srv/hrms/backend/requirements.txt
COPY backend/app /srv/hrms/backend/app
COPY backend/migrations /srv/hrms/backend/migrations

WORKDIR /srv/hrms/backend
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
