"""
L4 Memory System - User Profile + Context Memory
Minimax ile doldurulur, Gemini'ye verilir
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

from ..utils.logger import get_logger

logger = get_logger(__name__)


class L4MemorySystem:
    """
    L4 Bellek Sistemi
    
    - User Profile: Sürekli hatırlanması gereken bilgiler
    - Context Memory: Olaylar, projeler, toplantılar
    - Agent Notes: Hatırlatıcılar, günlük notlar
    
    Minimax ile doldurulur, Gemini'ye context olarak verilir.
    """
    
    def __init__(self, data_dir: Path, minimax_api_key: Optional[str] = None):
        """
        L4 Memory System başlat
        
        Args:
            data_dir: Veri dizini
            minimax_api_key: Minimax API key (opsiyonel)
        """
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Tek JSON dosya
        self.memory_file = data_dir / "L4_memory.json"
        
        # Minimax API (Anthropic SDK ile)
        self.minimax_api_key = minimax_api_key or os.getenv("MINIMAX_API_KEY")
        self.minimax_client = None
        
        # Minimax client'ı başlat (gerekirse)
        if self.minimax_api_key:
            try:
                import anthropic
                self.minimax_client = anthropic.Anthropic(
                    api_key=self.minimax_api_key,
                    base_url="https://api.minimax.io/anthropic"
                )
                logger.info("✅ Minimax client initialized")
            except ImportError:
                logger.warning("Anthropic SDK not installed. Install with: pip install anthropic")
            except Exception as e:
                logger.warning(f"Minimax client initialization failed: {e}")
        
        # İlk kurulum
        self.ensure_memory_file()
    
    def ensure_memory_file(self):
        """L4_memory.json dosyasını oluştur"""
        if not self.memory_file.exists():
            initial_data = {
                "user_profile": {
                    "basic": {
                        "name": "",
                        "age": None,
                        "occupation": "",
                        "location": "",
                        "timezone": "Europe/Istanbul"
                    },
                    "preferences": {
                        "language": "Turkish",
                        "communication_style": "",
                        "work_hours": "",
                        "interests": []
                    },
                    "relationships": {
                        "contacts": {},
                        "groups": []
                    },
                    "habits": {
                        "activity_pattern": "",
                        "peak_hours": [],
                        "typical_tasks": []
                    },
                    "expertise": [],
                    "current_projects": [],
                    "important_dates": {
                        "birthdays": {},
                        "anniversaries": {},
                        "deadlines": {}
                    },
                    "communication_patterns": {
                        "response_time": "",
                        "active_hours": [],
                        "preferred_channels": []
                    }
                },
                "memory": {
                    "contexts": {},
                    "agent_notes": {
                        "reminders": [],
                        "daily_notes": {}
                    },
                    "insights": {
                        "patterns": [],
                        "observations": [],
                        "recommendations": []
                    }
                },
                "metadata": {
                    "created": datetime.now().isoformat(),
                    "last_updated": None,
                    "version": "6.0",
                    "total_contexts": 0,
                    "total_reminders": 0
                }
            }
            
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, ensure_ascii=False, indent=2)
            
            logger.info("✅ L4 memory file created")
    
    def load_memory(self) -> Dict[str, Any]:
        """Belleği yükle"""
        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading L4 memory: {e}")
            self.ensure_memory_file()
            return self.load_memory()
    
    def save_memory(self, data: Dict[str, Any]):
        """Belleği kaydet"""
        try:
            data["metadata"]["last_updated"] = datetime.now().isoformat()
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving L4 memory: {e}")
    
    # ============================================================================
    # USER PROFILE
    # ============================================================================
    
    def get_user_profile(self) -> Dict[str, Any]:
        """
        User profile'ı getir (HER ZAMAN Gemini'ye verilir)
        
        Returns:
            User profile dict
        """
        memory = self.load_memory()
        return memory["user_profile"]
    
    def update_user_profile(self, field_path: str, value: Any) -> bool:
        """
        User profile güncelle
        
        Args:
            field_path: Nokta ile ayrılmış path (örn: "basic.name")
            value: Yeni değer
        
        Returns:
            Başarılı mı
        """
        try:
            memory = self.load_memory()
            
            # Path'i parse et
            parts = field_path.split('.')
            current = memory["user_profile"]
            
            # Son field'e kadar git
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            # Değeri güncelle
            current[parts[-1]] = value
            
            self.save_memory(memory)
            logger.info(f"✅ User profile updated: {field_path} = {value}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            return False
    
    # ============================================================================
    # CONTEXT MEMORY
    # ============================================================================
    
    def generate_context_id(self, context_type: str) -> str:
        """
        Time-based context ID oluştur
        
        Args:
            context_type: Context tipi (meeting, project, task, etc.)
        
        Returns:
            Context ID (örn: 20241220_100000_meeting)
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{timestamp}_{context_type}"
    
    def create_context(self, context_type: str, title: str, data: Dict[str, Any]) -> str:
        """
        Yeni context oluştur
        
        Args:
            context_type: Context tipi (meeting, project, task, event, etc.)
            title: Başlık
            data: Context verisi (date, time, description, tags, calendar_event_id, task_id, related_contexts, etc.)
        
        Returns:
            Context ID
        """
        try:
            memory = self.load_memory()
            
            # ID oluştur
            context_id = self.generate_context_id(context_type)
            
            # Context oluştur (yeni field'lar ile)
            context = {
                "type": context_type,
                "title": title,
                "created": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "date": data.get("date"),
                "time": data.get("time"),
                "description": data.get("description", ""),
                "tags": data.get("tags", []),
                "status": data.get("status", "active"),
                "priority": data.get("priority", "medium"),
                # Google Services bağlantıları
                "calendar_event_id": data.get("calendar_event_id"),
                "task_id": data.get("task_id"),
                # Context bağlantıları
                "related_contexts": data.get("related_contexts", []),
                "related_data": data.get("related_data", {}),
                # Ekstra data
                "location": data.get("location"),
                "attendees": data.get("attendees", []),
                "notes": data.get("notes", "")
            }
            
            # Kaydet
            memory["memory"]["contexts"][context_id] = context
            memory["metadata"]["total_contexts"] = len(memory["memory"]["contexts"])
            
            self.save_memory(memory)
            logger.info(f"✅ Context created: {context_id} - {title}")
            
            return context_id
            
        except Exception as e:
            logger.error(f"Error creating context: {e}")
            return ""
    
    def get_context(self, context_id: str, include_linked: bool = True) -> Optional[Dict[str, Any]]:
        """
        Context getir (bağlantılı context'ler ile)
        
        Args:
            context_id: Context ID
            include_linked: Bağlantılı context'leri de getir
        
        Returns:
            Context dict veya None
        """
        memory = self.load_memory()
        context = memory["memory"]["contexts"].get(context_id)
        
        if not context:
            return None
        
        # Bağlantılı context'leri de getir
        if include_linked and "related_contexts" in context:
            linked_contexts = []
            for link in context["related_contexts"]:
                linked_id = link.get("context_id")
                linked_ctx = memory["memory"]["contexts"].get(linked_id)
                if linked_ctx:
                    linked_contexts.append({
                        "context_id": linked_id,
                        "relation": link.get("relation"),
                        "title": linked_ctx.get("title"),
                        "type": linked_ctx.get("type"),
                        "date": linked_ctx.get("date")
                    })
            
            context["linked_contexts_details"] = linked_contexts
        
        return context
    
    def update_context(self, context_id: str, updates: Dict[str, Any]) -> bool:
        """
        Context güncelle
        
        Args:
            context_id: Context ID
            updates: Güncellenecek field'lar
        
        Returns:
            Başarılı mı
        """
        try:
            memory = self.load_memory()
            
            if context_id not in memory["memory"]["contexts"]:
                logger.warning(f"Context not found: {context_id}")
                return False
            
            # Güncelle
            context = memory["memory"]["contexts"][context_id]
            context.update(updates)
            context["last_updated"] = datetime.now().isoformat()
            
            self.save_memory(memory)
            logger.info(f"✅ Context updated: {context_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating context: {e}")
            return False
    
    def search_contexts(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Context ara (gelişmiş search)
        
        Args:
            query: Arama sorgusu
            filters: Filtreler (type, date_range, tags, status, priority, etc.)
        
        Returns:
            Bulunan context'ler
        """
        memory = self.load_memory()
        results = []
        query_lower = query.lower()
        
        for context_id, context in memory["memory"]["contexts"].items():
            # None context'leri atla
            if context is None:
                continue

            # String search (genişletilmiş)
            searchable_text = f"{context.get('title', '')} {context.get('description', '')} {context.get('notes', '')} {' '.join(context.get('tags', []))}"
            
            if query_lower in searchable_text.lower():
                # Filtreler
                if filters:
                    # Type filter
                    if "type" in filters and context.get("type") != filters["type"]:
                        continue
                    
                    # Tags filter
                    if "tags" in filters:
                        if not any(tag in context.get("tags", []) for tag in filters["tags"]):
                            continue
                    
                    # Status filter
                    if "status" in filters and context.get("status") != filters["status"]:
                        continue
                    
                    # Priority filter
                    if "priority" in filters and context.get("priority") != filters["priority"]:
                        continue
                    
                    # Date range filter
                    if "date_range" in filters:
                        ctx_date = context.get("date")
                        if ctx_date:
                            start = filters["date_range"].get("start")
                            end = filters["date_range"].get("end")
                            if start and ctx_date < start:
                                continue
                            if end and ctx_date > end:
                                continue
                
                results.append({
                    "context_id": context_id,
                    **context
                })
        
        # Tarihe göre sırala (yeniden eskiye)
        results.sort(key=lambda x: x.get("created", ""), reverse=True)
        
        return results
    
    def link_contexts(self, context_id_1: str, context_id_2: str, relation_type: str = "related_to") -> bool:
        """
        İki context'i birbirine bağla
        
        Args:
            context_id_1: İlk context ID
            context_id_2: İkinci context ID
            relation_type: İlişki tipi (related_to, follows, precedes, part_of)
        
        Returns:
            Başarılı mı
        """
        try:
            memory = self.load_memory()
            
            # Her iki context de var mı kontrol et
            if context_id_1 not in memory["memory"]["contexts"]:
                logger.warning(f"Context not found: {context_id_1}")
                return False
            
            if context_id_2 not in memory["memory"]["contexts"]:
                logger.warning(f"Context not found: {context_id_2}")
                return False
            
            # İlk context'e ikinci context'i ekle
            context1 = memory["memory"]["contexts"][context_id_1]
            if "related_contexts" not in context1:
                context1["related_contexts"] = []
            
            link_info = {
                "context_id": context_id_2,
                "relation": relation_type
            }
            
            # Duplicate kontrolü
            if not any(link["context_id"] == context_id_2 for link in context1["related_contexts"]):
                context1["related_contexts"].append(link_info)
                context1["last_updated"] = datetime.now().isoformat()
            
            # İkinci context'e de birinci context'i ekle (bidirectional)
            context2 = memory["memory"]["contexts"][context_id_2]
            if "related_contexts" not in context2:
                context2["related_contexts"] = []
            
            # Reverse relation
            reverse_relations = {
                "follows": "precedes",
                "precedes": "follows",
                "part_of": "contains",
                "contains": "part_of",
                "related_to": "related_to"
            }
            reverse_relation = reverse_relations.get(relation_type, "related_to")
            
            reverse_link_info = {
                "context_id": context_id_1,
                "relation": reverse_relation
            }
            
            if not any(link["context_id"] == context_id_1 for link in context2["related_contexts"]):
                context2["related_contexts"].append(reverse_link_info)
                context2["last_updated"] = datetime.now().isoformat()
            
            self.save_memory(memory)
            logger.info(f"✅ Contexts linked: {context_id_1} <-{relation_type}-> {context_id_2}")
            return True
            
        except Exception as e:
            logger.error(f"Error linking contexts: {e}")
            return False
    
    def link_data_to_context(self, context_id: str, data_type: str, data_id: str) -> bool:
        """
        WhatsApp/Email mesajını context'e bağla
        
        Args:
            context_id: Context ID
            data_type: Veri tipi (whatsapp_message, email, file, etc.)
            data_id: Veri ID
        
        Returns:
            Başarılı mı
        """
        try:
            memory = self.load_memory()
            
            if context_id not in memory["memory"]["contexts"]:
                logger.warning(f"Context not found: {context_id}")
                return False
            
            context = memory["memory"]["contexts"][context_id]
            
            # related_data field'i yoksa oluştur
            if "related_data" not in context:
                context["related_data"] = {}
            
            # Data type listesi yoksa oluştur
            if data_type not in context["related_data"]:
                context["related_data"][data_type] = []
            
            # Ekle (duplicate kontrolü)
            if data_id not in context["related_data"][data_type]:
                context["related_data"][data_type].append(data_id)
                context["last_updated"] = datetime.now().isoformat()
                
                self.save_memory(memory)
                logger.info(f"✅ Data linked to context: {context_id} <- {data_type}:{data_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error linking data to context: {e}")
            return False
    
    # ============================================================================
    # AGENT NOTES
    # ============================================================================
    
    def create_reminder(self, title: str, due_date: str, 
                       priority: str = "medium",
                       context_id: Optional[str] = None) -> str:
        """
        Hatırlatıcı oluştur
        
        Args:
            title: Başlık
            due_date: Bitiş tarihi (ISO format)
            priority: Öncelik (low, medium, high)
            context_id: İlgili context ID (opsiyonel)
        
        Returns:
            Reminder ID
        """
        try:
            memory = self.load_memory()
            
            # ID oluştur
            reminder_id = self.generate_context_id("reminder")
            
            # Reminder oluştur
            reminder = {
                "id": reminder_id,
                "title": title,
                "due_date": due_date,
                "priority": priority,
                "context_id": context_id,
                "status": "pending",
                "created": datetime.now().isoformat()
            }
            
            # Ekle
            memory["memory"]["agent_notes"]["reminders"].append(reminder)
            memory["metadata"]["total_reminders"] = len(memory["memory"]["agent_notes"]["reminders"])
            
            self.save_memory(memory)
            logger.info(f"✅ Reminder created: {reminder_id} - {title}")
            
            return reminder_id
            
        except Exception as e:
            logger.error(f"Error creating reminder: {e}")
            return ""
    
    def get_pending_reminders(self) -> List[Dict[str, Any]]:
        """
        Bekleyen hatırlatıcıları getir
        
        Returns:
            Pending reminder'lar
        """
        memory = self.load_memory()
        reminders = memory["memory"]["agent_notes"]["reminders"]
        
        # Sadece pending olanlar
        pending = [r for r in reminders if r.get("status") == "pending"]
        
        # Tarihe göre sırala
        pending.sort(key=lambda x: x.get("due_date", ""))
        
        return pending
    
    def mark_reminder_done(self, reminder_id: str) -> bool:
        """
        Hatırlatıcıyı tamamla
        
        Args:
            reminder_id: Reminder ID
        
        Returns:
            Başarılı mı
        """
        try:
            memory = self.load_memory()
            reminders = memory["memory"]["agent_notes"]["reminders"]
            
            for reminder in reminders:
                if reminder.get("id") == reminder_id:
                    reminder["status"] = "done"
                    reminder["completed_at"] = datetime.now().isoformat()
                    
                    self.save_memory(memory)
                    logger.info(f"✅ Reminder marked done: {reminder_id}")
                    return True
            
            logger.warning(f"Reminder not found: {reminder_id}")
            return False
            
        except Exception as e:
            logger.error(f"Error marking reminder done: {e}")
            return False
    
    def add_daily_note(self, date: str, summary: str, highlights: List[str]):
        """
        Günlük not ekle
        
        Args:
            date: Tarih (YYYY-MM-DD)
            summary: Özet
            highlights: Öne çıkanlar
        """
        try:
            memory = self.load_memory()
            
            memory["memory"]["agent_notes"]["daily_notes"][date] = {
                "summary": summary,
                "highlights": highlights,
                "created": datetime.now().isoformat()
            }
            
            self.save_memory(memory)
            logger.info(f"✅ Daily note added: {date}")
            
        except Exception as e:
            logger.error(f"Error adding daily note: {e}")
    
    # ============================================================================
    # MINIMAX INTEGRATION
    # ============================================================================
    
    def extract_info_with_minimax(self, text: str, task: str) -> Optional[Dict[str, Any]]:
        """
        Minimax ile bilgi çıkar (Anthropic SDK kullanarak)
        
        Args:
            text: Analiz edilecek metin
            task: Görev açıklaması
        
        Returns:
            Çıkarılan bilgi (JSON)
        """
        if not self.minimax_client:
            logger.warning("Minimax client not initialized")
            return None
        
        try:
            # Minimax API call (Anthropic SDK ile)
            message = self.minimax_client.messages.create(
                model="MiniMax-M2",  # M2 model (hızlı + akıllı)
                max_tokens=1000,
                temperature=0.1,
                system=f"You are an information extraction assistant. {task}\n\nAlways respond in valid JSON format.",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": text
                            }
                        ]
                    }
                ]
            )
            
            # Response'u parse et
            content = ""
            for block in message.content:
                if block.type == "text":
                    content += block.text
            
            # Parse JSON
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # JSON extract
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    return json.loads(content[json_start:json_end])
                return None
            
        except Exception as e:
            logger.error(f"Minimax extraction error: {e}")
            return None
    
    def auto_update_from_conversation(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Konuşmadan otomatik bilgi çıkar ve L4'ü güncelle (Minimax ile)
        
        Args:
            messages: Konuşma mesajları
        
        Returns:
            Çıkarılan bilgiler
        """
        if not messages:
            return {"status": "no_messages"}
        
        # Mevcut L4'ü yükle
        memory = self.load_memory()
        current_profile = memory["user_profile"]
        
        # Konuşmayı metne çevir
        conversation_text = ""
        for msg in messages[-10:]:  # Son 10 mesaj
            if isinstance(msg, dict):
                role = msg.get("role", "user")
                
                # Hem 'content' (eski format) hem de 'parts' (Gemini API formatı) destekle
                parts = msg.get("parts", [])
                if not parts and "content" in msg: # Fallback for older format
                    content_val = msg.get("content", "")
                    parts = [content_val] if not isinstance(content_val, list) else content_val

                content = " ".join(str(p) for p in parts)
                conversation_text += f"{role}: {content}\n\n"
            else:
                # String message (fallback)
                conversation_text += f"{str(msg)}\n\n"
        
        # Minimax ile bilgi çıkar (mevcut profile ile)
        task = f"""You are updating a user profile based on conversation.

CURRENT USER PROFILE:
{json.dumps(current_profile, ensure_ascii=False, indent=2)}

TASK:
Extract NEW information from the conversation and update ONLY the relevant fields.
- Use the EXACT field structure from current profile
- Update "basic" fields: name, age, occupation, location
- Add to lists (expertise, interests) without duplicating
- Create new contexts for important events/projects

Return JSON format:
{{
  "user_profile_updates": {{
    "basic.name": "...",
    "basic.age": 16,
    "basic.occupation": "...",
    "expertise": ["skill1", "skill2"],
    "interests": ["interest1"]
  }},
  "new_contexts": [
    {{"type": "project", "title": "...", "data": {{...}}}}
  ],
  "action_items": ["..."]
}}

IMPORTANT:
- Only include fields that have NEW information
- Use dot notation for nested fields (e.g., "basic.name")
- Don't duplicate existing information"""
        
        extracted = self.extract_info_with_minimax(conversation_text, task)
        
        if not extracted:
            return {"status": "extraction_failed"}
        
        # User profile güncelle
        if "user_profile_updates" in extracted:
            for field_path, value in extracted["user_profile_updates"].items():
                self.update_user_profile(field_path, value)
        
        # Yeni context'ler oluştur
        if "new_contexts" in extracted:
            for ctx in extracted["new_contexts"]:
                # ctx dict mi kontrol et
                if isinstance(ctx, dict):
                    self.create_context(
                        context_type=ctx.get("type", "general"),
                        title=ctx.get("title", ""),
                        data=ctx.get("data", {})
                    )
                else:
                    # String ise, basit context oluştur
                    self.create_context(
                        context_type="general",
                        title=str(ctx),
                        data={}
                    )
        
        logger.info(f"✅ Auto-updated from conversation: {len(extracted.get('user_profile_updates', {}))} profile updates, {len(extracted.get('new_contexts', []))} new contexts")
        
        return extracted
    
    # ============================================================================
    # GEMINI CONTEXT PREPARATION
    # ============================================================================
    
    def get_context_for_gemini(self) -> str:
        """
        Gemini için FULL L4 context hazırla (limit yok)

        Returns:
            Tüm L4 memory JSON string
        """
        memory = self.load_memory()

        # Tüm L4'ü JSON olarak döndür
        return json.dumps(memory, ensure_ascii=False, indent=2)


    # ============================================================================
    # STATISTICS
    # ============================================================================
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        L4 istatistikleri
        
        Returns:
            İstatistikler
        """
        memory = self.load_memory()
        
        return {
            "total_contexts": len(memory["memory"]["contexts"]),
            "total_reminders": len(memory["memory"]["agent_notes"]["reminders"]),
            "pending_reminders": len([r for r in memory["memory"]["agent_notes"]["reminders"] if r.get("status") == "pending"]),
            "user_profile_completeness": self._calculate_profile_completeness(memory["user_profile"]),
            "last_updated": memory["metadata"]["last_updated"],
            "version": memory["metadata"]["version"]
        }
    
    def _calculate_profile_completeness(self, profile: Dict[str, Any]) -> float:
        """Profile completeness hesapla (0.0-1.0)"""
        total_fields = 0
        filled_fields = 0
        
        def count_fields(obj):
            nonlocal total_fields, filled_fields
            if isinstance(obj, dict):
                for value in obj.values():
                    if isinstance(value, (dict, list)):
                        count_fields(value)
                    else:
                        total_fields += 1
                        if value:  # Not empty
                            filled_fields += 1
            elif isinstance(obj, list):
                total_fields += 1
                if obj:  # Not empty
                    filled_fields += 1
        
        count_fields(profile)
        
        return filled_fields / total_fields if total_fields > 0 else 0.0
