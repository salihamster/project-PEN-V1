// ========================================
// ARTIFACT PANEL (CANVAS) - GRID BASED
// ========================================

import { renderMarkup } from './utils.js';

let artifactPanelOpen = false;
let artifactViewMode = 'view'; // 'view' or 'edit'
let currentArtifactContent = '';
let currentArtifactTitle = '';
let currentArtifactPath = '';

export function setupArtifactPanel() {
  const panel = document.getElementById("artifactPanel");
  const closeBtn = document.getElementById("closeArtifactBtn");
  const modeSwitch = document.getElementById("artifactModeSwitch");
  const saveBtn = document.getElementById("artifactSaveBtn");
  
  if (!panel) return;
  
  if (closeBtn) {
    closeBtn.addEventListener("click", () => setArtifactPanelOpen(false));
  }
  
  if (modeSwitch) {
    modeSwitch.addEventListener("change", (e) => toggleArtifactMode(e.target.checked));
  }
  
  if (saveBtn) {
    saveBtn.addEventListener("click", saveArtifact);
  }
}

async function saveArtifact() {
  const statusEl = document.getElementById("artifactStatus");
  const editorEl = document.getElementById("artifactEditor");
  
  // Update content from editor if needed (Editor is always source of truth now)
  if (editorEl) {
    currentArtifactContent = editorEl.value;
  }
  
  console.log('[ARTIFACT SAVE] Saving file:', {
    path: currentArtifactPath,
    contentLength: currentArtifactContent?.length
  });
  
  // Show saving indicator
  if (statusEl) {
    statusEl.textContent = '💾 Kaydediliyor...';
    statusEl.style.color = 'var(--primary)';
  }
  
  // Save to backend
  try {
    const requestBody = {
      path: currentArtifactPath,
      content: currentArtifactContent
    };
    
    const response = await fetch('/api/pen/workspace/write', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestBody)
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const result = await response.json();
    
    if (result.status === 'success') {
      // If view mode is active, re-render to ensure consistency
      if (artifactViewMode === 'view') {
        updateArtifactDisplay();
      }
      
      // Show success feedback
      if (statusEl) {
        statusEl.textContent = '✓ Kaydedildi';
        statusEl.style.color = 'var(--success)';
        updateStatusText(statusEl, currentArtifactContent);
      }
    } else {
      throw new Error(result.message || 'Bilinmeyen hata');
    }
  } catch (error) {
    console.error('Save error:', error);
    if (statusEl) {
      statusEl.textContent = '❌ Hata oluştu';
      statusEl.style.color = 'var(--error)';
    }
    alert('Kaydetme hatası: ' + error.message);
  }
}

function toggleArtifactMode(isViewMode) {
  const contentEl = document.getElementById("artifactContent");
  const editorEl = document.getElementById("artifactEditor");
  const sliderEl = document.getElementById("artifactSlider");
  const modeSwitch = document.getElementById("artifactModeSwitch");
  
  // Update internal state
  artifactViewMode = isViewMode ? 'view' : 'edit';
  
  // Sync checkbox if called programmatically
  if (modeSwitch && modeSwitch.checked !== isViewMode) {
      modeSwitch.checked = isViewMode;
  }
  
  if (isViewMode) {
      // Switching to VIEW mode
      // 1. Get content from editor
      if (editorEl) {
          currentArtifactContent = editorEl.value;
      }
      // 2. Render content
      if (contentEl) {
          contentEl.innerHTML = renderMarkup(currentArtifactContent);
      }
      // 3. Slide to right (view)
      if (sliderEl) {
          sliderEl.classList.add('view-active');
      }
  } else {
      // Switching to EDIT mode
      // 1. Ensure editor has latest content (usually does, but for safety)
      if (editorEl) {
          editorEl.value = currentArtifactContent;
      }
      // 2. Slide to left (edit)
      if (sliderEl) {
          sliderEl.classList.remove('view-active');
      }
  }
}

function updateArtifactDisplay() {
  // Helper to refresh view if needed (e.g. after save)
  const contentEl = document.getElementById("artifactContent");
  if (artifactViewMode === 'view' && contentEl) {
      contentEl.innerHTML = renderMarkup(currentArtifactContent);
  }
}

export function toggleArtifactPanel() {
  setArtifactPanelOpen(!artifactPanelOpen);
}

export function setArtifactPanelOpen(isOpen) {
  artifactPanelOpen = isOpen;
  
  const panel = document.getElementById("artifactPanel");
  const mainContent = document.querySelector(".main-content");
  
  if (isOpen) {
    panel.classList.add("open");
    mainContent.classList.add("artifact-open");
  } else {
    panel.classList.remove("open");
    mainContent.classList.remove("artifact-open");
  }
}

export async function showArtifact(path, initialContent = null, type = "text") {
  console.log('[ARTIFACT] Opening:', path);
  
  currentArtifactPath = path;
  currentArtifactTitle = path.split('/').pop() || path;
  
  const titleEl = document.getElementById("artifactTitle");
  const statusEl = document.getElementById("artifactStatus");
  const contentEl = document.getElementById("artifactContent");
  const editorEl = document.getElementById("artifactEditor");
  const modeSwitch = document.getElementById("artifactModeSwitch");

  if (titleEl) titleEl.textContent = currentArtifactTitle;
  setArtifactPanelOpen(true);
  
  // Show loading state placeholder in both
  if (contentEl) contentEl.innerHTML = '<div style="padding:20px; color:#888;">Yükleniyor...</div>';
  if (editorEl) editorEl.value = "Yükleniyor...";

  try {
    // Always fetch fresh content from backend
    const response = await fetch(`/api/pen/file-content?name=${encodeURIComponent(path)}`);
    const data = await response.json();
    
    if (data.exists) {
        currentArtifactContent = data.content;
    } else {
        // Fallback to initial content if provided (e.g. for new files not yet saved)
        currentArtifactContent = initialContent || data.content || "";
    }
    
    // Set editor content immediately (it's always the source)
    if (editorEl) {
        editorEl.value = currentArtifactContent;
    }
    
    // Auto-detect mode based on extension
    const ext = path.split('.').pop()?.toLowerCase();
    const isMarkdown = ['md', 'markdown', 'txt'].includes(ext);
    
    // Set initial mode
    toggleArtifactMode(isMarkdown);
    
    if (statusEl) {
        updateStatusText(statusEl, currentArtifactContent);
    }

  } catch (err) {
      console.error("Error loading artifact:", err);
      const errorMsg = `Dosya yüklenemedi: ${err.message}`;
      if (contentEl) contentEl.innerHTML = `<div style="color:var(--error); padding:20px;">${errorMsg}</div>`;
      if (editorEl) editorEl.value = errorMsg;
  }
}

function updateStatusText(el, content) {
    if (!content) {
        el.textContent = "Boş dosya";
        return;
    }
    const size = new Blob([content]).size;
    const sizeStr = size < 1024 ? `${size} B` : 
                    size < 1024 * 1024 ? `${(size / 1024).toFixed(1)} KB` : 
                    `${(size / (1024 * 1024)).toFixed(1)} MB`;
    const lines = content.split('\n').length;
    el.textContent = `${lines} satır • ${sizeStr}`;
    el.style.color = '';
    
    setTimeout(() => { el.style.color = ''; }, 2000);
}
