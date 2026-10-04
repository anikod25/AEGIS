import { useState, useEffect, useCallback } from 'react'
import { dashboard } from '../services/api'

/**
 * Custom hook that fetches the dashboard summary from the real API.
 * Returns { summary, loading, error, refresh }.
 * refresh() is stable across renders (useCallback).
 */
export function useDashboard() {
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)

  const refresh = useCallback(() => {
    setLoading(true)
    setError(null)
    dashboard.getSummary()
      .then(data => setSummary(data))
      .catch(err => setError(err.message ?? 'Failed to load dashboard data.'))
      .finally(() => setLoading(false))
  }, [])

  // Fetch on mount
  useEffect(() => {
    refresh()
  }, [refresh])

  return { summary, loading, error, refresh }
}
