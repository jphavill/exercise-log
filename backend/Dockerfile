# syntax=docker/dockerfile:1.7
FROM python:3.12-slim

ARG BACKEND_SOURCE_HASH=unknown
LABEL com.exercise.backend-source-hash=$BACKEND_SOURCE_HASH

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip pip install -r /app/requirements.txt

COPY . /app

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && python seed.py && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
