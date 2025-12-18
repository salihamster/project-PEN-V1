"""Minimal web server for PENAgent.

Runs a simple HTTP API to expose pen_agent.PENAgent as a chat endpoint:
- POST /api/pen/chat {"message": "..."}
- POST /api/pen/reset

And serves the static web UI from ./web (index.html, style.css, script.js).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.routing import Mount
from pydantic import BaseModel

from src.agent.agent import PENAgent
from src.utils.logger import get_logger

logger = get_logger(__name__)

BASE_DIR = Path(__file__).parent
WEB_DIR = BASE_DIR / "web"

app = FastAPI(title="PEN Agent Web API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


class ToolRecord(BaseModel):
    name: str
    status: str
    parameters: Dict[str, Any] | None = None
    result: Any | None = None
    duration_ms: int | None = None
    started_at: str | None = None


# Single PENAgent instance for the process
_agent_instance: PENAgent | None = None


def get_agent() -> PENAgent:
    global _agent_instance
    if _agent_instance is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set in environment")
        minimax = os.getenv("MINIMAX_API_KEY")
        _agent_instance = PENAgent(api_key=api_key, minimax_api_key=minimax)
        _agent_instance.session_source = "web"  # Set session source for web
    return _agent_instance


@app.post("/api/pen/chat")
async def pen_chat(req: ChatRequest, show_tool_output: bool = Query(True)):
    try:
        agent = get_agent()
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        reply = agent.chat(user_message=req.message)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Agent error: {e}")

    # Extract tool calls from the current session (L1)
    tools: List[Dict[str, Any]] = []
    try:
        # Get the last tool interactions from L1
        tool_interactions = agent.layer_manager.l1.get_all_tool_interactions()
        
        # Return all tool interactions with complete details
        if tool_interactions:
            # Return all tool interactions from this session
            tools = tool_interactions
            
            # Optionally hide tool output if show_tool_output is False
            if not show_tool_output:
                for tool in tools:
                    tool["tool_output"] = "[Output hidden - use show_tool_output=true to view]"
    except Exception as e:
        logger.warning(f"Could not retrieve tool interactions: {e}")

    return {
        "reply": reply,
        "tools": tools,
    }


@app.get("/api/pen/models")
async def get_available_models():
    """Get list of available models with API keys configured"""
    try:
        from src.models.factory import ModelFactory
        models = ModelFactory.get_available_models_with_keys()
        return {"models": models, "default": "gemini-2.5-flash"}
    except Exception as e:
        logger.error(f"Error getting models: {e}")
        return {"models": [], "default": "gemini-2.5-flash"}

@app.get("/api/pen/history")
async def pen_history():
    """Get chat history from L1.json"""
    try:
        logger.info("History endpoint called")
        agent = get_agent()
        session_context = agent.layer_manager.l1.get_session_context()
        messages = session_context.get("messages", [])
        tools = session_context.get("tool_interactions", [])
        logger.info(f"Returning {len(messages)} messages and {len(tools)} tool interactions")
        return {
            "messages": messages,
            "tool_interactions": tools,
        }
    except Exception as e:
        logger.error(f"Could not retrieve history: {e}", exc_info=True)
        return {
            "messages": [],
            "tool_interactions": [],
        }


@app.post("/api/pen/reset")
async def pen_reset():
    try:
        agent = get_agent()
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    agent.reset()
    return {"status": "ok"}


@app.post("/api/pen/sleep")
async def pen_sleep():
    """Trigger sleep cycle to process and consolidate memories"""
    try:
        agent = get_agent()
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        logger.info("Sleep cycle triggered from web interface")
        # Run complete sleep cycle (includes L4 update, L1→L2+L2.5, reset)
        agent.sleep()
        logger.info("Sleep cycle completed successfully")
        return {
            "status": "success",
            "message": "Sleep cycle completed successfully. Session archived and agent reset."
        }
    except Exception as e:
        logger.error(f"Sleep cycle failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Sleep cycle failed: {str(e)}"
        )


@app.get("/{full_path:path}")
async def serve_static(full_path: str):
    """Serve static files and fallback to index.html for SPA routing"""
    file_path = WEB_DIR / full_path
    
    # If it's a file that exists, serve it
    if file_path.is_file():
        return FileResponse(file_path)
    
    # Otherwise serve index.html (for SPA routing)
    index_path = WEB_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    
    raise HTTPException(status_code=404, detail="Not found")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("web_server:app", host="127.0.0.1", port=8000, reload=True)
