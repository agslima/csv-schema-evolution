const uploadBtn = document.getElementById("uploadBtn");
const fileInput = document.getElementById("fileInput");
const progressBar = document.getElementById("progressBar");

uploadBtn.addEventListener("click", async () => {
    const file = fileInput.files[0];
    if (!file) return showToast("Please select a file", "error");
    if (!file.name.endsWith(".csv")) return showToast("Only CSV files allowed", "error");
    if (file.size > 50 * 1024 * 1024) return showToast("File too large (max 50MB)", "error");

    const formData = new FormData();
    formData.append("file", file);

    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/v1/files/upload");

    xhr.upload.addEventListener("progress", e => {
        if (e.lengthComputable) {
            const percent = (e.loaded / e.total) * 100;
            progressBar.style.width = percent + "%";
        }
    });

    xhr.onload = () => {
        if (xhr.status === 200 || xhr.status === 201) {
            showToast("File uploaded successfully!");
            fileInput.value = "";
            progressBar.style.width = "0%";
            loadFiles(); // refresh table
        } else {
            showToast("Upload failed: " + xhr.responseText, "error");
        }
    };

    xhr.send(formData);
});
