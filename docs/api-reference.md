# API Reference 📡

Base URL: `http://localhost:8000/api/v1`

## Endpoints

### 1. Upload File
Uploads a CSV file, detects its dialect, sanitizes content, and encrypts it for storage.

- **URL:** `/files/upload`
- **Method:** `POST`
- **Content-Type:** `multipart/form-data`

#### Request Parameters
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `file` | File | Yes | The CSV file to upload. Max size: 50MB. Allowed ext: `.csv` |

#### Success Response (201 Created)
```json
{
  "id": "651a2b3c4d5e6f7g8h9i0j1k",
  "filename": "sales_data.csv",
  "status": "processed",
  "records_count": 1500,
  "fields": ["date", "product_id", "amount", "currency"],
  "created_at": "2023-10-05T14:30:00Z"
}
```

**Error Responses**
​* **400 Bad Request:** Invalid file extension or "Formula Injection" detected.
* ​**413 Payload Too Large:** File exceeds the configured size limit.

### ​2. List Files

​Retrieves a list of all uploaded files and their processing status.

* **​URL:** `/files/`
* **​Method:** `GET`
  
​Success Response (200 OK)

```json
[
  {
    "id": "651a2b3c4d5e6f7g8h9i0j1k",
    "filename": "sales_data.csv",
    "status": "processed",
    "records_count": 1500,
    "fields": ["date", "product_id", "amount"],
    "created_at": "2023-10-05T14:30:00Z"
  }
]
```

### 3. Download File

​Retrieves the original CSV file. The file is decrypted on-the-fly before being streamed to the client.

* **​URL:** `/files/{file_id}/download`
* *"​Method:** `GET`

​Response
* **​Headers:** Content-Disposition: attachment; filename="sales_data.csv"
* **​Body:** Binary stream of the CSV file.

### ​4. Delete File

​Permanently removes the file content (GridFS) and metadata (MongoDB Collection).
* **​URL:** `/files/{file_id}`
​* **Method:** `DELETE`

​Success Response (200 OK)

```json
{
  "message": "File 651a2b3c... deleted successfully"
}
```

Error Response

**404 Not Found:** If the file ID does not exist.
