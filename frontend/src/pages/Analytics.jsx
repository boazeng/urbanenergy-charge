import { useEffect, useState } from 'react'
import KpiCard from '../components/KpiCard.jsx'
import { ConsumptionBar, RevenueArea, EvseDonut } from '../components/Charts.jsx'
import { api, fmtInt, fmtNum, fmtMoney } from '../api.js'

export default function Analytics() {
  const [d, setD] = useState(null)
  const [err, setErr] = useState(null)

  useEffect(() => {
    Promise.all([
      api.summary(), api.evseStatus(), api.consumption(7), api.revenue(30), api.partners(),
    ])
      .then(([summary, evse, consumption, revenue, partners]) =>
        setD({ summary, evse, consumption, revenue, partners }))
      .catch((e) => setErr(e.message))
  }, [])

  if (err) return <div className="ue-loading">שגיאה בטעינת נתונים: {err}<br />ודא שה-API רץ על פורט 8060.</div>
  if (!d) return <div className="ue-loading">טוען נתונים…</div>

  const s = d.summary
  const dl = s.deltas || {}
  const kpis = [
    { icon: 'globe', label: 'אתרים', value: fmtInt(s.locations), delta: dl.locations },
    { icon: 'energy', label: 'עמדות טעינה', value: fmtInt(s.chargingStations), delta: dl.chargingStations },
    { icon: 'briefcase', label: 'שותפים', value: fmtInt(s.partners), delta: dl.partners },
    { icon: 'users', label: 'נהגים', value: fmtInt(s.drivers), delta: dl.drivers },
    { icon: 'bolt', label: 'אנרגיה מצטברת', value: fmtInt(s.totalEnergyKwh), unit: 'kWh', delta: dl.totalEnergyKwh },
    { icon: 'invoices', label: 'יתרת ארנקים', value: fmtMoney(s.walletBalance), delta: dl.walletBalance },
    { icon: 'swap', label: 'טעינות ארנק', value: fmtInt(s.topupCount), delta: dl.topupCount },
    { icon: 'trending', label: 'סה״כ עסקאות טעינה', value: fmtMoney(s.totalChargingTransactions), delta: dl.totalChargingTransactions },
  ]

  const topPartners = [...d.partners]
    .sort((a, b) => b.wallet.totalUnsettledAmount - a.wallet.totalUnsettledAmount)
    .slice(0, 7)

  return (
    <>
      <div className="ue-head">
        <div>
          <div className="ue-title">לוח אנליטיקה</div>
          <div className="ue-sub">סקירת מערך הטעינה · Urban Energy — Yael Israel Group</div>
        </div>
      </div>

      <div className="ue-kpis">
        {kpis.map((k) => <KpiCard key={k.label} {...k} />)}
      </div>

      <div className="ue-panels">
        <div className="ue-panel">
          <div className="ue-panel-head">
            <span className="ue-panel-title">צריכת אנרגיה יומית</span>
            <span className="ue-panel-note">7 ימים אחרונים · kWh</span>
          </div>
          <ConsumptionBar data={d.consumption} />
        </div>
        <div className="ue-panel">
          <div className="ue-panel-head">
            <span className="ue-panel-title">סטטוס עמדות</span>
            <span className="ue-panel-note">בזמן אמת</span>
          </div>
          <EvseDonut data={d.evse} />
        </div>
      </div>

      <div className="ue-panels-2">
        <div className="ue-panel">
          <div className="ue-panel-head">
            <span className="ue-panel-title">הכנסות יומיות</span>
            <span className="ue-panel-note">30 ימים אחרונים · ₪</span>
          </div>
          <RevenueArea data={d.revenue} />
        </div>
        <div className="ue-panel">
          <div className="ue-panel-head">
            <span className="ue-panel-title">שותפים — יתרה לסליקה</span>
            <span className="ue-panel-note">Top 7</span>
          </div>
          <table className="ue-table">
            <thead>
              <tr><th>שותף</th><th>עמדות</th><th>יתרה לסליקה</th></tr>
            </thead>
            <tbody>
              {topPartners.map((p) => (
                <tr key={p.id}>
                  <td>{p.name}</td>
                  <td className="ue-num">{fmtInt(p.chargers)}</td>
                  <td className="ue-num ue-neg">{fmtMoney(p.wallet.totalUnsettledAmount)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  )
}
