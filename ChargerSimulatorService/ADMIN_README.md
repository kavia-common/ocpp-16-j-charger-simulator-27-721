Charger Simulator Admin UI

Build and serve:
- Navigate to admin-ui and run: npm install && npm run build
- The build outputs into src/api/../admin_build which FastAPI serves at /admin

Endpoints:
- GET /api/settings
- PUT /api/settings
- GET /api/sessions?status_filter=&idTag=&connectorId=&limit=&offset=
- GET /api/sessions/{sessionId}
- GET /api/live/stream (SSE)
- WS /api/live/ws

Environment sync:
- On first run, settings are seeded from environment variables SIM_IDTAG, SIM_CONNECTORID, SIM_CSMSURL, SIM_HEARTBEATINTERVAL, SIM_SAMPLINGINTERVAL, SIM_INITIATIONTIMINGWINDOWSEC, SIM_METERSTART, SIM_OFFLINECACHELIMIT, SIM_TLSENABLED, SIM_AUTHENABLED.
