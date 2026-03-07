// ========================================
// CONFIGURATION & CONSTANTS
// ========================================

export const API_BASE = "http://127.0.0.1:8000";

export const MAX_FILES = 10;

export const DEFAULT_MODEL = "gemini-3-flash-preview";

// Tool name to human-friendly activity messages
export const TOOL_ACTIVITY_MESSAGES = {
  // Time
  'get_current_time': { icon: 'fas fa-clock', messages: ['Saati kontrol ediyor'] },
  
  // WhatsApp
  'list_whatsapp_chats': { icon: 'fab fa-whatsapp', messages: ['WhatsApp sohbetlerini listeliyor'] },
  'get_whatsapp_messages': { icon: 'fab fa-whatsapp', messages: ['Sohbet mesajlarını okuyor'] },
  'search_messages': { icon: 'fas fa-search', messages: ['Mesajlarda arıyor'] },
  'get_recent_messages': { icon: 'fab fa-whatsapp', messages: ['Son mesajları getiriyor'] },
  'get_whatsapp_participants': { icon: 'fab fa-whatsapp', messages: ['Katılımcıları kontrol ediyor'] },
  'get_whatsapp_chronology': { icon: 'fab fa-whatsapp', messages: ['Sohbet kronolojisini çıkarıyor'] },
  'search_across_chats': { icon: 'fab fa-whatsapp', messages: ['Tüm sohbetlerde arıyor'] },
  'get_conversation_context': { icon: 'fab fa-whatsapp', messages: ['Konuşma bağlamını yüklüyor'] },
  
  // Email
  'list_email_subjects': { icon: 'fas fa-envelope', messages: ['Mail konularını listeliyor'] },
  'get_email_content': { icon: 'fas fa-envelope', messages: ['Mail içeriğini okuyor'] },
  'search_emails': { icon: 'fas fa-envelope', messages: ['Maillerde arıyor'] },
  'refresh_emails': { icon: 'fas fa-sync', messages: ['Mailleri yeniliyor'] },
  
  // Drive
  'search_drive_files': { icon: 'fab fa-google-drive', messages: ['Drive\'da arıyor'] },
  'refresh_drive_files': { icon: 'fas fa-sync', messages: ['Drive dosyalarını yeniliyor'] },
  
  // Web
  'search_web': { icon: 'fas fa-globe', messages: ['Web\'de arıyor'] },
  'fetch_webpage': { icon: 'fas fa-globe', messages: ['Sayfayı yüklüyor'] },
  
  // Context/Memory
  'create_context': { icon: 'fas fa-plus-circle', messages: ['Yeni bağlam oluşturuyor'] },
  'update_context': { icon: 'fas fa-edit', messages: ['Bağlamı güncelliyor'] },
  'search_contexts': { icon: 'fas fa-search', messages: ['Bağlamlarda arıyor'] },
  'get_context_details': { icon: 'fas fa-info-circle', messages: ['Bağlam detaylarını yüklüyor'] },
  'delete_context': { icon: 'fas fa-trash', messages: ['Bağlamı siliyor'] },
  'link_contexts': { icon: 'fas fa-link', messages: ['Bağlamları bağlıyor'] },
  
  // Statistics
  'get_statistics': { icon: 'fas fa-chart-bar', messages: ['İstatistikleri hesaplıyor'] },
  
  // Refresh
  'check_for_updates': { icon: 'fas fa-sync', messages: ['Güncellemeleri kontrol ediyor'] },
  
  // Default
  'default': { icon: 'fas fa-cog', messages: ['İşlem yapıyor'] }
};
