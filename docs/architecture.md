# System Architecture

This document provides a deep technical overview of the ingestion engine.

## 1. High-Level Overview

The system ingests CSV files, sanitizes content, infers schemas, and stores results securely in MongoDB GridFS.

### Key Components:
- FastAPI (Backend)
- CSV Processor (Schema inference + normalization)
- Sanitization Layer (CSV injection protection)
- MongoDB GridFS (Large file storage)
- Minimal web frontend (HTML + JS)

## 2. Architecture Diagram

(Insert rendered PNG)

## 3. Data Flow

1. User uploads CSV through web client.
2. FastAPI receives an upload request.
3. Sanitization layer validates filename, size, and content.
4. CSV processor:
   - detects delimiter
   - extracts key-value pairs
   - generates schema dynamically
5. Raw file + structured output are stored in MongoDB GridFS.
6. API exposes metadata for listing, searching, and downloading.

## 4. MongoDB Design

- `fs.files`: raw CSV file metadata
- `fs.chunks`: file binary content
- `processed_files`: structured table results

Indexes:
- `filename`
- `upload_date`

## 5. Security Considerations

- CSV injection filtering
- 50MB upload limit
- LGPD-compliant: no third-party services
- Sanitized logs
- Strict Content-Type checks

### 2. `docs/architecture.md`

This file explains "How it works" under the hood.

```markdown
# 🏗️ System Architecture

The CSV Schema Evolution Engine is built on a **Clean Architecture** principle, ensuring separation of concerns between the API, business logic, and infrastructure.

[attachment_0](attachment)

## Layer Breakdown

### 1. Presentation Layer (`app/api`)
- **Responsibility:** Handles HTTP requests, validates input using Pydantic models, and formats responses.
- **Key Components:** `FastAPI` routers, `Pydantic` schemas.

### 2. Service Layer (`app/services`)
- **Responsibility:** Contains the core business logic. It does not know about the database or the HTTP transport.
- **Key Components:**
  - **`csv_handler.py`**: Coordinates parsing and sanitization.
  - **`dialect_detector.py`**: Heuristic engine to guess CSV formats.

### 3. Core Layer (`app/core`)
- **Responsibility:** Cross-cutting concerns like configuration, security, and logging.
- **Key Components:**
  - `config.py`: Environment variable management.
  - `security.py`: Encryption/Decryption wrappers.
  - `middleware.py`: Request logging and correlation IDs.

### 4. Infrastructure/Utils Layer (`app/utils`, `app/db`)
- **Responsibility:** Interfaces with external systems (MongoDB, File System).
- **Key Components:**
  - `storage.py`: Handles GridFS chunking and encryption.
  - `mongo.py`: Async MongoDB client (Motor).

## Data Flow

1.  **Ingestion:** Request hits `POST /upload`. Middleware assigns a `Request-ID`.
2.  **Validation:** Validator checks file extension (`.csv`) and MIME type.
3.  **Processing:**
    * File is read into memory (if small) or streamed.
    * `DialectDetector` samples the first 8KB.
    * `csv_handler` parses rows using the detected dialect.
    * `sanitize_cell_value` cleans potential formula injections.
4.  **Storage:**
    * Content is encrypted using `Fernet` (AES).
    * Encrypted blobs are written to MongoDB GridFS.
    * Metadata is written to the `files` collection.
