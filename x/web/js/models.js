// ========================================
// MODEL SELECTOR
// ========================================

import { els } from './dom.js';
import { availableModels, selectedModel, setAvailableModels, setSelectedModel } from './state.js';
import { loadAvailableModelsAPI } from './api.js';

export async function loadAvailableModels() {
  try {
    console.log("Loading available models...");
    const data = await loadAvailableModelsAPI();
    
    setAvailableModels(data.models || []);
    const defaultModel = data.default || "gemini-2.5-flash";
    
    console.log("Available models:", availableModels);
    
    if (!els.modelDropdownContent) return;
    
    els.modelDropdownContent.innerHTML = "";
    
    if (availableModels.length === 0) {
      els.modelDropdownContent.innerHTML = '<div class="model-option"><span class="model-option-name">Model bulunamadı</span></div>';
      return;
    }
    
    const grouped = {};
    availableModels.forEach(model => {
      if (!grouped[model.provider]) {
        grouped[model.provider] = [];
      }
      grouped[model.provider].push(model);
    });
    
    Object.keys(grouped).sort().forEach(provider => {
      const group = document.createElement("div");
      group.className = "model-group";
      
      const title = document.createElement("div");
      title.className = "model-group-title";
      title.textContent = provider.charAt(0).toUpperCase() + provider.slice(1);
      group.appendChild(title);
      
      grouped[provider].forEach(model => {
        const option = document.createElement("div");
        option.className = "model-option";
        option.dataset.modelId = model.id;
        
        if (model.id === defaultModel) {
          option.classList.add("selected");
          setSelectedModel(model.id);
          if (els.selectedModelName) {
            els.selectedModelName.textContent = model.display_name;
          }
        }
        
        const name = document.createElement("span");
        name.className = "model-option-name";
        name.textContent = model.display_name;
        
        option.appendChild(name);
        
        option.addEventListener("click", () => {
          selectModel(model.id, model.display_name);
        });
        
        group.appendChild(option);
      });
      
      els.modelDropdownContent.appendChild(group);
    });
    
    setupModelDropdown();
    
  } catch (err) {
    console.error("Could not load models:", err);
    if (els.selectedModelName) {
      els.selectedModelName.textContent = "Gemini 2.5 Flash";
    }
  }
}

function setupModelDropdown() {
  if (!els.modelSelectorBtn || !els.modelDropdown) return;
  
  els.modelSelectorBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    const isOpen = els.modelDropdown.classList.contains("open");
    
    if (isOpen) {
      closeModelDropdown();
    } else {
      openModelDropdown();
    }
  });
  
  document.addEventListener("click", (e) => {
    if (!els.modelDropdown.contains(e.target) && !els.modelSelectorBtn.contains(e.target)) {
      closeModelDropdown();
    }
  });
  
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      closeModelDropdown();
    }
  });
}

function openModelDropdown() {
  els.modelDropdown.classList.add("open");
  els.modelSelectorBtn.classList.add("open");
}

function closeModelDropdown() {
  els.modelDropdown.classList.remove("open");
  els.modelSelectorBtn.classList.remove("open");
}

function selectModel(modelId, displayName) {
  setSelectedModel(modelId);
  
  if (els.selectedModelName) {
    els.selectedModelName.textContent = displayName;
  }
  
  const options = els.modelDropdownContent.querySelectorAll(".model-option");
  options.forEach(opt => {
    opt.classList.toggle("selected", opt.dataset.modelId === modelId);
  });
  
  closeModelDropdown();
  
  console.log("Model changed to:", selectedModel);
}
