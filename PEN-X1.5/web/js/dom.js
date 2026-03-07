// ========================================
// DOM ELEMENT REFERENCES
// ========================================

export let els = {};

export function initializeElements() {
  els = {
    messagesContent: document.getElementById("messagesContent"),
    chatMessages: document.getElementById("chatMessages"),
    welcomeMessage: document.getElementById("welcomeMessage"),
    messageInput: document.getElementById("messageInput"),
    sendBtn: document.getElementById("sendBtn"),
    resetBtn: document.getElementById("resetBtn"),
    sleepBtn: document.getElementById("sleepBtn"),
    modelSelectorBtn: document.getElementById("modelSelectorBtn"),
    modelDropdown: document.getElementById("modelDropdown"),
    modelDropdownContent: document.getElementById("modelDropdownContent"),
    selectedModelName: document.getElementById("selectedModelName"),
    toolsBody: document.getElementById("toolsBody"),
    toolsEmpty: document.getElementById("toolsEmpty"),
    toolOutputToggle: document.getElementById("toolOutputToggle"),
    toolsPanel: document.getElementById("toolsPanel"),
    toolsPanelToggle: document.getElementById("toolsPanelToggle"),
    closePanelBtn: document.getElementById("closePanelBtn"),
    mainContent: document.querySelector(".main-content"),
    chatMenuBtn: document.getElementById("chatMenuBtn"),
    chatMenuDropdown: document.getElementById("chatMenuDropdown"),
    menuSleepBtn: document.getElementById("menuSleepBtn"),
    menuResetBtn: document.getElementById("menuResetBtn"),
    // History sidebar elements
    sidebarToggle: document.getElementById("sidebarToggle"),
    historySidebar: document.getElementById("historySidebar"),
    historyList: document.getElementById("historyList"),
    historyEmpty: document.getElementById("historyEmpty"),
    backToCurrentBtn: document.getElementById("backToCurrentBtn"),
    sidebarCloseBtn: document.getElementById("sidebarCloseBtn"),
    historySearchInput: document.getElementById("historySearchInput"),
    backToChatBtn: document.getElementById("backToChatBtn"),
    chatPanelTitle: document.getElementById("chatPanelTitle"),
    chatInputArea: document.getElementById("chatInputArea"),
    // Settings elements
    settingsBtn: document.getElementById("settingsBtn"),
    exportChatBtn: document.getElementById("exportChatBtn"),
    settingsPage: document.getElementById("settingsPage"),
    settingsBackBtn: document.getElementById("settingsBackBtn"),
    appContainer: document.querySelector(".app"),
    themeSelect: document.getElementById("themeSelect"),
    fontSizeSelect: document.getElementById("fontSizeSelect"),
    // File attachments
    attachedFilesContainer: document.getElementById("attachedFiles"),
    inputContainer: document.getElementById("inputContainer"),
    attachFileBtn: document.getElementById("attachFileBtn"),
    fileInput: document.getElementById("fileInput"),
  };
  console.log("Elements initialized:", Object.keys(els).filter(k => els[k] !== null).length, "elements found");
  
  // Load panel state from localStorage
  const savedState = localStorage.getItem("toolsPanelCollapsed");
  if (savedState === "true") {
    window.toolsPanelCollapsed = true;
    els.mainContent?.classList.add("tools-collapsed");
  }
}
