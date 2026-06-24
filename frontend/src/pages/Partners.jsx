import { useFetch } from '../useFetch.js'
import { api, fmtInt, fmtMoney } from '../api.js'
import { PageHead, Loading, StatusPill } from '../components/ui.jsx'
import KpiCard from '../components/KpiCard.jsx'

export default function Partners() {
  const { data, err } = useFetch(api.partners)
  if (!data) return (<><PageHead title="שותפים" /><Loading error={err} /></>)

  const totalUnsettled = data.reduce((s, p) => s + p.wallet.totalUnsettledAmount, 0)
  const active = data.filter((p) => p.status === 'ACTIVE').length
  const sorted = [...data].sort((a, b) => b.wallet.totalUnsettledAmount - a.wallet.totalUnsettledAmount)

  return (
    <>
      <PageHead title="שותפים" sub={`${data.length} ארגוני שותפים · ${active} פעילים`} />
      <div className="ue-strip">
        <KpiCard icon="briefcase" label="סך שותפים" value={fmtInt(data.length)} />
        <KpiCard icon="invoices" label="סך יתרה לסליקה" value={fmtMoney(totalUnsettled)} />
      </div>
      <div className="ue-panel">
        <table className="ue-table">
          <thead>
            <tr><th>שותף</th><th>עיר</th><th>סטטוס</th><th>יתרה לסליקה</th></tr>
          </thead>
          <tbody>
            {sorted.map((p) => (
              <tr key={p.id}>
                <td>{p.name}</td>
                <td>{p.city || '—'}</td>
                <td><StatusPill status={p.status} /></td>
                <td className="ue-num ue-neg">{fmtMoney(p.wallet.totalUnsettledAmount)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}
