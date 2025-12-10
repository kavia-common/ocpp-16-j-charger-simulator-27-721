import React, { useEffect, useState } from 'react'
import { apiGet, apiPut } from '../api'

type Settings = {
  idTag: string
  connectorId: number
  csmsUrl: string
  heartbeatInterval: number
  samplingInterval: number
  initiationTimingWindowSec: number
  meterStart: number
  offlineCacheLimit: number
  tlsEnabled: boolean
  authEnabled: boolean
}

export default function ConfigPage() {
  const [settings, setSettings] = useState<Settings | null>(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    apiGet<Settings>('/settings').then(setSettings).catch(e => setError(String(e)))
  }, [])

  const onChange = (k: keyof Settings, v: any) => {
    if (!settings) return
    setSettings({...settings, [k]: v})
    setSaved(false)
  }

  const save = async () => {
    if (!settings) return
    setSaving(true)
    setError(null)
    try {
      const updated = await apiPut<Settings>('/settings', settings)
      setSettings(updated)
      setSaved(true)
    } catch (e:any) {
      setError(String(e))
    } finally {
      setSaving(false)
    }
  }

  if (error) return <div className="panel">Error: {error}</div>
  if (!settings) return <div className="panel">Loading settings...</div>

  return (
    <div className="panel">
      <h2>Configuration</h2>
      <div className="grid">
        <div>
          <label>idTag</label>
          <input value={settings.idTag} onChange={e => onChange('idTag', e.target.value)} />
        </div>
        <div>
          <label>connectorId</label>
          <input type="number" value={settings.connectorId} onChange={e => onChange('connectorId', Number(e.target.value))} />
        </div>
        <div>
          <label>CSMS URL</label>
          <input value={settings.csmsUrl} onChange={e => onChange('csmsUrl', e.target.value)} />
        </div>
        <div>
          <label>Heartbeat Interval (sec)</label>
          <input type="number" value={settings.heartbeatInterval} onChange={e => onChange('heartbeatInterval', Number(e.target.value))} />
        </div>
        <div>
          <label>Sampling Interval (sec)</label>
          <input type="number" value={settings.samplingInterval} onChange={e => onChange('samplingInterval', Number(e.target.value))} />
        </div>
        <div>
          <label>Initiation Timing Window (sec)</label>
          <input type="number" value={settings.initiationTimingWindowSec} onChange={e => onChange('initiationTimingWindowSec', Number(e.target.value))} />
        </div>
        <div>
          <label>Meter Start (Wh)</label>
          <input type="number" value={settings.meterStart} onChange={e => onChange('meterStart', Number(e.target.value))} />
        </div>
        <div>
          <label>Offline Cache Limit</label>
          <input type="number" value={settings.offlineCacheLimit} onChange={e => onChange('offlineCacheLimit', Number(e.target.value))} />
        </div>
        <div className="switch">
          <input id="tls" type="checkbox" checked={settings.tlsEnabled} onChange={e => onChange('tlsEnabled', e.target.checked)} />
          <label htmlFor="tls">Enable TLS (wss)</label>
        </div>
        <div className="switch">
          <input id="auth" type="checkbox" checked={settings.authEnabled} onChange={e => onChange('authEnabled', e.target.checked)} />
          <label htmlFor="auth">Enable Authentication</label>
        </div>
      </div>
      <div className="row" style={{marginTop: 12}}>
        <button className="btn" onClick={save} disabled={saving}>{saving ? 'Saving...' : 'Save'}</button>
        {saved && <span className="badge">Saved</span>}
      </div>
    </div>
  )
}
