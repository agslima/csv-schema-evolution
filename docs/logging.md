
# Logging & Observability 📝

The application uses a structured logging approach to ensure every operation is traceable.

## Configuration

​Logging is configured in `app/core/logging.py` and uses the standard Python logging library, making it compatible with aggregators like ELK Stack or Datadog.

## Request Correlation

Middleware is injected to assign a unique **Request ID** to every incoming HTTP request. This ID is passed down to the Service and Storage layers.

**Log Format:**

```text
[INFO] [req_id: 1234-5678] Request started: POST /api/v1/files/upload
[INFO] [req_id: 1234-5678] Detected dialect: Delimiter=',', Quote='"'
[INFO] [req_id: 1234-5678] File encrypted and saved to GridFS. ID: ...
```

## Log Levels

- **​INFO:** Standard business flow events (Upload, Download, Delete).
- **​WARNING:** Fallback events (e.g., "Dialect detection failed, falling back to Excel").
- **​ERROR:** Application crashes, Storage failures, or unhandled exceptions.

```text
[ERROR] [req_id: 1256] Failed to write to GridFS: ConnectionTimeout


