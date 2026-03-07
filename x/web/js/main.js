// ========================================
// MAIN ENTRY POINT
// ========================================

import { initializeElements } from './dom.js';
import { bindEvents } from './events.js';
import { loadHistory } from './chat.js';
import { loadAvailableModels } from './models.js';
import { setupFileAttachments } from './files.js';
import { connectSSE } from './sse.js';
import { setupSettings } from './settings.js';
import { setupArchivedPage } from './history.js';
import { setupArtifactPanel } from './artifact.js';
import { setupPENote } from './penote.js';
import { setupCalendar } from './calendar.js';

async function initializeApp() {
  console.log("DOMContentLoaded event fired");
  initializeElements();
  bindEvents();
  setupFileAttachments();
  setupSettings();
  setupArchivedPage();
  setupArtifactPanel();
  setupPENote();
  setupCalendar();
  console.log("Events bound, loading models and history...");
  
  await new Promise(resolve => setTimeout(resolve, 500));
  
  connectSSE();
  
  await loadAvailableModels();
  await loadHistory();
}

// Start the app when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeApp);
} else {
  initializeApp();
}
