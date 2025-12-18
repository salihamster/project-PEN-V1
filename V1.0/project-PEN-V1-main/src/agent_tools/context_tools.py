"""Context Tools - L4 User Profile Integration

Simplified context tools for new L4 architecture.
All methods proxy to L4UserProfile's context API.
"""

import json
from typing import Any, Dict, List, Optional

from layers.L4 import L4UserProfile  # type: ignore
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ContextTools:
    """Context management tools integrated with L4UserProfile."""

    def __init__(self, l4: L4UserProfile) -> None:
        """Initialize Context Tools.

        Args:
            l4: L4UserProfile instance
        """
        self.l4 = l4

    def create_context(
        self,
        context_type: str,
        title: str,
        date: Optional[str] = None,
        time: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: str = "planned",
        priority: str = "medium",
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        notes: Optional[str] = None,
        calendar_event_id: Optional[str] = None,
        task_id: Optional[str] = None,
        related_context_ids: Optional[List[str]] = None,
    ) -> str:
        """Create a new context.

        Args:
            context_type: Type of context (project, task, event, meeting, note, other)
            title: Context title
            date: Date in YYYY-MM-DD format
            time: Time in HH:MM format
            description: Context description
            tags: List of tags
            status: Status (planned, active, completed, cancelled, unknown)
            priority: Priority (low, medium, high)
            location: Location
            attendees: List of attendee names
            notes: Additional notes
            calendar_event_id: Google Calendar event ID
            task_id: Google Tasks task ID
            related_context_ids: List of related context IDs to link

        Returns:
            JSON string with status and context_id
        """
        try:
            logger.info(f"Creating context: {title} ({context_type})")

            # Parse tags if it's a string representation of a list
            parsed_tags = tags or []
            if isinstance(tags, str):
                try:
                    # Try to parse as JSON first
                    import ast
                    parsed_tags = ast.literal_eval(tags)
                    if not isinstance(parsed_tags, list):
                        parsed_tags = [tags]
                except (ValueError, SyntaxError):
                    # If parsing fails, treat as single tag
                    parsed_tags = [tags] if tags else []
            elif not isinstance(tags, list):
                # Convert any other type to list
                parsed_tags = [str(tags)] if tags else []

            # Parse attendees if it's a string
            parsed_attendees = attendees or []
            if isinstance(attendees, str):
                try:
                    import ast
                    parsed_attendees = ast.literal_eval(attendees)
                    if not isinstance(parsed_attendees, list):
                        parsed_attendees = [attendees]
                except (ValueError, SyntaxError):
                    parsed_attendees = [attendees] if attendees else []
            elif not isinstance(attendees, list):
                parsed_attendees = [str(attendees)] if attendees else []

            # Parse related_context_ids if it's a string
            parsed_related = related_context_ids or []
            if isinstance(related_context_ids, str):
                try:
                    import ast
                    parsed_related = ast.literal_eval(related_context_ids)
                    if not isinstance(parsed_related, list):
                        parsed_related = [related_context_ids]
                except (ValueError, SyntaxError):
                    parsed_related = [related_context_ids] if related_context_ids else []
            elif not isinstance(related_context_ids, list):
                parsed_related = [str(related_context_ids)] if related_context_ids else []

            data_fields = {
                "date": date,
                "time": time,
                "description": description or "",
                "tags": parsed_tags,
                "status": status,
                "priority": priority,
                "location": location,
                "attendees": parsed_attendees,
                "notes": notes or "",
                "calendar_event_id": calendar_event_id,
                "task_id": task_id,
            }

            context_id = self.l4.create_context(context_type, title, data_fields)

            # Link related contexts if provided
            if parsed_related:
                for related_id in parsed_related:
                    self.l4.link_contexts(context_id, related_id, "related_to")

            return json.dumps(
                {
                    "status": "success",
                    "context_id": context_id,
                    "message": f"Context created: {title}",
                    "details": {
                        "type": context_type,
                        "title": title,
                        "date": date,
                        "time": time,
                        "tags": parsed_tags,
                    },
                },
                ensure_ascii=False,
            )

        except Exception as e:
            logger.error(f"Error creating context: {e}")
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def update_context(
        self,
        context_id: str,
        title: Optional[str] = None,
        date: Optional[str] = None,
        time: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        notes: Optional[str] = None,
        calendar_event_id: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> str:
        """Update an existing context.

        Args:
            context_id: Context ID to update
            title: New title
            date: New date
            time: New time
            description: New description
            tags: New tags
            status: New status
            priority: New priority
            location: New location
            attendees: New attendees
            notes: New notes
            calendar_event_id: New calendar event ID
            task_id: New task ID

        Returns:
            JSON string with status
        """
        try:
            logger.info(f"Updating context: {context_id}")

            updates: Dict[str, Any] = {}
            if title is not None:
                updates["title"] = title
            if date is not None:
                updates["date"] = date
            if time is not None:
                updates["time"] = time
            if description is not None:
                updates["description"] = description
            if tags is not None:
                updates["tags"] = tags
            if status is not None:
                updates["status"] = status
            if priority is not None:
                updates["priority"] = priority
            if location is not None:
                updates["location"] = location
            if attendees is not None:
                updates["attendees"] = attendees
            if notes is not None:
                updates["notes"] = notes
            if calendar_event_id is not None:
                updates["calendar_event_id"] = calendar_event_id
            if task_id is not None:
                updates["task_id"] = task_id

            if not updates:
                return json.dumps(
                    {"status": "error", "message": "No fields to update"},
                    ensure_ascii=False,
                )

            success = self.l4.update_context(context_id, updates)

            if success:
                return json.dumps(
                    {
                        "status": "success",
                        "message": f"Context updated: {context_id}",
                        "updated_fields": list(updates.keys()),
                    },
                    ensure_ascii=False,
                )
            else:
                return json.dumps(
                    {"status": "error", "message": "Context not found"},
                    ensure_ascii=False,
                )

        except Exception as e:
            logger.error(f"Error updating context: {e}")
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def search_contexts(
        self,
        query: str,
        context_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        date_start: Optional[str] = None,
        date_end: Optional[str] = None,
        limit: int = 10,
    ) -> str:
        """Search contexts by query and optional filters.

        Args:
            query: Search query (searches title, description, tags, notes)
            context_type: Filter by context type
            tags: Filter by tags (intersection)
            status: Filter by status
            priority: Filter by priority
            date_start: Filter by date range start (YYYY-MM-DD)
            date_end: Filter by date range end (YYYY-MM-DD)
            limit: Maximum number of results

        Returns:
            JSON string with search results
        """
        try:
            logger.info(f"Searching contexts: query='{query}', type={context_type}")

            # Ensure limit is an integer
            try:
                limit = int(limit) if limit is not None else 10
            except (ValueError, TypeError):
                limit = 10

            filters: Dict[str, Any] = {}
            if context_type:
                filters["type"] = context_type
            if tags:
                filters["tags"] = tags
            if status:
                filters["status"] = status
            if priority:
                filters["priority"] = priority
            if date_start or date_end:
                filters["date_range"] = {}
                if date_start:
                    filters["date_range"]["start"] = date_start
                if date_end:
                    filters["date_range"]["end"] = date_end

            results = self.l4.search_contexts(query, filters)
            
            # Ensure results is a list and apply limit
            if not isinstance(results, list):
                results = []
            results = results[:limit] if limit > 0 else results

            formatted_results = []
            for result in results:
                if not isinstance(result, dict):
                    continue
                formatted_results.append(
                    {
                        "context_id": result.get("id"),
                        "type": result.get("type"),
                        "title": result.get("title"),
                        "date": result.get("date"),
                        "time": result.get("time"),
                        "status": result.get("status"),
                        "priority": result.get("priority"),
                        "tags": result.get("tags", []),
                        "description": (result.get("description", "") or "")[:100],
                    }
                )

            return json.dumps(
                {"status": "success", "total_results": len(formatted_results), "results": formatted_results},
                ensure_ascii=False,
            )

        except Exception as e:
            logger.error(f"Error searching contexts: {e}", exc_info=True)
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def link_contexts(
        self, context_id_1: str, context_id_2: str, relation_type: str = "related_to"
    ) -> str:
        """Link two contexts together.

        Args:
            context_id_1: First context ID
            context_id_2: Second context ID
            relation_type: Type of relation (related_to, follows, precedes, part_of)

        Returns:
            JSON string with status
        """
        try:
            logger.info(f"Linking contexts: {context_id_1} <-{relation_type}-> {context_id_2}")

            success = self.l4.link_contexts(context_id_1, context_id_2, relation_type)

            if success:
                return json.dumps(
                    {
                        "status": "success",
                        "message": f"Contexts linked: {relation_type}",
                        "link": {
                            "from": context_id_1,
                            "to": context_id_2,
                            "relation": relation_type,
                        },
                    },
                    ensure_ascii=False,
                )
            else:
                return json.dumps(
                    {"status": "error", "message": "Contexts not found"},
                    ensure_ascii=False,
                )

        except Exception as e:
            logger.error(f"Error linking contexts: {e}")
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    def get_context_details(self, context_id: str, include_linked: bool = True) -> str:
        """Get full details of a context.

        Args:
            context_id: Context ID
            include_linked: Include linked contexts

        Returns:
            JSON string with context details
        """
        try:
            logger.info(f"Getting context details: {context_id}")

            context = self.l4.get_context(context_id, include_linked=include_linked)

            if not context:
                return json.dumps(
                    {"status": "error", "message": "Context not found"},
                    ensure_ascii=False,
                )

            result = {
                "status": "success",
                "context": {
                    "context_id": context.get("id"),
                    "type": context.get("type"),
                    "title": context.get("title"),
                    "date": context.get("date"),
                    "time": context.get("time"),
                    "description": context.get("description"),
                    "tags": context.get("tags", []),
                    "status": context.get("status"),
                    "priority": context.get("priority"),
                    "location": context.get("location"),
                    "attendees": context.get("attendees", []),
                    "notes": context.get("notes"),
                    "calendar_event_id": context.get("calendar_event_id"),
                    "task_id": context.get("task_id"),
                    "created_at": context.get("created_at"),
                    "updated_at": context.get("updated_at"),
                },
            }

            if include_linked and "linked_contexts_details" in context:
                result["linked_contexts"] = context["linked_contexts_details"]

            return json.dumps(result, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Error getting context details: {e}")
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)
