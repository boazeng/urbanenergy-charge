import { useEffect, useState } from 'react'
import { auth } from '../api.js'
import { PageHead, Loading } from '../components/ui.jsx'
import KpiCard from '../components/KpiCard.jsx'

const ROLE_HE = { admin: 'מנהל', approver: 'מאשר', user: 'משתמש' }

export default function Admin() {
  const [data, setData] = useState(null)
  const [err, setErr] = useState(null)
  const [busy, setBusy] = useState(false)
  const [add, setAdd] = useState({ email: '', name: '', role: 'user' })

  const load = () => auth.users().then(setData).catch((e) => setErr(e.message))
  useEffect(() => {
    load()
  }, [])

  if (err) return (<><PageHead title="ניהול מערכת" /><Loading error={err} /></>)
  if (!data) return (<><PageHead title="ניהול מערכת" /><Loading /></>)

  const roles = data.roles || ['admin', 'approver', 'user']
  const users = data.users || []

  async function mutate(fn) {
    setBusy(true)
    try {
      await fn()
      await load()
    } catch (e) {
      alert(e.message)
    } finally {
      setBusy(false)
    }
  }

  const save = (u, changes) =>
    mutate(() => auth.saveUser({ email: u.email, name: u.name, role: u.role, active: u.active, ...changes }))
  const remove = (email) => { if (confirm(`למחוק את ${email}?`)) mutate(() => auth.deleteUser(email)) }
  const addUser = (e) => {
    e.preventDefault()
    if (!add.email) return
    mutate(() => auth.saveUser({ ...add, active: true })).then(() => setAdd({ email: '', name: '', role: 'user' }))
  }

  const admins = users.filter((u) => u.role === 'admin').length

  return (
    <>
      <PageHead title="ניהול מערכת" sub="הרשאות גישה ותפקידים" />
      <div className="ue-strip">
        <KpiCard icon="users" label="משתמשים" value={users.length} />
        <KpiCard icon="briefcase" label="מנהלים" value={admins} />
      </div>

      <div className="ue-panel" style={{ marginBottom: 18 }}>
        <div className="ue-panel-head"><span className="ue-panel-title">הוספת משתמש</span></div>
        <form onSubmit={addUser} className="ue-addrow">
          <input className="ue-field" type="email" placeholder="אימייל (Gmail)" value={add.email}
            onChange={(e) => setAdd({ ...add, email: e.target.value })} required />
          <input className="ue-field" placeholder="שם (אופציונלי)" value={add.name}
            onChange={(e) => setAdd({ ...add, name: e.target.value })} />
          <select className="ue-field" value={add.role} onChange={(e) => setAdd({ ...add, role: e.target.value })}>
            {roles.map((r) => <option key={r} value={r}>{ROLE_HE[r] || r}</option>)}
          </select>
          <button className="tact-btn tact-btn-primary" disabled={busy}>הוסף</button>
        </form>
      </div>

      <div className="ue-panel">
        <div className="ue-panel-head"><span className="ue-panel-title">משתמשים מורשים</span></div>
        <table className="ue-table">
          <thead>
            <tr><th>אימייל</th><th>שם</th><th>תפקיד</th><th>פעיל</th><th></th></tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.email}>
                <td>{u.email}</td>
                <td>{u.name || '—'}</td>
                <td>
                  <select className="ue-field" value={u.role} disabled={busy}
                    onChange={(e) => save(u, { role: e.target.value })}>
                    {roles.map((r) => <option key={r} value={r}>{ROLE_HE[r] || r}</option>)}
                  </select>
                </td>
                <td>
                  <input type="checkbox" checked={!!u.active} disabled={busy}
                    onChange={() => save(u, { active: !u.active })} />
                </td>
                <td className="ue-num">
                  <button className="tact-btn tact-btn-ghost" disabled={busy}
                    onClick={() => remove(u.email)}>מחק</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}
