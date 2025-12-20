# CSV Ingestion & Processing Engine

### Backend‑First Data Ingestion Service (FastAPI + MongoDB GridFS)

<p align="left">
  <a href="https://github.com/agslima/csv-schema-evolution/actions/workflows/ci-cd.yml"/>
    <img alt="CI/CD Pipeline" src="https://github.com/agslima/csv-schema-evolution/actions/workflows/ci-cd.yml/badge.svg">
  </a>
  <a href="https://codecov.io/github/agslima/csv-schema-evolution" >
    <img src="https://codecov.io/github/agslima/csv-schema-evolution/graph/badge.svg?token=776AEW3J4C"/>
  </a>
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10+-blue">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-async-green">
  <img alt="MongoDB" src="https://img.shields.io/badge/MongoDB-GridFS-brightgreen">
  <a href="https://www.bestpractices.dev/projects/11596">  
  </a>
  <img src="https://img.shields.io/badge/SLSA-Level%202-brightgreen.svg">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-lightgrey">
</p>

> **A backend‑centric engine for securely ingesting, sanitizing, and normalizing heterogeneous CSV files.**

This project focuses on **data safety, correctness, and operational transparency**. It was designed to process sensitive CSV files **without relying on third‑party online tools**, ensuring full control over data handling and compliance requirements.

## TL;DR

- Secure backend service for ingesting untrusted CSVs
- Focused on compliance, sanitization, and observability
- Designed for real production pipelines, not ad-hoc scripts
- Best entry points: `/docs/architecture.md` and `/docs/processing-engine.md`

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
| `Name; John``Age, 23``City, NY` | Sanitization → Dialect Detection → Schema Inference → Normalization | `{ "name": "John", "age": 23, "city": "NY" }` |

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
    A[User Upload] -->|Stream| B(FastAPI Endpoint)
    B -->|Validation| C{Sanitizer}
    C -->|Safe Content| D[Processor Engine]
    D -->|Schema Inference| E[Normalizer]
    E -->|Structured Data| F[(MongoDB / GridFS)]
    C -->|Malicious Input| X[Reject Request]
```

### Design Tradeoffs

* **FastAPI + async I/O** for high concurrency during file uploads
* **MongoDB GridFS** to store large files without memory pressure
* **Heuristic dialect detection** to avoid forcing users to configure CSV formats
* **Encryption at rest** to minimize exposure of sensitive data

> [!NOTE]
> GridFS was chosen to simplify transactional consistency between file storage and metadata during early ingestion stages, with future support for object storage planned.
> When dialect detection confidence falls below a defined threshold, the engine fails fast with an explicit error rather than producing ambiguous output

Detailed architecture documentation is available in `/docs`.

<!--
---

## Screenshots

| Upload CSV | Processed Table Preview |
|---|---|
| ![image](https://github.com/agslima/csv-schema-evolution/blob/main/docs/screenshots/job-done.png) | ![image](https://github.com/agslima/csv-schema-evolution/blob/main/docs/screenshots/table.png) |
| **GIF Demo** |
| ![image]([https://github.com/agslima](https://github.com/agslima/csv-schema-evolution/blob/main/docs/screenshots/demo.gif)|

### Demonstration:

1. Secure Upload

Users upload files via a clean interface with immediate validation.

2. Automated Processing

The system ingests, cleans, and presents the data.
Upload Flow
![Upload Interface](docs/demo/screenshots/upload_page.png)

Processed Table Preview
![Processed CSV Output](docs/demo/screenshots/table_output.png)

3. GIF Demo
![CSV Ingestion Demo](docs/demo/csv_ingestion_demo.gif)

-->

---

## How to run this? 🚀

### Prerequisites

* Docker & Docker Compose

##### 1. Clone the repository

```bash
git clone https://github.com/agslima/csv-schema-evolution.git
cd csv-schema-evolution
```

#### 1. Run the Stack

```bash
docker-compose up -d --build
```

#### 2. Access the Interfaces

* **Web UI:** http://localhost:3000
* **API Docs (Swagger):** http://localhost:8000/docs
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

The system is designed with LGPD principles in mind, including **data minimization**, **purpose limitation**, and **access control**. Full details are available in `docs/security.md`.

---

## Testing & Quality 

The project is developed using **Test-Driven Development (TDD)** and maintains **high test coverage** across all critical paths, with exclusions explicitly documented boilerplate.

Test levels include:

* Unit tests for core algorithms (dialect detection, sanitization)
* Integration tests covering full HTTP request lifecycles
* Storage and database interaction tests

Coverage is continuously measured via **Codecov** and enforced in CI. See `docs/testing.md` for details.

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

## Documentation Index 

For detailed implementation guides, please refer to:

* 📡 API Reference — [`docs/api-reference.md`](https://github.com/agslima/csv-schema-evolution/blob/main/docs/api-reference.md)
* 🏗 Architecture — [`docs/architecture.md`](https://github.com/agslima/csv-schema-evolution/blob/main/docs/architecture.md)
* ⚙ Processing Engine — [`docs/processing-engine.md`](https://github.com/agslima/csv-schema-evolution/blob/main/docs/processing-engine.md)
* 🔁 CI/CD & Supply Chain Security — [`docs/ci-cd.md`](https://github.com/agslima/csv-schema-evolution/blob/main/docs/ci-cd.md)
* 🔒 Security & Compliance — [`docs/security.md`](https://github.com/agslima/csv-schema-evolution/blob/main/docs/security.md)
* 🧪 Testing Strategy — [`docs/testing.md`](https://github.com/agslima/csv-schema-evolution/blob/main/docs/testing.md)
* 📝 Logging & Observability — [`docs/logging.md`](https://github.com/agslima/csv-schema-evolution/blob/main/docs/logging.md)
* 🚀 Setup & Installation Guide — [`docs/setup.md`](https://github.com/agslima/csv-schema-evolution/blob/main/docs/setup.md)
  
---

## Roadmap

Planned enhancements aligned with real ingestion pipelines:

* Chunked processing for very large datasets
* RFC 4180‑compliant parsing
* Export formats (Parquet, JSON, XLSX)
* Background workers (Celery + Redis)
* Role‑based access control (RBAC)

---
## Contributing 

1. ​Fork the project
2. ​Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. ​Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. ​Push to the Branch (`git push origin feature/AmazingFeature`)
5. ​Open a Pull Request

---

## License 

This project is licensed under the MIT License. See the LICENSE file for details.
