// ========================================
// SERVER-SENT EVENTS (SSE)
// ========================================

import { API_BASE } from './config.js';
import { eventSource, setEventSource } from './state.js';
import { showActivity } from './activity.js';

export function connectSSE() {
  if (eventSource) {
    eventSource.close();
  }
  
  const es = new EventSource(`${API_BASE}/api/pen/events`);
  setEventSource(es);
  
  es.onopen = () => {
    console.log("SSE connected");
  };
  
  es.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handleSSEEvent(data);
    } catch (e) {
      console.error("SSE parse error:", e);
    }
  };
  
  es.onerror = (err) => {
    console.log("SSE error, reconnecting in 3s...");
    es.close();
    setTimeout(connectSSE, 3000);
  };
}

function handleSSEEvent(event) {
  if (event.type === "keepalive") {
    return;
  }
  
  if (event.type === "connected") {
    console.log("SSE connected to server");
    return;
  }
  
  if (event.type === "tool_activity") {
    const { tool_name, status } = event.data;
    console.log(`🔧 Tool event: ${tool_name} - ${status}`);
    
    if (status === "running") {
      showActivity(tool_name);
    }
  }

  if (event.type === "sync_log") {
    const logData = event.data;
    // Dispatch custom event for settings page to pick up
    const customEvent = new CustomEvent('pen-sync-log', { detail: logData });
    document.dispatchEvent(customEvent);
  }
}
