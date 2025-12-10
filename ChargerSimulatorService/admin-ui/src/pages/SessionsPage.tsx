import React, { useEffect, useState } from 'react'
import { apiGet } from '../api'

type SessionItem = {
  id: number
  sessionId: string
  connectorId: number
  idTag: string
  startedAt: string
  endedAt: string | null
  status: string
  energyWh: number
}

type ListResp = { items: SessionItem[]; total: number; limit: number; offset: number }

export default function SessionsPage() {
  const [items, setItems] = useState<SessionItem[]>([])
  const [total, setTotal] = useState(0)
  const [filters, setFilters] = useState({ status: '', idTag: '', connectorId: '' })
  const [detail, setDetail] = useState<any | null>(null)

  const load = async () => {
    const qs = new URLSearchParams()
    if (filters.status) qs.set('status_filter', filters.status)
    if (filters.idTag) qs.set('idTag', filters.idTag)
    if (filters.connectorId) qs.set('connectorId', filters.connectorId)
    const resp = await apiGet<ListResp>(`/sessions?${qs.toString()}`)
    setItems(resp.items)
    setTotal(resp.total)
  }

  useEffect(() => { load() }, [])

  const openDetail = async (sid: string) => {
    const data = await apiGet<any>(`/sessions/${sid}`)
    setDetail(data)
  }

  return (
    <div className="panel">
      <h2>Sessions</h2>
      <div className="grid">
        <div>
          <label>Status</label>
          <select value={filters.status} onChange={e => setFilters({...filters, status: e.target.value})}>
            <option value="">Any</option>
            <option>Running</option>
            <option>Completed</option>
            <option>Failed</option>
          </select>
        </div>
        <div>
          <label>idTag</label>
          <input value={filters.idTag} onChange={e => setFilters({...filters, idTag: e.target.value})} />
        </div>
        <div>
          <label>connectorId</label>
          <input value={filters.connectorId} onChange={e => setFilters({...filters, connectorId: e.target.value})} />
        </div>
        <div style={{alignSelf:'end'}}>
          <button className="btn" onClick={load}>Apply</button>
        </div>
      </div>

      <table className="table" style={{marginTop: 12}}>
        <thead>
          <tr><th>Session</th><th>Connector</th><th>idTag</th><th>Started</th><th>Ended</th><th>Status</th><th>Energy (Wh)</th></tr>
        </thead>
        <tbody>
          {items.map(it => (
            <tr key={it.id} onClick={() => openDetail(it.sessionId)} style={{cursor:'pointer'}}>
              <td>{it.sessionId}</td>
              <td>{it.connectorId}</td>
              <td>{it.idTag}</td>
              <td>{it.startedAt}</td>
              <td>{it.endedAt || '-'}</td>
              <td>{it.status}</td>
              <td>{it.energyWh}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div style={{marginTop:12}}>{total} total</div>

      {detail && (
        <div className="panel" style={{marginTop:16}}>
          <h3>Session Detail: {detail.summary.sessionId}</h3>
          <div className="grid">
            <div className="panel">
              <h4>Summary</h4>
              <div>Status: {detail.summary.status}</div>
              <div>Started: {detail.summary.startedAt}</div>
              <div>Ended: {detail.summary.endedAt || '-'}</div>
              <div>Energy: {detail.summary.energyWh} Wh</div>
            </div>
            <div className="panel">
              <h4>Meter Stats</h4>
              <div>Samples: {detail.meterStats.count}</div>
              <div>First: {detail.meterStats.firstTs || '-'}</div>
              <div>Last: {detail.meterStats.lastTs || '-'}</div>
            </div>
          </div>
          <div className="panel">
            <h4>Timeline</h4>
            <ul>
              {detail.events.map((e:any) => (
                <li key={e.id}>{e.ts} - {e.type} - {e.payload}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}
