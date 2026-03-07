"""
Tool Executor Logging Integration

Add this to tool_executor.py's _manage_tool_outputs method
"""

from src.utils.ttl_logger import get_ttl_logger

def _manage_tool_outputs(self, tool_input: Dict[str, Any]) -> str:
    """Manage tool outputs (expand, collapse, list)."""
    action = tool_input.get("action", "list")
    ids = tool_input.get("ids", [])
    
    # 🔥 LOG: manage_tool_outputs call
    try:
        logger = get_ttl_logger()
        logger.log_manage_tool_outputs_call(action, ids, success=True)
    except:
        pass
    
    if action == "list":
        outputs = self.l1_layer.get_output_status()
        return json.dumps({
            "status": "ok",
            "outputs": outputs
        }, ensure_ascii=False)
    
    elif action == "expand":
        expanded = []
        failed = []
        for interaction_id in ids:
            if self.l1_layer.expand_output(interaction_id):
                expanded.append(interaction_id)
            else:
                failed.append(interaction_id)
        
        return json.dumps({
            "status": "ok",
            "expanded": expanded,
            "failed": failed,
            "message": f"Expanded {len(expanded)} outputs"
        }, ensure_ascii=False)
    
    elif action == "collapse":
        collapsed = []
        failed = []
        for interaction_id in ids:
            if self.l1_layer.collapse_output(interaction_id):
                collapsed.append(interaction_id)
            else:
                failed.append(interaction_id)
        
        return json.dumps({
            "status": "ok",
            "collapsed": collapsed,
            "failed": failed,
            "message": f"Collapsed {len(collapsed)} outputs"
        }, ensure_ascii=False)
    
    elif action == "collapse_all":
        count = self.l1_layer.collapse_all_outputs()
        return json.dumps({
            "status": "ok",
            "collapsed_count": count,
            "message": f"Collapsed {count} outputs"
        }, ensure_ascii=False)
    
    else:
        return json.dumps({
            "status": "error",
            "message": f"Unknown action: {action}"
        }, ensure_ascii=False)
