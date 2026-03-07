// ========================================
// CHAT FUNCTIONS
// ========================================

import { els } from './dom.js';
import { isSending, setIsSending, attachedFiles } from './state.js';
import { sendChatMessage, loadChatHistory, resetChat, startSleepCycle } from './api.js';
import { appendMessage, resetChatUI } from './messages.js';
import { showThinking, hideActivity } from './activity.js';
import { updateTools } from './tools.js';
import { clearAttachedFiles } from './files.js';
import { showConfirmModal } from './utils.js';

export async function sendMessage() {
  if (isSending) return;
  const text = els.messageInput.value.trim();
  if (!text && attachedFiles.length === 0) return;

  setIsSending(true);
  els.messageInput.value = "";
  els.messageInput.style.height = "auto";
  els.messageInput.disabled = true;
  els.sendBtn.disabled = true;
  
  const filesToSend = attachedFiles.map(f => ({ ...f }));
  clearAttachedFiles();

  appendMessage("user", text, { files: filesToSend });
  
  showThinking();

  const requestStartTime = Date.now();

  try {
    const data = await sendChatMessage(text, filesToSend);
    
    let currentTurnTools = [];
    if (Array.isArray(data.tools) && data.tools.length > 0) {
      updateTools(data.tools);
      
      // Filter tools for this specific turn to avoid showing all history in the message
      // We check if the tool timestamp is after the request start time (minus a buffer)
      currentTurnTools = data.tools.filter(t => {
          if (!t.timestamp) return false;
          
          let tStr = t.timestamp;
          // Ensure timestamp is treated as UTC if it doesn't have timezone info
          if (!tStr.endsWith("Z") && !tStr.includes("+")) {
              tStr += "Z";
          }
          
          const tTime = new Date(tStr).getTime();
          return tTime >= (requestStartTime - 5000); // Increased buffer to 5s to be safe
      });
    }
    
    hideActivity();

    if (data.error) {
      appendMessage("system", data.error);
    } else {
      if (Array.isArray(data.messages)) {
        data.messages.forEach((m) => {
          if (m.role === "assistant" || m.role === "model") {
            appendMessage("assistant", m.content || "", { typewriter: true, tools: currentTurnTools });
          }
        });
      } else if (data.reply) {
        appendMessage("assistant", data.reply, { typewriter: true, tools: currentTurnTools });
      }
    }
  } catch (err) {
    hideActivity();
    appendMessage("system", `Connection error: ${err.message}`);
  } finally {
    setIsSending(false);
    els.messageInput.disabled = false;
    els.sendBtn.disabled = false;
    els.messageInput.focus();
  }
}

export async function loadHistory() {
  try {
    console.log("Loading chat history...");
    const data = await loadChatHistory();
    console.log("History data received:", data);
    
    const messages = data.messages || [];
    const allTools = data.tool_interactions || [];
    console.log("Messages count:", messages.length);
    console.log("Tools count:", allTools.length);
    
    if (messages.length > 0) {
      if (els.welcomeMessage) {
        els.welcomeMessage.style.display = "none";
      }
      
      // Create a map of message_id to tools for that message
      const toolsByMessage = new Map();
      
      // Group tools by their associated message (based on timestamp proximity)
      // Tools typically execute BEFORE the assistant message, so we look for tools
      // that happened within 10 seconds BEFORE each assistant message
      messages.forEach((msg, index) => {
        if (msg.role !== 'assistant') return; // Only match tools to assistant messages
        
        let msgTStr = msg.timestamp;
        if (!msgTStr.endsWith("Z") && !msgTStr.includes("+")) msgTStr += "Z";
        const msgTimestamp = new Date(msgTStr).getTime();

        const relevantTools = allTools.filter(tool => {
          let toolTStr = tool.timestamp;
          if (!toolTStr.endsWith("Z") && !toolTStr.includes("+")) toolTStr += "Z";
          const toolTimestamp = new Date(toolTStr).getTime();
          
          // Tool should be before or very close to the message
          // Increased window to 30 seconds to account for generation time
          const timeDiff = msgTimestamp - toolTimestamp;
          return timeDiff >= -2000 && timeDiff < 30000; // -2s to 30s window
        });
        
        if (relevantTools.length > 0) {
          toolsByMessage.set(index, relevantTools);
        }
      });
      
      messages.forEach((msg, index) => {
        try {
          const role = msg.role || "user";
          const content = msg.content || "";
          const timestamp = msg.timestamp || new Date().toISOString();
          const files = msg.metadata?.files || [];
          const tools = toolsByMessage.get(index) || [];
          
          console.log(`Loading message ${index}: role=${role}, content_length=${content.length}, files=${files.length}, tools=${tools.length}`);
          appendMessage(role, content, { timestamp, animate: false, files, tools });
        } catch (msgErr) {
          console.error("Error loading individual message:", msgErr, msg);
        }
      });
      
      if (allTools.length > 0) {
        try {
          updateTools(allTools);
        } catch (toolErr) {
          console.error("Error updating tools:", toolErr);
        }
      }
      
      setTimeout(async () => {
        const { scrollToBottom } = await import('./utils.js');
        scrollToBottom();
      }, 100);
    } else {
      console.log("No messages in history");
    }
  } catch (err) {
    console.error("Could not load chat history:", err);
  }
}

export async function handleResetChat() {
  const confirmed = await showConfirmModal(
    "Sohbeti silmek istedi��inize emin misiniz? Bu işlem geri alınamaz."
  );
  
  if (!confirmed) return;
  
  await resetChatUI();
  try {
    await resetChat();
  } catch {
    // silently ignore
  }
}

export async function handleSleepCycle() {
  const confirmed = await showConfirmModal(
    "Uyku döngüsünü başlatmak istediğinize emin misiniz? Bu işlem birkaç dakika sürebilir."
  );
  
  if (!confirmed) return;
  
  appendMessage("system", "Uyku döngüsü başlatılıyor...");
  
  try {
    const data = await startSleepCycle();
    
    if (data.status === "success") {
      appendMessage("system", "Uyku döngüsü başarıyla tamamlandı! Hafıza güncellemeleri yapıldı.");
      setTimeout(async () => {
        await resetChatUI();
        loadHistory();
      }, 1000);
    } else {
      appendMessage("system", `Uyku hatası: ${data.message || "Bilinmeyen hata"}`);
    }
  } catch (err) {
    appendMessage("system", `Uyku döngüsü başlatılamadı: ${err.message}`);
  }
}

export function exportChat() {
  const messages = els.messagesContent.querySelectorAll(".message");
  let exportText = "# PEN Sohbet Dışa Aktarımı\n";
  exportText += `Tarih: ${new Date().toLocaleString("tr-TR")}\n\n`;
  
  messages.forEach(msg => {
    const isUser = msg.classList.contains("user");
    const isAssistant = msg.classList.contains("assistant");
    const content = msg.querySelector(".message-content")?.textContent || "";
    
    if (isUser) {
      exportText += `## Siz\n${content}\n\n`;
    } else if (isAssistant) {
      exportText += `## PEN\n${content}\n\n`;
    }
  });
  
  const blob = new Blob([exportText], { type: "text/markdown" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `pen-sohbet-${new Date().toISOString().slice(0,10)}.md`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
