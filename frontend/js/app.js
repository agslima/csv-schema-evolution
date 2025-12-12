/**
 * Main Application Logic
 */
const app = {
    init() {
        this.cacheDOM();
        this.bindEvents();
        this.loadFiles();
        // Auto-refresh every 10 seconds to check for status updates
        setInterval(() => this.loadFiles(), 10000); 
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
        this.showAlert(null); // Clear alerts

        try {
            await API.uploadFile(file, idField);
            this.showAlert("File uploaded successfully!", "success");
            this.uploadForm.reset();
            this.loadFiles(); // Refresh list immediately
        } catch (error) {
            console.error(error);
            this.showAlert(`Error: ${error.message}`, "danger");
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
        if (files.length === 0) {
            this.tableBody.innerHTML = `<tr><td colspan="6" class="text-center text-muted">No files found.</td></tr>`;
            return;
        }

        const html = files.map(file => {
            // Badges for status
            let badgeClass = "bg-secondary";
            if (file.status === "processed") badgeClass = "bg-success";
            if (file.status === "error") badgeClass = "bg-danger";
            if (file.status === "pending") badgeClass = "bg-warning text-dark";

            // Format fields list (truncate if too long)
            const fieldsStr = file.fields.slice(0, 5).join(", ") + (file.fields.length > 5 ? "..." : "");

            return `
                <tr>
                    <td class="fw-bold">${file.filename}</td>
                    <td class="small text-muted">${new Date().toLocaleDateString()}</td> 
                    <td><span class="badge ${badgeClass}">${file.status.toUpperCase()}</span></td>
                    <td>${file.records_count.toLocaleString()}</td>
                    <td class="small text-muted" title="${file.fields.join(", ")}">${fieldsStr}</td>
                    <td>
                        <div class="btn-group btn-group-sm">
                            <a href="${API.getDownloadUrl(file.id)}" class="btn btn-outline-primary" target="_blank">Download</a>
                            <button class="btn btn-outline-danger" onclick="app.deleteFile('${file.id}')">Delete</button>
                        </div>
                    </td>
                </tr>
            `;
        }).join("");

        this.tableBody.innerHTML = html;
    },

    async deleteFile(id) {
        if(!confirm("Are you sure you want to delete this file?")) return;
        
        try {
            await API.deleteFile(id);
            this.loadFiles();
        } catch (error) {
            alert(error.message);
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

// Expose app to global scope so inline onclicks works (like in delete button)
window.app = app;

// Initialize when DOM is ready
document.addEventListener("DOMContentLoaded", () => app.init());