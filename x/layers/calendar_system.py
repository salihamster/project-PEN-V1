"""Calendar System Layer

This module implements the Time Management System for the PEN agent.
It handles Fixed, Windowed (Flexible), and Uncertain events with varying levels of detail (Zoom levels).

Responsibilities:
- Manage events (Create, Update, Delete, Chain).
- Provide hierarchical views:
  - Daily: Exact times.
  - Weekly: Time blocks (Morning, Afternoon, Evening).
  - Monthly: Weekly summaries.
- Handle recurrence and event chaining.
- Provide metadata about the time range of available data.

Data Storage: layers/data/calendar.json
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from enum import Enum


class EventType(str, Enum):
    FIXED = "fixed"       # Specific date and time
    WINDOWED = "windowed" # Flexible within a time range
    UNCERTAIN = "uncertain" # Vague period (e.g. "Summer 2026")


class ViewMode(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass
class CalendarEvent:
    """Represents a single event in the calendar."""
    
    id: str
    title: str
    description: str = ""
    type: EventType = EventType.FIXED
    
    # Timing - Fixed
    start_time: Optional[str] = None  # ISO format
    end_time: Optional[str] = None    # ISO format
    
    # Timing - Windowed (Flexible)
    window_start: Optional[str] = None
    window_end: Optional[str] = None
    duration_minutes: int = 60
    
    # Timing - Uncertain
    period_name: Optional[str] = None  # e.g., "2026 Q1", "Summer"
    
    # Recurrence
    recurrence: Optional[Dict[str, Any]] = None  # {freq: "daily", interval: 1, until: "..."}
    parent_id: Optional[str] = None # If this is an instance of a recurring event
    
    # Chaining
    chain_prev_id: Optional[str] = None
    chain_next_id: Optional[str] = None
    
    # Links & Status
    linked_context_id: Optional[str] = None # Link to L4
    linked_file: Optional[str] = None # Link to a file in user_docs
    status: str = "active" # active, cancelled, completed
    tags: List[str] = field(default_factory=list)
    
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary manually to avoid deepcopy issues."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "type": self.type.value if hasattr(self.type, "value") else str(self.type),
            "start_time": self.start_time,
            "end_time": self.end_time,
            "window_start": self.window_start,
            "window_end": self.window_end,
            "duration_minutes": self.duration_minutes,
            "period_name": self.period_name,
            "recurrence": self.recurrence,
            "parent_id": self.parent_id,
            "chain_prev_id": self.chain_prev_id,
            "chain_next_id": self.chain_next_id,
            "linked_context_id": self.linked_context_id,
            "linked_file": self.linked_file,
            "status": self.status,
            "tags": self.tags,
            "created_at": self.created_at
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "CalendarEvent":
        # Handle Enum conversion
        if "type" in data:
            try:
                data["type"] = EventType(data["type"])
            except ValueError:
                data["type"] = EventType.FIXED
        return CalendarEvent(**data)


class CalendarSystem:
    """
    Advanced Calendar System with Zoom Levels and Intelligent Event Handling.
    """

    def __init__(self, data_dir: Optional[str] = None) -> None:
        if data_dir is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(script_dir, "data")

        self.data_dir = data_dir
        self.data_file = os.path.join(data_dir, "calendar.json")
        self._ensure_data_file()

    def _ensure_data_file(self) -> None:
        os.makedirs(self.data_dir, exist_ok=True)
        if not os.path.exists(self.data_file):
            self._save_data({"events": {}, "metadata": {"created_at": datetime.utcnow().isoformat()}})

    def _load_data(self) -> Dict[str, Any]:
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"events": {}, "metadata": {}}

    def _save_data(self, data: Dict[str, Any]) -> None:
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # =========================================================================
    # Event Management (CRUD)
    # =========================================================================

    def create_event(self, 
                     title: str, 
                     description: str = "",
                     # Fixed
                     start_time: str = None, 
                     end_time: str = None,
                     # Windowed
                     window_start: str = None, 
                     window_end: str = None, 
                     duration_minutes: int = 60,
                     # Uncertain
                     period_name: str = None,
                     # Recurrence
                     recurrence: Dict[str, Any] = None,
                     tags: List[str] = None,
                     linked_context_id: str = None,
                     linked_file: str = None) -> str:
        """
        Intelligent event creation. Determines type based on parameters provided.
        """
        data = self._load_data()
        event_id = f"evt_{uuid.uuid4().hex[:8]}"
        
        # Determine Type
        e_type = EventType.FIXED
        if period_name:
            e_type = EventType.UNCERTAIN
        elif window_start and window_end:
            e_type = EventType.WINDOWED
        elif start_time:
            e_type = EventType.FIXED
        else:
            # Default to windowed for 'today' if nothing specified, or error?
            # For now, let's assume if no time given, it's a "someday" uncertain event
            e_type = EventType.UNCERTAIN
            period_name = "General"

        new_event = CalendarEvent(
            id=event_id,
            title=title,
            description=description,
            type=e_type,
            start_time=start_time,
            end_time=end_time,
            window_start=window_start,
            window_end=window_end,
            duration_minutes=duration_minutes,
            period_name=period_name,
            recurrence=recurrence,
            tags=tags or [],
            linked_context_id=linked_context_id,
            linked_file=linked_file
        )

        data["events"][event_id] = new_event.to_dict()
        self._save_data(data)
        return event_id

    def delete_event(self, event_id: str) -> bool:
        data = self._load_data()
        if event_id in data["events"]:
            del data["events"][event_id]
            self._save_data(data)
            return True
        return False

    def update_event(self, event_id: str, updates: Dict[str, Any]) -> bool:
        data = self._load_data()
        if event_id not in data["events"]:
            return False
        
        # Merge updates
        event_dict = data["events"][event_id]
        event_dict.update(updates)
        # Validate Enum if type changed
        if "type" in updates:
            try:
                event_dict["type"] = EventType(updates["type"])
            except:
                pass
                
        data["events"][event_id] = event_dict
        self._save_data(data)
        return True

    def get_event_details(self, event_id: str) -> Dict[str, Any]:
        """Get full details for a specific event."""
        data = self._load_data()
        return data["events"].get(event_id, {})

    def chain_events(self, prev_event_id: str, next_event_id: str) -> bool:
        """Link two events sequentially."""
        data = self._load_data()
        if prev_event_id not in data["events"] or next_event_id not in data["events"]:
            return False
            
        data["events"][prev_event_id]["chain_next_id"] = next_event_id
        data["events"][next_event_id]["chain_prev_id"] = prev_event_id
        
        self._save_data(data)
        return True

    # =========================================================================
    # The Time Engine (Reading & Parsing)
    # =========================================================================

    def read_calendar(self, 
                      start_date_str: str, 
                      end_date_str: str = None, 
                      view_mode: str = "daily") -> str:
        """
        Main query tool. Returns formatted string based on Zoom Level.
        
        Args:
            start_date_str: YYYY-MM-DD
            end_date_str: YYYY-MM-DD (Defaults to start_date if None)
            view_mode: 'daily', 'weekly', 'monthly'
        """
        # Parse Dates
        try:
            start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
            if end_date_str:
                end_dt = datetime.strptime(end_date_str, "%Y-%m-%d")
            else:
                end_dt = start_dt + timedelta(days=1)
            
            # End date is inclusive for the user, but exclusive for logic usually.
            # Let's make it inclusive for filtering.
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
            
        except ValueError:
            return "Error: Invalid date format. Use YYYY-MM-DD."

        # Fetch relevant events
        events = self._get_events_in_range(start_dt, end_dt)
        
        # Route to View Handler
        # Ensure string comparison
        view_mode_str = str(view_mode).lower() if view_mode else "daily"
        
        if view_mode_str == ViewMode.DAILY.value:
            return self._render_daily_view(events, start_dt, end_dt)
        elif view_mode_str == ViewMode.WEEKLY.value:
            return self._render_weekly_view(events, start_dt, end_dt)
        elif view_mode_str == ViewMode.MONTHLY.value:
            return self._render_monthly_view(events, start_dt, end_dt)
        else:
            return self._render_daily_view(events, start_dt, end_dt)

    def _get_events_in_range(self, start_dt: datetime, end_dt: datetime) -> List[CalendarEvent]:
        """Filter events that fall within the range."""
        data = self._load_data()
        result = []
        
        for e_data in data["events"].values():
            event = CalendarEvent.from_dict(e_data)
            
            # 1. Check Fixed Events
            if event.type == EventType.FIXED and event.start_time:
                try:
                    e_start = datetime.fromisoformat(event.start_time)
                    if start_dt <= e_start <= end_dt:
                        result.append(event)
                except:
                    continue
            
            # 2. Check Windowed Events
            elif event.type == EventType.WINDOWED and event.window_start:
                try:
                    w_start = datetime.fromisoformat(event.window_start)
                    w_end = datetime.fromisoformat(event.window_end) if event.window_end else w_start
                    # If windows overlap
                    if (start_dt <= w_end) and (end_dt >= w_start):
                        result.append(event)
                except:
                    continue
            
            # 3. Check Uncertain (simplified: if created within range or logic needed)
            # For now, Uncertain events are usually listed separately or if period matches.
            # Skipping complex period parsing for V1.
            
            # 4. Check Recurrence (Simplified)
            elif event.recurrence:
                # TODO: Implement full recurrence expansion. 
                # Current stub: Check if it's "daily" or matches weekday
                pass

        return sorted(result, key=lambda x: x.start_time or x.window_start or "9999")

    # --- View Renderers ---

    def _render_daily_view(self, events: List[CalendarEvent], start: datetime, end: datetime) -> str:
        """Detailed view: Exact times."""
        output = [f"=== DAILY VIEW ({start.date()} to {end.date()}) ==="]
        
        # Group by day
        current_day = start
        while current_day <= end:
            day_events = [e for e in events if self._is_on_day(e, current_day)]
            
            output.append(f"\n📅 {current_day.strftime('%A, %Y-%m-%d')}")
            
            if not day_events:
                output.append("  (No events)")
            
            for e in day_events:
                if e.type == EventType.FIXED:
                    time_str = datetime.fromisoformat(e.start_time).strftime("%H:%M")
                    output.append(f"  • {time_str} | {e.title} [{e.status}] (ID: {e.id})")
                elif e.type == EventType.WINDOWED:
                    output.append(f"  • [Flexible] {e.title} (Duration: {e.duration_minutes}m)")
                
            current_day += timedelta(days=1)
            
        return "\n".join(output)

    def _render_weekly_view(self, events: List[CalendarEvent], start: datetime, end: datetime) -> str:
        """Summary view: Morning / Afternoon / Evening blocks."""
        output = [f"=== WEEKLY SUMMARY ({start.date()} to {end.date()}) ==="]
        
        current_day = start
        while current_day <= end:
            day_events = [e for e in events if self._is_on_day(e, current_day)]
            
            # Bins
            morning = []   # 05:00 - 12:00
            afternoon = [] # 12:00 - 18:00
            evening = []   # 18:00 - 05:00
            
            for e in day_events:
                hour = 12 # default for flexible
                if e.start_time:
                    hour = datetime.fromisoformat(e.start_time).hour
                
                if 5 <= hour < 12:
                    morning.append(e.title)
                elif 12 <= hour < 18:
                    afternoon.append(e.title)
                else:
                    evening.append(e.title)
            
            # Condensed Line
            summary_parts = []
            if morning: summary_parts.append(f"Morning: {', '.join(morning)}")
            if afternoon: summary_parts.append(f"Afternoon: {', '.join(afternoon)}")
            if evening: summary_parts.append(f"Evening: {', '.join(evening)}")
            
            if not summary_parts:
                summary_str = "Clear"
            else:
                summary_str = " | ".join(summary_parts)
                
            output.append(f"📅 {current_day.strftime('%a %d')}: {summary_str}")
            
            current_day += timedelta(days=1)
            
        return "\n".join(output)

    def _render_monthly_view(self, events: List[CalendarEvent], start: datetime, end: datetime) -> str:
        """High-level view: Weekly summaries."""
        output = [f"=== MONTHLY OVERVIEW ({start.strftime('%B %Y')}) ==="]
        
        # Iterate by weeks
        current_week_start = start
        while current_week_start <= end:
            current_week_end = min(current_week_start + timedelta(days=6), end)
            
            # Count events in this week
            count = 0
            titles = []
            
            # Check range intersection (naive)
            for e in events:
                if self._is_in_range(e, current_week_start, current_week_end):
                    count += 1
                    if len(titles) < 3: # Only show first 3 titles
                        titles.append(e.title)
            
            week_label = f"Week of {current_week_start.day}-{current_week_end.day}"
            if count == 0:
                output.append(f"📌 {week_label}: Clear")
            else:
                more_txt = f", +{count-3} more" if count > 3 else ""
                output.append(f"📌 {week_label}: {count} events ({', '.join(titles)}{more_txt})")
            
            current_week_start += timedelta(days=7)
            
        return "\n".join(output)

    # --- Helper Logic ---

    def _is_on_day(self, event: CalendarEvent, day: datetime) -> bool:
        """Check if event occurs on specific day."""
        day_start = day.replace(hour=0, minute=0, second=0)
        day_end = day.replace(hour=23, minute=59, second=59)
        return self._is_in_range(event, day_start, day_end)

    def _is_in_range(self, event: CalendarEvent, range_start: datetime, range_end: datetime) -> bool:
        """Check if event falls within a datetime range."""
        try:
            if event.start_time:
                e_start = datetime.fromisoformat(event.start_time)
                return range_start <= e_start <= range_end
            elif event.window_start:
                w_start = datetime.fromisoformat(event.window_start)
                # Simple overlap check
                return w_start <= range_end # Simplified
            return False
        except Exception:
            return False

    # =========================================================================
    # Context & Meta
    # =========================================================================

    def get_system_context(self) -> str:
        """
        Returns instructions and metadata for the Agent when Calendar Tools are active.
        Use this in the System Prompt or Tool Output.
        """
        data = self._load_data()
        total_events = len(data["events"])
        
        # Find date range of data
        dates = []
        for e in data["events"].values():
            if e.get("start_time"):
                dates.append(e["start_time"])
        
        if dates:
            min_date = min(dates)[:10]
            max_date = max(dates)[:10]
            range_info = f"Data available from {min_date} to {max_date}"
        else:
            range_info = "No events scheduled yet."

        return f"""
[CALENDAR SYSTEM ACTIVE]
Status: {total_events} events total. {range_info}.
Usage Guide:
1. 'read_calendar(view_mode="weekly")' -> Best for general planning ("What's up this week?").
2. 'read_calendar(view_mode="daily")' -> Use when checking specific availability.
3. 'create_event' -> System auto-detects type (Fixed vs Flexible) based on params.
4. 'chain_events' -> Use to link dependent tasks (e.g. A must happen before B).
"""