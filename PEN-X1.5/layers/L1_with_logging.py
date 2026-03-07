"""
L1 Layer with TTL Logging Integration

This file shows how to integrate TTL logging into L1.py
Copy the relevant sections to your L1.py file.
"""

# ==================== ADD TO IMPORTS ====================
from src.utils.ttl_logger import get_ttl_logger

# ==================== ADD TO add_tool_interaction METHOD ====================
def add_tool_interaction(
    self,
    tool_name: str,
    tool_input: dict[str, Any],
    tool_output: Any,
    execution_time_ms: Optional[float] = None,
    error: Optional[str] = None
) -> ToolInteraction:
    """Record a tool call and its output."""
    # Calculate output size for TTL system
    output_str = tool_output
    if not isinstance(output_str, str):
        try:
            output_str = json.dumps(output_str)
        except:
            output_str = str(output_str)
    output_size = len(output_str)
    
    interaction = ToolInteraction(
        tool_name=tool_name,
        tool_input=tool_input,
        tool_output=tool_output,
        execution_time_ms=execution_time_ms,
        error=error,
        output_size=output_size
    )
    self.tool_interactions.append(interaction)
    self.session_metadata.tool_call_count += 1
    self._update_last_activity()
    
    # 🔥 LOG: Tool call
    try:
        logger = get_ttl_logger()
        logger.log_tool_call(tool_name, output_size, interaction.ttl_counter)
    except:
        pass
    
    self.save_to_file()
    return interaction


# ==================== ADD TO tick_ttl METHOD ====================
def tick_ttl(self) -> list[str]:
    """Decrement TTL counters and auto-collapse expired outputs."""
    if not self.should_activate_ttl():
        return []
    
    # 🔥 LOG: TTL activation
    try:
        logger = get_ttl_logger()
        token_count = self.estimate_token_count()
        aggressive = self.is_aggressive_mode()
        logger.log_ttl_activation(token_count, aggressive)
    except:
        pass
    
    collapsed_ids = []
    aggressive = self.is_aggressive_mode()
    
    for ti in self.tool_interactions:
        if ti.pinned:
            continue
        
        if ti.ttl_counter == -1:
            if ti.output_size == 0:
                output_str = json.dumps(ti.tool_output) if not isinstance(ti.tool_output, str) else ti.tool_output
                ti.output_size = len(output_str)
            
            if ti.output_size >= self.OUTPUT_SIZE_THRESHOLD:
                ti.ttl_counter = self.TTL_SHORT
            else:
                ti.ttl_counter = self.TTL_LONG
            
            if aggressive:
                ti.ttl_counter = max(1, ti.ttl_counter // 2)
            continue
        
        if ti.ttl_counter <= -2:
            continue
        
        ti.ttl_counter -= 1
        
        if ti.ttl_counter == 0 and not ti.collapsed:
            ti.collapsed = True
            collapsed_ids.append(ti.interaction_id)
            
            # 🔥 LOG: Collapse event
            try:
                logger = get_ttl_logger()
                logger.log_collapse(ti.tool_name, ti.interaction_id, 
                                   ti.ttl_counter, ti.output_size, auto=True)
            except:
                pass
    
    if collapsed_ids:
        self.save_to_file()
        
        # 🔥 LOG: Tick event
        try:
            logger = get_ttl_logger()
            token_count = self.estimate_token_count()
            logger.log_tick_ttl(collapsed_ids, token_count)
        except:
            pass
    
    return collapsed_ids


# ==================== ADD TO collapse_output METHOD ====================
def collapse_output(self, interaction_id: str) -> bool:
    """Collapse a specific tool output."""
    for ti in self.tool_interactions:
        if ti.interaction_id == interaction_id:
            ti.collapsed = True
            ti.ttl_counter = 0
            
            # 🔥 LOG: Manual collapse
            try:
                logger = get_ttl_logger()
                logger.log_collapse(ti.tool_name, ti.interaction_id,
                                   ti.ttl_counter, ti.output_size, auto=False)
            except:
                pass
            
            self.save_to_file()
            return True
    return False


# ==================== ADD TO expand_output METHOD ====================
def expand_output(self, interaction_id: str) -> bool:
    """Expand a collapsed tool output with TTL doubling logic."""
    for ti in self.tool_interactions:
        if ti.interaction_id == interaction_id:
            ti.collapsed = False
            ti.expand_count += 1
            
            # After 3 expands, pin it permanently
            if ti.expand_count >= 3:
                ti.pinned = True
                ti.ttl_counter = -1
            else:
                base_ttl = self.TTL_SHORT if ti.output_size >= self.OUTPUT_SIZE_THRESHOLD else self.TTL_LONG
                ti.ttl_counter = base_ttl * (2 ** ti.expand_count)
            
            # 🔥 LOG: Expand event
            try:
                logger = get_ttl_logger()
                logger.log_expand(ti.tool_name, ti.interaction_id,
                                 ti.expand_count, ti.ttl_counter, ti.pinned)
            except:
                pass
            
            self.save_to_file()
            return True
    return False


# ==================== ADD NEW METHOD ====================
def log_context_size(self):
    """Log current context size to TTL logger."""
    try:
        logger = get_ttl_logger()
        token_count = self.estimate_token_count()
        message_count = len(self.messages)
        tool_output_count = len(self.tool_interactions)
        collapsed_count = sum(1 for ti in self.tool_interactions if ti.collapsed)
        
        logger.log_context_size(token_count, message_count, 
                               tool_output_count, collapsed_count)
    except:
        pass
