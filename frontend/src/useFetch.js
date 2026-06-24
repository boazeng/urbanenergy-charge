import { useEffect, useState } from 'react'

// Tiny data-loading hook shared by the list screens.
export function useFetch(fn, deps = []) {
  const [data, setData] = useState(null)
  const [err, setErr] = useState(null)
  useEffect(() => {
    let alive = true
    fn()
      .then((d) => alive && setData(d))
      .catch((e) => alive && setErr(e.message))
    return () => {
      alive = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)
  return { data, err }
}
