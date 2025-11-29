const API_BASE = "http://127.0.0.1:8000"; // Backend API endpointi buraya gelecek

let isSending = false;
let lastUserMessageAt = null;
let showToolOutput = true;
let expandAllTools = false; // Controls expanding all tool details in the sidebar

let els = {};

function initializeElements() {
  els = {
    messagesContent: document.getElementById("messagesContent"),
    chatMessages: document.getElementById("chatMessages"),
    welcomeMessage: document.getElementById("welcomeMessage"),
    messageInput: document.getElementById("messageInput"),
    sendBtn: document.getElementById("sendBtn"),
    resetBtn: document.getElementById("resetBtn"),
    toolsBody: document.getElementById("toolsBody"),
    toolsEmpty: document.getElementById("toolsEmpty"),
    toolOutputToggle: document.getElementById("toolOutputToggle"),
  };
  console.log("Elements initialized:", Object.keys(els).filter(k => els[k] !== null).length, "elements found");
}

function appendMessage(role, content, options = {}) {
  const { timestamp = new Date().toISOString(), animate = true } = options;

  if (role === "user" && els.welcomeMessage) {
    els.welcomeMessage.style.display = "none";
  }

  const msg = document.createElement("div");
  msg.className = `message ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.textContent = role === "user" ? "S" : role === "assistant" ? "P" : "!";

  const wrapper = document.createElement("div");
  wrapper.className = "message-wrapper";

  const header = document.createElement("div");
  header.className = "message-header";
  const who = role === "user" ? "Sen" : role === "assistant" ? "PEN" : "Sistem";
  const t = new Date(timestamp).toLocaleTimeString("tr-TR", { hour: "2-digit", minute: "2-digit" });
  header.innerHTML = `<span>${who}</span><span class="message-time">${t}</span>`;

  const body = document.createElement("div");
  body.className = "message-content";
  body.textContent = content;

  wrapper.appendChild(header);
  wrapper.appendChild(body);

  const copyBtn = document.createElement("button");
  copyBtn.className = "message-copy-btn";
  copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
  copyBtn.addEventListener("click", async (e) => {
    e.stopPropagation();
    try {
      await navigator.clipboard.writeText(content);
      copyBtn.innerHTML = '<i class="fas fa-check"></i>';
      setTimeout(() => (copyBtn.innerHTML = '<i class="fas fa-copy"></i>'), 1000);
    } catch {
      // yoksay
    }
  });

  msg.appendChild(avatar);
  msg.appendChild(wrapper);
  msg.appendChild(copyBtn);

  els.messagesContent.appendChild(msg);
  scrollToBottom();
}

function showTyping() {
  if (document.getElementById("typingIndicator")) return;
  const div = document.createElement("div");
  div.id = "typingIndicator";
  div.className = "typing-indicator";
  div.innerHTML = '<div class="typing-dots"><span></span><span></span><span></span></div>';
  els.messagesContent.appendChild(div);
  scrollToBottom();
}

function hideTyping() {
  const el = document.getElementById("typingIndicator");
  if (el) el.remove();
}

function scrollToBottom() {
  if (!els.messagesContent) return;
  els.messagesContent.scrollTop = els.messagesContent.scrollHeight;
}

function resetChatUI() {
  els.messagesContent.innerHTML = "";
  if (els.welcomeMessage) {
    els.messagesContent.appendChild(els.welcomeMessage);
    els.welcomeMessage.style.display = "";
  }
  if (els.toolsBody) {
    els.toolsBody.innerHTML = "";
    if (els.toolsEmpty) {
      els.toolsEmpty.style.display = "block";
      els.toolsBody.appendChild(els.toolsEmpty);
    }
  }
}

function updateTools(tools) {
  if (!els.toolsBody || !Array.isArray(tools)) return;

  els.toolsBody.innerHTML = "";

  if (tools.length === 0) {
    if (els.toolsEmpty) {
      els.toolsEmpty.style.display = "block";
      els.toolsBody.appendChild(els.toolsEmpty);
    }
    return;
  }

  if (els.toolsEmpty) {
    els.toolsEmpty.style.display = "none";
  }

  tools.forEach((tool) => {
    const item = document.createElement("div");
    item.className = "tool-item";
    item.style.cursor = "pointer";

    const top = document.createElement("div");
    top.className = "tool-top";

    const name = document.createElement("div");
    name.className = "tool-name";
    name.textContent = tool.name || tool.tool_name || tool.tool || "tool";

    const status = document.createElement("div");
    status.className = "tool-status";
    const st = (
      (tool.status || tool.tool_status || (tool.error ? "failed" : "completed") || "")
    ).toLowerCase();
    status.classList.add(st || "running");
    status.textContent =
      st === "completed" ? "Tamamlandı" : st === "failed" ? "Hata" : "Çalışıyor";

    top.appendChild(name);
    top.appendChild(status);

    const meta = document.createElement("div");
    meta.className = "tool-meta";
    const parts = [];
    const duration = tool.duration_ms ?? tool.execution_time_ms;
    if (duration != null) parts.push(`${Math.round(duration)} ms`);
    if (tool.started_at) parts.push(tool.started_at);
    else if (tool.timestamp) parts.push(tool.timestamp);
    if (parts.length) meta.textContent = parts.join(" · ");

    item.appendChild(top);
    if (parts.length) item.appendChild(meta);

    const detailsContainer = document.createElement("div");
    detailsContainer.className = "tool-details-container";
    detailsContainer.style.display = expandAllTools ? "block" : "none";

    const paramsData = tool.parameters ?? tool.tool_input;
    if (paramsData != null) {
      const details = document.createElement("div");
      details.className = "tool-details";
      const title = document.createElement("div");
      title.className = "tool-details-title";
      title.textContent = "Parametreler";
      const pre = document.createElement("pre");
      pre.className = "tool-details-pre";
      try {
        pre.textContent = typeof paramsData === "string" ? paramsData : JSON.stringify(paramsData, null, 2);
      } catch {
        pre.textContent = String(paramsData);
      }
      details.appendChild(title);
      details.appendChild(pre);
      detailsContainer.appendChild(details);
    }

    const resultData = tool.result ?? tool.tool_output;
    if (resultData != null) {
      const details = document.createElement("div");
      details.className = "tool-details";
      const title = document.createElement("div");
      title.className = "tool-details-title";
      title.textContent = "Sonuç";
      const pre = document.createElement("pre");
      pre.className = "tool-details-pre";
      try {
        pre.textContent = typeof resultData === "string" ? resultData : JSON.stringify(resultData, null, 2);
      } catch {
        pre.textContent = String(resultData);
      }
      details.appendChild(title);
      details.appendChild(pre);
      detailsContainer.appendChild(details);
    }

    item.appendChild(detailsContainer);

    // Toggle single item details on click
    item.addEventListener("click", (e) => {
      e.stopPropagation();
      const isHidden = detailsContainer.style.display === "none";
      detailsContainer.style.display = isHidden ? "block" : "none";
    });

    els.toolsBody.appendChild(item);
  });
}

async function sendMessage() {
  if (isSending) return;
  const text = els.messageInput.value.trim();
  if (!text) return;

  isSending = true;
  els.messageInput.value = "";
  els.messageInput.disabled = true;
  els.sendBtn.disabled = true;

  appendMessage("user", text);
  showTyping();

  try {
    const url = new URL(`${API_BASE}/api/pen/chat`);
    url.searchParams.append("show_tool_output", showToolOutput);
    
    const res = await fetch(url.toString(), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });

    if (!res.ok) {
      throw new Error(`Sunucu hatası: ${res.status}`);
    }

    const data = await res.json();
    hideTyping();

    if (data.error) {
      appendMessage("system", data.error);
    } else {
      if (Array.isArray(data.messages)) {
        data.messages.forEach((m) => {
          if (m.role === "assistant" || m.role === "model") {
            appendMessage("assistant", m.content || "");
          }
        });
      } else if (data.reply) {
        appendMessage("assistant", data.reply);
      }

      if (Array.isArray(data.tools)) {
        updateTools(data.tools);
      }
    }
  } catch (err) {
    hideTyping();
    appendMessage("system", `Bağlantı hatası: ${err.message}`);
  } finally {
    isSending = false;
    els.messageInput.disabled = false;
    els.sendBtn.disabled = false;
    els.messageInput.focus();
  }
}

async function loadChatHistory() {
  try {
    console.log("Loading chat history from:", `${API_BASE}/api/pen/history`);
    const res = await fetch(`${API_BASE}/api/pen/history`);
    console.log("History response status:", res.status);
    
    if (!res.ok) throw new Error(`Failed to load history: ${res.status}`);
    
    const data = await res.json();
    console.log("History data received:", data);
    
    const messages = data.messages || [];
    console.log("Messages count:", messages.length);
    
    if (messages.length > 0) {
      // Hide welcome message
      if (els.welcomeMessage) {
        els.welcomeMessage.style.display = "none";
      }
      
      // Load all messages from history
      messages.forEach((msg) => {
        try {
          const role = msg.role || "user";
          const content = msg.content || "";
          const timestamp = msg.timestamp || new Date().toISOString();
          
          console.log(`Loading message: role=${role}, content_length=${content.length}`);
          appendMessage(role, content, { timestamp, animate: false });
        } catch (msgErr) {
          console.error("Error loading individual message:", msgErr, msg);
        }
      });
      
      // Load tool interactions if available
      const tools = data.tool_interactions || [];
      console.log("Tools count:", tools.length);
      if (tools.length > 0) {
        try {
          updateTools(tools);
        } catch (toolErr) {
          console.error("Error updating tools:", toolErr);
        }
      }
      
      // Scroll to bottom after loading all messages
      setTimeout(() => scrollToBottom(), 100);
    } else {
      console.log("No messages in history");
    }
  } catch (err) {
    console.error("Could not load chat history:", err);
    // Continue normally if history fails to load
  }
}

function bindEvents() {
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

  if (els.resetBtn) {
    els.resetBtn.addEventListener("click", async () => {
      resetChatUI();
      try {
        await fetch(`${API_BASE}/api/pen/reset`, { method: "POST" });
      } catch {
        // sessizce geç
      }
    });
  }

  if (els.toolOutputToggle) {
    els.toolOutputToggle.addEventListener("click", () => {
      // Keep original behavior for API call parameter
      showToolOutput = !showToolOutput;
      // Also expand/collapse all tool details in the current UI
      expandAllTools = showToolOutput; // align toggle with expansion state for simplicity
      els.toolOutputToggle.classList.toggle("active", expandAllTools);
      els.toolOutputToggle.title = expandAllTools 
        ? "Ayrıntıları gizle" 
        : "Ayrıntıları göster";

      // Apply to existing rendered items
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
}

async function initializeApp() {
  console.log("DOMContentLoaded event fired");
  initializeElements();
  bindEvents();
  console.log("Events bound, waiting 500ms before loading history...");
  // Wait a bit for the server to be ready
  await new Promise(resolve => setTimeout(resolve, 500));
  await loadChatHistory();
}

window.addEventListener("DOMContentLoaded", initializeApp);
