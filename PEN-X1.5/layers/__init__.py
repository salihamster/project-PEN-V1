"""
Layered Memory Architecture for PEN Agent.

This module implements a multi-layer memory system:
- L1: Active session-based memory
- L2: Archived session memory
- L2.5: Keyword-indexed search layer
- L4: Transport/persistence layer

Usage:
    from layers.layer_manager import LayerManager
    
    manager = LayerManager()
    manager.add_user_message("Hello")
    manager.add_assistant_message("Hi there!")
    results = manager.search_memory("previous conversations")
    manager.trigger_sleep_cycle()
"""

from layers.L1 import L1, MessageRole, InteractionType
from layers.L2 import L2
from layers.L2_5 import L2_5
from layers.L4 import L4UserProfile
from layers.layer_manager import LayerManager
from layers.sleep_cycle_manager import SleepCycleManager

__all__ = [
    "L1",
    "L2",
    "L2_5",
    "L4UserProfile",
    "LayerManager",
    "SleepCycleManager",
    "MessageRole",
    "InteractionType"
]
