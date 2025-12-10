# ocpp-16-j-charger-simulator-27-721

## Admin UI and API

This project includes a React-based Admin UI served by the FastAPI backend.

- Access the Admin UI at: http://localhost:3001/admin
- Manage settings (idTag, connectorId, csmsUrl, intervals, TLS/auth), monitor live state (SSE), and review sessions with an OCPP message timeline.
- Build the UI with Vite: see ChargerSimulatorService/admin-ui (npm install; npm run build).

For full details, see ChargerSimulatorService/ADMIN_README.md.