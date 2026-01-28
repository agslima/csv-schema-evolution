<!-- Copilot instructions for AI coding agents in this repository -->

# Agent Instructions — csv_schema_evolution

Resumo curto: este repositorio expoe uma API de upload/processing de CSVs
(FastAPI + MongoDB/GridFS) e um frontend estatico em JS. As instrucoes abaixo
refletem o codigo atual.

## Arquitetura (big picture)
- **Frontend**: arquivos estaticos em `frontend/` (`frontend/js/api.js`,
  `frontend/js/app.js`) consomem a API REST.
- **Backend**: FastAPI em `backend/app/`.
  - Entrypoint: `backend/app/main.py` (routers em `/api/v1/files` e
    `/api/v1/health`).
  - Rotas: `backend/app/api/v1/endpoints/files.py` e
    `backend/app/api/v1/endpoints/health.py`.
- **Servicos**:
  - `backend/app/services/file_service.py`: orquestra upload/list/download/delete.
  - `backend/app/services/csv_handler.py`: parsing, sanitizacao, deteccao de
    dialeto e suporte a layout vertical.
  - `backend/app/services/cleanup.py`: job de limpeza (APScheduler).
- **Repositorios**:
  - `backend/app/repositories/file_repository.py`: GridFS, metadados e criptografia.
  - `backend/app/utils/storage.py` esta **deprecated**.
- **Utils**:
  - `backend/app/utils/sanitize.py`: `sanitize_cell_value` (CSV injection).
  - `backend/app/utils/validators.py`: validacoes de CSV (extensao/content-type).
- **DB**: `backend/app/db/mongo.py` usa `AsyncIOMotorClient` e
  `AsyncIOMotorGridFSBucket`.

## Padroes e convencoes especificos
- Tamanho maximo: `settings.MAX_FILE_SIZE_MB` em
  `backend/app/core/config.py`, validado em `file_repository.save_file`.
- Fluxo de upload:
  1. `file_service.save_upload` le bytes e salva o arquivo bruto no GridFS
     (`raw_fs_id`).
  2. Processa e sanitiza com `csv_handler.process_csv_content`.
  3. Salva o CSV sanitizado no GridFS (`processed_fs_id`) e atualiza metadados
     (`fields`, `records_count`, `status`).
- Fluxo de download:
  - `file_service.download_processed_file` streama o CSV sanitizado via
    `processed_fs_id`.
  - Se nao existir `processed_fs_id`, reprocessa, salva o sanitizado e atualiza
    metadados.
- CSV Injection: `sanitize_cell_value` prefixa `'` quando a celula comeca com
  `=`, `+`, `-` ou `@`.
- Criptografia: `app/core/security.py` usa Fernet. Hoje a chave e gerada em
  runtime (nao persistente) — para producao, use uma chave estavel via config/env.

## Comandos uteis / workflows
- Testes: `pytest -v backend/tests` (integracao requer MongoDB).
- Backend local: `cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- Stack completo: `docker-compose up --build`
- CI: workflows em `.github/workflows/01-pr-validation.yml` e
  `.github/workflows/02-delivery.yml`.

## Integracoes e pontos de atencao
- GridFS: operacoes centralizadas em `backend/app/repositories/file_repository.py`.
- Frontend ↔ Backend: `frontend/js/api.js` e `frontend/js/app.js`.
- Validacao: `validate_csv_file` existe, mas o upload atual valida apenas
  extensao; use a funcao se precisar validar content-type.

## Exemplos rapidos
- Upload via service:

```py
from app.services.file_service import save_upload
result = await save_upload(uploaded_file, id_field=None)
```

- Download sanitizado:

```py
from app.services.file_service import download_processed_file
payload, filename = await download_processed_file(file_id)
```

## Exemplos de Requests HTTP

Todos os exemplos usam `BASE_URL=http://localhost:8000`.

### Upload (POST /api/v1/files/upload)
```bash
# Sem id_field
curl -X POST "http://localhost:8000/api/v1/files/upload" \
  -F "file=@myfile.csv"

# Com id_field (query param)
curl -X POST "http://localhost:8000/api/v1/files/upload?id_field=record_id" \
  -F "file=@myfile.csv"
```

**Resposta (200/201)**
```json
{
  "id": "654f7a2b9c1e4b3a...",
  "filename": "myfile.csv",
  "status": "processed",
  "records_count": 12,
  "fields": ["name", "email", "created_at"]
}
```

### Listar Arquivos (GET /api/v1/files/)
```bash
curl "http://localhost:8000/api/v1/files/"
```

### Download (GET /api/v1/files/{file_id}/download)
```bash
curl -OJ "http://localhost:8000/api/v1/files/654f7a2b9c1e4b3a.../download"
```

### Deletar (DELETE /api/v1/files/{file_id})
```bash
curl -X DELETE "http://localhost:8000/api/v1/files/654f7a2b9c1e4b3a..."
```

### Health Check (GET /api/v1/health/)
```bash
curl "http://localhost:8000/api/v1/health/"
```

### Liveness (GET /api/v1/health/live)
```bash
curl "http://localhost:8000/api/v1/health/live"
```

### Readiness (GET /api/v1/health/ready)
```bash
curl "http://localhost:8000/api/v1/health/ready"
```

## Observacoes / Detalhes Tecnicos
- O upload e processado de forma sincrona no endpoint (processa antes de
  responder).
- Parsing roda em threadpool (`csv_handler.process_csv_content`).
- Metadados ficam em `db.files`: `status`, `fields`, `records_count`,
  `raw_fs_id`, `processed_fs_id`.
