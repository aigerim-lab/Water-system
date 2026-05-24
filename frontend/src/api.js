const API_BASE = import.meta.env.VITE_API_URL || ''

async function post(path, body) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'API error')
  }
  return res.json()
}

async function get(path) {
  const res = await fetch(`${API_BASE}${path}`)
  if (!res.ok) throw new Error('API error')
  return res.json()
}

export const api = {
  health: () => get('/api/health'),
  meta: () => get('/api/dashboard/meta'),
  filterOptions: (filters) => post('/api/dashboard/filter-options', filters),
  summary: (filters) => post('/api/dashboard/summary', filters),
  charts: (filters) => post('/api/dashboard/charts', filters),
  ml: (filters, target) => post('/api/dashboard/ml', { ...filters, target }),
  compare: (payload) => post('/api/dashboard/compare', payload),
  chat: (payload) => post('/api/dashboard/chat', payload),
  exportCsv: async (filters) => {
    const res = await fetch(`${API_BASE}/api/dashboard/export/csv`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(filters),
    })
    if (!res.ok) throw new Error('Export failed')
    return res.blob()
  },
}
