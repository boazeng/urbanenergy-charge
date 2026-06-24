// Single place that talks to the management API.
// Same-origin '/api' in prod (nginx proxies it to the backend); the Vite dev
// server proxies '/api' → localhost:8060. Override with VITE_API_BASE if needed.
const BASE = import.meta.env.VITE_API_BASE ?? '/api'

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

// --- auth (shared-auth endpoints live at the root, not under /api) ---
async function authPost(path, body) {
  const r = await fetch(path, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || `${path} → ${r.status}`)
  return r.json()
}

export const auth = {
  me: async () => {
    try {
      const r = await fetch('/auth/me')
      return r.ok ? await r.json() : null
    } catch {
      return null
    }
  },
  users: () => fetch('/auth/users').then((r) => r.json()),
  saveUser: (user) => authPost('/auth/users', user),
  deleteUser: (email) => authPost('/auth/users/delete', { email }),
  logoutUrl: '/logout',
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
