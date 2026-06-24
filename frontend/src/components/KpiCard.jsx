import TactIcon from './TactIcon.jsx'

function Delta({ value }) {
  if (value == null) return null
  if (value === 0) return <span className="ue-delta flat">ללא שינוי</span>
  const up = value > 0
  return (
    <span className={`ue-delta ${up ? 'up' : 'down'}`}>
      <TactIcon name={up ? 'trending' : 'trendingDown'} size={14} />
      {up ? '+' : ''}{value}% השבוע
    </span>
  )
}

export default function KpiCard({ icon, label, value, unit, delta }) {
  return (
    <div className="ue-kpi">
      <div className="ue-kpi-top">
        <span className="ue-kpi-label">{label}</span>
        <span className="ue-kpi-ico"><TactIcon name={icon} size={20} /></span>
      </div>
      <div className="ue-kpi-val">
        {value}{unit && <span className="ue-kpi-unit"> {unit}</span>}
      </div>
      <Delta value={delta} />
    </div>
  )
}
