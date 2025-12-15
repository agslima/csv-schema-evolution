# Setup Guide

This guide explains how to run the project locally or via Docker.

## 1. Requirements

- Python 3.10+
- Docker + Docker Compose
- MongoDB (optional if running without Docker)

## 2. Clone the repository

```bash
git clone https://github.com/agslima/csv_schema_evolution.git
cd csv_schema_evolution


##3. Local environment

```bash
python -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

### Run backend

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 4. Docker Compose

```bash
docker-compose up --build
```

## Services

- FastAPI: http://localhost:8000
- Mongo Express: http://localhost:8081
