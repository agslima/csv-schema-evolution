let currentPage = 1;
const pageSize = 5;
let filesData = [];

const filesTable = document.getElementById("filesTable");
const searchInput = document.getElementById("searchInput");
const prevPageBtn = document.getElementById("prevPage");
const nextPageBtn = document.getElementById("nextPage");
const pageInfo = document.getElementById("pageInfo");

searchInput.addEventListener("input", () => {
    currentPage = 1;
    renderTable();
});

prevPageBtn.addEventListener("click", () => {
    if (currentPage > 1) { currentPage--; renderTable(); }
});
nextPageBtn.addEventListener("click", () => {
    if (currentPage * pageSize < filteredFiles().length) { currentPage++; renderTable(); }
});

async function loadFiles() {
    const res = await fetch("/api/v1/files/");
    filesData = await res.json();
    renderTable();
}

function filteredFiles() {
    const q = searchInput.value.toLowerCase();
    return filesData.filter(f => f.filename.toLowerCase().includes(q));
}

function renderTable() {
    const start = (currentPage - 1) * pageSize;
    const pageFiles = filteredFiles().slice(start, start + pageSize);

    filesTable.innerHTML = "";
    pageFiles.forEach(f => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td class="border px-2 py-1">${f.filename}</td>
            <td class="border px-2 py-1">${f.status}</td>
            <td class="border px-2 py-1">${f.records_count}</td>
            <td class="border px-2 py-1">
                <button class="bg-blue-500 text-white px-2 py-1 rounded" onclick="downloadFile('${f.id}','${f.filename}')">Download</button>
                <button class="bg-red-500 text-white px-2 py-1 rounded" onclick="deleteFile('${f.id}')">Delete</button>
            </td>
        `;
        filesTable.appendChild(tr);
    });
    pageInfo.innerText = `Page ${currentPage} of ${Math.ceil(filteredFiles().length / pageSize)}`;
}

function downloadFile(id, filename) {
    fetch(`/api/v1/files/${id}/download`).then(res => res.blob())
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
    });
}

function deleteFile(id) {
    if (!confirm("Are you sure?")) return;
    fetch(`/api/v1/files/${id}`, { method: "DELETE" }).then(res => {
        if (res.ok) {
            showToast("File deleted");
            loadFiles();
        } else {
            showToast("Delete failed", "error");
        }
    });
}

// initial load
loadFiles();
