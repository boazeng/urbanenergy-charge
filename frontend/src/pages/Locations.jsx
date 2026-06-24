import { useFetch } from '../useFetch.js'
import { api, fmtInt } from '../api.js'
import { PageHead, Loading, StatusPill } from '../components/ui.jsx'
import KpiCard from '../components/KpiCard.jsx'

export default function Locations() {
  const { data, err } = useFetch(api.locations)
  if (!data) return (<><PageHead title="אתרים" /><Loading error={err} /></>)

  const active = data.filter((l) => l.status === 'ACTIVE').length
  const chargers = data.reduce((s, l) => s + l.chargers, 0)

  return (
    <>
      <PageHead title="אתרים" sub={`${data.length} אתרי טעינה`} />
      <div className="ue-strip">
        <KpiCard icon="globe" label="סך אתרים" value={fmtInt(data.length)} />
        <KpiCard icon="target" label="אתרים פעילים" value={fmtInt(active)} />
        <KpiCard icon="energy" label="עמדות באתרים" value={fmtInt(chargers)} />
      </div>
      <div className="ue-panel">
        <table className="ue-table">
          <thead>
            <tr><th>אתר</th><th>עיר</th><th>מחוז</th><th>עמדות</th><th>סטטוס</th></tr>
          </thead>
          <tbody>
            {data.map((l) => (
              <tr key={l.id}>
                <td>{l.name}</td>
                <td>{l.city || '—'}</td>
                <td>{l.state || '—'}</td>
                <td className="ue-num">{fmtInt(l.chargers)}</td>
                <td><StatusPill status={l.status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}
