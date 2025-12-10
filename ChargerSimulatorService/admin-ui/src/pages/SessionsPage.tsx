import React, { useEffect, useMemo, useState } from 'react'
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
  const [activeTab, setActiveTab] = useState<'summary'|'timeline'>('summary')
  const [msgFilters, setMsgFilters] = useState<{direction:string, action:string}>({direction:'', action:''})
  const [messages, setMessages] = useState<any[]>([])
  const [loadingMsgs, setLoadingMsgs] = useState(false)

  const fmtTs = (s?: string | null) => s ? new Date(s).toLocaleString() : '-'
  const iconFor = (direction: string) => direction === 'sent' ? '⬆️' : '⬇️'
  const isError = (m: any) => (m.kind === 'ocpp' && m.status && m.status !== 'Accepted')
  const groupedPhase = (action: string) => {
    if (['BootNotification','Heartbeat','StatusNotification'].includes(action)) return 'Preparing'
    if (['StartTransaction','MeterValues'].includes(action)) return 'Charging'
    if (['StopTransaction'].includes(action)) return 'Finishing'
    return 'Other'
  }

  const loadMessages = async (sid: string, filters: {direction?:string, action?:string} = {}) => {
    setLoadingMsgs(true)
    try {
      const qs = new URLSearchParams()
      if (filters.direction) qs.set('direction', filters.direction)
      if (filters.action) qs.set('action', filters.action)
      qs.set('limit','500')
      const resp = await apiGet<{items:any[]; count:number}>(`/sessions/${sid}/messages?${qs.toString()}`)
      setMessages(resp.items)
    } finally {
      setLoadingMsgs(false)
    }
  }

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
    setActiveTab('summary')
    setMsgFilters({direction:'', action:''})
    setMessages([])
    // pre-load messages for timeline
    loadMessages(sid, {})
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
            <div className="row" style={{justifyContent:'space-between', alignItems:'center'}}>
              <div className="row" style={{gap:8}}>
                <button className={`btn ${activeTab==='summary'?'':'secondary'}`} onClick={()=>setActiveTab('summary')}>Summary</button>
                <button className={`btn ${activeTab==='timeline'?'':'secondary'}`} onClick={()=>setActiveTab('timeline')}>Timeline</button>
              </div>
              {activeTab==='timeline' && (
                <div className="row" style={{gap:8}}>
                  <select value={msgFilters.direction} onChange={e=>{ const v=e.target.value; setMsgFilters(f=>({...f, direction:v})); if(detail) loadMessages(detail.summary.sessionId, {direction:v, action:msgFilters.action}) }}>
                    <option value="">Any direction</option>
                    <option value="sent">Sent</option>
                    <option value="received">Received</option>
                  </select>
                  <input placeholder="Action (e.g. StartTransaction)" value={msgFilters.action} onChange={e=>{ const v=e.target.value; setMsgFilters(f=>({...f, action:v})); }} onBlur={()=>detail && loadMessages(detail.summary.sessionId, {direction:msgFilters.direction, action:msgFilters.action})} />
                  <button className="btn secondary" onClick={()=> detail && loadMessages(detail.summary.sessionId, msgFilters)}>Refresh</button>
                </div>
              )}
            </div>

            {activeTab==='summary' && (
              <>
                <h4>Raw Events</h4>
                <ul>
                  {detail.events.map((e:any) => (
                    <li key={e.id}>{fmtTs(e.ts)} - {e.type} - {String(e.payload)}</li>
                  ))}
                </ul>
              </>
            )}

            {activeTab==='timeline' && (
              <>
                <h4>OCPP Messages Timeline</h4>
                {loadingMsgs && <div>Loading messages...</div>}
                {!loadingMsgs && (
                  <div style={{maxHeight: 400, overflow: 'auto', border: '1px solid #233', borderRadius: 6}}>
                    <table className="table">
                      <thead>
                        <tr>
                          <th style={{width:180}}>Timestamp</th>
                          <th style={{width:80}}>Dir</th>
                          <th>Action</th>
                          <th>Pair</th>
                          <th>Status</th>
                          <th>Key</th>
                          <th>Payload</th>
                        </tr>
                      </thead>
                      <tbody>
                        {messages.map((m:any) => {
                          const [expand, setExpand] = useState(false) as any // scoped hack in map not ideal but works for simple rendering
                          const keys: string[] = []
                          if (m.action === 'StartTransaction') {
                            if (m.direction==='received') keys.push(`idTag=${m.payload?.idTag}`)
                            if (m.direction==='sent') keys.push(`transactionId=${m.payload?.transactionId}`)
                          } else if (m.action === 'MeterValues') {
                            keys.push(`mv=${(m.payload?.meterValue||[]).length}`)
                          } else if (m.action === 'StatusNotification') {
                            keys.push(`status=${m.payload?.status}`)
                          }
                          return (
                            <tr key={m.id} className={isError(m)?'err-row':''} style={{color: isError(m)? 'var(--err)' : undefined}}>
                              <td>{fmtTs(m.ts)}</td>
                              <td title={m.direction}>{iconFor(m.direction)} {m.direction}</td>
                              <td><span className="badge">{m.action}</span></td>
                              <td style={{fontSize:12}}>{m.relatedMessageId || ''}</td>
                              <td>{m.status || '-'}</td>
                              <td>{keys.join(' ')}</td>
                              <td>
                                <details>
                                  <summary>view</summary>
                                  <pre style={{whiteSpace:'pre-wrap'}}>{JSON.stringify(m.payload, null, 2)}</pre>
                                </details>
                              </td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
