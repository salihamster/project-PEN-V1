// ========================================
// SETTINGS PAGE
// ========================================

import { els } from './dom.js';
import { setSettingsOpen, settingsOpen } from './state.js';
import { loadSettingsDataAPI, loadL4ProfileAPI, syncDataAPI } from './api.js';

export function setupSettings() {
  if (els.settingsBtn) {
    els.settingsBtn.addEventListener("click", () => {
      openSettings();
      loadSettingsData();
    });
  }
  
  if (els.settingsBackBtn) {
    els.settingsBackBtn.addEventListener("click", closeSettings);
  }
  
  if (els.exportChatBtn) {
    els.exportChatBtn.addEventListener("click", async () => {
      const { exportChat } = await import('./chat.js');
      exportChat();
    });
  }
  
  loadSettings();
  
  if (els.themeSelect) {
    els.themeSelect.addEventListener("change", (e) => {
      setTheme(e.target.value);
      saveSettings();
    });
  }
  
  if (els.fontSizeSelect) {
    els.fontSizeSelect.addEventListener("change", (e) => {
      setFontSize(e.target.value);
      saveSettings();
    });
  }
  
  document.querySelectorAll(".settings-nav-item").forEach(tab => {
    tab.addEventListener("click", () => {
      const tabId = tab.dataset.tab;
      switchSettingsTab(tabId);
    });
  });
  
  const viewL4Btn = document.getElementById("viewL4ProfileBtn");
  if (viewL4Btn) {
    viewL4Btn.addEventListener("click", loadL4Profile);
  }
  
  setupDataSync();
}

function openSettings() {
  setSettingsOpen(true);
  if (els.appContainer) {
    els.appContainer.classList.add("settings-open");
  }
  if (els.settingsPage) {
    els.settingsPage.classList.add("open");
  }
}

function closeSettings() {
  setSettingsOpen(false);
  if (els.appContainer) {
    els.appContainer.classList.remove("settings-open");
  }
  if (els.settingsPage) {
    els.settingsPage.classList.remove("open");
  }
}

function switchSettingsTab(tabId) {
  document.querySelectorAll(".settings-nav-item").forEach(tab => {
    tab.classList.toggle("active", tab.dataset.tab === tabId);
  });
  
  document.querySelectorAll(".settings-panel").forEach(panel => {
    panel.classList.remove("active");
  });
  
  const targetPanel = document.getElementById(`panel${tabId.charAt(0).toUpperCase() + tabId.slice(1)}`);
  if (targetPanel) {
    targetPanel.classList.add("active");
  }
  
  if (tabId === "profile") {
    loadL4Profile();
  }
}

async function loadSettingsData() {
  try {
    const data = await loadSettingsDataAPI();
    if (!data) return;
    
    fillApiKey("inputGeminiKey", data.api_keys?.gemini);
    fillApiKey("inputOpenaiKey", data.api_keys?.openai);
    fillApiKey("inputAnthropicKey", data.api_keys?.anthropic);
    fillApiKey("inputBraveKey", data.api_keys?.brave);
    
    if (data.email_config) {
      const email = data.email_config;
      const emailInput = document.getElementById("inputEmailAddress");
      const serverInput = document.getElementById("inputImapServer");
      const portInput = document.getElementById("inputImapPort");
      if (email.address && emailInput) emailInput.value = email.address;
      if (email.imap_server && serverInput) serverInput.value = email.imap_server;
      if (email.imap_port && portInput) portInput.value = email.imap_port;
    }
    
    const tools = data.tools || {};
    if (document.getElementById("toolWhatsapp")) {
      document.getElementById("toolWhatsapp").checked = tools.whatsapp !== false;
    }
    if (document.getElementById("toolEmail")) {
      document.getElementById("toolEmail").checked = tools.email === true;
    }
    if (document.getElementById("toolDrive")) {
      document.getElementById("toolDrive").checked = tools.drive !== false;
    }
    if (document.getElementById("toolWeb")) {
      document.getElementById("toolWeb").checked = tools.web === true;
    }
    if (document.getElementById("toolMemory")) {
      document.getElementById("toolMemory").checked = tools.memory !== false;
    }
    
    const emailStatus = document.getElementById("emailConfigStatus");
    if (emailStatus && data.email_config) {
      if (data.email_config.configured) {
        emailStatus.textContent = `Yapılandırılmış: ${data.email_config.address}`;
      } else {
        emailStatus.textContent = "Yapılandırılmamış - .env dosyasını kontrol edin";
      }
    }
  } catch (err) {
    console.error("Failed to load settings:", err);
  }
}

function fillApiKey(inputId, keyInfo) {
  const input = document.getElementById(inputId);
  if (!input) return;
  
  if (keyInfo?.configured && keyInfo?.masked) {
    input.value = keyInfo.masked;
    input.dataset.configured = "true";
  } else {
    input.value = "";
    input.dataset.configured = "false";
  }
}

async function loadL4Profile() {
  const box = document.getElementById("l4ProfileBox");
  if (!box) return;
  
  box.innerHTML = '<div class="l4-loading">Yukleniyor...</div>';
  
  try {
    const data = await loadL4ProfileAPI();
    let html = '';
    
    html += `<div class="l4-section-box">`;
    html += `<div class="l4-section-header" onclick="this.parentElement.classList.toggle('open')">`;
    html += `<span class="l4-section-title">Ozet</span>`;
    html += `<i class="fas fa-chevron-down l4-section-icon"></i>`;
    html += `</div>`;
    html += `<div class="l4-section-content">`;
    if (data.summary) {
      html += `<p>${data.summary}</p>`;
    } else {
      html += `<p class="l4-empty">Henuz ozet olusturulmamis.</p>`;
    }
    html += `</div></div>`;
    
    const profile = data.profile || {};
    const categories = [
      { key: "name", label: "Isim" },
      { key: "preferences", label: "Tercihler" },
      { key: "interests", label: "Ilgi Alanlari" },
      { key: "projects", label: "Projeler" },
      { key: "goals", label: "Hedefler" },
      { key: "expertise", label: "Uzmanlik" },
      { key: "relationships", label: "Iliskiler" },
      { key: "habits", label: "Aliskanliklar" }
    ];
    
    categories.forEach(cat => {
      const value = profile[cat.key];
      if (value && (typeof value === "string" ? value : value.length > 0)) {
        const itemCount = Array.isArray(value) ? value.length : 1;
        html += `<div class="l4-section-box">`;
        html += `<div class="l4-section-header" onclick="this.parentElement.classList.toggle('open')">`;
        html += `<span class="l4-section-title">${cat.label}</span>`;
        html += `<span class="l4-section-count">${itemCount}</span>`;
        html += `<i class="fas fa-chevron-down l4-section-icon"></i>`;
        html += `</div>`;
        html += `<div class="l4-section-content">`;
        
        if (Array.isArray(value)) {
          value.forEach(item => {
            html += `<div class="l4-item">${item}</div>`;
          });
        } else {
          html += `<div class="l4-item">${value}</div>`;
        }
        html += `</div></div>`;
      }
    });
    
    box.innerHTML = html;
    
  } catch (err) {
    console.error("Failed to load L4 profile:", err);
    box.innerHTML = '<div class="l4-empty">Profil yuklenemedi.</div>';
  }
}

function loadSettings() {
  const settings = JSON.parse(localStorage.getItem("penSettings") || "{}");
  
  if (settings.theme && els.themeSelect) {
    els.themeSelect.value = settings.theme;
    setTheme(settings.theme);
  }
  
  if (settings.fontSize && els.fontSizeSelect) {
    els.fontSizeSelect.value = settings.fontSize;
    setFontSize(settings.fontSize);
  }
}

function saveSettings() {
  const settings = {
    theme: els.themeSelect?.value || "dark",
    fontSize: els.fontSizeSelect?.value || "medium"
  };
  localStorage.setItem("penSettings", JSON.stringify(settings));
}

function setTheme(theme) {
  document.body.removeAttribute("data-theme");
  if (theme === "light") {
    document.body.setAttribute("data-theme", "light");
  } else if (theme === "system") {
    if (window.matchMedia("(prefers-color-scheme: light)").matches) {
      document.body.setAttribute("data-theme", "light");
    }
  }
}

function setFontSize(size) {
  document.body.removeAttribute("data-font-size");
  if (size !== "medium") {
    document.body.setAttribute("data-font-size", size);
  }
}

function setupDataSync() {
  const syncBtn = document.getElementById("runSyncBtn");
  const whatsappBtn = document.getElementById("runSyncWhatsappBtn");
  const emailBtn = document.getElementById("runSyncEmailBtn");
  const syncStatus = document.getElementById("syncStatus");
  const syncLog = document.getElementById("syncLog");
  
  const handleSync = async (source, btn) => {
    if (!btn || btn.classList.contains("running")) return;
    
    const originalText = btn.innerHTML;
    btn.classList.add("running");
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Isleniyor...';
    
    // Disable other buttons
    [syncBtn, whatsappBtn, emailBtn].forEach(b => {
        if (b && b !== btn) b.disabled = true;
    });
    
    syncStatus.className = "sync-status running";
    syncStatus.textContent = `Veri guncelleniyor (${source === 'all' ? 'Hepsi' : source}), lutfen bekleyin...`;
    
    syncLog.innerHTML = "";
    syncLog.classList.remove("has-content");
    
    try {
      const data = await syncDataAPI(source);
      
      if (data.logs && data.logs.length > 0) {
        syncLog.classList.add("has-content");
        data.logs.forEach(log => {
          const line = document.createElement("div");
          line.className = `log-line ${log.level}`;
          line.textContent = log.message;
          syncLog.appendChild(line);
        });
        syncLog.scrollTop = syncLog.scrollHeight;
      }
      
      if (data.status === "success") {
        syncStatus.className = "sync-status success";
        syncStatus.textContent = `Basarili! ${data.statistics?.whatsapp_chats || 0} sohbet, ${data.statistics?.whatsapp_messages || 0} mesaj, ${data.statistics?.emails || 0} email`;
      } else {
        syncStatus.className = "sync-status error";
        syncStatus.textContent = `Hata: ${data.error || "Bilinmeyen hata"}`;
      }
      
    } catch (err) {
      console.error("Sync error:", err);
      syncStatus.className = "sync-status error";
      syncStatus.textContent = `Baglanti hatasi: ${err.message}`;
    } finally {
      btn.classList.remove("running");
      btn.innerHTML = originalText;
      
      // Enable all buttons
      [syncBtn, whatsappBtn, emailBtn].forEach(b => {
        if (b) b.disabled = false;
      });
    }
  };
  
  if (syncBtn) {
    syncBtn.addEventListener("click", () => handleSync("all", syncBtn));
  }
  
  if (whatsappBtn) {
    whatsappBtn.addEventListener("click", () => handleSync("whatsapp", whatsappBtn));
  }
  
  if (emailBtn) {
    emailBtn.addEventListener("click", () => handleSync("email", emailBtn));
  }

  // Listen for SSE sync logs
  document.addEventListener('pen-sync-log', (e) => {
    const log = e.detail;
    if (!syncLog) return;
    
    syncLog.classList.add("has-content");
    const line = document.createElement("div");
    line.className = `log-line ${log.level}`;
    line.textContent = log.message;
    syncLog.appendChild(line);
    syncLog.scrollTop = syncLog.scrollHeight;
  });
}

// Global function for password visibility toggle
window.togglePasswordVisibility = function(inputId, btn) {
  const input = document.getElementById(inputId);
  if (!input) return;
  
  if (input.type === "password") {
    input.type = "text";
    btn.innerHTML = '<i class="fas fa-eye-slash"></i>';
  } else {
    input.type = "password";
    btn.innerHTML = '<i class="fas fa-eye"></i>';
  }
};
