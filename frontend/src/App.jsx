import { useEffect, useState } from 'react'
import Topbar from './components/Topbar.jsx'
import Analytics from './pages/Analytics.jsx'
import Partners from './pages/Partners.jsx'
import Locations from './pages/Locations.jsx'
import Billing from './pages/Billing.jsx'
import Sessions from './pages/Sessions.jsx'
import Admin from './pages/Admin.jsx'
import { PageHead } from './components/ui.jsx'
import { auth } from './api.js'

const LABELS = { chargers: 'עמדות' }

function NeedsMapping({ name }) {
  return (
    <>
      <PageHead title={name} />
      <div className="ue-loading">
        מסך «{name}» — ממתין למיפוי ה-endpoint של Evoltsoft.<br />
        כדי לחבר נתונים אמיתיים, צריך ללכוד HAR של דף ה{name} בפורטל (כמו שעשינו לאנליטיקה).
      </div>
    </>
  )
}

export default function App() {
  const [page, setPage] = useState('analytics')
  const [user, setUser] = useState(null)

  useEffect(() => {
    auth.me().then(setUser)
  }, [])

  const isAdmin = user?.role === 'admin'
  const pages = {
    analytics: <Analytics />,
    partners: <Partners />,
    locations: <Locations />,
    sessions: <Sessions />,
    billing: <Billing />,
    ...(isAdmin ? { admin: <Admin /> } : {}),
  }

  return (
    <div className="tact-aurora ue-shell">
      <Topbar active={page} onNav={setPage} user={user} />
      <main className="ue-main">
        <div className="container">
          {pages[page] || <NeedsMapping name={LABELS[page]} />}
        </div>
      </main>
    </div>
  )
}
