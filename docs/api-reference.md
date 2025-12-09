# API Reference (v1)

Base URL: http://localhost:8000/api/v1/

---

## POST /files/upload
Upload a CSV file.

### Request

```bash
curl -X POST
-F "file=@data.csv"
http://localhost:8000/api/v1/files/upload
```

### Responses:
- 200 OK – file processed
- 400 – invalid file
- 413 – file too large
- 422 – CSV injection risk detected

---

## GET /files/
List uploaded files with metadata.

---

## GET /files/{id}/download
Download processed CSV file.

---

## DELETE /files/{id}
Remove file from GridFS.

---

## GET /health
API health status.
