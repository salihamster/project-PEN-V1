// ========================================
// GLOBAL STATE
// ========================================

import { DEFAULT_MODEL } from './config.js';

export let isSending = false;
export let lastUserMessageAt = null;
export let showToolOutput = true;
export let expandAllTools = false;
export let selectedModel = DEFAULT_MODEL;
export let eventSource = null;
export let toolsPanelCollapsed = false;
export let historySidebarOpen = false;
export let viewingArchivedSession = null;
export let settingsOpen = false;
export let attachedFiles = [];
export let availableModels = [];
export let currentActivityEl = null;
export let activityQueue = [];
export let cachedSessions = [];

// Setters
export function setIsSending(value) { isSending = value; }
export function setLastUserMessageAt(value) { lastUserMessageAt = value; }
export function setShowToolOutput(value) { showToolOutput = value; }
export function setExpandAllTools(value) { expandAllTools = value; }
export function setSelectedModel(value) { selectedModel = value; }
export function setEventSource(value) { eventSource = value; }
export function setToolsPanelCollapsed(value) { toolsPanelCollapsed = value; }
export function setHistorySidebarOpen(value) { historySidebarOpen = value; }
export function setViewingArchivedSession(value) { viewingArchivedSession = value; }
export function setSettingsOpen(value) { settingsOpen = value; }
export function setAttachedFiles(value) { attachedFiles = value; }
export function setAvailableModels(value) { availableModels = value; }
export function setCurrentActivityEl(value) { currentActivityEl = value; }
export function setActivityQueue(value) { activityQueue = value; }
export function setCachedSessions(value) { cachedSessions = value; }
