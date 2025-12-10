import React, { useEffect, useState } from 'react'
import { sse, apiGet } from '../api'

type LiveState = {
  connectorStatus: string
  transactionId: string | null
  lastHeartbeatTs: string | null
  meterValues: any[]
  connectivity: any[]
  offlineQueueDepth: number
}
export default function LivePage() {
  const [snap, setSnap] = useState<{ts:string, state: LiveState} | null>(null)

  useEffect(() => {
    // Prime once
    apiGet<LiveState>('/settings').catch(()=>{}) // no-op, ensure API reachable
    const es = sse('/api/live/stream', (data) => setSnap(data))
    return () => es.close()
  }, [])

  return (
    <div className="panel">
      <h2>Live Dashboard</h2>
      {!snap ? <div>Waiting for live data...</div> : (
        <>
          <div className="grid">
            <div className="panel">
              <h3>Status</h3>
              <div>Connector: <span className={`status-${snap.state.connectorStatus}`}>{snap.state.connectorStatus}</span></div>
              <div>Transaction: {snap.state.transactionId || '-'}</div>
              <div>Last Heartbeat: {snap.state.lastHeartbeatTs || '-'}</div>
            </div>
            <div className="panel">
              <h3>Connectivity</h3>
              <div>Offline Queue: <span className="badge">{snap.state.offlineQueueDepth}</span></div>
              <ul>
                {snap.state.connectivity.slice(-5).map((c:any, idx:number) => (
                  <li key={idx}>{c.ts} - {c.state}</li>
                ))}
              </ul>
            </div>
          </div>
          <div className="panel">
            <h3>Last MeterValues</h3>
            <table className="table">
              <thead><tr><th>ts</th><th>session</th><th>measurand</th><th>value</th><th>context</th></tr></thead>
              <tbody>
                {snap.state.meterValues.slice(-20).map((m:any) => (
                  <tr key={m.id}>
                    <td>{m.ts}</td>
                    <td>{m.sessionId || '-'}</td>
                    <td>{m.measurand}</td>
                    <td>{m.value}</td>
                    <td>{m.context}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}
