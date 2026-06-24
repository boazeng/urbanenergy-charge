import { useFetch } from '../useFetch.js'
import { api, fmtInt, fmtNum, fmtMoney, fmtDateTime, fmtDuration } from '../api.js'
import { PageHead, Loading, SessionStatus } from '../components/ui.jsx'
import KpiCard from '../components/KpiCard.jsx'

export default function Sessions() {
  const { data, err } = useFetch(() => api.sessions(50))
  if (!data) return (<><PageHead title="טעינות" /><Loading error={err} /></>)

  const kwh = data.reduce((s, x) => s + x.kwh, 0)
  const cost = data.reduce((s, x) => s + x.cost, 0)

  return (
    <>
      <PageHead title="טעינות" sub={`${data.length} הטעינות האחרונות`} />
      <div className="ue-strip">
        <KpiCard icon="bolt" label="טעינות מוצגות" value={fmtInt(data.length)} />
        <KpiCard icon="energy" label="אנרגיה (בתצוגה)" value={fmtNum(kwh)} unit="kWh" />
        <KpiCard icon="invoices" label="הכנסה (בתצוגה)" value={fmtMoney(cost)} />
      </div>
      <div className="ue-panel">
        <table className="ue-table">
          <thead>
            <tr>
              <th>מס׳</th><th>עמדה</th><th>נהג</th><th>תאריך</th>
              <th>משך</th><th>kWh</th><th>עלות</th><th>סטטוס</th>
            </tr>
          </thead>
          <tbody>
            {data.map((s) => (
              <tr key={s.id}>
                <td className="ue-num">{s.transactionId}</td>
                <td>{s.charger || '—'}</td>
                <td>{s.driver || '—'}</td>
                <td>{fmtDateTime(s.startedAt)}</td>
                <td>{fmtDuration(s.durationS)}</td>
                <td className="ue-num">{fmtNum(s.kwh)}</td>
                <td className="ue-num">{fmtMoney(s.cost)}</td>
                <td><SessionStatus status={s.status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}
