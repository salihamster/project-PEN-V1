// ========================================
// UTILITY FUNCTIONS
// ========================================

import { els } from './dom.js';

export function scrollToBottom() {
  if (!els.chatMessages) return;
  els.chatMessages.scrollTop = els.chatMessages.scrollHeight;
}

export function scrollToAnchor() {
  if (!els.chatMessages) return;
  const containerHeight = els.chatMessages.clientHeight;
  const scrollHeight = els.chatMessages.scrollHeight;
  const targetScroll = scrollHeight - containerHeight * 0.75;
  els.chatMessages.scrollTop = Math.max(0, targetScroll);
}

export function formatFileSize(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

export function getFileIconClass(mimeType) {
  if (mimeType.startsWith("image/")) return "fa-image";
  if (mimeType.startsWith("video/")) return "fa-video";
  if (mimeType.startsWith("audio/")) return "fa-music";
  if (mimeType.includes("pdf")) return "fa-file-pdf";
  if (mimeType.includes("word") || mimeType.includes("document")) return "fa-file-word";
  if (mimeType.includes("excel") || mimeType.includes("spreadsheet")) return "fa-file-excel";
  if (mimeType.includes("powerpoint") || mimeType.includes("presentation")) return "fa-file-powerpoint";
  if (mimeType.includes("zip") || mimeType.includes("rar") || mimeType.includes("7z")) return "fa-file-archive";
  if (mimeType.includes("text") || mimeType.includes("json") || mimeType.includes("javascript") || mimeType.includes("python")) return "fa-file-code";
  return "fa-file";
}

export function renderMarkup(text) {
  if (!text) return '';
  
  // 1. Extract Code Blocks to placeholders
  const codeBlocks = [];
  let processedText = text.replace(/```(\w*)\n?([\s\S]*?)```/g, (match, lang, code) => {
    const id = `__CODE_BLOCK_${codeBlocks.length}__`;
    codeBlocks.push({
      id: id,
      lang: lang || 'text',
      code: code.trim() // Keep raw code for copy, but trimming ends
    });
    return id;
  });

  let safe = processedText
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  const lines = safe.split(/\r?\n/);
  const processed = [];
  let inList = false;
  let listItems = [];
  let lastWasEmpty = false;
  let inTable = false;
  let tableRows = [];
  
  for (let i = 0; i < lines.length; i++) {
    let line = lines[i];
    let matched = false;
    
    // Restore code blocks if they are on a line by themselves (mostly they are)
    // But since we replaced the whole block with a placeholder, it might be embedded in the text flow if we split by newline
    // Actually, since ``` are multiline, the placeholder replaced the newlines too. 
    // So the placeholder is likely "inline" in our 'safe' string or constitutes a whole 'line' if we split by \n.
    // However, splitting `safe` by newline MIGHT break the placeholder if we didn't handle it right.
    // But `replace` consumed the newlines inside the block. So the placeholder is a single token.
    
    // Check if line contains a code block placeholder
    if (line.trim().startsWith('__CODE_BLOCK_') && line.trim().endsWith('__')) {
       // It's likely purely a code block placeholder
       const match = line.match(/__CODE_BLOCK_(\d+)__/);
       if (match) {
         const index = parseInt(match[1]);
         const block = codeBlocks[index];
         if (block) {
            // Render the code block
            const escapedCode = block.code
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;');
            
            const langClass = block.lang ? `language-${block.lang}` : 'language-text';
            
            processed.push(`
              <div class="code-block-wrapper">
                <div class="code-block-header">
                  <span class="code-lang">${block.lang || 'Code'}</span>
                  <button class="copy-code-btn" data-code="${encodeURIComponent(block.code)}">
                    <i class="fas fa-copy"></i> Kopyala
                  </button>
                </div>
                <pre><code class="${langClass}">${escapedCode}</code></pre>
              </div>
            `);
            matched = true;
            lastWasEmpty = false;
            continue;
         }
       }
    }

    const headerMatch = line.match(/^(#{1,6})\s+(.+)$/);
    if (headerMatch) {
      const level = headerMatch[1].length;
      const content = headerMatch[2];
      processed.push(`<h${level} class="md-heading">${processInline(content)}</h${level}>`);
      matched = true;
      lastWasEmpty = false;
      continue;
    }
    
    const ulMatch = line.match(/^[\s]*[-*]\s+(.+)$/);
    if (ulMatch) {
      if (!inList) {
        inList = 'ul';
        listItems = [];
      }
      if (inList === 'ul') {
        listItems.push(`<li>${processInline(ulMatch[1])}</li>`);
        matched = true;
        lastWasEmpty = false;
        continue;
      }
    }
    
    const olMatch = line.match(/^[\s]*\d+\.\s+(.+)$/);
    if (olMatch) {
      if (!inList) {
        inList = 'ol';
        listItems = [];
      }
      if (inList === 'ol') {
        listItems.push(`<li>${processInline(olMatch[1])}</li>`);
        matched = true;
        lastWasEmpty = false;
        continue;
      }
    }
    
    const quoteMatch = line.match(/^>\s+(.+)$/);
    if (quoteMatch) {
      processed.push(`<blockquote class="md-quote">${processInline(quoteMatch[1])}</blockquote>`);
      matched = true;
      lastWasEmpty = false;
      continue;
    }
    
    if (line.match(/^[-*]{3,}$/)) {
      processed.push('<hr class="md-hr">');
      matched = true;
      lastWasEmpty = false;
      continue;
    }
    
    // Table detection - lines with pipes
    const tableMatch = line.match(/^\s*\|(.+)\|\s*$/);
    if (tableMatch) {
      if (!inTable) {
        inTable = true;
        tableRows = [];
      }
      // Check if this is a separator line (contains dashes and pipes)
      const isSeparator = line.match(/^\s*\|[\s\-:|]+\|\s*$/);
      if (!isSeparator) {
        tableRows.push(line);
      }
      matched = true;
      lastWasEmpty = false;
      continue;
    }
    
    if (inList && !matched) {
      processed.push(`<${inList} class="md-list">${listItems.join('')}</${inList}>`);
      inList = false;
      listItems = [];
    }
    
    if (inTable && !matched) {
      // End of table
      if (tableRows.length > 0) {
        processed.push(renderTable(tableRows));
      }
      inTable = false;
      tableRows = [];
    }
    
    if (!matched) {
      if (line.trim() === '') {
        // Only add empty line if the last one wasn't empty
        if (!lastWasEmpty) {
          processed.push('');
          lastWasEmpty = true;
        }
      } else {
        processed.push(`<p>${processInline(line)}</p>`);
        lastWasEmpty = false;
      }
    }
  }
  
  if (inList) {
    processed.push(`<${inList} class="md-list">${listItems.join('')}</${inList}>`);
  }
  
  return processed.join('');
}

function renderTable(tableRows) {
  if (tableRows.length === 0) return '';
  
  // Parse table rows
  const rows = tableRows.map(row => {
    return row
      .split('|')
      .map(cell => cell.trim())
      .filter(cell => cell.length > 0);
  });
  
  if (rows.length === 0) return '';
  
  let html = '<table class="md-table"><tbody>';
  
  // First row is header
  if (rows.length > 0) {
    html += '<tr class="md-table-header">';
    rows[0].forEach(cell => {
      html += `<th>${processInline(cell)}</th>`;
    });
    html += '</tr>';
  }
  
  // Rest are data rows
  for (let i = 1; i < rows.length; i++) {
    html += '<tr>';
    rows[i].forEach(cell => {
      html += `<td>${processInline(cell)}</td>`;
    });
    html += '</tr>';
  }
  
  html += '</tbody></table>';
  return html;
}

function processInline(text) {
  text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
  text = text.replace(/\*\*(.+?)\*\*/g, '<b>$1</b>');
  text = text.replace(/\*(.+?)\*/g, '<i>$1</i>');
  text = text.replace(/_(.+?)_/g, '<i>$1</i>');
  text = text.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" class="md-image">'); // Images
  text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="md-link">$1</a>'); // Links
  return text;
}

export function formatSessionTime(dateStr) {
  if (!dateStr) return "";
  const date = new Date(dateStr);
  return date.toLocaleTimeString("tr-TR", { hour: "2-digit", minute: "2-digit" });
}

export function groupSessionsByDate(sessions) {
  const groups = {};
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today.getTime() - 86400000);
  const weekAgo = new Date(today.getTime() - 7 * 86400000);
  const monthAgo = new Date(today.getTime() - 30 * 86400000);
  
  sessions.forEach(session => {
    const date = new Date(session.archived_at);
    const sessionDay = new Date(date.getFullYear(), date.getMonth(), date.getDate());
    
    let groupKey;
    if (sessionDay >= today) {
      groupKey = "Bugün";
    } else if (sessionDay >= yesterday) {
      groupKey = "Dün";
    } else if (sessionDay >= weekAgo) {
      groupKey = "Bu Hafta";
    } else if (sessionDay >= monthAgo) {
      groupKey = "Bu Ay";
    } else {
      groupKey = "Daha Eski";
    }
    
    if (!groups[groupKey]) {
      groups[groupKey] = [];
    }
    groups[groupKey].push(session);
  });
  
  return groups;
}

export function createWelcomeMessage() {
  const div = document.createElement("div");
  div.className = "welcome-message";
  div.id = "welcomeMessage";
  div.innerHTML = `
    <div class="welcome-icon">
      <i class="fas fa-bolt"></i>
    </div>
    <h3>Merhaba! Ben PEN</h3>
    <p>WhatsApp, email, Drive ve hafıza verilerinizle ilgili size yardımcı olmak için buradayım.</p>
    <div class="welcome-suggestions">
      <button class="suggestion-chip" data-text="Search for 'meeting' in my WhatsApp chats">
        <i class="fas fa-search"></i> WhatsApp'ta ara
      </button>
      <button class="suggestion-chip" data-text="What happened in the last 3 days?">
        <i class="fas fa-clock"></i> Son 3 günü özetle
      </button>
      <button class="suggestion-chip" data-text="What can you do?">
        <i class="fas fa-magic"></i> Neler yapabilirsin?
      </button>
    </div>
  `;
  return div;
}

export function showConfirmModal(message, onConfirm, onCancel) {
  return new Promise((resolve) => {
    const overlay = document.createElement("div");
    overlay.className = "confirm-modal-overlay";
    overlay.innerHTML = `
      <div class="confirm-modal">
        <div class="confirm-modal-icon">
          <i class="fas fa-exclamation-triangle"></i>
        </div>
        <div class="confirm-modal-title">Dikkat!</div>
        <div class="confirm-modal-message">${message}</div>
        <div class="confirm-modal-actions">
          <button class="confirm-modal-btn cancel">İptal</button>
          <button class="confirm-modal-btn confirm">Evet</button>
        </div>
      </div>
    `;
    
    document.body.appendChild(overlay);
    
    requestAnimationFrame(() => {
      overlay.classList.add("active");
    });
    
    const closeModal = (result) => {
      overlay.classList.remove("active");
      setTimeout(() => {
        overlay.remove();
        resolve(result);
      }, 200);
    };
    
    overlay.querySelector(".confirm-modal-btn.cancel").addEventListener("click", () => {
      closeModal(false);
      if (onCancel) onCancel();
    });
    
    overlay.querySelector(".confirm-modal-btn.confirm").addEventListener("click", () => {
      closeModal(true);
      if (onConfirm) onConfirm();
    });
    
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) {
        closeModal(false);
        if (onCancel) onCancel();
      }
    });
    
    const escHandler = (e) => {
      if (e.key === "Escape") {
        document.removeEventListener("keydown", escHandler);
        closeModal(false);
        if (onCancel) onCancel();
      }
    };
    document.addEventListener("keydown", escHandler);
  });
}
