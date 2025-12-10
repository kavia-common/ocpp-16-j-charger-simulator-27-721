# Charger Simulator Admin UI

## Overview
The Charger Simulator Admin UI is a React (Vite) single-page application bundled with the FastAPI backend and served at /admin. It provides an interface to configure runtime settings, monitor live state, and explore sessions with an OCPP message timeline.

The backend exposes a set of Admin API endpoints for settings, live streaming, sessions, and timeline data. A SQLite database persists settings, session records, and OCPP message logs, with optional synchronization from environment variables on startup.

## Accessing the Admin UI
- URL: http://localhost:3001/admin (adjust the port if you run on a different one)
- Navigation:
  - Config: Edit runtime parameters such as idTag, connectorId, csmsUrl, intervals, TLS, and auth.
  - Live: Observe connector state, active transaction info, recent MeterValues, connectivity, and offline queue depth.
  - Sessions: Browse historical sessions and drill into a session’s OCPP message timeline.

## Configuration Page
The Configuration page allows editing the following settings:
- idTag: Default idTag used for transactions.
- connectorId: Connector ID (integer).
- csmsUrl: WebSocket URL for CSMS (ws:// or wss://).
- heartbeatInterval: Heartbeat interval seconds.
- samplingInterval: Sampling interval seconds for MeterValues.
- initiationTimingWindowSec: Allowed window after Preparing to accept RemoteStart.
- meterStart: Starting meter value (Wh).
- offlineCacheLimit: Max cached MeterValues while offline.
- tlsEnabled: Enable TLS for WebSocket (wss).
- authEnabled: Enable authentication for CSMS connection.

Persistence model:
- Settings are stored in SQLite in a single-row settings table and returned via the Admin API.
- Optional .env synchronization on startup: settings are seeded on first run from environment variables named SIM_<Field>, for example SIM_IDTAG, SIM_CONNECTORID, SIM_CSMSURL, SIM_HEARTBEATINTERVAL, SIM_SAMPLINGINTERVAL, SIM_INITIATIONTIMINGWINDOWSEC, SIM_METERSTART, SIM_OFFLINECACHELIMIT, SIM_TLSENABLED, SIM_AUTHENABLED.

Validation and effect:
- Basic typing and range validation are handled by the backend schema.
- Changes take effect immediately for downstream components that read settings at runtime. If your simulator engine caches values, ensure it reloads or re-reads after update.

## Live Dashboard
Displayed data:
- Connector state and transaction info (transactionId, connectorStatus, lastHeartbeatTs).
- Last N MeterValues (including measurands such as power, current, voltage, SoC).
- Connectivity history (recent connectivity state entries).
- Offline queue depth (approximate count of cached MeterValues without session linkage).

Streaming mechanism:
- The UI uses Server-Sent Events (SSE) via GET /api/live/stream, emitting a JSON object every second.
- A WebSocket is also available at /api/live/ws for future use; the current UI uses SSE.

## Sessions & History
- Sessions list with filters (status, idTag, connectorId) and pagination parameters (limit, offset) supported by the backend API.
- Session detail view provides:
  - Summary (status, start/end timestamps, energy).
  - Meter stats (sample count and time bounds).
  - Timeline tab with OCPP messages.

OCPP message timeline:
- Shows key OCPP actions such as BootNotification, Heartbeat, StatusNotification, StartTransaction, MeterValues, StopTransaction, RemoteStartTransaction, and RemoteStopTransaction.
- Indicates direction: sent (from simulator) or received (from CSMS).
- Displays timestamps in ISO 8601; payloads are expandable JSON.
- Highlights errors when resultStatus is not “Accepted”.
- Filters allow narrowing by direction and action.
- Pagination/virtualization: The Sessions page fetches up to a limit per request (default 200 for messages, 1000 for combined timeline in backend). If you anticipate very large sessions, use filters and client-side virtualization in the table to maintain UI performance.

## OCPP Message Logging Instrumentation
Database table: ocpp_messages
- Columns:
  - id: autoincrement primary key
  - sessionId: session identifier (string)
  - transactionId: optional transaction id
  - connectorId: optional connector id
  - direction: 'sent' or 'received'
  - action: OCPP action name (e.g., BootNotification, Heartbeat, StatusNotification, StartTransaction, MeterValues, StopTransaction, RemoteStartTransaction, RemoteStopTransaction)
  - messageId: OCPP frame messageId
  - relatedMessageId: the counterpart ID to pair CALL/CALLRESULT/CALLERROR
  - ts: ISO 8601 timestamp
  - payload: JSON (serialized to text)
  - resultStatus: e.g., Accepted/Rejected or error code
  - replayed: boolean (0/1) indicating store-and-forward replay

How to instrument the OCPP WebSocket engine:
- On every send (CALL) and receive (CALLRESULT/CALLERROR) hook, insert a row into ocpp_messages.
- Pair CALL/CALLRESULT/CALLERROR via messageId and relatedMessageId so the UI can display correspondence.
- When store-and-forward replays occur, set replayed=1.

Pseudocode:
```python
from src.api.db import add_ocpp_message
from datetime import datetime

def now_iso():
    from datetime import timezone
    return datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")

# Example: sending StartTransaction CALL
add_ocpp_message(
    session_id=session_id,
    direction="sent",
    action="StartTransaction",
    message_id=call_id,               # unique id of the CALL frame
    ts=now_iso(),
    payload=payload_dict,
    connector_id=connector_id,
    transaction_id=None,
)

# Example: receiving StartTransaction CALLRESULT
add_ocpp_message(
    session_id=session_id,
    direction="received",
    action="StartTransaction",
    message_id=result_id,             # id of the CALLRESULT (if available in your stack)
    related_message_id=call_id,       # link to prior CALL
    ts=now_iso(),
    payload=result_payload,
    connector_id=connector_id,
    transaction_id=result_payload.get("transactionId"),
    result_status=result_payload.get("idTagInfo", {}).get("status", "Accepted"),
)

# Example: replaying cached MeterValues (store-and-forward)
add_ocpp_message(
    session_id=session_id,
    direction="sent",
    action="MeterValues",
    message_id=replay_msg_id,
    ts=now_iso(),
    payload=meter_values_payload,
    connector_id=connector_id,
    transaction_id=active_tx_id,
    replayed=True,
)
```

## API Endpoints (Admin UI Backend)
Settings
- GET /api/settings
- PUT /api/settings

Live stream
- GET /api/live/stream (SSE, emits a JSON object every second)
- WS /api/live/ws (WebSocket alternative)

Sessions
- GET /api/sessions
  - Query params: status_filter, idTag, connectorId, limit (default 50), offset (default 0)
- GET /api/sessions/{sessionId}
- GET /api/sessions/{sessionId}/messages?limit=&after=&before=&action=&direction=
  - Default limit 200
- GET /api/sessions/{sessionId}/timeline?limit=
  - Default limit 1000
Note: See interfaces/openapi.json for the latest schema. The OpenAPI is generated from the FastAPI app.

## Build and Serve Admin UI
Location: ChargerSimulatorService/admin-ui (Vite + React)

Build steps:
- From ChargerSimulatorService/admin-ui:
  - npm install
  - npm run build

Output:
- The Vite build outputs to src/api/../admin_build as configured in vite.config.ts.
- FastAPI serves the static build under /admin automatically after build.

Dev server (optional):
- You can run npm run dev to preview the UI on Vite’s dev server (default 5173), but API calls expect the backend to be running on 3001 unless proxied.

## Environment Variables and .env
A .env.example should be used as reference. The admin backend reads environment variables for initial settings synchronization on first run:

- SIM_IDTAG
- SIM_CONNECTORID
- SIM_CSMSURL
- SIM_HEARTBEATINTERVAL
- SIM_SAMPLINGINTERVAL
- SIM_INITIATIONTIMINGWINDOWSEC
- SIM_METERSTART
- SIM_OFFLINECACHELIMIT
- SIM_TLSENABLED
- SIM_AUTHENABLED

These populate the SQLite settings row if empty on startup. The database path can be overridden with CHARGER_SIM_DB_PATH.

## Troubleshooting
- Blank page at /admin:
  - Ensure the Admin UI has been built: (cd admin-ui && npm install && npm run build).
  - Check that the backend can access the admin_build directory (created by the build).
- CORS or mixed-content (wss vs ws):
  - The backend enables permissive CORS for development. When using wss, ensure your CSMS TLS configuration and certificates are valid, and the URL uses wss://.
- Database migration:
  - The ocpp_messages table and other tables are created automatically on startup via init_db().
  - If you observe schema issues locally, stop the app, remove the local SQLite database, and restart to re-initialize. Default path: ChargerSimulatorService/src/api/../data/charger_sim.db (or CHARGER_SIM_DB_PATH if set).

## Roadmap / Next Steps
- Optional authentication for the Admin UI.
- Additional timeline filters (e.g., by resultStatus), export to CSV, and a distinct visualization for store-and-forward replays.
- Virtualized lists for very large message sets and advanced search (regex, payload fields).
- Multi-connector enhancements in UI and backend aggregation.

## Sources
- Backend code: src/api/main.py, src/api/routers.py, src/api/db.py
- Frontend code: admin-ui/src (ConfigPage.tsx, LivePage.tsx, SessionsPage.tsx, api.ts), vite.config.ts
- OpenAPI: interfaces/openapi.json
