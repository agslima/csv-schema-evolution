/**
 * Main Application Logic
 */
const app = {
    init() {
        this.cacheDOM();
        this.bindEvents();
        this.loadFiles();
        setInterval(() => this.loadFiles(), 10000); 
    },

    // --- SECURITY FIX: HTML Escaping Utility ---
    escapeHtml(unsafe) {
        if (unsafe === null || unsafe === undefined) return "";
        return String(unsafe)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    },

    cacheDOM() {
        this.uploadForm = document.getElementById("uploadForm");
        this.fileInput = document.getElementById("csvFile");
        this.idInput = document.getElementById("idField");
        this.uploadBtn = document.getElementById("uploadBtn");
        this.spinner = this.uploadBtn.querySelector(".spinner-border");
        this.tableBody = document.getElementById("filesTableBody");
        this.alertArea = document.getElementById("alertArea");
    },

    bindEvents() {
        this.uploadForm.addEventListener("submit", (e) => this.handleUpload(e));
    },

    async handleUpload(e) {
        e.preventDefault();
        const file = this.fileInput.files[0];
        const idField = this.idInput.value.trim();

        if (!file) return;

        this.setLoading(true);
        this.showAlert(null);

        try {
            await API.uploadFile(file, idField);
            this.showAlert("File uploaded successfully!", "success");
            this.uploadForm.reset();
            this.loadFiles();
        } catch (error) {
            console.error(error);
            this.showAlert(`Error: ${this.escapeHtml(error.message)}`, "danger");
        } finally {
            this.setLoading(false);
        }
    },

    async loadFiles() {
        try {
            const files = await API.listFiles();
            this.renderTable(files);
        } catch (error) {
            console.error("Failed to load files", error);
        }
    },

    renderTable(files) {
        if (!files || files.length === 0) {
            this.tableBody.innerHTML = `<tr><td colspan="6" class="text-center text-muted">No files found.</td></tr>`;
            return;
        }

        const html = files.map(file => {
            let badgeClass = "bg-secondary";
            if (file.status === "processed") badgeClass = "bg-success";
            if (file.status === "error") badgeClass = "bg-danger";
            if (file.status === "pending") badgeClass = "bg-warning text-dark";

            const fieldsList = file.fields || [];
            
            const safeFields = fieldsList.map(f => this.escapeHtml(f)); 
            const fieldsStr = safeFields.slice(0, 5).join(", ") + (safeFields.length > 5 ? "..." : "");

            const dateStr = file.created_at 
                ? new Date(file.created_at).toLocaleString() 
                : "Just now";
            
            // --- SECURITY FIX: Sanitizing Variables ---
            const safeFilename = this.escapeHtml(file.filename);
            const safeStatus = this.escapeHtml(file.status || 'unknown').toUpperCase();
            const safeId = this.escapeHtml(file.id);

            return `
                <tr>
                    <td class="fw-bold">${safeFilename}</td>
                    <td class="small text-muted">${dateStr}</td> 
                    <td><span class="badge ${badgeClass}">${safeStatus}</span></td>
                    <td>${(file.records_count || 0).toLocaleString()}</td>
                    <td class="small text-muted" title="${safeFields.join(", ")}">${fieldsStr}</td>
                    <td>
                        <div class="btn-group btn-group-sm">
                            <a href="${API.getDownloadUrl(safeId)}" class="btn btn-outline-primary" target="_blank">Download</a>
                            
                            <button class="btn btn-outline-danger" onclick="app.deleteFile('${safeId}')">Delete</button>
                        </div>
                    </td>
                </tr>
            `;
        }).join("");

        this.tableBody.innerHTML = html;
    },

    async handleDownload(id, filename) {
        try {
            await API.downloadFile(id, filename);
        } catch (error) {
            this.showAlert(`Download failed: ${error.message}`, "danger");
        }
    },
    
    async deleteFile(id) {
        if(!confirm("Are you sure you want to delete this file?")) return;
        
        try {
            await API.deleteFile(id);
            this.loadFiles();
        } catch (error) {
            alert(this.escapeHtml(error.message));
        }
    },

    setLoading(isLoading) {
        this.uploadBtn.disabled = isLoading;
        if (isLoading) {
            this.spinner.classList.remove("d-none");
            this.uploadBtn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Uploading...`;
        } else {
            this.spinner.classList.add("d-none");
            this.uploadBtn.innerText = "Upload & Process";
        }
    },

    showAlert(message, type = "success") {
        if (!message) {
            this.alertArea.innerHTML = "";
            return;
        }
        
        this.alertArea.innerHTML = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message} 
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
    }
};

window.app = app;
document.addEventListener("DOMContentLoaded", () => app.init());