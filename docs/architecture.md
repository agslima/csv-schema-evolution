# System Architecture 🏗️

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

## Design Tradeoffs

- MongoDB + GridFS was chosen over S3 to avoid external dependencies and keep data fully controlled.
- Fernet was chosen for simplicity and correctness over implementing custom crypto.
- Dialect detection samples only 8KB to balance accuracy and performance.

## MongoDB Design

- `fs.files`: raw CSV file metadata
- `fs.chunks`: file binary content
- `processed_files`: structured table results

Indexes:
- `filename`
- `upload_date`
