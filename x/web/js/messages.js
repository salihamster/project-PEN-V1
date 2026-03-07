// ========================================
// MESSAGE MANAGEMENT
// ========================================

import { els } from './dom.js';
import { renderMarkup, scrollToBottom, getFileIconClass, formatFileSize } from './utils.js';
import { undoMessageAPI, loadChatHistory, fetchFileContent } from './api.js';
import { setAttachedFiles, attachedFiles } from './state.js';
import { renderAttachedFiles } from './files.js';
import { updateTools } from './tools.js';
import { showArtifact } from './artifact.js';

// Get Font Awesome icon class based on file extension
function getFileIconForExt(ext) {
  const iconMap = {
    'md': 'fa-file-lines',
    'txt': 'fa-file-lines',
    'py': 'fa-file-code',
    'js': 'fa-file-code',
    'jsx': 'fa-file-code',
    'ts': 'fa-file-code',
    'tsx': 'fa-file-code',
    'html': 'fa-file-code',
    'css': 'fa-file-code',
    'json': 'fa-file-code',
    'yaml': 'fa-file-code',
    'yml': 'fa-file-code',
    'xml': 'fa-file-code',
    'sql': 'fa-database',
    'sh': 'fa-file-code',
    'bash': 'fa-file-code',
    'pdf': 'fa-file-pdf',
    'doc': 'fa-file-word',
    'docx': 'fa-file-word',
    'xls': 'fa-file-excel',
    'xlsx': 'fa-file-excel',
    'ppt': 'fa-file-powerpoint',
    'pptx': 'fa-file-powerpoint',
    'zip': 'fa-file-zipper',
    'rar': 'fa-file-zipper',
    'default': 'fa-file'
  };
  return iconMap[ext] || iconMap['default'];
}

export function highlightCodeBlocks(container) {
  // Syntax Highlighting
  if (window.Prism) {
    window.Prism.highlightAllUnder(container);
  }

  // Copy Buttons
  container.querySelectorAll('.copy-code-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.stopPropagation();
      const code = decodeURIComponent(btn.getAttribute('data-code'));
      try {
        await navigator.clipboard.writeText(code);
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-check"></i> Kopyalandı';
        btn.classList.add('copied');
        setTimeout(() => {
          btn.innerHTML = originalText;
          btn.classList.remove('copied');
        }, 2000);
      } catch (err) {
        console.error('Failed to copy code:', err);
      }
    });
  });
}

export function appendMessage(role, content, options = {}) {
  const { timestamp = new Date().toISOString(), animate = true, typewriter = false, files = [], tools = [] } = options;

  if (role === "user" && els.welcomeMessage) {
    els.welcomeMessage.style.display = "none";
  }

  const msg = document.createElement("div");
  msg.className = `message ${role}`;
  
  if (!animate) {
    msg.classList.add("no-animate");
    msg.classList.add("complete");
  }

  if (role !== "system") {
    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.textContent = role === "user" ? "S" : "P";
    msg.appendChild(avatar);
  }

  const wrapper = document.createElement("div");
  wrapper.className = "message-wrapper";

  if (role !== "system") {
    const header = document.createElement("div");
    header.className = "message-header";
    const who = role === "user" ? "You" : "PEN";
    const t = new Date(timestamp).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });
    header.innerHTML = `<span>${who}</span><span class="message-time">${t}</span>`;
    wrapper.appendChild(header);
  }

  // --- ARTIFACT CHIPS ---
  if (role === "assistant" && tools && tools.length > 0) {
    // ... (Artifact code remains same - truncated for brevity in replace tool, but included in full file logic)
    // To avoid complexity in replace, I will keep existing logic if I can match exact block.
    // However, since I'm rewriting appendMessage, I must include it all.
    
    // NOTE: To save context tokens, I will assume the previous 'Artifact Chips' block is correct and just copy it here.
    // But wait, the `replace` tool requires exact match.
    // I will rewrite the whole function.
    
    const chipsContainer = document.createElement("div");
    chipsContainer.className = "artifact-chips";
    let hasChips = false;

    const relevantTools = tools.filter(t => {
        const toolName = t.name || t.tool_name;
        return ['read_file', 'write_to_file', 'replace_in_file', 'write_file', 'create_document', 'update_document', 'append_document', 'create_artifact', 'update_artifact'].includes(toolName);
    });

    relevantTools.forEach(tool => {
        const toolName = tool.name || tool.tool_name;
        const isWrite = ['write_to_file', 'replace_in_file', 'write_file', 'create_document', 'update_document', 'append_document', 'create_artifact', 'update_artifact'].includes(toolName);
        const params = tool.parameters || tool.tool_input || tool.input || tool.args || {};
        const path = params.path || params.file_path || "unknown";
        const fileName = path.split(/[/\\]/).pop();
        const ext = fileName.split('.').pop()?.toLowerCase() || 'default';
        const actionType = isWrite ? (toolName.includes('replace') || toolName.includes('update') ? 'edited' : 'created') : 'read';
        const actionText = actionType === 'created' ? 'Oluşturuldu' : actionType === 'edited' ? 'Düzenlendi' : 'Okundu';
        const iconClass = getFileIconForExt(ext);
        
        const chip = document.createElement("div");
        chip.className = "artifact-chip";
        chip.setAttribute('data-type', ext);
        
        chip.innerHTML = `
            <div class="artifact-chip-icon"><i class="fas ${iconClass}"></i></div>
            <div class="artifact-chip-info">
                <div class="artifact-chip-name">${fileName}</div>
                <div class="artifact-chip-meta">
                    <span class="artifact-chip-badge ${actionType}">${actionText}</span>
                </div>
            </div>
        `;
        
        chip.addEventListener("click", () => {
            showArtifact(path);
        });

        if (isWrite && animate) {
            showArtifact(path);
        }

        chipsContainer.appendChild(chip);
        hasChips = true;
    });

    if (hasChips) {
        wrapper.appendChild(chipsContainer);
    }
  }
  // -------------------------

  if (files && files.length > 0) {
    const filesSection = document.createElement("div");
    filesSection.className = "message-files";
    files.forEach(f => {
      const fileType = f.type || "";
      const iconClass = getFileIconClass(fileType);
      const iconType = fileType.startsWith("image/") ? "image" : "document";
      const chip = document.createElement("div");
      chip.className = "message-file-chip";
      chip.innerHTML = `
        <span class="file-chip-icon ${iconType}"><i class="fas ${iconClass}"></i></span>
        <span class="file-chip-name">${f.name || 'Dosya'}</span>
        <span class="file-chip-size">${f.size ? formatFileSize(f.size) : ''}</span>
      `;
      chip.style.cursor = "pointer";
      chip.addEventListener("click", () => {
        fetchFileContent(f.name, f.type);
      });
      filesSection.appendChild(chip);
    });
    wrapper.appendChild(filesSection);
  }

  const body = document.createElement("div");
  body.className = "message-content";
  
  if (role === "assistant" && typewriter && animate) {
    body.innerHTML = "";
    wrapper.appendChild(body);
    
    msg.appendChild(wrapper);
    els.messagesContent.appendChild(msg);
    scrollToBottom();
    
    typewriterEffect(body, content, msg, wrapper);
    return;
  }
  
  body.innerHTML = renderMarkup(content);
  wrapper.appendChild(body);
  msg.appendChild(wrapper);
  
  // Highlight code blocks immediately for non-typewriter messages
  highlightCodeBlocks(body);

  if (role !== "system") {
    const actionsDiv = document.createElement("div");
    actionsDiv.className = "message-actions";
    
    const copyBtn = document.createElement("button");
    copyBtn.className = "message-action-btn copy-btn";
    copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
    copyBtn.title = "Kopyala";
    copyBtn.addEventListener("click", async (e) => {
      e.stopPropagation();
      try {
        await navigator.clipboard.writeText(content);
        copyBtn.innerHTML = '<i class="fas fa-check"></i>';
        setTimeout(() => (copyBtn.innerHTML = '<i class="fas fa-copy"></i>'), 1000);
      } catch {
        // ignore error
      }
    });
    actionsDiv.appendChild(copyBtn);
    
    if (role === "user") {
      msg._attachedFiles = files || [];
      
      const undoBtn = document.createElement("button");
      undoBtn.className = "message-action-btn undo-btn";
      undoBtn.innerHTML = '<i class="fas fa-undo"></i>';
      undoBtn.title = "Geri al";
      undoBtn.addEventListener("click", async (e) => {
        e.stopPropagation();
        await undoMessage(msg, content, msg._attachedFiles);
      });
      actionsDiv.appendChild(undoBtn);
      msg.classList.add("complete");
    }
    
    wrapper.appendChild(actionsDiv);
  }

  els.messagesContent.appendChild(msg);
  
  requestAnimationFrame(() => {
    scrollToBottom();
  });
  
  if (role === "system" || role === "assistant") {
    msg.classList.add("complete");
  }
}

async function typewriterEffect(element, text, messageEl, wrapperEl) {
  const chars = text.split('');
  let currentText = '';
  let i = 0;
  
  const baseSpeed = 4;
  const variation = 6;
  const pauseChars = ['.', '!', '?'];
  const pauseDuration = 40;
  
  const typeChar = () => {
    if (i >= chars.length) {
      addMessageActions(wrapperEl, text);
      messageEl.classList.add("complete");
      // Highlight code blocks after typing is done
      highlightCodeBlocks(element);
      scrollToBottom();
      return;
    }
    
    const char = chars[i];
    currentText += char;
    element.innerHTML = renderMarkup(currentText);
    i++;
    
    let delay = baseSpeed + Math.random() * variation;
    
    if (pauseChars.includes(char)) {
      delay += pauseDuration;
    }
    
    if (char === ' ') {
      delay = baseSpeed / 2;
    }
    
    if (i % 5 === 0) {
      scrollToBottom();
    }
    
    setTimeout(typeChar, delay);
  };
  
  setTimeout(typeChar, 50);
}

function addMessageActions(wrapperEl, content) {
  const actionsDiv = document.createElement("div");
  actionsDiv.className = "message-actions";
  
  const copyBtn = document.createElement("button");
  copyBtn.className = "message-action-btn copy-btn";
  copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
  copyBtn.title = "Kopyala";
  copyBtn.addEventListener("click", async (e) => {
    e.stopPropagation();
    try {
      await navigator.clipboard.writeText(content);
      copyBtn.innerHTML = '<i class="fas fa-check"></i>';
      setTimeout(() => (copyBtn.innerHTML = '<i class="fas fa-copy"></i>'), 1000);
    } catch {
      // ignore error
    }
  });
  actionsDiv.appendChild(copyBtn);
  
  wrapperEl.appendChild(actionsDiv);
}

async function undoMessage(messageEl, content, savedFiles = []) {
  const allMessages = Array.from(els.messagesContent.querySelectorAll('.message'));
  const messageIndex = allMessages.indexOf(messageEl);
  
  if (messageIndex === -1) {
    console.error("Could not find message in DOM");
    return;
  }
  
  let messagesToRemove = 0;
  for (let i = messageIndex; i < allMessages.length; i++) {
    const msg = allMessages[i];
    if (msg.classList.contains('user') || msg.classList.contains('assistant')) {
      messagesToRemove++;
    }
  }
  
  console.log("Messages to remove:", messagesToRemove);
  
  if (messagesToRemove > 2) {
    const { showConfirmModal } = await import('./utils.js');
    const confirmed = await showConfirmModal(
      "Bu geri alma geri alınamaz. Emin misin?"
    );
    
    if (!confirmed) {
      return;
    }
  }
  
  let l1Index = 0;
  for (let i = 0; i < messageIndex; i++) {
    const msg = allMessages[i];
    if (msg.classList.contains('user') || msg.classList.contains('assistant')) {
      l1Index++;
    }
  }
  
  try {
    const data = await undoMessageAPI(l1Index);
    console.log("Undo result:", data);
    
    for (let i = allMessages.length - 1; i >= messageIndex; i--) {
      allMessages[i].remove();
    }
    
    els.messageInput.value = content;
    els.messageInput.focus();
    
    els.messageInput.dispatchEvent(new Event('input'));
    
    if (savedFiles && savedFiles.length > 0) {
      const restoredFiles = savedFiles.map(f => {
        const blob = new Blob([f.content], { type: f.type });
        const file = new File([blob], f.name, { type: f.type });
        return {
          ...f,
          file: file
        };
      });
      setAttachedFiles(restoredFiles);
      renderAttachedFiles();
    }
    
    try {
      const historyData = await loadChatHistory();
      const tools = historyData.tool_interactions || [];
      updateTools(tools);
    } catch (e) {
      console.error("Could not reload tools:", e);
    }
    
    const remainingMessages = els.messagesContent.querySelectorAll('.message');
    if (remainingMessages.length === 0 && els.welcomeMessage) {
      els.welcomeMessage.style.display = "";
    }
    
    scrollToBottom();
    
  } catch (err) {
    console.error("Undo error:", err);
  }
}

export async function resetChatUI() {
  els.messagesContent.innerHTML = "";
  
  const { createWelcomeMessage } = await import('./utils.js');
  let welcomeEl = els.welcomeMessage;
  if (!welcomeEl || !welcomeEl.parentNode) {
    welcomeEl = createWelcomeMessage();
    els.welcomeMessage = welcomeEl;
  }
  els.messagesContent.appendChild(welcomeEl);
  welcomeEl.style.display = "";
  
  welcomeEl.querySelectorAll(".suggestion-chip").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const text = btn.getAttribute("data-text") || "";
      els.messageInput.value = text;
      const { sendMessage } = await import('./chat.js');
      sendMessage();
    });
  });
  
  if (els.toolsBody) {
    els.toolsBody.innerHTML = "";
    let toolsEmptyEl = els.toolsEmpty;
    if (!toolsEmptyEl || !toolsEmptyEl.parentNode) {
      toolsEmptyEl = document.createElement("div");
      toolsEmptyEl.className = "tools-empty";
      toolsEmptyEl.id = "toolsEmpty";
      toolsEmptyEl.innerHTML = '<i class="fas fa-wrench"></i><span>Henüz araç kullanılmadı</span>';
      els.toolsEmpty = toolsEmptyEl;
    }
    toolsEmptyEl.style.display = "block";
    els.toolsBody.appendChild(toolsEmptyEl);
  }
}
