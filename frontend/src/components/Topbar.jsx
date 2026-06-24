import TactLogo from './TactLogo.jsx'
import { auth } from '../api.js'

const NAV = [
  { key: 'analytics', label: 'אנליטיקה' },
  { key: 'partners', label: 'שותפים' },
  { key: 'locations', label: 'אתרים' },
  { key: 'chargers', label: 'עמדות' },
  { key: 'sessions', label: 'טעינות' },
  { key: 'billing', label: 'חיוב וסליקה' },
]

export default function Topbar({ active = 'analytics', onNav = () => {}, user = null }) {
  const isAdmin = user?.role === 'admin'
  const nav = isAdmin ? [...NAV, { key: 'admin', label: 'ניהול מערכת' }] : NAV
  const initials = (user?.name || user?.email || 'בא').trim().slice(0, 2)

  return (
    <header className="tact-bar ue-bar">
      <div className="ue-bar-side">
        <TactLogo word="urban energy" size={1.05} />
      </div>

      <nav className="tact-nav">
        {nav.map((n) => (
          <button key={n.key} className={n.key === active ? 'active' : ''} onClick={() => onNav(n.key)}>
            {n.label}
          </button>
        ))}
      </nav>

      <div className="ue-bar-side">
        {user && (
          <div className="ue-userwrap">
            <span className="ue-email">{user.email}</span>
            <a className="ue-logout" href={auth.logoutUrl}>יציאה</a>
            <div className="ue-user">{initials}</div>
          </div>
        )}
      </div>
    </header>
  )
}
