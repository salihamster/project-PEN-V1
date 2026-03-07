from typing import Dict, Any, List, Optional
import json
from layers.calendar_system import CalendarSystem

class CalendarTools:
    """Tools for managing the Calendar System."""
    
    def __init__(self, calendar_system: CalendarSystem):
        self.calendar = calendar_system
        
    def read_calendar(self, start_date: str, end_date: str = None, view_mode: str = "daily") -> str:
        """
        Reads calendar events within a date range.
        """
        result_text = self.calendar.read_calendar(start_date, end_date, view_mode)
        return json.dumps({
            "status": "success",
            "calendar_view": result_text
        }, ensure_ascii=False)
        
    def create_event(self, 
                     title: str, 
                     description: str = "",
                     start_time: str = None, 
                     end_time: str = None,
                     window_start: str = None, 
                     window_end: str = None, 
                     duration_minutes: int = 60,
                     period_name: str = None,
                     tags: List[str] = None,
                     linked_context_id: str = None) -> str:
        """
        Creates a new calendar event. System automatically determines type.
        """
        event_id = self.calendar.create_event(
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            window_start=window_start,
            window_end=window_end,
            duration_minutes=duration_minutes,
            period_name=period_name,
            tags=tags,
            linked_context_id=linked_context_id
        )
        return json.dumps({"status": "success", "event_id": event_id, "message": f"Event '{title}' created."})

    def chain_events(self, prev_event_id: str, next_event_id: str) -> str:
        """Links two events sequentially."""
        success = self.calendar.chain_events(prev_event_id, next_event_id)
        if success:
            return json.dumps({"status": "success", "message": f"Events {prev_event_id} -> {next_event_id} chained."})
        return json.dumps({"status": "error", "message": "Failed to chain events. IDs may be invalid."})

    def delete_event(self, event_id: str) -> str:
        """
        Deletes a calendar event by its ID.
        
        Args:
            event_id: The unique identifier of the event to delete
            
        Returns:
            JSON string with status and message
        """
        # First, get event details before deleting
        event_data = self.calendar.get_event_details(event_id)
        
        if not event_data:
            return json.dumps({
                "status": "error", 
                "message": f"Event ID '{event_id}' not found in calendar. Cannot delete."
            })
        
        # Get event title for confirmation message
        event_title = event_data.get("title", "Unknown")
        
        # Delete the event
        success = self.calendar.delete_event(event_id)
        
        if success:
            return json.dumps({
                "status": "success", 
                "event_id": event_id,
                "event_title": event_title,
                "message": f"✓ Event '{event_title}' (ID: {event_id}) has been permanently deleted from calendar."
            })
        
        return json.dumps({
            "status": "error", 
            "message": f"Failed to delete event '{event_title}' (ID: {event_id}). Unknown error occurred."
        })

    def calendar_tools_open(self) -> str:
        """
        Returns instructions and metadata for using the Calendar system.
        """
        context_info = self.calendar.get_system_context()
        return json.dumps({
            "status": "success",
            "system_context": context_info
        }, ensure_ascii=False)
