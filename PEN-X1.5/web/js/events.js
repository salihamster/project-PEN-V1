// ========================================
// EVENT HANDLERS
// ========================================

import { els } from './dom.js';
import { sendMessage, handleResetChat, handleSleepCycle, exportChat } from './chat.js';
import { toggleToolsPanel } from './tools.js';
import { setShowToolOutput, setExpandAllTools, showToolOutput, expandAllTools, setHistorySidebarOpen, historySidebarOpen } from './state.js';

export function bindEvents() {
  els.sendBtn.addEventListener("click", sendMessage);
  els.messageInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  document.querySelectorAll(".suggestion-chip").forEach((btn) => {
    btn.addEventListener("click", () => {
      const text = btn.getAttribute("data-text") || "";
      els.messageInput.value = text;
      sendMessage();
    });
  });

  if (els.toolOutputToggle) {
    els.toolOutputToggle.addEventListener("click", () => {
      setShowToolOutput(!showToolOutput);
      setExpandAllTools(showToolOutput);
      els.toolOutputToggle.classList.toggle("active", expandAllTools);
      els.toolOutputToggle.title = expandAllTools 
        ? "Hide details" 
        : "Show details";

      const containers = els.toolsBody?.querySelectorAll('.tool-details-container');
      if (containers) {
        containers.forEach((el) => {
          el.style.display = expandAllTools ? 'block' : 'none';
        });
      }
    });
  }

  els.messageInput.addEventListener("input", () => {
    els.messageInput.style.height = "auto";
    els.messageInput.style.height = `${Math.min(els.messageInput.scrollHeight, 140)}px`;
  });
  
  if (els.toolsPanelToggle) {
    els.toolsPanelToggle.addEventListener("click", () => {
      toggleToolsPanel();
    });
  }
  
  if (els.closePanelBtn) {
    els.closePanelBtn.addEventListener("click", () => {
      toggleToolsPanel();
    });
  }
  
  document.addEventListener("click", async (e) => {
    const { toolsPanelCollapsed } = await import('./state.js');
    if (toolsPanelCollapsed) return;
    
    const panel = els.toolsPanel;
    const toggleBtn = els.toolsPanelToggle;
    const closeBtn = els.closePanelBtn;
    
    if (panel && !panel.contains(e.target) && 
        toggleBtn && !toggleBtn.contains(e.target) &&
        closeBtn && !closeBtn.contains(e.target)) {
      toggleToolsPanel();
    }
  });
  
  setupChatMenu();
  setupHistorySidebar();
  
  if (els.exportChatBtn) {
    els.exportChatBtn.addEventListener("click", exportChat);
  }
}

function setupChatMenu() {
  if (!els.chatMenuBtn || !els.chatMenuDropdown) return;
  
  els.chatMenuBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    const isOpen = els.chatMenuDropdown.classList.contains("open");
    
    if (isOpen) {
      closeChatMenu();
    } else {
      openChatMenu();
    }
  });
  
  document.addEventListener("click", (e) => {
    if (!els.chatMenuDropdown.contains(e.target) && !els.chatMenuBtn.contains(e.target)) {
      closeChatMenu();
    }
  });
  
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      closeChatMenu();
    }
  });
  
  if (els.menuSleepBtn) {
    els.menuSleepBtn.addEventListener("click", async () => {
      closeChatMenu();
      await handleSleepCycle();
    });
  }
  
  if (els.menuResetBtn) {
    els.menuResetBtn.addEventListener("click", async () => {
      closeChatMenu();
      await handleResetChat();
    });
  }
}

function openChatMenu() {
  els.chatMenuDropdown.classList.add("open");
}

function closeChatMenu() {
  els.chatMenuDropdown.classList.remove("open");
}

function setupHistorySidebar() {
  if (els.sidebarToggle) {
    els.sidebarToggle.addEventListener("click", toggleHistorySidebar);
  }
  
  if (els.sidebarCloseBtn) {
    els.sidebarCloseBtn.addEventListener("click", toggleHistorySidebar);
  }
  
  if (els.historySearchInput) {
    els.historySearchInput.addEventListener("input", async (e) => {
      const { filterSessions } = await import('./history.js');
      filterSessions(e.target.value);
    });
  }
  
  document.addEventListener("click", (e) => {
    if (!historySidebarOpen) return;
    
    const sidebar = els.historySidebar;
    const toggleBtn = els.sidebarToggle;
    
    if (sidebar && !sidebar.contains(e.target) && toggleBtn && !toggleBtn.contains(e.target)) {
      toggleHistorySidebar();
    }
  });
}

async function toggleHistorySidebar() {
  setHistorySidebarOpen(!historySidebarOpen);
  
  if (els.mainContent) {
    els.mainContent.classList.toggle("sidebar-open", historySidebarOpen);
  }
  
  // Close artifact panel when sidebar opens
  if (historySidebarOpen) {
    const { setArtifactPanelOpen } = await import('./artifact.js');
    setArtifactPanelOpen(false);
    
    const { loadArchivedSessions } = await import('./history.js');
    loadArchivedSessions();
  }
}
