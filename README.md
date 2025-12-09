# CSV Ingestion & Processing Engine

![Status](https://github.com/agslima/csv_schema_evolution/actions/workflows/ci.yml/badge.svg)
<p align="left">
  <img alt="CI" src="https://img.shields.io/github/actions/workflow/status/agslima/csv_schema_evolution/ci.yml?label=CI%2FCD">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10+-blue">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-async-green">
  <img alt="MongoDB" src="https://img.shields.io/badge/MongoDB-GridFS-brightgreen">
  <img alt="LGPD Safe" src="https://img.shields.io/badge/Data%20Protection-LGPD%20Safe-orange">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-lightgrey">
</p>

## Backend-Focused Full Stack Application (FastAPI + MongoDB GridFS)
A secure, extensible, and compliance-oriented engine for ingesting, sanitizing, normalizing, and analyzing CSV files at scale.
Built to handle heterogeneous schemas, protect user data (LGPD), and provide a backend-centric architecture suitable for real production environments.

## Project Purpose

This system was originally developed to solve a real business problem: users frequently uploaded CSV files with inconsistent structures, repeated keys, missing fields, or schema drift. Existing online tools could not be used due to:

* **LGPD/compliance restrictions**
* **Sensitive client data**
* **Lack of ownership/control over data processing**
* **No guarantees of CSV Injection protection**
* **Inability to infer schemas or normalize data safely**

### ✔ What the engine does

It performs secure ingestion and converts unstructured CSV key-value patterns into proper, user-friendly tables.

Example input:
Name, John
Age, 23
Name, Mary
Age, 30
City, NY

### ✔ Why this matters

This allows teams to:

* Analyze inconsistent data sources
* Generate structured tables automatically
* Avoid dangerous online tools that leak data
* Comply with LGPD and other regulations
* Prepare data for analytics or migration pipelines


---

## Arquitetura

```text
csv_schema_evolution/
├── backend/
│   ├── app/
│   │   ├── main.py              # Aplicação FastAPI principal
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── files.py     # Rotas API (upload, listagem, download, delete)
│   │   │       └── health.py    # Health check
│   │   ├── services/
│   │   │   ├── csv_processor.py # Processamento de CSV
│   │   │   ├── storage.py       # Gerenciamento GridFS
│   │   │   └── sanitize.py      # Proteção CSV Injection
│   │   ├── db/
│   │   │   └── mongo.py         # Conexão MongoDB e GridFS
│   │   ├── models/
│   │   │   └── file_models.py   # Modelos Pydantic
│   │   └── utils/
│   │       └── validators.py    # Validações
│   ├── requirements.txt         # Dependências Python
│   └── Dockerfile
│
├── frontend/
│   ├── index.html
│   └── assets/
│       ├── style.css
│       └── js/
│           ├── upload.js        # Upload handler
│           ├── files_list.js    # Listagem de arquivos
│           └── ui_utils.js      # Utilitários de UI
│
├── tests/
│   ├── conftest.py              # Configuração pytest
│   ├── unit/
│   │   ├── test_csv_processor.py
│   │   └── test_sanitize.py
│   └── integration/
│       └── test_api_files.py
│
├── .github/
│   ├── copilot-instructions.md  # Instruções para agentes AI
│   └── workflows/
│       └── ci.yml               # GitHub Actions (testes + build Docker)
│
├── docker-compose.yml           # FastAPI + MongoDB + Mongo Express
├── pytest.ini                   # Configuração pytest
├── run_tests.py                 # Test runner simples
├── requirements.txt             # Dependências Python
└── README.md                    # Documentação
````

---

## Funcionalidades

- **Upload seguro de CSVs** (máx. 50 MB).
- **Processamento backend Python**:

  - Detecta delimitador automaticamente (`,` ou `;`).
  - Corrige campos, gera schema dinâmico.
  - Previne CSV Injection.
- **Armazenamento MongoDB** via GridFS.
- **Listagem de arquivos** com:

  - Busca por nome.
  - Paginação.
- **Download** de arquivos processados.
- **Logs automáticos** de campos e ocorrências.

---

## Stack Tecnológica

| Camada        | Tecnologia                     |
| ------------- | ------------------------------ |
| **Backend**   | FastAPI + Uvicorn (Python 3.10+) |
| **Banco**     | MongoDB (GridFS)               |
| **Frontend**  | HTML + JS vanilla              |
| **Async**     | Motor (async MongoDB driver)   |
| **Testes**    | pytest + pytest-asyncio        |
| **CI/CD**     | GitHub Actions                 |
| **Container** | Docker / Docker Compose        |

---

## Instalação Local

### 1️⃣ Clonar o repositório

```bash
git clone https://github.com/seuusuario/csv-uploader.git
cd csv-uploader
```

### 2️⃣ Configurar ambiente

Crie e ative o ambiente virtual:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 3️⃣ Instalar dependências

```bash
cd backend
pip install -r requirements.txt
```

### 4️⃣ Executar com Docker Compose

```bash
docker-compose up --build
```

O app estará disponível em **[http://localhost:8000](http://localhost:8000)**

---

## Uso

1. Acesse a interface web.
2. Faça upload de um ou mais arquivos CSV.
3. Aguarde o processamento (com barra de progresso).
4. Baixe o arquivo processado ou visualize na lista.
5. Use a busca para encontrar arquivos anteriores.

---

## Testes Automatizados

Execute testes rápidos (sem DB):

```bash
python run_tests.py
```

Execute todos os testes com pytest:

```bash
pytest -v tests/
```

Tipos de testes:

- **tests/unit/** → testes isolados de sanitização e validação CSV.
- **tests/integration/** → testes de API REST (upload, listagem, download, delete).
  - Requerem MongoDB rodando (`docker-compose up`).

---

## Segurança

- Upload limitado a **50 MB**.
- Aceita **apenas arquivos CSV** (`.csv`).
- Proteção contra **CSV Injection** (`=`, `+`, `-`, `@` no início de célula).
- Filtragem de entradas de usuário.
- Logging e mensagens de erro seguros.

---

## CI/CD com GitHub Actions

Arquivo: `.github/workflows/ci.yml`

Executa automaticamente:

- Instala dependências.
- Roda testes (`pytest`).
- Faz build da imagem Docker.

---

## Docker Compose

Arquivo: `docker-compose.yml`

Serviços incluídos:

- `web`: app FastAPI (Uvicorn).
- `mongo`: banco de dados MongoDB.
- `mongo-express`: painel web em [http://localhost:8081](http://localhost:8081).

Subir ambiente:

```bash
docker-compose up --build
```

Ou executar o backend localmente (sem Docker):

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## API Endpoints (REST)

| Método   | Endpoint                    | Descrição                             |
| -------- | --------------------------- | ------------------------------------- |
| `POST`   | `/api/v1/files/upload`      | Upload de arquivo CSV                 |
| `GET`    | `/api/v1/files/`            | Lista arquivos com metadados          |
| `GET`    | `/api/v1/files/{file_id}/download` | Download do arquivo processado  |
| `DELETE` | `/api/v1/files/{file_id}`   | Remove arquivo do MongoDB             |
| `GET`    | `/api/v1/health/`           | Health check da API                   |

**Exemplo de upload:**

```bash
curl -X POST "http://localhost:8000/api/v1/files/upload" \
  -F "file=@myfile.csv"
```

Ver `.github/copilot-instructions.md` para exemplos completos (curl, JavaScript, Node.js).

---

## Possíveis Melhorias Futuras

- Autenticação e autorização (JWT / OAuth2).
- Dashboard de estatísticas e análises.
- Controle de versão e histórico de alterações de arquivos.
- Processamento assíncrono com task queue (Celery + Redis).
- Interface React/Vue para melhor UX.
- Suporte a mais formatos (Excel, Parquet, JSON).
- Testes de carga e performance (k6, locust).

---

## Desenvolvimento

Para agentes AI e desenvolvedores trabalhando neste repositório, veja `.github/copilot-instructions.md` para:

- Arquitetura detalhada
- Padrões de código específicos
- Comandos úteis de desenvolvimento
- Exemplos de requests HTTP
- Guia de testes

---
