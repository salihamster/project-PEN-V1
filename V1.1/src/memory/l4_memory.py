"""
L4 Memory System - User Profile + Context Memory
 provided to Gemini
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
    L4 Memory System
    
    - User Profile: Information that needs to be remembered continuously
    - Context Memory: Events, projects, meetings
    - Agent Notes: Reminders, daily notes
    
    Filled with Minimax, provided to Gemini as context.
    """
    
    def __init__(self, data_dir: Path, minimax_api_key: Optional[str] = None):
        """
        Initialize L4 Memory System
        
        Args:
            data_dir: Data directory
            minimax_api_key: Minimax API key (optional)
        """
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Tek JSON dosya
        self.memory_file = data_dir / "L4_memory.json"
        
        # Minimax API (Anthropic SDK ile)
        self.minimax_api_key = minimax_api_key or os.getenv("MINIMAX_API_KEY")
        self.minimax_client = None
        
        # Initialize Minimax client (if needed)
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
        
        # Initial setup
        self.ensure_memory_file()
    
    def ensure_memory_file(self):
        """Create L4_memory.json file"""
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
        """Load memory"""
        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading L4 memory: {e}")
            self.ensure_memory_file()
            return self.load_memory()
    
    def save_memory(self, data: Dict[str, Any]):
        """Save memory"""
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
        Get user profile (ALWAYS provided to Gemini)
        
        Returns:
            User profile dict
        """
        memory = self.load_memory()
        return memory["user_profile"]
    
    def update_user_profile(self, field_path: str, value: Any) -> bool:
        """
        Update user profile
        
        Args:
            field_path: Dot-separated path (e.g., "basic.name")
            value: New value
        
        Returns:
            Success status
        """
        try:
            memory = self.load_memory()
            
            # Parse path
            parts = field_path.split('.')
            current = memory["user_profile"]
            
            # Navigate to last field
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            # Update value
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
        Generate time-based context ID
        
        Args:
            context_type: Context type (meeting, project, task, etc.)
        
        Returns:
            Context ID (e.g., 20241220_100000_meeting)
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{timestamp}_{context_type}"
    
    def create_context(self, context_type: str, title: str, data: Dict[str, Any]) -> str:
        """
        Create new context
        
        Args:
            context_type: Context type (meeting, project, task, event, etc.)
            title: Title
            data: Context data (date, time, description, tags, calendar_event_id, task_id, related_contexts, etc.)
        
        Returns:
            Context ID
        """
        try:
            memory = self.load_memory()
            
            # Generate ID
            context_id = self.generate_context_id(context_type)
            
            # Create context (with new fields)
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
                # Google Services links
                "calendar_event_id": data.get("calendar_event_id"),
                "task_id": data.get("task_id"),
                # Context links
                "related_contexts": data.get("related_contexts", []),
                "related_data": data.get("related_data", {}),
                # Extra data
                "location": data.get("location"),
                "attendees": data.get("attendees", []),
                "notes": data.get("notes", "")
            }
            
            # Save
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
        Get context (with linked contexts)
        
        Args:
            context_id: Context ID
            include_linked: Also get linked contexts
        
        Returns:
            Context dict or None
        """
        memory = self.load_memory()
        context = memory["memory"]["contexts"].get(context_id)
        
        if not context:
            return None
        
        # Also get linked contexts
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
        Update context
        
        Args:
            context_id: Context ID
            updates: Fields to update
        
        Returns:
            Success status
        """
        try:
            memory = self.load_memory()
            
            if context_id not in memory["memory"]["contexts"]:
                logger.warning(f"Context not found: {context_id}")
                return False
            
            # Update
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
        Search contexts (advanced search)
        
        Args:
            query: Search query
            filters: Filters (type, date_range, tags, status, priority, etc.)
        
        Returns:
            Found contexts
        """
        memory = self.load_memory()
        results = []
        query_lower = query.lower()
        
        for context_id, context in memory["memory"]["contexts"].items():
            # None context'leri atla
            if context is None:
                continue

            # String search (extended)
            searchable_text = f"{context.get('title', '')} {context.get('description', '')} {context.get('notes', '')} {' '.join(context.get('tags', []))}"
            
            if query_lower in searchable_text.lower():
                # Filters
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
        
        # Sort by date (newest to oldest)
        results.sort(key=lambda x: x.get("created", ""), reverse=True)
        
        return results
    
    def link_contexts(self, context_id_1: str, context_id_2: str, relation_type: str = "related_to") -> bool:
        """
        Link two contexts together
        
        Args:
            context_id_1: First context ID
            context_id_2: Second context ID
            relation_type: Relation type (related_to, follows, precedes, part_of)
        
        Returns:
            Success status
        """
        try:
            memory = self.load_memory()
            
            # Check if both contexts exist
            if context_id_1 not in memory["memory"]["contexts"]:
                logger.warning(f"Context not found: {context_id_1}")
                return False
            
            if context_id_2 not in memory["memory"]["contexts"]:
                logger.warning(f"Context not found: {context_id_2}")
                return False
            
            # Add second context to first
            context1 = memory["memory"]["contexts"][context_id_1]
            if "related_contexts" not in context1:
                context1["related_contexts"] = []
            
            link_info = {
                "context_id": context_id_2,
                "relation": relation_type
            }
            
            # Duplicate check
            if not any(link["context_id"] == context_id_2 for link in context1["related_contexts"]):
                context1["related_contexts"].append(link_info)
                context1["last_updated"] = datetime.now().isoformat()
            
            # Add first context to second (bidirectional)
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
        Link WhatsApp/Email message to context
        
        Args:
            context_id: Context ID
            data_type: Data type (whatsapp_message, email, file, etc.)
            data_id: Data ID
        
        Returns:
            Success status
        """
        try:
            memory = self.load_memory()
            
            if context_id not in memory["memory"]["contexts"]:
                logger.warning(f"Context not found: {context_id}")
                return False
            
            context = memory["memory"]["contexts"][context_id]
            
            # Create related_data field if not exists
            if "related_data" not in context:
                context["related_data"] = {}
            
            # Create data type list if not exists
            if data_type not in context["related_data"]:
                context["related_data"][data_type] = []
            
            # Add (duplicate check)
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
        Create reminder
        
        Args:
            title: Title
            due_date: Due date (ISO format)
            priority: Priority (low, medium, high)
            context_id: Related context ID (optional)
        
        Returns:
            Reminder ID
        """
        try:
            memory = self.load_memory()
            
            # Generate ID
            reminder_id = self.generate_context_id("reminder")
            
            # Create reminder
            reminder = {
                "id": reminder_id,
                "title": title,
                "due_date": due_date,
                "priority": priority,
                "context_id": context_id,
                "status": "pending",
                "created": datetime.now().isoformat()
            }
            
            # Add
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
        Get pending reminders
        
        Returns:
            Pending reminders
        """
        memory = self.load_memory()
        reminders = memory["memory"]["agent_notes"]["reminders"]
        
        # Only pending ones
        pending = [r for r in reminders if r.get("status") == "pending"]
        
        # Sort by date
        pending.sort(key=lambda x: x.get("due_date", ""))
        
        return pending
    
    def mark_reminder_done(self, reminder_id: str) -> bool:
        """
        Mark reminder as done
        
        Args:
            reminder_id: Reminder ID
        
        Returns:
            Success status
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
        Add daily note
        
        Args:
            date: Date (YYYY-MM-DD)
            summary: Summary
            highlights: Highlights
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
        Extract information with Minimax (using Anthropic SDK)
        
        Args:
            text: Text to analyze
            task: Task description
        
        Returns:
            Extracted information (JSON)
        """
        if not self.minimax_client:
            logger.warning("Minimax client not initialized")
            return None
        
        try:
            # Minimax API call (using Anthropic SDK)
            message = self.minimax_client.messages.create(
                model="MiniMax-M2",  # M2 model (fast + smart)
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
            
            # Parse response
            content = ""
            for block in message.content:
                if block.type == "text":
                    content += block.text
            
            # Parse JSON
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Extract JSON
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
        Auto-extract information from conversation and update L4 (with Minimax)
        
        Args:
            messages: Conversation messages
        
        Returns:
            Extracted information
        """
        if not messages:
            return {"status": "no_messages"}
        
        # Load current L4
        memory = self.load_memory()
        current_profile = memory["user_profile"]
        
        # Convert conversation to text
        conversation_text = ""
        for msg in messages[-10:]:  # Last 10 messages
            if isinstance(msg, dict):
                role = msg.get("role", "user")
                
                # Support both 'content' (old format) and 'parts' (Gemini API format)
                parts = msg.get("parts", [])
                if not parts and "content" in msg: # Fallback for older format
                    content_val = msg.get("content", "")
                    parts = [content_val] if not isinstance(content_val, list) else content_val

                content = " ".join(str(p) for p in parts)
                conversation_text += f"{role}: {content}\n\n"
            else:
                # String message (fallback)
                conversation_text += f"{str(msg)}\n\n"
        
        # Extract information with Minimax (with current profile)
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
        
        # Update user profile
        if "user_profile_updates" in extracted:
            for field_path, value in extracted["user_profile_updates"].items():
                self.update_user_profile(field_path, value)
        
        # Create new contexts
        if "new_contexts" in extracted:
            for ctx in extracted["new_contexts"]:
                # Check if ctx is dict
                if isinstance(ctx, dict):
                    self.create_context(
                        context_type=ctx.get("type", "general"),
                        title=ctx.get("title", ""),
                        data=ctx.get("data", {})
                    )
                else:
                    # If string, create simple context
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
        Prepare FULL L4 context for Gemini (no limit)

        Returns:
            All L4 memory as JSON string
        """
        memory = self.load_memory()

        # Return all L4 as JSON
        return json.dumps(memory, ensure_ascii=False, indent=2)


    # ============================================================================
    # STATISTICS
    # ============================================================================
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        L4 statistics
        
        Returns:
            Statistics
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
        """Calculate profile completeness (0.0-1.0)"""
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
