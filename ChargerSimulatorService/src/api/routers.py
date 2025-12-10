from typing import Optional, Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi import Response, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from datetime import datetime
import asyncio
import json

from .db import get_settings, update_settings, get_live_state, list_sessions, get_session_detail

router = APIRouter()

class SettingsModel(BaseModel):
    idTag: str = Field(..., description="Default idTag used for transactions")
    connectorId: int = Field(..., description="Connector ID")
    csmsUrl: str = Field(..., description="WebSocket URL for CSMS")
    heartbeatInterval: int = Field(..., description="Heartbeat interval seconds")
    samplingInterval: int = Field(..., description="Sampling interval seconds for MeterValues")
    initiationTimingWindowSec: int = Field(..., description="Allowed window after Preparing to accept RemoteStart")
    meterStart: int = Field(..., description="Starting meter value (Wh)")
    offlineCacheLimit: int = Field(..., description="Max cached MeterValues while offline")
    tlsEnabled: bool = Field(..., description="Use TLS for WebSocket (wss)")
    authEnabled: bool = Field(..., description="Use authentication for CSMS connection")

@router.get("/settings", summary="Get runtime settings", tags=["Admin"])
def read_settings() -> Dict[str, Any]:
    """
    PUBLIC_INTERFACE
    Return the current runtime settings from the SQLite store.
    """
    return get_settings()

@router.put("/settings", summary="Update runtime settings", tags=["Admin"])
def write_settings(payload: SettingsModel) -> Dict[str, Any]:
    """
    PUBLIC_INTERFACE
    Update and persist runtime settings.
    """
    updated = update_settings(payload.model_dump())
    return updated

@router.get("/sessions", summary="List sessions", tags=["Sessions"])
def sessions_list(status_filter: Optional[str] = None, idTag: Optional[str] = None, connectorId: Optional[int] = None,
                  limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """
    PUBLIC_INTERFACE
    List sessions with optional filters and pagination.
    """
    filters = {"status": status_filter, "idTag": idTag, "connectorId": connectorId}
    return list_sessions(filters, limit, offset)

@router.get("/sessions/{sessionId}", summary="Get session details", tags=["Sessions"])
def session_detail(sessionId: str) -> Dict[str, Any]:
    """
    PUBLIC_INTERFACE
    Retrieve a session detail including timeline and MeterValues stats.
    """
    data = get_session_detail(sessionId)
    if not data:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    return data

@router.get("/live/stream", summary="Live state stream (SSE)", tags=["Live"])
def live_stream():
    """
    PUBLIC_INTERFACE
    Server-Sent Events stream of live state. Emits a JSON object every second.
    """
    async def event_generator():
        while True:
            snapshot = get_live_state()
            yield f"data: {json.dumps({'ts': datetime.utcnow().isoformat()+'Z', 'state': snapshot})}\n\n"
            await asyncio.sleep(1)
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.websocket("/live/ws")
async def live_ws(ws: WebSocket):
    """
    PUBLIC_INTERFACE
    WebSocket providing live state updates every second.
    """
    await ws.accept()
    try:
        while True:
            snapshot = get_live_state()
            await ws.send_json({"ts": datetime.utcnow().isoformat() + "Z", "state": snapshot})
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        return
