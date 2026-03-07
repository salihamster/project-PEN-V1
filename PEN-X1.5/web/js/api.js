// ========================================
// API CALLS
// ========================================

import { API_BASE } from './config.js';
import { showToolOutput, selectedModel } from './state.js';

export async function sendChatMessage(text, files = []) {
  const url = new URL(`${API_BASE}/api/pen/chat`);
  url.searchParams.append("show_tool_output", showToolOutput);
  url.searchParams.append("model", selectedModel);
  
  let res;
  if (files.length > 0) {
    console.log(`Sending ${files.length} files with message`);
    const formData = new FormData();
    formData.append("message", text);
    files.forEach((fileObj, idx) => {
      console.log(`Adding file_${idx}: ${fileObj.name} (${fileObj.size} bytes)`);
      formData.append(`file_${idx}`, fileObj.file);
    });
    res = await fetch(url.toString(), {
      method: "POST",
      body: formData,
    });
  } else {
    res = await fetch(url.toString(), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });
  }

  if (!res.ok) {
    throw new Error(`Server error: ${res.status}`);
  }

  return await res.json();
}

export async function loadChatHistory() {
  const res = await fetch(`${API_BASE}/api/pen/history`);
  if (!res.ok) throw new Error(`Failed to load history: ${res.status}`);
  return await res.json();
}

export async function resetChat() {
  await fetch(`${API_BASE}/api/pen/reset`, { method: "POST" });
}

export async function startSleepCycle() {
  const res = await fetch(`${API_BASE}/api/pen/sleep`, { method: "POST" });
  if (!res.ok) throw new Error(`Failed to start sleep: ${res.status}`);
  return await res.json();
}

export async function undoMessageAPI(messageIndex) {
  const url = new URL(`${API_BASE}/api/pen/undo`);
  url.searchParams.append("message_index", messageIndex);
  const res = await fetch(url.toString(), { method: "POST" });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.message || "Undo failed");
  }
  return await res.json();
}

export async function loadAvailableModelsAPI() {
  const res = await fetch(`${API_BASE}/api/pen/models`);
  if (!res.ok) throw new Error(`Failed to load models: ${res.status}`);
  return await res.json();
}

export async function loadArchivedSessionsAPI() {
  const res = await fetch(`${API_BASE}/api/pen/archived-sessions`);
  if (!res.ok) throw new Error("Failed to load sessions");
  return await res.json();
}

export async function loadArchivedSessionAPI(sessionId) {
  const res = await fetch(`${API_BASE}/api/pen/archived-session/${sessionId}`);
  if (!res.ok) throw new Error("Failed to load session");
  return await res.json();
}

export async function loadSettingsDataAPI() {
  const res = await fetch(`${API_BASE}/api/pen/settings`);
  if (!res.ok) return null;
  return await res.json();
}

export async function loadL4ProfileAPI() {
  const res = await fetch(`${API_BASE}/api/pen/l4-profile`);
  if (!res.ok) throw new Error("Failed to load profile");
  return await res.json();
}

export async function syncDataAPI(source = "all") {
  const url = new URL(`${API_BASE}/api/pen/sync-data`);
  url.searchParams.append("source", source);
  const res = await fetch(url.toString(), { method: "POST" });
  return await res.json();
}

export async function fetchFileContent(fileName, fileType) {
  try {
    // Try to fetch from user_docs
    const url = new URL(`${API_BASE}/api/pen/file-content`);
    url.searchParams.append("name", fileName);
    
    const res = await fetch(url.toString());
    if (!res.ok) {
      throw new Error(`Failed to fetch file: ${res.status}`);
    }
    
    const data = await res.json();
    
    // Show in artifact panel
    const { showArtifact } = await import('./artifact.js');
    showArtifact(fileName, data.content || data.text || "İçerik yüklenemedi.");
    
    return data;
  } catch (error) {
    console.error("Error fetching file content:", error);
    throw error;
  }
}
