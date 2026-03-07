// ========================================
// FILE ATTACHMENTS
// ========================================

import { els } from './dom.js';
import { MAX_FILES } from './config.js';
import { attachedFiles, setAttachedFiles } from './state.js';
import { getFileIconClass, formatFileSize } from './utils.js';

export function setupFileAttachments() {
  const container = els.inputContainer;
  const input = els.messageInput;
  if (!container || !input) return;
  
  if (els.attachFileBtn && els.fileInput) {
    els.attachFileBtn.addEventListener("click", () => {
      els.fileInput.click();
    });
    
    els.fileInput.addEventListener("change", (e) => {
      if (e.target.files.length > 0) {
        handleFiles(e.target.files);
        e.target.value = "";
      }
    });
  }
  
  container.addEventListener("dragover", (e) => {
    e.preventDefault();
    container.classList.add("drag-over");
  });
  
  container.addEventListener("dragleave", (e) => {
    e.preventDefault();
    container.classList.remove("drag-over");
  });
  
  container.addEventListener("drop", (e) => {
    e.preventDefault();
    container.classList.remove("drag-over");
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFiles(files);
    }
  });
  
  input.addEventListener("paste", (e) => {
    const items = e.clipboardData?.items;
    if (!items) return;
    
    for (const item of items) {
      if (item.type.startsWith("image/")) {
        e.preventDefault();
        const file = item.getAsFile();
        if (file) handleFiles([file]);
        return;
      }
    }
    
    const text = e.clipboardData.getData("text");
    if (text) {
      const wordCount = text.trim().split(/\s+/).length;
      if (wordCount > 500) {
        e.preventDefault();
        const blob = new Blob([text], { type: "text/plain" });
        const file = new File([blob], `yapistirilan-metin-${Date.now()}.txt`, { type: "text/plain" });
        handleFiles([file]);
      }
    }
  });
}

async function handleFiles(files) {
  const remaining = MAX_FILES - attachedFiles.length;
  if (remaining <= 0) {
    alert(`Maksimum ${MAX_FILES} dosya ekleyebilirsiniz.`);
    return;
  }
  
  const filesToAdd = Array.from(files).slice(0, remaining);
  
  const newFiles = [];
  for (const file of filesToAdd) {
    const content = await file.arrayBuffer();
    
    const fileObj = {
      id: `file-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      file: file,
      name: file.name,
      size: file.size,
      type: file.type,
      content: content,
    };
    newFiles.push(fileObj);
  }
  
  setAttachedFiles([...attachedFiles, ...newFiles]);
  
  if (files.length > remaining) {
    alert(`${files.length - remaining} dosya eklenmedi. Maksimum ${MAX_FILES} dosya.`);
  }
  
  renderAttachedFiles();
}

export function renderAttachedFiles() {
  const container = els.attachedFilesContainer;
  if (!container) return;
  
  container.innerHTML = "";
  
  if (attachedFiles.length === 0) {
    container.classList.remove("has-files");
    return;
  }
  
  container.classList.add("has-files");
  
  attachedFiles.forEach(fileObj => {
    const chip = document.createElement("div");
    chip.className = "file-chip";
    chip.dataset.fileId = fileObj.id;
    
    const iconClass = getFileIconClass(fileObj.type);
    const iconType = fileObj.type.startsWith("image/") ? "image" : "document";
    
    chip.innerHTML = `
      <span class="file-chip-icon ${iconType}">
        <i class="fas ${iconClass}"></i>
      </span>
      <span class="file-chip-name" title="${fileObj.name}">${fileObj.name}</span>
      <span class="file-chip-size">${formatFileSize(fileObj.size)}</span>
      <button class="file-chip-remove" title="Kaldir">
        <i class="fas fa-times"></i>
      </button>
    `;
    
    chip.querySelector(".file-chip-remove").addEventListener("click", () => {
      removeAttachedFile(fileObj.id);
    });
    
    container.appendChild(chip);
  });
}

function removeAttachedFile(fileId) {
  setAttachedFiles(attachedFiles.filter(f => f.id !== fileId));
  renderAttachedFiles();
}

export function clearAttachedFiles() {
  setAttachedFiles([]);
  renderAttachedFiles();
}
