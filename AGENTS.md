<!-- Agent instructions for csv-schema-evolution -->

# AGENTS.md

These notes are for coding agents working in this repo. Keep changes small,
prefer existing patterns, and validate behavior with local tests when possible.

## Project snapshot
- Backend: FastAPI in `backend/app/` (routers in `api/v1/`, services in
  `services/`, repositories in `repositories/`).
- Storage: MongoDB + GridFS via `backend/app/db/mongo.py`.
- Frontend: static JS in `frontend/` consuming the REST API.

## Key conventions
- Upload flow: save raw file to GridFS, parse/sanitize once, store processed CSV
  in GridFS, and persist schema metadata in `db.files`.
- Download flow: stream the stored processed CSV; avoid re-parsing on download.
- Use `app.repositories.file_repository` for GridFS and metadata access;
  `app.utils.storage` is deprecated.
- CSV sanitization: `app/utils/sanitize.py` (`sanitize_cell_value`).

## Common paths
- API routes: `backend/app/api/v1/endpoints/files.py`,
  `backend/app/api/v1/endpoints/health.py`.
- Services: `backend/app/services/file_service.py`,
  `backend/app/services/csv_handler.py`.
- Repo/storage: `backend/app/repositories/file_repository.py`.

## Commands
- Quick tests (no DB): `python run_tests.py`
- Full tests: `pytest -v` (integration tests require MongoDB)
- Full stack: `docker-compose up --build`

## More detail
- See `.github/copilot-instructions.md` for a deeper architecture and workflow
  guide.
