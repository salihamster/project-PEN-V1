"""L4 User Profile and Context Layer

This module implements the L4 layer for the PEN agent.
REFACTORED VERSION: Pure Information & Context Repository.

Responsibilities:
- Maintain a persistent user profile (static info, preferences, behavioral directives).
- Store and manage contextual entities (projects, knowledge, plans, memories).
- Act as a bridge to the Calendar system (via linked_calendar_event_ids).
- Provide a simple list of available context headers to the System Prompt.
- Allow on-demand retrieval of full context content via tools.

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
    """Represents a contextual entity (Information/Knowledge) in the L4 layer.

    Types:
    - knowledge: General information, notes, documentation.
    - plan: To-do lists, strategies, roadmaps (not scheduled events).
    - memory: Important anecdotes, user history.
    - shadow: A context created specifically to back a Calendar Event (hidden from main list).
    """

    id: str
    title: str
    type: str = "knowledge"  # knowledge, plan, memory, shadow
    content: str = ""  # Main content (Markdown supported)
    description: str = ""  # Short summary for quick preview
    status: str = "active"  # active, archived
    priority: str = "medium"
    tags: List[str] = field(default_factory=list)
    
    # Bridges
    linked_calendar_event_ids: List[str] = field(default_factory=list)
    related_context_ids: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    access_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to a JSON-serializable dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "type": self.type,
            "content": self.content,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "tags": self.tags,
            "linked_calendar_event_ids": self.linked_calendar_event_ids,
            "related_context_ids": self.related_context_ids,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "access_count": self.access_count,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "L4Context":
        """Create an L4Context from a dictionary, filling missing fields."""
        return L4Context(
            id=data["id"],
            title=data.get("title", "Untitled"),
            type=data.get("type", "knowledge"),
            content=data.get("content", ""),
            description=data.get("description", ""),
            status=data.get("status", "active"),
            priority=data.get("priority", "medium"),
            tags=list(data.get("tags", [])),
            linked_calendar_event_ids=list(data.get("linked_calendar_event_ids", [])),
            related_context_ids=list(data.get("related_context_ids", [])),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            updated_at=data.get("updated_at", datetime.utcnow().isoformat()),
            access_count=data.get("access_count", 0),
        )


# =============================================================================
# L4 User Profile Layer
# =============================================================================


class L4UserProfile:
    """User profile and context management layer.

    Data layout (L4.json):
        {
          "user_profile": {
              "static_info": { ... },
              "behavioral_directives": [ ... ],
              ...
          },
          "contexts": { "by_id": { ... } },
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
        "behavioral_directives": [], # Rules for how the model should act
        "notes": [],
    }

    def __init__(self, data_dir: Optional[str] = None) -> None:
        if data_dir is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(script_dir, "data")

        self.data_dir = data_dir
        self.data_file = os.path.join(data_dir, "L4.json")

        # Initialize Gemini model
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
            self._reset_file()
        else:
            # Normalize existing file
            data = self._safe_load_file()
            normalized = self._normalize_data(data)
            self._write_file(normalized)

    def _reset_file(self) -> None:
        """Reset L4.json to default state."""
        initial_data = {
            "user_profile": dict(self.DEFAULT_USER_PROFILE),
            "contexts": {
                "by_id": {},
            },
            "metadata": {
                "created_at": datetime.utcnow().isoformat(),
                "last_updated": None,
                "version": "3.0"
            },
        }
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f, ensure_ascii=False, indent=2)

    def _safe_load_file(self) -> Dict[str, Any]:
        """Load JSON file with basic error handling."""
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
                "contexts": {"by_id": {}},
                "metadata": {"version": "3.0"}
            }

    def _normalize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure data structure matches expected schema."""
        # User Profile
        if "user_profile" not in data or not isinstance(data["user_profile"], dict):
            data["user_profile"] = {}
        user_profile = data["user_profile"]

        for key, default in self.DEFAULT_USER_PROFILE.items():
            if key not in user_profile:
                user_profile[key] = list(default) if isinstance(default, list) else default
        data["user_profile"] = user_profile

        # Contexts
        if "contexts" not in data or not isinstance(data["contexts"], dict):
            data["contexts"] = {"by_id": {}}
        contexts = data["contexts"]
        if "by_id" not in contexts or not isinstance(contexts["by_id"], dict):
            contexts["by_id"] = {}
        data["contexts"] = contexts
        
        # Remove legacy fields if they exist (clean up from previous versions)
        if "memory" in data:
            del data["memory"]
        if "index" in contexts:
            del contexts["index"]

        # Metadata
        if "metadata" not in data or not isinstance(data["metadata"], dict):
            data["metadata"] = {}
        metadata = data["metadata"]
        metadata.setdefault("version", "3.0")
        data["metadata"] = metadata

        return data

    def _write_file(self, data: Dict[str, Any]) -> None:
        """Write the entire data structure to disk."""
        data["metadata"]["last_updated"] = datetime.utcnow().isoformat()
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_profile(self) -> Dict[str, Any]:
        """Load the full L4 data structure."""
        data = self._safe_load_file()
        return self._normalize_data(data)

    def save_profile(self, data: Dict[str, Any]) -> None:
        """Save the L4 data structure to disk."""
        normalized = self._normalize_data(data)
        self._write_file(normalized)

    # ---------------------------------------------------------------------
    # Public API - User Profile & Directives
    # ---------------------------------------------------------------------

    def get_user_general_info(self) -> Dict[str, Any]:
        """Return general user info (static info)."""
        data = self.load_profile()
        return data.get("user_profile", {})

    def get_behavioral_directives(self) -> List[str]:
        """Return the list of rules for model behavior."""
        data = self.load_profile()
        return data.get("user_profile", {}).get("behavioral_directives", [])

    def add_behavioral_directive(self, directive: str) -> bool:
        """Add a new behavior rule."""
        data = self.load_profile()
        directives = data["user_profile"]["behavioral_directives"]
        if directive not in directives:
            directives.append(directive)
            self.save_profile(data)
            return True
        return False

    # ---------------------------------------------------------------------
    # Public API - Context Management (CRUD)
    # ---------------------------------------------------------------------

    def _generate_context_id(self, data: Dict[str, Any]) -> str:
        """Generate a new unique context ID."""
        ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        base = data.get("contexts", {}).get("by_id", {})
        counter = len(base) + 1
        return f"ctx_{ts}_{counter}"

    def create_context(self, 
                       title: str, 
                       content: str, 
                       type: str = "knowledge", 
                       tags: List[str] = None, 
                       description: str = "") -> str:
        """Create a new context and return its ID."""
        data = self.load_profile()
        ctx_id = self._generate_context_id(data)
        
        if tags is None:
            tags = []

        context = L4Context(
            id=ctx_id,
            title=title,
            type=type,
            content=content,
            description=description,
            tags=tags
        )

        data["contexts"]["by_id"][ctx_id] = context.to_dict()
        self.save_profile(data)
        return ctx_id

    def read_context(self, context_id_or_title: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve full context details by ID or Title.
        Updates access count.
        """
        data = self.load_profile()
        by_id = data["contexts"]["by_id"]
        
        target_ctx = None
        target_id = None
        
        # Try finding by ID
        if context_id_or_title in by_id:
            target_ctx = by_id[context_id_or_title]
            target_id = context_id_or_title
        else:
            # Try finding by Title (case-insensitive)
            query = context_id_or_title.lower().strip()
            for cid, cdata in by_id.items():
                if cdata.get("title", "").lower().strip() == query:
                    target_ctx = cdata
                    target_id = cid
                    break
        
        if target_ctx:
            # Update access count
            ctx_obj = L4Context.from_dict(target_ctx)
            ctx_obj.access_count += 1
            by_id[target_id] = ctx_obj.to_dict()
            self.save_profile(data)
            return ctx_obj.to_dict()
            
        return None

    def update_context(self, context_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing context."""
        data = self.load_profile()
        by_id = data["contexts"]["by_id"]
        if context_id not in by_id:
            return False

        ctx = L4Context.from_dict(by_id[context_id])

        for key, value in updates.items():
            if hasattr(ctx, key):
                setattr(ctx, key, value)
        
        # Special handling for appending content if requested
        if "append_content" in updates:
            if ctx.content:
                ctx.content += "\n\n" + updates["append_content"]
            else:
                ctx.content = updates["append_content"]

        ctx.updated_at = datetime.utcnow().isoformat()
        by_id[context_id] = ctx.to_dict()
        self.save_profile(data)
        return True

    def delete_context(self, context_id: str) -> bool:
        """Delete a context by ID and remove references."""
        data = self.load_profile()
        by_id = data["contexts"]["by_id"]
        
        if context_id not in by_id:
            return False
        
        del by_id[context_id]
        
        # Cleanup relations
        for other_id, other_data in by_id.items():
            ctx = L4Context.from_dict(other_data)
            if context_id in ctx.related_context_ids:
                ctx.related_context_ids.remove(context_id)
                by_id[other_id] = ctx.to_dict()
                
        self.save_profile(data)
        return True

    def link_to_calendar(self, context_id: str, event_id: str) -> bool:
        """Link a context to a calendar event ID."""
        data = self.load_profile()
        by_id = data["contexts"]["by_id"]
        
        if context_id not in by_id:
            return False
            
        ctx = L4Context.from_dict(by_id[context_id])
        if event_id not in ctx.linked_calendar_event_ids:
            ctx.linked_calendar_event_ids.append(event_id)
            ctx.updated_at = datetime.utcnow().isoformat()
            by_id[context_id] = ctx.to_dict()
            self.save_profile(data)
            return True
            
        return True

    def get_contexts_headers(self) -> List[Dict[str, str]]:
        """
        Get a filtered list of context headers (ID, Title, Type) for the System Prompt.
        Excludes 'shadow' contexts and archived ones.
        """
        data = self.load_profile()
        by_id = data["contexts"]["by_id"]
        
        headers = []
        for cid, cdata in by_id.items():
            if cdata.get("status") == "archived":
                continue
            if cdata.get("type") == "shadow":
                continue
                
            headers.append({
                "id": cid,
                "title": cdata.get("title", "Untitled"),
                "type": cdata.get("type", "knowledge"),
                "description": (cdata.get("description") or "")[:50]  # Short preview
            })
            
        # Sort by updated_at (recent first)
        headers.sort(key=lambda x: by_id[x["id"]].get("updated_at", ""), reverse=True)
        return headers

    def consolidate_profile_data(self) -> Dict[str, Any]:
        """
        Consolidates user profile data using Gemini.
        Refines lists (deduplicates, merges synonyms) without losing detail.
        Does NOT summarize into a narrative.
        """
        if not self.gemini_model:
            return {}
        
        data = self.load_profile()
        user_profile = data.get("user_profile", {})
        
        # Prepare the data for the LLM
        # We process key lists. Behavioral directives are handled carefully or skipped to preserve raw rules.
        fields_to_consolidate = ["preferences", "interests", "projects", "goals", "expertise", "relationships", "habits", "notes"]
        
        subset_profile = {k: user_profile.get(k, []) for k in fields_to_consolidate}
        
        prompt = f"""You are the Data Curator for the PEN Agent's memory.

Your task is to CLEAN and CONSOLIDATE the User Profile data.
The goal is to remove duplicates and merge synonymous items WITHOUT losing any specific details.

INPUT DATA:
{json.dumps(subset_profile, indent=2)}

INSTRUCTIONS:
1. **Deduplicate:** Remove exact duplicates.
2. **Merge Synonyms:** Combine items that mean exactly the same thing (e.g., "Likes Python" + "Python programming" -> "Python programming").
3. **Preserve Detail:** Do NOT summarize. If an item has a specific nuance, keep it.
4. **No Narratives:** Return the data in the exact same JSON structure (lists of strings).
5. **Directives:** Do not invent new fields.

Return ONLY the valid JSON object.
"""
        
        try:
            response = self.gemini_model.generate_content(prompt)
            cleaned_text = response.text.strip()
            
            # Extract JSON
            start = cleaned_text.find("{")
            end = cleaned_text.rfind("}")
            if start != -1 and end > start:
                json_str = cleaned_text[start : end + 1]
                cleaned_data = json.loads(json_str)
                
                # Apply updates to profile
                changes_made = False
                for k, v in cleaned_data.items():
                    if k in user_profile and isinstance(v, list):
                        # Simple check if list changed
                        if v != user_profile[k]:
                            user_profile[k] = v
                            changes_made = True
                
                if changes_made:
                    data["user_profile"] = user_profile
                    data["metadata"]["last_consolidated"] = datetime.utcnow().isoformat()
                    self.save_profile(data)
                    return {"status": "success", "message": "Profile consolidated"}
            
            return {"status": "no_change", "message": "No valid JSON returned or no changes needed"}

        except Exception as e:
            print(f"Error consolidating profile: {e}")
            return {"status": "error", "message": str(e)}

    # ---------------------------------------------------------------------
    # Insight Extraction (Gemini)
    # ---------------------------------------------------------------------

    def extract_insights_from_session(self, l1_session_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract user insights, new knowledge contexts, and behavioral directives.
        """
        if not self.gemini_model:
            return {"status": "no_llm", "insights": {}}

        messages = l1_session_context.get("messages", [])
        if not messages:
            return {"status": "no_messages", "insights": {}}

        conversation_lines = []
        for msg in messages:
            role = msg.get("role", "user").upper()
            content = msg.get("content", "")
            conversation_lines.append(f"{role}: {content}")
        conversation_text = "\n".join(conversation_lines)

        prompt = f"""Analyze the conversation and extract Long-Term Information for the PEN Agent.

We need to extract 3 types of data:
1. **User Profile Updates**: Facts about user (name, preferences, goals, etc.).
2. **Behavioral Directives**: Specific instructions user gave on HOW the agent should behave/act (e.g. "Don't use emojis", "Always write tests").
3. **Contexts (Knowledge/Plans)**: Structured information clusters (Projects, Ideas, Documentation). 
   - DO NOT extract Calendar Events (meetings, reminders) here. We only want pure information.
   - If user talks about a project, create a "knowledge" context for it.

OUTPUT JSON FORMAT:
{{
  "user_profile": {{
      "name": "...",
      "preferences": ["..."],
      "interests": ["..."],
      "projects": ["..."],
      "goals": ["..."],
      "relationships": ["..."],
      "habits": ["..."],
      "notes": ["..."]
  }},
  "behavioral_directives": [
      "string: exact rule/instruction from user"
  ],
  "new_contexts": [
      {{
          "title": "string (Unique Header)",
          "type": "knowledge|plan|memory",
          "content": "markdown string: Full detailed content/notes",
          "description": "string: One sentence summary",
          "tags": ["tag1", "tag2"]
      }}
  ]
}}

RULES:
- Be concise but lossless for 'content'.
- Ignore casual chat. Focus on permanent info.
- For behavioral_directives, be strict. Only add if user explicitly asked to change behavior.

CONVERSATION:
{conversation_text}

JSON:
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
            return {"status": "success", "insights": insights}
        except Exception as exc:
            return {"status": "error", "insights": {}, "error": str(exc)}

    def update_profile_from_session(self, l1_session_context: Dict[str, Any]) -> Dict[str, Any]:
        """Update L4 based on session insights."""
        extraction = self.extract_insights_from_session(l1_session_context)
        if extraction.get("status") != "success":
            return extraction

        insights = extraction.get("insights", {})
        data = self.load_profile()
        user_profile = data["user_profile"]

        # 1. Update Profile Fields
        updates_count = 0
        incoming_profile = insights.get("user_profile", {})
        
        for key, val in incoming_profile.items():
            if key in user_profile:
                if isinstance(val, list):
                    # Append unique items
                    for item in val:
                        if item not in user_profile[key]:
                            user_profile[key].append(item)
                            updates_count += 1
                elif isinstance(val, str) and val and not user_profile[key]:
                    user_profile[key] = val
                    updates_count += 1

        # 2. Update Behavioral Directives
        new_directives = insights.get("behavioral_directives", [])
        for direct in new_directives:
            if direct not in user_profile["behavioral_directives"]:
                user_profile["behavioral_directives"].append(direct)
                updates_count += 1

        # 3. Create New Contexts
        contexts_created = 0
        new_contexts = insights.get("new_contexts", [])
        for ctx in new_contexts:
            self.create_context(
                title=ctx.get("title", "Untitled"),
                content=ctx.get("content", ""),
                type=ctx.get("type", "knowledge"),
                tags=ctx.get("tags", []),
                description=ctx.get("description", "")
            )
            contexts_created += 1

        data["user_profile"] = user_profile
        self.save_profile(data)

        return {
            "status": "success",
            "updates_count": updates_count,
            "contexts_created": contexts_created
        }