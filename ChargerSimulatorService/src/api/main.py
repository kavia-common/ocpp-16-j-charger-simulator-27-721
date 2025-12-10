import os
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(
    title="OCPP 1.6J Charger Simulator",
    description="Simulator for OCPP 1.6J Charge Points with Offline Capabilities",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Data Models ---

class SimulatorConfig(BaseModel):
    chargerId: str
    centralSystemUrl: str
    heartbeatInterval: int
    # Add other config fields as needed

class Session(BaseModel):
    sessionId: str
    connectorId: int
    status: str
    startTime: str
    energyConsumed: float

# --- API Stubs ---

@app.get("/api/config", response_model=SimulatorConfig, tags=["Configuration"])
async def get_config():
    """
    Get the current simulator configuration.
    """
    # STUB: Return dummy config
    return SimulatorConfig(
        chargerId="CS001",
        centralSystemUrl="ws://localhost:9000/ocpp/CS001",
        heartbeatInterval=60
    )

@app.put("/api/config", response_model=SimulatorConfig, tags=["Configuration"])
async def update_config(config: SimulatorConfig):
    """
    Update the simulator configuration.
    """
    # STUB: Return echoed config
    return config

@app.get("/api/sessions", response_model=List[Session], tags=["Sessions"])
async def get_sessions():
    """
    Get a list of historical or active charging sessions.
    """
    # STUB: Return empty list
    return []

@app.get("/health")
def health_check():
    return {"message": "Healthy"}

# --- WebSockets ---

@app.websocket("/ws/live")
async def websocket_live_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for the frontend to receive real-time logs and status updates.
    """
    await websocket.accept()
    try:
        while True:
            # Keep the connection open.
            # In a real implementation, this would subscribe to an event bus 
            # and push messages to the client.
            await websocket.receive_text()
    except WebSocketDisconnect:
        print("Frontend client disconnected")

@app.websocket("/ws/ocpp")
async def websocket_ocpp_traffic(websocket: WebSocket):
    """
    WebSocket endpoint to observe raw OCPP traffic (optional, or for debugging).
    """
    await websocket.accept()
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass


# --- Static Files (SPA) ---

# Determine the path to the frontend build directory
# This file is in src/api/main.py, so we go up two levels to ChargerSimulatorService
# then into frontend/dist
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRONTEND_DIST = os.path.join(BASE_DIR, "frontend", "dist")

if os.path.exists(FRONTEND_DIST):
    # Mount assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    # Serve index.html for the root and client-side routing fallback
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Allow API and WebSocket routes to pass through
        if full_path.startswith("api/") or full_path.startswith("ws/") or full_path == "health" or full_path == "docs" or full_path == "openapi.json":
            raise HTTPException(status_code=404, detail="Not Found") # Let FastAPI handle these if they don't match

        # Serve index.html for everything else (SPA routing)
        index_path = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"error": "Frontend build index.html not found"}
else:
    print(f"Frontend dist directory not found at {FRONTEND_DIST}. Running in API-only mode.")

