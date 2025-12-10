const base = ''

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${base}/api${path}`)
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`)
  return res.json()
}

export async function apiPut<T>(path: string, body: any): Promise<T> {
  const res = await fetch(`${base}/api${path}`, {
    method: 'PUT',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  })
  if (!res.ok) throw new Error(`PUT ${path} failed: ${res.status}`)
  return res.json()
}

export function sse(url: string, onData: (data: any) => void): EventSource {
  const es = new EventSource(`${base}${url}`)
  es.onmessage = (evt) => {
    try { onData(JSON.parse(evt.data)) } catch { /* ignore */ }
  }
  return es
}
