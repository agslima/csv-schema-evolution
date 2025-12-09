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

## Architecture Overview

This application is designed with a backend-first mindset, following clean, modular design and production-grade patterns.

```text
backend/
├── app/
│   ├── main.py              # FastAPI entrypoint
│   ├── api/v1/              # REST endpoints
│   ├── services/            # Core business logic
│   │   ├── csv_processor.py # Schema inference, sanitization, transforms
│   │   ├── sanitize.py      # CSV Injection protection
│   │   └── storage.py       # GridFS IO layer
│   ├── db/mongo.py          # MongoDB client + GridFS handler
│   ├── models/              # Pydantic models
│   └── utils/validators.py  # Input validation
```

flowchart TD
    A[Web UI<br>(HTML + JS)] -->|Upload/Download| B[FastAPI API<br>Uvicorn]

    B --> C1[CSV Processor<br>- Schema Inference<br>- Delimiter Detect]
    B --> C2[Sanitizer<br>- CSV Injection Check]
    B --> C3[Storage Layer<br>GridFS Handler]

    C1 --> D[MongoDB + GridFS]
    C2 --> D
    C3 --> D

## Key Backend Engineering Decisions

| Decision |	Rationale |
| -- | -- |
| FastAPI + Async I/O (Motor) | High throughput for file-heavy workloads |
| MongoDB + GridFS |	Stores arbitrarily large CSVs and avoids RAM bottlenecks |
| Schema Inference Engine	| Converts inconsistent key-value patterns into relational tables |
| CSV Injection Sanitization |	Prevents spreadsheet attacks (=, +, @, -) |
| Test suite (unit + integration) |	Ensures correctness for processors, sanitizers, and API |

---

## Features

### 🛡 Security

* LGPD-friendly processing (no third-party tools)
* CSV Injection protection
* File size limit (50 MB)
* Strict content-type validation
* Sanitized metadata stored separately from raw file streams

### 🧠 Automated CSV Processing

* Dynamic schema generation
* Delimiter autodetection
* Normalization of inconsistent key-value patterns
* Type guessing & field correction
* Detailed logs of anomalies and processing events

### 📦 Storage (MongoDB GridFS)

* Resilient storage for large CSVs
* Metadata + structured output stored as documents
* Supports large file ingestion without memory overload

###🔁 CI/CD

* GitHub Actions (tests + Docker build)
* Isolated modules for pipeline execution
* Reproducible environment via Docker Compose

### Demonstration:

Upload Flow
![Upload Interface](docs/screenshots/upload_page.png)

Processed Table Preview
![Processed CSV Output](docs/screenshots/table_output.png)

GIF Demo
![CSV Ingestion Demo](docs/demo/csv_ingestion_demo.gif)

---

## Documentation

For more details about the documentation of this project, please access:

- ![System Architecture](docs/demo/architecture.md)
- ![Setup Guide](/docs/setup.md)
- ![API Reference](docs/demo//docs/api_reference.md)
- ![Tests guide](docs/demo/test.md)
- ![CSV Processing Engine](/docs/processing_engine.md)

---

## Roadmap (Planned Backend Enhancements)

These align with real-world ingestion & data engineering pipelines:

* Chunked file processing for huge datasets
* RFC 4180-compliant CSV parser
* Data transformation layer (cleaning, mapping, enrichment)
* Data analysis & pattern detection
* Conversion to XLSX, JSON, Parquet
* Versioning of processed datasets
* Background workers (Celery + Redis) for async heavy workloads
* User authentication + RBAC
* Admin dashboard (React or Vue)
* Rule engine to define extraction/transformation logic
* Report generation (PDF / HTML)

---

## License

