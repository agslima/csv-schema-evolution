/**
 * API Abstraction Layer
 * Handles communication with the FastAPI Backend
 */
// const API_BASE_URL = "http://localhost:8000/api/v1";

const API_BASE_URL = "/api/v1";

const API = {
    async uploadFile(file, idField = null) {
        const formData = new FormData();
        formData.append("file", file);
        
        // Construct URL with query param if idField exists
        let url = `${API_BASE_URL}/files/upload`;
        if (idField) {
            url += `?id_field=${encodeURIComponent(idField)}`;
        }

        const response = await fetch(url, {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Upload failed");
        }
        return response.json();
    },

    async listFiles() {
        const response = await fetch(`${API_BASE_URL}/files/`);
        if (!response.ok) throw new Error("Failed to fetch files");
        return response.json();
    },

    async deleteFile(fileId) {
        const response = await fetch(`${API_BASE_URL}/files/${fileId}`, {
            method: "DELETE"
        });
        if (!response.ok) throw new Error("Failed to delete file");
        return response.json();
    },
    
    getDownloadUrl(fileId) {
        return `${API_BASE_URL}/files/${fileId}/download`;
    }
};