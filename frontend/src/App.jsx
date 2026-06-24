import { useState } from 'react'
import Topbar from './components/Topbar.jsx'
import Analytics from './pages/Analytics.jsx'
import Partners from './pages/Partners.jsx'
import Locations from './pages/Locations.jsx'
import Billing from './pages/Billing.jsx'
import Sessions from './pages/Sessions.jsx'
import { PageHead } from './components/ui.jsx'

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

const PAGES = {
  analytics: <Analytics />,
  partners: <Partners />,
  locations: <Locations />,
  sessions: <Sessions />,
  billing: <Billing />,
}

export default function App() {
  const [page, setPage] = useState('analytics')
  return (
    <div className="tact-aurora ue-shell">
      <Topbar active={page} onNav={setPage} />
      <main className="ue-main">
        <div className="container">
          {PAGES[page] || <NeedsMapping name={LABELS[page]} />}
        </div>
      </main>
    </div>
  )
}
