export interface SimulatorConfig {
  chargerId: string;
  centralSystemUrl: string;
  heartbeatInterval: number;
}

export interface Session {
  sessionId: string;
  connectorId: number;
  status: 'Active' | 'Finished';
  startTime: string;
  endTime?: string;
  energyConsumed: number;
}

export interface LogMessage {
  timestamp: string;
  level: 'info' | 'warn' | 'error' | 'debug';
  message: string;
  source: string;
}
