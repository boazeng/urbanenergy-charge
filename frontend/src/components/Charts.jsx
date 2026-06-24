import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  AreaChart, Area, PieChart, Pie, Cell,
} from 'recharts'
import { fmtNum, fmtMoney, fmtKwh, fmtInt } from '../api.js'

const STEEL = '#1F3A5F'
const STEEL_L = '#2A4F7A'
const GREEN = '#2F8F5B'
const RUST = '#D64A2E'
const TAUPE = '#9A9384'
const AXIS = '#706A60'
const GRID = '#E7E2D6'

// EVSE status -> colour (steel family + green for available)
export const EVSE_COLORS = {
  AVAILABLE: GREEN,
  CHARGING: STEEL,
  PREPARING: STEEL_L,
  FINISHING: '#6E8FB5',
  UNKNOWN: TAUPE,
}
const EVSE_HE = {
  AVAILABLE: 'זמין', CHARGING: 'טוען', PREPARING: 'בהכנה',
  FINISHING: 'מסיים', UNKNOWN: 'לא ידוע',
}

const ddmm = (iso) => { const d = new Date(iso); return `${d.getDate()}/${d.getMonth() + 1}` }

function Box({ children }) {
  return (
    <div style={{
      background: 'var(--color-bg-white)', border: '1px solid var(--color-border)',
      borderRadius: 10, padding: '8px 12px', boxShadow: 'var(--shadow-md)',
      fontSize: '.82rem', fontFamily: 'var(--font-family)',
    }}>{children}</div>
  )
}

export function ConsumptionBar({ data }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} margin={{ top: 6, right: 6, left: 6, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID} vertical={false} />
        <XAxis dataKey="date" tickFormatter={ddmm} tick={{ fill: AXIS, fontSize: 12 }} axisLine={{ stroke: GRID }} tickLine={false} />
        <YAxis tick={{ fill: AXIS, fontSize: 12 }} axisLine={false} tickLine={false} width={48} />
        <Tooltip cursor={{ fill: 'rgba(31,58,95,0.06)' }}
          content={({ active, payload, label }) => active && payload?.length
            ? <Box><div style={{ color: AXIS }}>{ddmm(label)}</div><b>{fmtKwh(payload[0].value)}</b></Box> : null} />
        <Bar dataKey="totalKwh" fill={STEEL} radius={[6, 6, 0, 0]} maxBarSize={42} />
      </BarChart>
    </ResponsiveContainer>
  )
}

export function RevenueArea({ data }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <AreaChart data={data} margin={{ top: 6, right: 6, left: 6, bottom: 0 }}>
        <defs>
          <linearGradient id="rev" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={STEEL} stopOpacity={0.28} />
            <stop offset="100%" stopColor={STEEL} stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID} vertical={false} />
        <XAxis dataKey="date" tickFormatter={ddmm} tick={{ fill: AXIS, fontSize: 12 }} axisLine={{ stroke: GRID }} tickLine={false} minTickGap={24} />
        <YAxis tick={{ fill: AXIS, fontSize: 12 }} axisLine={false} tickLine={false} width={48} />
        <Tooltip content={({ active, payload, label }) => active && payload?.length
          ? <Box><div style={{ color: AXIS }}>{ddmm(label)}</div><b>{fmtMoney(payload[0].value)}</b></Box> : null} />
        <Area type="monotone" dataKey="revenue" stroke={STEEL} strokeWidth={2.5} fill="url(#rev)" />
      </AreaChart>
    </ResponsiveContainer>
  )
}

export function EvseDonut({ data }) {
  const rows = Object.entries(data).map(([k, v]) => ({ key: k, name: EVSE_HE[k] || k, value: v }))
  const total = rows.reduce((s, r) => s + r.value, 0)
  return (
    <div>
      <ResponsiveContainer width="100%" height={190}>
        <PieChart>
          <Pie data={rows} dataKey="value" nameKey="name" innerRadius={58} outerRadius={84} paddingAngle={2} stroke="none">
            {rows.map((r) => <Cell key={r.key} fill={EVSE_COLORS[r.key] || TAUPE} />)}
          </Pie>
          <Tooltip content={({ active, payload }) => active && payload?.length
            ? <Box><b>{payload[0].name}:</b> {fmtInt(payload[0].value)}</Box> : null} />
        </PieChart>
      </ResponsiveContainer>
      <div className="ue-legend">
        {rows.map((r) => (
          <div className="ue-legend-row" key={r.key}>
            <span className="ue-legend-name">
              <span className="ue-dot" style={{ background: EVSE_COLORS[r.key] || TAUPE }} />
              {r.name}
            </span>
            <span className="ue-legend-val">{fmtInt(r.value)} · {Math.round(r.value / total * 100)}%</span>
          </div>
        ))}
      </div>
    </div>
  )
}
