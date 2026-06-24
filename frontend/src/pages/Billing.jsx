import { useFetch } from '../useFetch.js'
import { api, fmtInt, fmtMoney } from '../api.js'
import { PageHead, Loading } from '../components/ui.jsx'
import KpiCard from '../components/KpiCard.jsx'

export default function Billing() {
  const { data, err } = useFetch(api.partners)
  if (!data) return (<><PageHead title="חיוב וסליקה" /><Loading error={err} /></>)

  const toSettle = data.filter((p) => p.wallet.totalUnsettledAmount > 0)
  const total = toSettle.reduce((s, p) => s + p.wallet.totalUnsettledAmount, 0)
  const sorted = [...toSettle].sort((a, b) => b.wallet.totalUnsettledAmount - a.wallet.totalUnsettledAmount)

  return (
    <>
      <PageHead
        title="חיוב וסליקה"
        sub="יתרות לסילוק מול Priority"
        right={<button className="tact-btn tact-btn-primary ue-settle-btn" disabled>ייצוא סליקה ל-Priority</button>}
      />
      <div className="ue-strip">
        <KpiCard icon="invoices" label="סך לסליקה" value={fmtMoney(total)} />
        <KpiCard icon="briefcase" label="שותפים לסליקה" value={fmtInt(toSettle.length)} />
      </div>
      <div className="ue-panel">
        <div className="ue-panel-head">
          <span className="ue-panel-title">יתרות פתוחות לסילוק</span>
          <span className="ue-panel-note">ממוין לפי גובה היתרה</span>
        </div>
        <table className="ue-table">
          <thead>
            <tr><th>שותף</th><th>עיר</th><th>יתרה לסליקה</th></tr>
          </thead>
          <tbody>
            {sorted.map((p) => (
              <tr key={p.id}>
                <td>{p.name}</td>
                <td>{p.city || '—'}</td>
                <td className="ue-num ue-neg">{fmtMoney(p.wallet.totalUnsettledAmount)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}
