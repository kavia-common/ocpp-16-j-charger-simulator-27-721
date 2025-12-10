from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from .db import init_db
from .routers import router as admin_router

# Initialize FastAPI with basic metadata
app = FastAPI(
    title="Charger Simulator Admin API",
    description="Configuration, live monitoring, and session history for the OCPP 1.6J Charger Simulator.",
    version="0.1.0",
)

# Init DB at startup
@app.on_event("startup")
def _startup():
    init_db()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health
@app.get("/", tags=["Health"], summary="Health Check")
def health_check():
    """Return service liveness."""
    return {"message": "Healthy"}

# API routes
app.include_router(admin_router, prefix="/api")

# Serve embedded React app (built) from /admin
ADMIN_BUILD_DIR = os.path.join(os.path.dirname(__file__), "..", "admin_build")

if not os.path.isdir(ADMIN_BUILD_DIR):
    # ensure directory exists to avoid mount failure; runtime could be empty before build
    os.makedirs(ADMIN_BUILD_DIR, exist_ok=True)

app.mount("/admin", StaticFiles(directory=ADMIN_BUILD_DIR, html=True), name="admin")

# SPA fallback for /admin: serve index.html for nested routes
@app.get("/admin/{full_path:path}", include_in_schema=False)
def admin_spa(full_path: str):
    index_path = os.path.join(ADMIN_BUILD_DIR, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    return {"message": "Admin UI not built yet"}
