// ========================================
// TOOLS PANEL
// ========================================

import { els } from './dom.js';
import { expandAllTools, toolsPanelCollapsed, setToolsPanelCollapsed } from './state.js';

export function updateTools(tools) {
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
      st === "completed" ? "Completed" : st === "failed" ? "Failed" : "Running";

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
      title.textContent = "Parameters";
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
      title.textContent = "Result";
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

    item.addEventListener("click", (e) => {
      e.stopPropagation();
      const isHidden = detailsContainer.style.display === "none";
      detailsContainer.style.display = isHidden ? "block" : "none";
      item.classList.toggle("expanded", isHidden);
    });

    els.toolsBody.appendChild(item);
  });
}

export function toggleToolsPanel() {
  const newState = !toolsPanelCollapsed;
  setToolsPanelCollapsed(newState);
  
  if (els.mainContent) {
    els.mainContent.classList.toggle("tools-collapsed", newState);
  }
  
  localStorage.setItem("toolsPanelCollapsed", newState.toString());
  
  console.log("Tools panel:", newState ? "collapsed" : "expanded");
}

export function openToolsPanel() {
  if (toolsPanelCollapsed) {
    toggleToolsPanel();
  }
}
