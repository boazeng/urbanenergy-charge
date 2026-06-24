// Small shared UI atoms used across the list screens.

export function PageHead({ title, sub, right }) {
  return (
    <div className="ue-head">
      <div>
        <div className="ue-title">{title}</div>
        {sub && <div className="ue-sub">{sub}</div>}
      </div>
      {right}
    </div>
  )
}

export function Loading({ error }) {
  return (
    <div className="ue-loading">
      {error ? `שגיאה בטעינת נתונים: ${error}` : 'טוען נתונים…'}
    </div>
  )
}

export function StatusPill({ status }) {
  const on = status === 'ACTIVE'
  return <span className={`ue-status ${on ? 'on' : 'off'}`}>{on ? 'פעיל' : 'לא פעיל'}</span>
}

const SESSION_LABEL = { Finished: 'הושלם', Running: 'בטעינה', Rejected: 'נדחה' }
const SESSION_CLS = { Finished: 'fin', Running: 'run', Rejected: 'rej' }

export function SessionStatus({ status }) {
  return <span className={`ue-status ${SESSION_CLS[status] || 'off'}`}>{SESSION_LABEL[status] || status}</span>
}
