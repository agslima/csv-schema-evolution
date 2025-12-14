
# Testing Strategy 🧪 

## Test Levels

### 1. Unit Tests (`tests/unit/`)

Focuses on isolated logic. We mock external dependencies (MongoDB, Storage) to test edge cases.

- **Key Focus:** `DialectDetector`, `Sanitization`, `Edge Cases`.
- **Example:** Testing what happens if a CSV has a row with no data.

### 2. Integration Tests (`tests/integration/`)

Focuses on the full HTTP lifecycle. We spin up a test instance of the `FastAPI` app and hit the endpoints using `httpx`.

- **Key Focus:** Upload flow, Download headers, Error handling (404, 400).

## Maintaining 100% Coverage

This project maintains near-100% coverage. 
Certain boilerplate paths (server startup, dependency wiring) are excluded by design.

### Running Tests

```bash
# Run tests and generate report
pytest --cov=app --cov-report=term-missing --cov-config=.coveragerc tests/
