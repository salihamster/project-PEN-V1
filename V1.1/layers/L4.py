"""L4 User Profile and Context Layer

This module implements the L4 layer for the PEN agent.

Responsibilities:
- Maintain a persistent user profile (name, preferences, projects, goals, etc.)
- Store and manage contextual entities (projects, tasks, events, meetings, notes)
- Maintain a flexible memory system for user-related information outside the profile
- Extract insights from L1 session data using Gemini
- Provide a simple search API over stored contexts

All data is stored in a single JSON file (L4.json) under layers/data.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import google.generativeai as genai

from src.config import GEMINI_API_KEY  # type: ignore


# =============================================================================
# Data Models
# =============================================================================


@dataclass
class L4Context:
    """Represents a contextual entity in the L4 layer.

    This can be a project, task, event, meeting, note, or any other
    time-bound or logically grouped entity.
    """

    id: str
    type: str
    title: str
    date: Optional[str] = None
    time: Optional[str] = None
    status: str = "unknown"
    priority: str = "medium"
    tags: List[str] = field(default_factory=list)
    description: str = ""
    location: Optional[str] = None
    attendees: List[str] = field(default_factory=list)
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    calendar_event_id: Optional[str] = None
    task_id: Optional[str] = None
    related_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to a JSON-serializable dictionary."""
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "date": self.date,
            "time": self.time,
            "status": self.status,
            "priority": self.priority,
            "tags": self.tags,
            "description": self.description,
            "location": self.location,
            "attendees": self.attendees,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "calendar_event_id": self.calendar_event_id,
            "task_id": self.task_id,
            "related_ids": self.related_ids,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "L4Context":
        """Create an L4Context from a dictionary, filling missing fields."""
        return L4Context(
            id=data["id"],
            type=data.get("type", "other"),
            title=data.get("title", ""),
            date=data.get("date"),
            time=data.get("time"),
            status=data.get("status", "unknown"),
            priority=data.get("priority", "medium"),
            tags=list(data.get("tags", [])),
            description=data.get("description", ""),
            location=data.get("location"),
            attendees=list(data.get("attendees", [])),
            notes=data.get("notes", ""),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            updated_at=data.get("updated_at", datetime.utcnow().isoformat()),
            calendar_event_id=data.get("calendar_event_id"),
            task_id=data.get("task_id"),
            related_ids=list(data.get("related_ids", [])),
        )


# =============================================================================
# L4 User Profile Layer
# =============================================================================


class L4UserProfile:
    """User profile and context management layer.

    This is the single source of truth for user-related long-term information
    and structured contexts (projects, tasks, events, etc.).

    Data layout (L4.json):
        {
          "user_profile": { ... },
          "memory": { ... },
          "contexts": { "by_id": { ... }, "index": {} },
          "metadata": { ... }
        }
    """

    DEFAULT_USER_PROFILE: Dict[str, Any] = {
        "name": "",
        "preferences": [],
        "interests": [],
        "projects": [],
        "goals": [],
        "expertise": [],
        "relationships": [],
        "habits": [],
        "notes": [],
    }

    def __init__(self, data_dir: Optional[str] = None) -> None:
        if data_dir is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(script_dir, "data")

        self.data_dir = data_dir
        self.data_file = os.path.join(data_dir, "L4.json")

        # Initialize Gemini model (optional but recommended)
        self.gemini_model: Optional[genai.GenerativeModel]
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            self.gemini_model = genai.GenerativeModel("gemini-2.0-flash-exp")
        else:
            self.gemini_model = None

        self._ensure_data_file()

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------

    def _ensure_data_file(self) -> None:
        """Ensure that the L4.json file exists with a valid schema."""
        os.makedirs(self.data_dir, exist_ok=True)

        if not os.path.exists(self.data_file):
            initial_data = {
                "user_profile": dict(self.DEFAULT_USER_PROFILE),
                "contexts": {
                    "by_id": {},
                    "index": {},
                },
                "metadata": {
                    "created_at": datetime.utcnow().isoformat(),
                    "last_updated": None,
                    "total_insights": 0,
                    "sessions_processed": 0,
                    "total_contexts": 0,
                },
            }
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(initial_data, f, ensure_ascii=False, indent=2)
        else:
            # Normalize existing file
            data = self._safe_load_file()
            normalized = self._normalize_data(data)
            self._write_file(normalized)

    def _safe_load_file(self) -> Dict[str, Any]:
        """Load JSON file with basic error handling.

        If loading fails, a fresh default structure is returned.
        """
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            # Backup corrupt file
            backup_path = self.data_file + ".backup"
            try:
                if os.path.exists(self.data_file):
                    os.replace(self.data_file, backup_path)
            except Exception:
                pass
            return {
                "user_profile": dict(self.DEFAULT_USER_PROFILE),
                "memory": {},
                "contexts": {"by_id": {}, "index": {}},
                "metadata": {
                    "created_at": datetime.utcnow().isoformat(),
                    "last_updated": None,
                    "total_insights": 0,
                    "sessions_processed": 0,
                    "total_contexts": 0,
                },
            }

    def _normalize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure data structure matches expected schema.

        Adds missing keys and default values as needed.
        """
        if "user_profile" not in data or not isinstance(data["user_profile"], dict):
            data["user_profile"] = {}
        user_profile = data["user_profile"]

        # Ensure all user profile keys exist
        for key, default in self.DEFAULT_USER_PROFILE.items():
            if key not in user_profile:
                user_profile[key] = list(default) if isinstance(default, list) else default

        data["user_profile"] = user_profile

        # Memory
        if "memory" not in data or not isinstance(data["memory"], dict):
            data["memory"] = {}

        # Contexts
        if "contexts" not in data or not isinstance(data["contexts"], dict):
            data["contexts"] = {"by_id": {}, "index": {}}
        contexts = data["contexts"]
        if "by_id" not in contexts or not isinstance(contexts["by_id"], dict):
            contexts["by_id"] = {}
        if "index" not in contexts or not isinstance(contexts["index"], dict):
            contexts["index"] = {}
        data["contexts"] = contexts

        # Metadata
        if "metadata" not in data or not isinstance(data["metadata"], dict):
            data["metadata"] = {}
        metadata = data["metadata"]
        metadata.setdefault("created_at", datetime.utcnow().isoformat())
        metadata.setdefault("last_updated", None)
        metadata.setdefault("total_insights", 0)
        metadata.setdefault("sessions_processed", 0)
        metadata.setdefault("total_contexts", len(contexts["by_id"]))
        data["metadata"] = metadata

        return data

    def _write_file(self, data: Dict[str, Any]) -> None:
        """Write the entire data structure to disk."""
        data["metadata"]["last_updated"] = datetime.utcnow().isoformat()
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_profile(self) -> Dict[str, Any]:
        """Load the full L4 data structure from disk and normalize it."""
        data = self._safe_load_file()
        return self._normalize_data(data)

    def save_profile(self, data: Dict[str, Any]) -> None:
        """Save the L4 data structure to disk.

        This should be the only method used to persist changes.
        """
        normalized = self._normalize_data(data)
        self._write_file(normalized)

    # ---------------------------------------------------------------------
    # Public API - User Profile
    # ---------------------------------------------------------------------

    def get_profile_for_context(self) -> Dict[str, Any]:
        """Return the user_profile section for use in agent context."""
        data = self.load_profile()
        return data.get("user_profile", {})

    def get_profile_summary(self) -> str:
        """Return a human-readable summary of the user profile."""
        data = self.load_profile()
        user_profile = data.get("user_profile", {})

        lines: List[str] = ["User Profile:"]

        name = user_profile.get("name")
        if name:
            lines.append(f"Name: {name}")

        for category in [
            "preferences",
            "interests",
            "projects",
            "goals",
            "expertise",
            "relationships",
            "habits",
        ]:
            items = user_profile.get(category, [])
            if items:
                lines.append("")
                lines.append(f"{category.title()}:")
                for item in items[:5]:
                    lines.append(f"  - {item}")
                remaining = len(items) - 5
                if remaining > 0:
                    lines.append(f"  ... and {remaining} more")

        notes = user_profile.get("notes", [])
        if notes:
            lines.append("")
            lines.append("Notes:")
            for note in notes[:5]:
                lines.append(f"  - {note}")

        return "\n".join(lines)

    # ---------------------------------------------------------------------
    # Public API - Memory Management
    # ---------------------------------------------------------------------

    def set_memory(self, key: str, value: Any) -> None:
        """Set a memory item for the user.

        Args:
            key: Memory key (string identifier)
            value: Any value to store (will be JSON-serialized)
        """
        data = self.load_profile()
        data["memory"][key] = value
        self.save_profile(data)

    def get_memory(self, key: str, default: Any = None) -> Any:
        """Get a memory item for the user.

        Args:
            key: Memory key
            default: Default value if key not found

        Returns:
            The stored value or default
        """
        data = self.load_profile()
        return data["memory"].get(key, default)

    def delete_memory(self, key: str) -> bool:
        """Delete a memory item.

        Args:
            key: Memory key to delete

        Returns:
            True if deleted, False if not found
        """
        data = self.load_profile()
        if key in data["memory"]:
            del data["memory"][key]
            self.save_profile(data)
            return True
        return False

    def get_all_memory(self) -> Dict[str, Any]:
        """Get all memory items.

        Returns:
            Dictionary of all memory items
        """
        data = self.load_profile()
        return dict(data["memory"])

    def clear_memory(self) -> None:
        """Clear all memory items."""
        data = self.load_profile()
        data["memory"] = {}
        self.save_profile(data)

    def search_memory(self, query: str) -> List[Dict[str, Any]]:
        """Search memory items by key or value.

        Args:
            query: Search query (case-insensitive)

        Returns:
            List of matching memory items with keys and values
        """
        data = self.load_profile()
        results = []
        query_lower = query.lower()

        for key, value in data["memory"].items():
            key_lower = key.lower()
            value_str = str(value).lower()

            if query_lower in key_lower or query_lower in value_str:
                results.append({
                    "key": key,
                    "value": value
                })

        return results

    # ---------------------------------------------------------------------
    # Public API - Context Management
    # ---------------------------------------------------------------------

    def _generate_context_id(self, data: Dict[str, Any]) -> str:
        """Generate a new unique context ID."""
        ts = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        base = data.get("contexts", {}).get("by_id", {})
        counter = len(base) + 1
        return f"ctx_{ts}_{counter}"

    def create_context(self, context_type: str, title: str, data_fields: Dict[str, Any]) -> str:
        """Create a new context and return its ID."""
        data = self.load_profile()
        ctx_id = self._generate_context_id(data)

        context = L4Context(
            id=ctx_id,
            type=context_type,
            title=title,
            date=data_fields.get("date"),
            time=data_fields.get("time"),
            status=data_fields.get("status", "planned"),
            priority=data_fields.get("priority", "medium"),
            tags=list(data_fields.get("tags", [])),
            description=data_fields.get("description", ""),
            location=data_fields.get("location"),
            attendees=list(data_fields.get("attendees", [])),
            notes=data_fields.get("notes", ""),
            calendar_event_id=data_fields.get("calendar_event_id"),
            task_id=data_fields.get("task_id"),
        )

        data["contexts"]["by_id"][ctx_id] = context.to_dict()
        data["metadata"]["total_contexts"] = len(data["contexts"]["by_id"])
        self.save_profile(data)
        return ctx_id

    def update_context(self, context_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing context.

        Returns True if updated, False if not found.
        """
        data = self.load_profile()
        by_id = data["contexts"]["by_id"]
        if context_id not in by_id:
            return False

        ctx = L4Context.from_dict(by_id[context_id])

        for key, value in updates.items():
            if hasattr(ctx, key):
                setattr(ctx, key, value)

        ctx.updated_at = datetime.utcnow().isoformat()
        by_id[context_id] = ctx.to_dict()
        self.save_profile(data)
        return True

    def link_contexts(self, context_id_1: str, context_id_2: str, relation_type: str = "related_to") -> bool:
        """Link two contexts together.

        relation_type is currently informational only.
        Returns True if both contexts exist, False otherwise.
        """
        data = self.load_profile()
        by_id = data["contexts"]["by_id"]

        if context_id_1 not in by_id or context_id_2 not in by_id:
            return False

        ctx1 = L4Context.from_dict(by_id[context_id_1])
        ctx2 = L4Context.from_dict(by_id[context_id_2])

        if context_id_2 not in ctx1.related_ids:
            ctx1.related_ids.append(context_id_2)
        if context_id_1 not in ctx2.related_ids:
            ctx2.related_ids.append(context_id_1)

        now = datetime.utcnow().isoformat()
        ctx1.updated_at = now
        ctx2.updated_at = now

        by_id[context_id_1] = ctx1.to_dict()
        by_id[context_id_2] = ctx2.to_dict()
        self.save_profile(data)
        return True

    def get_context(self, context_id: str, include_linked: bool = True) -> Optional[Dict[str, Any]]:
        """Return a context by ID, optionally including linked contexts."""
        data = self.load_profile()
        by_id = data["contexts"]["by_id"]
        if context_id not in by_id:
            return None

        ctx = L4Context.from_dict(by_id[context_id])
        result: Dict[str, Any] = ctx.to_dict()

        if include_linked and ctx.related_ids:
            linked: List[Dict[str, Any]] = []
            for rid in ctx.related_ids:
                raw = by_id.get(rid)
                if raw:
                    linked.append(L4Context.from_dict(raw).to_dict())
            result["linked_contexts_details"] = linked

        return result

    def delete_context(self, context_id: str) -> bool:
        """Delete a context by ID.
        
        Also removes all links to this context from other contexts.
        
        Args:
            context_id: Context ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        data = self.load_profile()
        by_id = data["contexts"]["by_id"]
        
        if context_id not in by_id:
            return False
        
        # Remove the context
        del by_id[context_id]
        
        # Remove all references to this context from other contexts
        for other_id, other_ctx_data in by_id.items():
            other_ctx = L4Context.from_dict(other_ctx_data)
            if context_id in other_ctx.related_ids:
                other_ctx.related_ids.remove(context_id)
                other_ctx.updated_at = datetime.utcnow().isoformat()
                by_id[other_id] = other_ctx.to_dict()
        
        # Update metadata
        data["metadata"]["total_contexts"] = len(by_id)
        self.save_profile(data)
        return True

    def search_contexts(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search contexts by simple text query and optional filters.

        This is intentionally simple and in-memory. If it becomes slow,
        a proper index can be implemented later.
        """
        data = self.load_profile()
        by_id = data["contexts"]["by_id"]
        filters = filters or {}

        query_lower = query.lower().strip()
        results: List[Dict[str, Any]] = []

        for raw in by_id.values():
            ctx = L4Context.from_dict(raw)

            # Filter by type, status, priority
            if "type" in filters and ctx.type != filters["type"]:
                continue
            if "status" in filters and ctx.status != filters["status"]:
                continue
            if "priority" in filters and ctx.priority != filters["priority"]:
                continue

            # Filter by tags (intersection)
            if "tags" in filters:
                required_tags = set(filters["tags"])
                if not required_tags.intersection(set(ctx.tags)):
                    continue

            # Filter by date range
            if "date_range" in filters and ctx.date is not None:
                dr = filters["date_range"]
                if "start" in dr and ctx.date < dr["start"]:
                    continue
                if "end" in dr and ctx.date > dr["end"]:
                    continue

            # Text match
            if query_lower:
                haystack = " ".join(
                    [
                        ctx.title or "",
                        ctx.description or "",
                        " ".join(ctx.tags),
                        ctx.notes or "",
                    ]
                ).lower()
                if query_lower not in haystack:
                    continue

            results.append(ctx.to_dict())

        return results

    # ---------------------------------------------------------------------
    # Insight Extraction from L1
    # ---------------------------------------------------------------------

    def extract_insights_from_session(self, l1_session_context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract user insights from a full L1 session using Gemini.

        Returns a dict with keys:
            - status: "success" | "no_llm" | "no_messages" | "parse_error" | "error"
            - insights: {...} (see prompt template)
            - error: optional error message
        """
        if not self.gemini_model:
            return {"status": "no_llm", "insights": {}}

        messages = l1_session_context.get("messages", [])
        if not messages:
            return {"status": "no_messages", "insights": {}}

        # Build plain text conversation
        conversation_lines: List[str] = []
        for msg in messages:
            role = msg.get("role", "user").upper()
            content = msg.get("content", "")
            conversation_lines.append(f"{role}: {content}")
        conversation_text = "\n".join(conversation_lines)

        prompt = f"""Analyze the following conversation and extract ALL factual information about the USER in detail.

CATEGORIES:
- name: User's name (if mentioned)
- preferences: User preferences, likes, dislikes, choices
- interests: Topics, subjects, areas user is interested in
- projects: ALL projects user is working on or planning (extract FULL details)
- goals: User's goals, objectives, and plans
- expertise: User's skills, knowledge areas, and competencies
- relationships: People mentioned (names, relationships, roles)
- habits: User's habits, routines, and patterns
- notes: Any other important facts, corrections, or clarifications
- contexts: Important tasks/events/meetings/projects as structured entries with MAXIMUM detail

OUTPUT STRICT JSON WITH THIS SHAPE:
{{
  "name": "string or empty string",
  "preferences": ["..."],
  "interests": ["..."],
  "projects": ["..."],
  "goals": ["..."],
  "expertise": ["..."],
  "relationships": ["..."],
  "habits": ["..."],
  "notes": ["..."],
  "contexts": [
    {{
      "type": "project|task|event|meeting|note|other",
      "title": "string",
      "date": "YYYY-MM-DD or null",
      "time": "HH:MM or null",
      "status": "planned|active|completed|cancelled|unknown",
      "priority": "low|medium|high",
      "tags": ["..."],
      "description": "string - DETAILED description with all known information",
      "location": "string or null",
      "attendees": ["..."],
      "notes": "string - ALL additional details, context, corrections, and important information"
    }}
  ]
}}

CRITICAL RULES:
1. Extract ALL FACTS explicitly mentioned by the user - be thorough and comprehensive
2. For projects/contexts: Include EVERY detail mentioned (deadlines, team members, status updates, corrections, etc.)
3. If user corrects information (e.g., "X is NOT Y"), capture the correction in notes field
4. For descriptions and notes: Be detailed and specific, not generic
5. Include context and background information when available
6. If a field has no data, use empty string, empty array, or null as appropriate
7. ALWAYS return valid JSON only. No explanation around it.
8. Prioritize accuracy over brevity - capture complete information

EXAMPLES OF GOOD vs BAD EXTRACTION:

BAD (too generic):
{{
  "contexts": [{{
    "title": "Aliye Project",
    "description": "General notes about the user's Aliye project.",
    "notes": ""
  }}]
}}

GOOD (detailed and accurate):
{{
  "contexts": [{{
    "title": "Aliye System",
    "description": "Aliye System is an AI system project being developed by the user. It is a separate project from Penelope.",
    "notes": "Important correction: This is NOT 'Penelope's free consciousness version' as previously incorrectly stated. User explicitly corrected this misinformation. Accurate details should be verified with user."
  }}]
}}

CONVERSATION:
{conversation_text}

Return ONLY the JSON object with MAXIMUM detail:
"""

        try:
            response = self.gemini_model.generate_content(prompt)
            raw_text = response.text or ""

            start = raw_text.find("{")
            end = raw_text.rfind("}")
            if start == -1 or end <= start:
                return {"status": "parse_error", "insights": {}}

            json_str = raw_text[start : end + 1]
            insights = json.loads(json_str)
            if not isinstance(insights, dict):
                return {"status": "parse_error", "insights": {}}

            # Ensure minimal structure
            for key, default in self.DEFAULT_USER_PROFILE.items():
                insights.setdefault(key, [] if isinstance(default, list) else "")
            insights.setdefault("contexts", [])

            return {"status": "success", "insights": insights}
        except Exception as exc:  # noqa: BLE001
            return {"status": "error", "insights": {}, "error": str(exc)}

    def update_profile_from_session(self, l1_session_context: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile and contexts using insights from an L1 session.

        Returns a status dict with:
            - status: "success" | "no_llm" | "no_messages" | "parse_error" | "error"
            - updates_count: int (number of new items added to profile lists)
            - contexts_created: int
            - session_id: optional session id
        """
        extraction = self.extract_insights_from_session(l1_session_context)
        status = extraction.get("status")
        if status != "success":
            return {"status": status, "updates_count": 0, "contexts_created": 0}

        insights: Dict[str, Any] = extraction.get("insights", {})

        data = self.load_profile()
        user_profile = data["user_profile"]

        # Ensure keys exist
        for key, default in self.DEFAULT_USER_PROFILE.items():
            user_profile.setdefault(key, [] if isinstance(default, list) else default)

        updates_count = 0

        # Name update
        incoming_name = insights.get("name") or ""
        if isinstance(incoming_name, str) and incoming_name.strip() and not user_profile.get("name"):
            user_profile["name"] = incoming_name.strip()
            updates_count += 1

        # List categories
        for category in [
            "preferences",
            "interests",
            "projects",
            "goals",
            "expertise",
            "relationships",
            "habits",
            "notes",
        ]:
            existing: List[str] = list(user_profile.get(category, []))
            new_items: List[str] = list(insights.get(category, [])) if isinstance(insights.get(category), list) else []

            for item in new_items:
                if not isinstance(item, str):
                    continue
                item_norm = item.strip()
                if not item_norm:
                    continue
                
                # Improved duplicate check - only skip if EXACT match or very similar
                item_lower = item_norm.lower()
                is_duplicate = False
                
                for e in existing:
                    e_lower = e.lower()
                    # Exact match
                    if item_lower == e_lower:
                        is_duplicate = True
                        break
                    # Very similar (>80% overlap) - only for short strings
                    if len(item_lower) < 50 and len(e_lower) < 50:
                        if item_lower in e_lower or e_lower in item_lower:
                            is_duplicate = True
                            break
                
                if not is_duplicate:
                    existing.append(item_norm)
                    updates_count += 1

            user_profile[category] = existing

        data["user_profile"] = user_profile

        # Contexts from insights
        contexts_created = 0
        contexts_updated = 0
        raw_contexts = insights.get("contexts", [])
        
        if isinstance(raw_contexts, list):
            existing_contexts = data["contexts"]["by_id"]
            
            for c in raw_contexts:
                if not isinstance(c, dict):
                    continue
                c_type = c.get("type", "other") or "other"
                c_title = c.get("title") or ""
                if not c_title.strip():
                    continue
                
                c_title_norm = c_title.strip()
                c_date = c.get("date")
                
                # Check for duplicate context (same title + type, or same title + date)
                existing_ctx_id = None
                for ctx_id, ctx_data in existing_contexts.items():
                    existing_title = ctx_data.get("title", "").strip()
                    existing_type = ctx_data.get("type", "")
                    existing_date = ctx_data.get("date")
                    
                    # Match by title + type
                    if existing_title.lower() == c_title_norm.lower() and existing_type == c_type:
                        existing_ctx_id = ctx_id
                        break
                    
                    # Match by title + date (for events/meetings)
                    if c_date and existing_date:
                        if existing_title.lower() == c_title_norm.lower() and existing_date == c_date:
                            existing_ctx_id = ctx_id
                            break
                
                fields = {
                    "date": c_date,
                    "time": c.get("time"),
                    "status": c.get("status", "planned") or "planned",
                    "priority": c.get("priority", "medium") or "medium",
                    "tags": c.get("tags", []) or [],
                    "description": c.get("description", "") or "",
                    "location": c.get("location"),
                    "attendees": c.get("attendees", []) or [],
                    "notes": c.get("notes", "") or "",
                    "calendar_event_id": None,
                    "task_id": None,
                }
                
                if existing_ctx_id:
                    # Update existing context with new information
                    existing_ctx = L4Context.from_dict(existing_contexts[existing_ctx_id])
                    
                    # Merge notes (append new info)
                    new_notes = fields.get("notes", "")
                    if new_notes and new_notes not in existing_ctx.notes:
                        if existing_ctx.notes:
                            existing_ctx.notes += "\n\n" + new_notes
                        else:
                            existing_ctx.notes = new_notes
                    
                    # Update other fields if they have new info
                    if fields.get("description") and not existing_ctx.description:
                        existing_ctx.description = fields["description"]
                    if fields.get("date") and not existing_ctx.date:
                        existing_ctx.date = fields["date"]
                    if fields.get("time") and not existing_ctx.time:
                        existing_ctx.time = fields["time"]
                    if fields.get("location") and not existing_ctx.location:
                        existing_ctx.location = fields["location"]
                    
                    # Merge tags
                    for tag in fields.get("tags", []):
                        if tag not in existing_ctx.tags:
                            existing_ctx.tags.append(tag)
                    
                    # Merge attendees
                    for attendee in fields.get("attendees", []):
                        if attendee not in existing_ctx.attendees:
                            existing_ctx.attendees.append(attendee)
                    
                    # Update status/priority if more specific
                    if fields.get("status") != "planned" and existing_ctx.status == "planned":
                        existing_ctx.status = fields["status"]
                    if fields.get("priority") != "medium" and existing_ctx.priority == "medium":
                        existing_ctx.priority = fields["priority"]
                    
                    existing_ctx.updated_at = datetime.utcnow().isoformat()
                    existing_contexts[existing_ctx_id] = existing_ctx.to_dict()
                    contexts_updated += 1
                else:
                    # Create new context
                    self.create_context(c_type, c_title_norm, fields)
                    contexts_created += 1

        # Metadata
        data["metadata"]["total_insights"] = int(data["metadata"].get("total_insights", 0)) + updates_count
        data["metadata"]["sessions_processed"] = int(data["metadata"].get("sessions_processed", 0)) + 1

        self.save_profile(data)

        return {
            "status": "success",
            "updates_count": updates_count,
            "contexts_created": contexts_created,
            "session_id": l1_session_context.get("session_id"),
        }
