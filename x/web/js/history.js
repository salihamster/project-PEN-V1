// ========================================
// HISTORY & ARCHIVED SESSIONS
// ========================================

import { els } from './dom.js';
import { cachedSessions, viewingArchivedSession, setCachedSessions, setViewingArchivedSession } from './state.js';
import { loadArchivedSessionsAPI, loadArchivedSessionAPI } from './api.js';
import { formatSessionTime, groupSessionsByDate, renderMarkup } from './utils.js';
import { highlightCodeBlocks } from './messages.js';

export async function loadArchivedSessions() {
  if (!els.historyList) return;
  
  try {
    const data = await loadArchivedSessionsAPI();
    setCachedSessions(data.sessions || []);
    
    renderSessionList(cachedSessions);
  } catch (err) {
    console.error("Could not load archived sessions:", err);
  }
}

function renderSessionList(sessions) {
  els.historyList.innerHTML = "";
  
  if (sessions.length === 0) {
    if (els.historyEmpty) {
      els.historyEmpty.style.display = "flex";
      els.historyList.appendChild(els.historyEmpty);
    }
    return;
  }
  
  if (els.historyEmpty) {
    els.historyEmpty.style.display = "none";
  }
  
  const groups = groupSessionsByDate(sessions);
  
  Object.keys(groups).forEach(groupKey => {
    const groupDiv = document.createElement("div");
    groupDiv.className = "history-date-group";
    
    const titleDiv = document.createElement("div");
    titleDiv.className = "history-date-title";
    titleDiv.textContent = groupKey;
    groupDiv.appendChild(titleDiv);
    
    groups[groupKey].forEach(session => {
      const item = createHistoryItem(session);
      groupDiv.appendChild(item);
    });
    
    els.historyList.appendChild(groupDiv);
  });
}

function createHistoryItem(session) {
  const item = document.createElement("div");
  item.className = "history-item";
  item.dataset.sessionId = session.session_id;
  
  const icon = document.createElement("i");
  icon.className = "history-item-icon fas fa-comment";
  
  const content = document.createElement("div");
  content.className = "history-item-content";
  
  const title = document.createElement("div");
  title.className = "history-item-title";
  title.textContent = session.summary || "Sohbet";
  
  const date = document.createElement("div");
  date.className = "history-item-date";
  date.textContent = formatSessionTime(session.archived_at);
  
  content.appendChild(title);
  content.appendChild(date);
  item.appendChild(icon);
  item.appendChild(content);
  
  item.addEventListener("click", () => loadArchivedSession(session.session_id));
  
  return item;
}

export function filterSessions(query) {
  if (!query.trim()) {
    renderSessionList(cachedSessions);
    return;
  }
  
  const lowerQuery = query.toLowerCase();
  const filtered = cachedSessions.filter(session => {
    const summary = (session.summary || "").toLowerCase();
    return summary.includes(lowerQuery);
  });
  
  renderSessionList(filtered);
}

async function loadArchivedSession(sessionId) {
  try {
    const data = await loadArchivedSessionAPI(sessionId);
    const messages = data.messages || [];
    
    setViewingArchivedSession(sessionId);
    
    const titleEl = document.getElementById("archivedChatTitle");
    if (titleEl) {
      titleEl.textContent = data.summary || "Eski Sohbet";
    }
    
    const archivedMessages = document.getElementById("archivedMessages");
    if (archivedMessages) {
      archivedMessages.innerHTML = "";
      messages.forEach(msg => {
        const msgEl = createArchivedMessageEl(msg.role, msg.content, msg.timestamp);
        archivedMessages.appendChild(msgEl);
      });
    }
    
    renderArchivedHistoryList();
    
    openArchivedPage();
    
  } catch (err) {
    console.error("Could not load archived session:", err);
  }
}

function createArchivedMessageEl(role, content, timestamp) {
  const msg = document.createElement("div");
  msg.className = `message ${role} no-animate complete`;
  
  if (role !== "system") {
    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.textContent = role === "user" ? "S" : "P";
    msg.appendChild(avatar);
  }
  
  const wrapper = document.createElement("div");
  wrapper.className = "message-wrapper";
  
  const body = document.createElement("div");
  body.className = "message-content";
  body.innerHTML = renderMarkup(content);
  wrapper.appendChild(body);
  msg.appendChild(wrapper);
  
  // Apply syntax highlighting and copy buttons
  highlightCodeBlocks(body);
  
  return msg;
}

function openArchivedPage() {
  const appEl = document.querySelector(".app");
  const archivedPage = document.getElementById("archivedChatPage");
  
  if (appEl) appEl.classList.add("archived-open");
  if (archivedPage) archivedPage.classList.add("open");
}

export function closeArchivedPage() {
  const appEl = document.querySelector(".app");
  const archivedPage = document.getElementById("archivedChatPage");
  
  if (appEl) appEl.classList.remove("archived-open");
  if (archivedPage) archivedPage.classList.remove("open");
  
  setViewingArchivedSession(null);
}

function renderArchivedHistoryList() {
  const listEl = document.getElementById("archivedHistoryList");
  if (!listEl || !cachedSessions.length) return;
  
  listEl.innerHTML = "";
  const groups = groupSessionsByDate(cachedSessions);
  
  Object.keys(groups).forEach(groupKey => {
    const groupDiv = document.createElement("div");
    groupDiv.className = "history-date-group";
    
    const titleDiv = document.createElement("div");
    titleDiv.className = "history-date-title";
    titleDiv.textContent = groupKey;
    groupDiv.appendChild(titleDiv);
    
    groups[groupKey].forEach(session => {
      const item = document.createElement("div");
      item.className = "history-item";
      if (session.session_id === viewingArchivedSession) {
        item.classList.add("active");
      }
      
      const icon = document.createElement("i");
      icon.className = "history-item-icon fas fa-comment";
      
      const content = document.createElement("div");
      content.className = "history-item-content";
      
      const title = document.createElement("div");
      title.className = "history-item-title";
      title.textContent = session.summary || "Sohbet";
      
      const date = document.createElement("div");
      date.className = "history-item-date";
      date.textContent = formatSessionTime(session.archived_at);
      
      content.appendChild(title);
      content.appendChild(date);
      item.appendChild(icon);
      item.appendChild(content);
      
      item.addEventListener("click", () => loadArchivedSession(session.session_id));
      groupDiv.appendChild(item);
    });
    
    listEl.appendChild(groupDiv);
  });
}

export function setupArchivedPage() {
  const backBtn = document.getElementById("archivedBackBtn");
  if (backBtn) {
    backBtn.addEventListener("click", closeArchivedPage);
  }
  
  const logoBtn = document.getElementById("archivedLogoBtn");
  if (logoBtn) {
    logoBtn.addEventListener("click", closeArchivedPage);
  }
  
  const searchInput = document.getElementById("archivedHistorySearch");
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      filterArchivedSessions(e.target.value);
    });
  }
}

function filterArchivedSessions(query) {
  if (!query.trim()) {
    renderArchivedHistoryList();
    return;
  }
  
  const lowerQuery = query.toLowerCase();
  const filtered = cachedSessions.filter(session => {
    const summary = (session.summary || "").toLowerCase();
    return summary.includes(lowerQuery);
  });
  
  renderArchivedHistoryListFiltered(filtered);
}

function renderArchivedHistoryListFiltered(sessions) {
  const listEl = document.getElementById("archivedHistoryList");
  if (!listEl) return;
  
  listEl.innerHTML = "";
  
  if (sessions.length === 0) {
    listEl.innerHTML = '<div class="history-empty"><i class="fas fa-search"></i><span>Sonuç bulunamadı</span></div>';
    return;
  }
  
  const groups = groupSessionsByDate(sessions);
  
  Object.keys(groups).forEach(groupKey => {
    const groupDiv = document.createElement("div");
    groupDiv.className = "history-date-group";
    
    const titleDiv = document.createElement("div");
    titleDiv.className = "history-date-title";
    titleDiv.textContent = groupKey;
    groupDiv.appendChild(titleDiv);
    
    groups[groupKey].forEach(session => {
      const item = document.createElement("div");
      item.className = "history-item";
      if (session.session_id === viewingArchivedSession) {
        item.classList.add("active");
      }
      
      const icon = document.createElement("i");
      icon.className = "history-item-icon fas fa-comment";
      
      const content = document.createElement("div");
      content.className = "history-item-content";
      
      const title = document.createElement("div");
      title.className = "history-item-title";
      title.textContent = session.summary || "Sohbet";
      
      const date = document.createElement("div");
      date.className = "history-item-date";
      date.textContent = formatSessionTime(session.archived_at);
      
      content.appendChild(title);
      content.appendChild(date);
      item.appendChild(icon);
      item.appendChild(content);
      
      item.addEventListener("click", () => loadArchivedSession(session.session_id));
      groupDiv.appendChild(item);
    });
    
    listEl.appendChild(groupDiv);
  });
}
