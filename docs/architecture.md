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
