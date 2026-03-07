// ========================================
// ACTIVITY INDICATOR
// ========================================

import { els } from './dom.js';
import { TOOL_ACTIVITY_MESSAGES } from './config.js';
import { currentActivityEl, setCurrentActivityEl } from './state.js';
import { scrollToBottom } from './utils.js';

export function showActivity(toolName) {
  const toolInfo = TOOL_ACTIVITY_MESSAGES[toolName] || TOOL_ACTIVITY_MESSAGES['default'];
  const message = toolInfo.messages[0];
  const icon = toolInfo.icon;
  
  if (!currentActivityEl) {
    const activityEl = document.createElement("div");
    activityEl.id = "activityIndicator";
    activityEl.className = "activity-indicator";
    activityEl.innerHTML = `
      <div class="activity-avatar">P</div>
      <div class="activity-box">
        <div class="activity-content">
          <div class="activity-text">
            <i class="${icon} activity-icon"></i>
            <span class="activity-message">${message}</span>
            <span class="activity-dots"><span></span><span></span><span></span></span>
          </div>
        </div>
      </div>
    `;
    els.messagesContent.appendChild(activityEl);
    setCurrentActivityEl(activityEl);
    scrollToBottom();
  } else {
    updateActivity(toolName);
  }
}

export function updateActivity(toolName) {
  if (!currentActivityEl) return;
  
  const toolInfo = TOOL_ACTIVITY_MESSAGES[toolName] || TOOL_ACTIVITY_MESSAGES['default'];
  const message = toolInfo.messages[0];
  const icon = toolInfo.icon;
  
  const contentEl = currentActivityEl.querySelector('.activity-content');
  const currentText = contentEl.querySelector('.activity-text');
  
  currentText.classList.add('sliding-out');
  
  setTimeout(() => {
    contentEl.innerHTML = `
      <div class="activity-text">
        <i class="${icon} activity-icon"></i>
        <span class="activity-message">${message}</span>
        <span class="activity-dots"><span></span><span></span><span></span></span>
      </div>
    `;
    scrollToBottom();
  }, 200);
}

export function showThinking() {
  if (!currentActivityEl) {
    showActivity('default');
  }
  updateActivityText('Düşünüyor', 'fas fa-lightbulb');
}

export function showTyping() {
  if (!currentActivityEl) {
    const activityEl = document.createElement("div");
    activityEl.id = "activityIndicator";
    activityEl.className = "activity-indicator";
    activityEl.innerHTML = `
      <div class="activity-avatar">P</div>
      <div class="activity-box">
        <div class="activity-content">
          <div class="activity-text">
            <i class="fas fa-pen activity-icon"></i>
            <span class="activity-message">Yazıyor</span>
            <span class="activity-dots"><span></span><span></span><span></span></span>
          </div>
        </div>
      </div>
    `;
    els.messagesContent.appendChild(activityEl);
    setCurrentActivityEl(activityEl);
    scrollToBottom();
  } else {
    updateActivityText('Yazıyor', 'fas fa-pen');
  }
}

export function updateActivityText(message, icon) {
  if (!currentActivityEl) return;
  
  const contentEl = currentActivityEl.querySelector('.activity-content');
  const currentText = contentEl.querySelector('.activity-text');
  
  if (currentText) {
    currentText.classList.add('sliding-out');
    
    setTimeout(() => {
      contentEl.innerHTML = `
        <div class="activity-text">
          <i class="${icon} activity-icon"></i>
          <span class="activity-message">${message}</span>
          <span class="activity-dots"><span></span><span></span><span></span></span>
        </div>
      `;
      scrollToBottom();
    }, 200);
  }
}

export function hideTyping() {
  if (currentActivityEl) {
    currentActivityEl.remove();
    setCurrentActivityEl(null);
  }
}

export function hideActivity() {
  hideTyping();
}
