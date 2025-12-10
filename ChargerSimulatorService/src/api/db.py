import os
import sqlite3
from contextlib import contextmanager
from typing import Iterator, Optional, Any, Dict
from pathlib import Path
from dotenv import load_dotenv

DB_PATH = os.environ.get("CHARGER_SIM_DB_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "charger_sim.db"))
Path(os.path.dirname(DB_PATH)).mkdir(parents=True, exist_ok=True)

# Ensure .env is loaded once at import so startup sync can use env values
load_dotenv(override=False)

SETTINGS_DEFAULTS: Dict[str, Any] = {
    "idTag": "TEST123",
    "connectorId": 1,
    "csmsUrl": "ws://localhost:9000/ocpp",
    "heartbeatInterval": 60,
    "samplingInterval": 5,
    "initiationTimingWindowSec": 30,
    "meterStart": 0,
    "offlineCacheLimit": 1000,
    "tlsEnabled": False,
    "authEnabled": False,
}

def _env_or_default(key: str, default: Any) -> Any:
    """
    Helper: get value from environment (string), coerce to type of default.
    """
    env_key = f"SIM_{key}".upper()
    raw = os.environ.get(env_key)
    if raw is None:
        return default
    # Try to coerce based on default type
    try:
        if isinstance(default, bool):
            return str(raw).lower() in ("1", "true", "yes", "on")
        if isinstance(default, int):
            return int(raw)
        if isinstance(default, float):
            return float(raw)
        return str(raw)
    except Exception:
        return default

@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    """
    SQLite connection context manager with row_factory for dict-like access.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db() -> None:
    """
    Initialize DB schema and seed defaults if needed.
    """
    with get_conn() as conn:
        cur = conn.cursor()
        # settings - single row table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                idTag TEXT,
                connectorId INTEGER,
                csmsUrl TEXT,
                heartbeatInterval INTEGER,
                samplingInterval INTEGER,
                initiationTimingWindowSec INTEGER,
                meterStart INTEGER,
                offlineCacheLimit INTEGER,
                tlsEnabled INTEGER,
                authEnabled INTEGER
            )
        """)
        # sessions summary header
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sessionId TEXT UNIQUE,
                connectorId INTEGER,
                idTag TEXT,
                startedAt TEXT,
                endedAt TEXT,
                status TEXT,
                energyWh INTEGER DEFAULT 0
            )
        """)
        # session events: timeline (OCPP messages, state transitions, meter stats)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS session_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sessionId TEXT,
                ts TEXT,
                type TEXT,
                payload TEXT
            )
        """)
        # meter values cache (for live and offline queue depth)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS meter_values (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sessionId TEXT,
                ts TEXT,
                measurand TEXT,
                value REAL,
                context TEXT
            )
        """)
        # connectivity state log
        cur.execute("""
            CREATE TABLE IF NOT EXISTS connectivity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT,
                state TEXT
            )
        """)
        # live_state singleton (connector state, transaction info)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS live_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                connectorStatus TEXT,
                transactionId TEXT,
                lastHeartbeatTs TEXT
            )
        """)
        # NEW: ocpp_messages log table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ocpp_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sessionId TEXT,
                transactionId TEXT,
                connectorId INTEGER,
                direction TEXT, -- sent | received
                action TEXT,    -- BootNotification, Heartbeat, StatusNotification, StartTransaction, MeterValues, StopTransaction, RemoteStartTransaction, RemoteStopTransaction, ...
                messageId TEXT,
                relatedMessageId TEXT,
                ts TEXT,        -- ISO8601 timestamp
                payload TEXT,   -- JSON string
                resultStatus TEXT, -- Accepted/Rejected or error codes
                replayed INTEGER DEFAULT 0
            )
        """)
        # indices for performance
        cur.execute("CREATE INDEX IF NOT EXISTS idx_ocpp_messages_session_ts ON ocpp_messages(sessionId, ts)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_ocpp_messages_msgid ON ocpp_messages(messageId)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_ocpp_messages_related ON ocpp_messages(relatedMessageId)")
        # seed settings if empty
        cur.execute("SELECT COUNT(*) as c FROM settings")
        if cur.fetchone()["c"] == 0:
            values = {k: _env_or_default(k, v) for k, v in SETTINGS_DEFAULTS.items()}
            cur.execute("""
                INSERT INTO settings (id, idTag, connectorId, csmsUrl, heartbeatInterval, samplingInterval,
                                      initiationTimingWindowSec, meterStart, offlineCacheLimit, tlsEnabled, authEnabled)
                VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                values["idTag"],
                values["connectorId"],
                values["csmsUrl"],
                values["heartbeatInterval"],
                values["samplingInterval"],
                values["initiationTimingWindowSec"],
                values["meterStart"],
                values["offlineCacheLimit"],
                1 if values["tlsEnabled"] else 0,
                1 if values["authEnabled"] else 0,
            ))
        # seed live_state
        cur.execute("SELECT COUNT(*) as c FROM live_state")
        if cur.fetchone()["c"] == 0:
            cur.execute("INSERT INTO live_state (id, connectorStatus, transactionId, lastHeartbeatTs) VALUES (1, 'Available', NULL, NULL)")

# PUBLIC_INTERFACE
def get_settings() -> dict:
    """Return the singleton settings row as a JSON-serializable dict."""
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM settings WHERE id = 1").fetchone()
        if not row:
            return {k: v for k, v in SETTINGS_DEFAULTS.items()}
        d = dict(row)
        d["tlsEnabled"] = bool(d.get("tlsEnabled", 0))
        d["authEnabled"] = bool(d.get("authEnabled", 0))
        return d

# PUBLIC_INTERFACE
def update_settings(payload: dict) -> dict:
    """Update settings row with provided fields and return updated record."""
    current = get_settings()
    current.update(payload or {})
    with get_conn() as conn:
        conn.execute("""
            UPDATE settings SET
                idTag = ?, connectorId = ?, csmsUrl = ?, heartbeatInterval = ?, samplingInterval = ?,
                initiationTimingWindowSec = ?, meterStart = ?, offlineCacheLimit = ?, tlsEnabled = ?, authEnabled = ?
            WHERE id = 1
        """, (
            current["idTag"],
            int(current["connectorId"]),
            current["csmsUrl"],
            int(current["heartbeatInterval"]),
            int(current["samplingInterval"]),
            int(current["initiationTimingWindowSec"]),
            int(current["meterStart"]),
            int(current["offlineCacheLimit"]),
            1 if current.get("tlsEnabled") else 0,
            1 if current.get("authEnabled") else 0,
        ))
    return get_settings()

# PUBLIC_INTERFACE
def get_live_state() -> dict:
    """Return connector state, transaction info, last N meter values, connectivity, and offline queue depth."""
    with get_conn() as conn:
        live = conn.execute("SELECT * FROM live_state WHERE id = 1").fetchone()
        meter_values = conn.execute("SELECT * FROM meter_values ORDER BY ts DESC LIMIT 50").fetchall()
        connectivity = conn.execute("SELECT * FROM connectivity ORDER BY ts DESC LIMIT 20").fetchall()
        # offline queue depth as total meter_values without a session id or flagged - simplified
        offline_depth = conn.execute("SELECT COUNT(*) as c FROM meter_values WHERE sessionId IS NULL").fetchone()["c"]
    return {
        "connectorStatus": live["connectorStatus"] if live else "Unknown",
        "transactionId": live["transactionId"] if live else None,
        "lastHeartbeatTs": live["lastHeartbeatTs"] if live else None,
        "meterValues": [dict(r) for r in meter_values][::-1],
        "connectivity": [dict(r) for r in connectivity][::-1],
        "offlineQueueDepth": offline_depth,
    }

# PUBLIC_INTERFACE
def list_sessions(filters: Optional[dict] = None, limit: int = 50, offset: int = 0) -> dict:
    """List sessions with basic filters (status, idTag, connectorId)."""
    filters = filters or {}
    clauses = []
    params: list[Any] = []
    if "status" in filters and filters["status"]:
        clauses.append("status = ?")
        params.append(filters["status"])
    if "idTag" in filters and filters["idTag"]:
        clauses.append("idTag = ?")
        params.append(filters["idTag"])
    if "connectorId" in filters and filters["connectorId"]:
        clauses.append("connectorId = ?")
        params.append(int(filters["connectorId"]))
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with get_conn() as conn:
        rows = conn.execute(
            f"SELECT * FROM sessions {where} ORDER BY startedAt DESC LIMIT ? OFFSET ?",
            (*params, int(limit), int(offset)),
        ).fetchall()
        total = conn.execute(f"SELECT COUNT(*) as c FROM sessions {where}", params).fetchone()["c"]
    return {"items": [dict(r) for r in rows], "total": total, "limit": limit, "offset": offset}

# PUBLIC_INTERFACE
def get_session_detail(session_id: str) -> dict:
    """Return session summary with timeline of events and basic meter stats."""
    with get_conn() as conn:
        s = conn.execute("SELECT * FROM sessions WHERE sessionId = ?", (session_id,)).fetchone()
        events = conn.execute("SELECT * FROM session_events WHERE sessionId = ? ORDER BY ts ASC", (session_id,)).fetchall()
        meters = conn.execute("SELECT * FROM meter_values WHERE sessionId = ? ORDER BY ts ASC", (session_id,)).fetchall()
    if not s:
        return {}
    # simple stats
    stats = {
        "count": len(meters),
        "firstTs": meters[0]["ts"] if meters else None,
        "lastTs": meters[-1]["ts"] if meters else None,
    }
    return {
        "summary": dict(s),
        "events": [dict(e) for e in events],
        "meterValues": [dict(m) for m in meters],
        "meterStats": stats,
    }

# PUBLIC_INTERFACE
def add_ocpp_message(
    session_id: str,
    direction: str,
    action: str,
    message_id: str,
    ts: str,
    payload: dict,
    connector_id: int | None = None,
    transaction_id: str | None = None,
    related_message_id: str | None = None,
    result_status: str | None = None,
    replayed: bool = False,
) -> int:
    """Insert an OCPP message log row and return inserted id."""
    import json as _json
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO ocpp_messages
                (sessionId, transactionId, connectorId, direction, action, messageId, relatedMessageId, ts, payload, resultStatus, replayed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                transaction_id,
                connector_id,
                direction,
                action,
                message_id,
                related_message_id,
                ts,
                _json.dumps(payload) if isinstance(payload, (dict, list)) else str(payload),
                result_status,
                1 if replayed else 0,
            ),
        )
        return int(cur.lastrowid)

# PUBLIC_INTERFACE
def get_session_messages(session_id: str, limit: int = 100, after: str | None = None, before: str | None = None, action: str | None = None, direction: str | None = None) -> list[dict]:
    """Return OCPP messages for a session filtered and ordered by timestamp ascending."""
    clauses = ["sessionId = ?"]
    params: list[Any] = [session_id]
    if after:
        clauses.append("ts > ?")
        params.append(after)
    if before:
        clauses.append("ts < ?")
        params.append(before)
    if action:
        clauses.append("action = ?")
        params.append(action)
    if direction:
        clauses.append("direction = ?")
        params.append(direction)
    where = " AND ".join(clauses)
    with get_conn() as conn:
        rows = conn.execute(
            f"SELECT * FROM ocpp_messages WHERE {where} ORDER BY ts ASC LIMIT ?",
            (*params, int(limit)),
        ).fetchall()
    out = []
    import json as _json
    for r in rows:
        d = dict(r)
        # try parse payload
        try:
            d["payload"] = _json.loads(d.get("payload") or "{}")
        except Exception:
            pass
        d["replayed"] = bool(d.get("replayed", 0))
        out.append(d)
    return out

# PUBLIC_INTERFACE
def get_session_timeline(session_id: str, limit: int = 500) -> list[dict]:
    """Return a normalized timeline combining session_events and ocpp_messages for a session."""
    with get_conn() as conn:
        evs = conn.execute("SELECT id, ts, type, payload FROM session_events WHERE sessionId = ? ORDER BY ts ASC", (session_id,)).fetchall()
        msgs = conn.execute("SELECT * FROM ocpp_messages WHERE sessionId = ? ORDER BY ts ASC LIMIT ?", (session_id, int(limit))).fetchall()
    import json as _json
    timeline: list[dict] = []
    for e in evs:
        item = {"kind": "event", "id": e["id"], "ts": e["ts"], "type": e["type"]}
        try:
            item["payload"] = _json.loads(e["payload"] or "{}")
        except Exception:
            item["payload"] = e["payload"]
        timeline.append(item)
    for m in msgs:
        d = dict(m)
        try:
            d["payload"] = _json.loads(d.get("payload") or "{}")
        except Exception:
            pass
        d["replayed"] = bool(d.get("replayed", 0))
        # Normalize for UI
        item = {
            "kind": "ocpp",
            "id": d["id"],
            "ts": d["ts"],
            "direction": d["direction"],
            "action": d["action"],
            "messageId": d["messageId"],
            "relatedMessageId": d.get("relatedMessageId"),
            "status": d.get("resultStatus"),
            "replayed": d.get("replayed", False),
            "connectorId": d.get("connectorId"),
            "transactionId": d.get("transactionId"),
            "payload": d.get("payload"),
        }
        timeline.append(item)
    # final sort by timestamp then id
    timeline.sort(key=lambda x: (x.get("ts") or "", x.get("id") or 0))
    return timeline
