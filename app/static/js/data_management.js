const uploadForm = document.getElementById("uploadForm");
const fileInput = document.getElementById("fileInput");
const filesTable = document.getElementById("filesTable");
const refreshBtn = document.getElementById("refreshBtn");
const toast = document.getElementById("toast");

function bytesToSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function showToast(text, timeout = 2800) {
  toast.textContent = text;
  toast.hidden = false;
  setTimeout(() => {
    toast.hidden = true;
  }, timeout);
}

async function fetchFiles() {
  const res = await fetch("/api/files");
  if (!res.ok) throw new Error("Failed to fetch files");
  return res.json();
}

function buildRow(doc) {
  const tr = document.createElement("tr");

  const created = new Date(doc.created_at).toLocaleString();

  tr.innerHTML = `
    <td>${doc.original_name}</td>
    <td>${doc.file_type.toUpperCase()}</td>
    <td>${bytesToSize(doc.size_bytes)}</td>
    <td>${doc.chunk_count}</td>
    <td>${created}</td>
    <td class="actions">
      <button class="secondary" data-action="replace" data-id="${doc.id}">Replace</button>
      <button data-action="delete" data-id="${doc.id}">Delete</button>
      <input class="inline-input" type="file" accept=".pdf,.docx,.txt" data-input="${doc.id}" />
    </td>
  `;

  return tr;
}

async function renderFiles() {
  filesTable.innerHTML = "";
  const docs = await fetchFiles();
  if (!docs.length) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td colspan="6">No indexed files yet.</td>`;
    filesTable.appendChild(tr);
    return;
  }

  docs.forEach((doc) => filesTable.appendChild(buildRow(doc)));
}

async function uploadFiles(files) {
  const fd = new FormData();
  for (const file of files) fd.append("files", file);

  const res = await fetch("/api/files", { method: "POST", body: fd });
  const payload = await res.json();
  if (!res.ok) {
    throw new Error(payload.detail || "Upload failed");
  }

  const indexed = payload.indexed?.length || 0;
  const failed = payload.failed?.length || 0;
  showToast(`Indexed: ${indexed}, Failed: ${failed}`);
}

async function deleteFile(documentId) {
  const res = await fetch(`/api/files/${documentId}`, { method: "DELETE" });
  if (!res.ok) {
    const payload = await res.json();
    throw new Error(payload.detail || "Delete failed");
  }
  showToast("Document deleted");
}

async function replaceFile(documentId, file) {
  const fd = new FormData();
  fd.append("file", file);

  const res = await fetch(`/api/files/${documentId}`, { method: "PUT", body: fd });
  if (!res.ok) {
    const payload = await res.json();
    throw new Error(payload.detail || "Replace failed");
  }
  showToast("Document replaced and re-indexed");
}

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!fileInput.files?.length) {
    showToast("Choose at least one file");
    return;
  }

  try {
    await uploadFiles(fileInput.files);
    fileInput.value = "";
    await renderFiles();
  } catch (error) {
    showToast(error.message || "Upload failed");
  }
});

refreshBtn.addEventListener("click", async () => {
  try {
    await renderFiles();
  } catch (error) {
    showToast("Unable to refresh files");
  }
});

filesTable.addEventListener("click", async (event) => {
  const target = event.target;
  if (!(target instanceof HTMLButtonElement)) return;

  const action = target.dataset.action;
  const id = target.dataset.id;
  if (!action || !id) return;

  try {
    if (action === "delete") {
      if (!window.confirm("Delete this document and its vectors?")) return;
      await deleteFile(id);
      await renderFiles();
      return;
    }

    if (action === "replace") {
      const input = document.querySelector(`input[data-input='${id}']`);
      if (!(input instanceof HTMLInputElement)) return;
      input.click();
      input.onchange = async () => {
        const file = input.files?.[0];
        if (!file) return;
        try {
          await replaceFile(id, file);
          await renderFiles();
        } catch (error) {
          showToast(error.message || "Replace failed");
        } finally {
          input.value = "";
        }
      };
    }
  } catch (error) {
    showToast(error.message || "Action failed");
  }
});

renderFiles().catch(() => showToast("Unable to load documents"));
