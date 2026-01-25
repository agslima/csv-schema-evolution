/**
 * API Abstraction Layer
 * Handles communication with the FastAPI Backend
 */
// const API_BASE_URL = "http://localhost:8000/api/v1";

const API_BASE_URL = "/api/v1";

const API = {
    async _request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        
        // merge headers (e.g., add Authorization)
        const headers = {
            ...options.headers,
            // "Authorization": "Bearer " + localStorage.getItem("token") // Uncomment if using JWT
        };
        
        const config = {
            ...options,
            headers
        };

        try {
            const response = await fetch(url, config);

            // Handle 401 (Unauthorized) globally
            if (response.status === 401) {
                // redirect to login or refresh token
                window.location.href = "/login"; 
                return;
            }

            if (!response.ok) {
                // Try to parse detailed error from backend, fallback to status text
                let errorMsg = response.statusText;
                try {
                    const data = await response.json();
                    errorMsg = data.detail || errorMsg;
                } catch (e) { /* ignore JSON parse fail */ }
                
                throw new Error(errorMsg);
            }

            // Return JSON by default, or the raw response if needed (for blobs)
            if (options.returnRaw) return response;
            return response.json();

        } catch (error) {
            console.error(`API Call Failed: ${endpoint}`, error);
            throw error; // Re-throw so the UI can show the alert
        }
    },

    async uploadFile(file, idField = null) {
        const formData = new FormData();
        formData.append("file", file);
        
        let query = "";
        if (idField) {
            query = `?id_field=${encodeURIComponent(idField)}`;
        }

        return this._request(`/files/upload${query}`, {
            method: "POST",
            body: formData
            // Note: fetch automatically handles Content-Type for FormData
        });
    },

    async listFiles() {
        return this._request("/files/");
    },

    async deleteFile(fileId) {
        if (!fileId) throw new Error("Missing File ID");
        
        return this._request(`/files/${encodeURIComponent(fileId)}`, {
            method: "DELETE"
        });
    },

    getDownloadUrl(fileId) {
        if (!fileId) throw new Error("Missing File ID");
        return `${API_BASE_URL}/files/${encodeURIComponent(fileId)}/download`;
    },
    
    async downloadFile(fileId, filename) {
        const response = await this._request(`/files/${encodeURIComponent(fileId)}/download`, {
            method: "GET",
            returnRaw: true 
        });

        const blob = await response.blob();
        
        // Create a temporary "Object URL" that points to the data in RAM
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename || "download.csv"; // Force the browser to download
        document.body.appendChild(a); // Required for Firefox
        a.click();
        
        // Cleanup: Release memory
        setTimeout(() => {
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        }, 100);
    }
};
