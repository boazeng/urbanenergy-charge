import TactLogo from './TactLogo.jsx'

const NAV = [
  { key: 'analytics', label: 'אנליטיקה' },
  { key: 'partners', label: 'שותפים' },
  { key: 'locations', label: 'אתרים' },
  { key: 'chargers', label: 'עמדות' },
  { key: 'sessions', label: 'טעינות' },
  { key: 'billing', label: 'חיוב וסליקה' },
]

export default function Topbar({ active = 'analytics', onNav = () => {} }) {
  return (
    <header className="tact-bar ue-bar">
      <div className="ue-bar-side">
        <TactLogo word="urban energy" size={1.05} />
      </div>

      <nav className="tact-nav">
        {NAV.map((n) => (
          <button
            key={n.key}
            className={n.key === active ? 'active' : ''}
            onClick={() => onNav(n.key)}
          >
            {n.label}
          </button>
        ))}
      </nav>

      <div className="ue-bar-side">
        <div className="ue-user">בא</div>
      </div>
    </header>
  )
}
