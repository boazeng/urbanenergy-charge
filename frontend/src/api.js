// Single place that talks to the management API. Swap BASE later for prod.
const BASE = 'http://localhost:8060/api'

async function get(path) {
  const r = await fetch(`${BASE}${path}`)
  if (!r.ok) throw new Error(`${path} → ${r.status}`)
  return r.json()
}

export const api = {
  summary: () => get('/analytics/summary'),
  evseStatus: () => get('/analytics/evse-status'),
  sessionStatus: () => get('/analytics/session-status'),
  consumption: (days = 7) => get(`/analytics/consumption?days=${days}`),
  revenue: (days = 30) => get(`/analytics/revenue?days=${days}`),
  partners: () => get('/partners'),
  locations: () => get('/locations'),
  sessions: (limit = 50) => get(`/sessions?limit=${limit}`),
}

// --- formatting helpers (Hebrew locale, ≤2 decimals, thousands separators) ---
export const fmtInt = (n) => new Intl.NumberFormat('he-IL').format(Math.round(n ?? 0))
export const fmtNum = (n) =>
  new Intl.NumberFormat('he-IL', { maximumFractionDigits: 2 }).format(n ?? 0)
export const fmtKwh = (n) => `${fmtNum(n)} kWh`
export const fmtMoney = (n) => `₪ ${fmtNum(n)}`
export const fmtDateTime = (iso) =>
  iso ? new Intl.DateTimeFormat('he-IL', { dateStyle: 'short', timeStyle: 'short' }).format(new Date(iso)) : '—'
export const fmtDuration = (s) => {
  if (!s) return '—'
  const m = Math.floor(s / 60)
  return m ? `${m} דק׳` : `${s} שנ׳`
}
