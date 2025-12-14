# CSV Ingestion & Processing Engine

### Backend‑First Data Ingestion Service (FastAPI + MongoDB GridFS)

> **A backend‑centric engine for securely ingesting, sanitizing, and normalizing heterogeneous CSV files.**

This project focuses on **data safety, correctness, and operational transparency**. It was designed to process sensitive CSV files **without relying on third‑party online tools**, ensuring full control over data handling and compliance requirements.

---

## Problem Statement

In real production environments, CSV files are rarely clean or standardized. Users frequently upload files with:

* Inconsistent schemas and repeated keys
* Missing or optional fields
* Unknown delimiters and quoting rules
* Data that may trigger **CSV / Formula Injection** when opened in spreadsheet software

Existing online CSV tools were **not an option** due to:

* LGPD and data protection constraints
* Sensitive client information
* Lack of transparency in processing pipelines
* No guarantees around sanitization or secure storage

This system was built to solve those problems in a **controlled, auditable backend service**.

---

## What the Engine Does

The engine ingests unstructured or semi‑structured CSV files and converts them into **normalized, user‑friendly tabular data**.

| Raw Input                       | Processing Stages                                                   | Structured Output                             |
| ------------------------------- | ------------------------------------------------------------------- | --------------------------------------------- |
| `Name, John``Age, 23``City, NY` | Sanitization → Dialect Detection → Schema Inference → Normalization | `{ "name": "John", "age": 23, "city": "NY" }` |

### Key Outcomes

* Safe ingestion of untrusted CSV files
* Automatic schema inference without user configuration
* Protection against spreadsheet‑based attacks
* Structured output suitable for analytics, migration, or reporting pipelines

---

## High‑Level Architecture

The system follows **Clean Architecture** principles with a clear separation between API, business logic, and infrastructure.

```mermaid
graph LR
    A[Client Upload] -->|Stream| B(FastAPI API)
    B --> C{Validation & Sanitization}
    C -->|Safe| D[Processing Engine]
    D --> E[Schema Normalizer]
    E --> F[(MongoDB + GridFS)]
    C -->|Rejected| X[Error Response]
```

### Design Tradeoffs

* **FastAPI + async I/O** for high concurrency during file uploads
* **MongoDB GridFS** to store large files without memory pressure
* **Heuristic dialect detection** to avoid forcing users to configure CSV formats
* **Encryption at rest** to minimize exposure of sensitive data

Detailed architecture documentation is available in `/docs`.

---

## API Overview

| Method | Endpoint                      | Description                              |
| ------ | ----------------------------- | ---------------------------------------- |
| POST   | `/api/v1/files/upload`        | Upload, sanitize, and process a CSV file |
| GET    | `/api/v1/files/`              | List uploaded files and metadata         |
| GET    | `/api/v1/files/{id}/download` | Download decrypted CSV                   |
| DELETE | `/api/v1/files/{id}`          | Permanently delete file and metadata     |
| GET    | `/api/v1/health`              | Health check                             |

Full request/response payloads and error models are documented in **docs/api-reference.md**.

---

## Security & Compliance (Summary)

Security is enforced **by design**, not as an afterthought:

* Encryption at rest using AES (Fernet)
* Strict file type and size validation (default 50MB)
* Active mitigation of CSV / Formula Injection (`=`, `+`, `-`, `@`)
* No third‑party data processing services
* Clear separation between raw file storage and metadata

LGPD alignment is achieved through **data minimization, purpose limitation, and strong access control**. Full details are available in `docs/security.md`.

---

## Testing & Quality

The project is developed using **Test-Driven Development (TDD)** and maintains **near-100% test coverage**, excluding explicitly documented boilerplate.

Test levels include:

* Unit tests for core algorithms (dialect detection, sanitization)
* Integration tests covering full HTTP request lifecycles
* Storage and database interaction tests

Coverage is continuously measured via Codecov and enforced in CI. See `docs/testing.md` for details.

---

## CI/CD & Supply Chain Security

The CI/CD pipeline is designed to detect security issues early and ensure **artifact integrity** across the entire build lifecycle.

Every commit and pull request triggers an automated workflow that performs:

* **Secret Scanning** — Prevents accidental leakage of credentials and sensitive values before code is merged.
* **Static Analysis & Dependency Scanning** — Identifies vulnerable dependencies and insecure code patterns in both application code and third‑party libraries.
* **Automated Testing & Coverage Enforcement** — Ensures correctness, guards against regressions, and enforces coverage thresholds.
* **Container Hardening** — Validates Dockerfiles and scans container images for known vulnerabilities.
* **Artifact Integrity & Provenance** — Built images are signed and accompanied by a Software Bill of Materials (SBOM).

This pipeline reduces supply‑chain risk and provides traceability required for security reviews and compliance audits.

<details><summary>Tooling used</summary>
    
- Secret scanning: Gitleaks  
- SAST / SCA: Snyk, Bandit, Pylint  
- Test coverage: Pytest + Codecov  
- Docker linting: Hadolint  
- Container scanning: Trivy  
- Image signing: Cosign  
- SBOM generation: Syft

</details>

---

## Observability

The application implements structured logging with request correlation IDs, enabling full traceability across API, service, and storage layers.

Example:

```text
[INFO] [req_id: 1234] Request started: POST /api/v1/files/upload
[INFO] [req_id: 1234] Detected dialect: delimiter="," quote="\""
[ERROR] [req_id: 1234] Failed to write to GridFS: ConnectionTimeout
```

Logging configuration and operational guidance are documented in `docs/logging.md`.

---

## Local Development

### Prerequisites

* Docker
* Docker Compose

### Run the Stack

```bash
docker-compose up -d --build
```

### Access

* API Docs (Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)
* Web UI (if enabled): [http://localhost:3000](http://localhost:3000)

---

## Documentation Index

All implementation details are intentionally kept out of this README and documented separately:

* 📡 API Reference — `docs/api-reference.md`
* 🏗 Architecture — `docs/architecture.md`
* ⚙ Processing Engine — `docs/processing-engine.md`
* 🔒 Security & Compliance — `docs/security.md`
* 🧪 Testing Strategy — `docs/testing.md`
* 📝 Logging & Observability — `docs/logging.md`

---

## Roadmap

Planned enhancements aligned with real ingestion pipelines:

* Chunked processing for very large datasets
* RFC 4180‑compliant parsing
* Export formats (Parquet, JSON, XLSX)
* Background workers (Celery + Redis)
* Role‑based access control (RBAC)

---

## License

Distributed under the MIT License.
