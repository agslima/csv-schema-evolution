# 🔒 Security & Compliance

This application is designed with "Security by Design" principles.

## 1. Encryption at Rest
We do not store plain-text CSVs. All files are encrypted **before** they touch the database.

- **Algorithm:** AES-128 via Fernet (Symmetric Encryption).
- **Key Management:** Keys are loaded from environment variables (`ENCRYPTION_KEY`).
- **Implementation:** `app/core/security.py` handles the byte-level transformation.

## 2. Input Validation
- **Extension Allowlist:** Only `.csv` files are accepted.
- **MIME Type Check:** Content-Type headers are validated against `text/csv` or `application/vnd.ms-excel`.
- **Size Limiting:** The application enforces a strict size limit (Default: 50MB) to prevent Denial of Service (DoS) via memory exhaustion.

## 3. Output Sanitization
As detailed in the Processing Engine, we actively neutralize **Formula Injection** attacks to protect the users who download and open these files in Excel.

## 4. Database Security
- **No SQL Injection:** We use MongoDB (NoSQL) with ODM usage (Motor), effectively eliminating SQL Injection risks.
- **GridFS Isolation:** Binary file data is separated from metadata, allowing for optimized storage policies.

