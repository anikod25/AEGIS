import { useState, useEffect, useCallback } from 'react'
import { reports } from '../services/api'
import DashboardCard from '../components/DashboardCard'
import './ReportsPage.css'

const TYPE_LABEL = { url: 'URL', phishing: 'Email', password: 'Password' }
const RISK_ORDER = ['critical', 'high', 'medium', 'low', 'safe']
const RISK_COLORS = {
  critical: 'var(--danger)',
  high:     '#f0803c',
  medium:   'var(--warning)',
  low:      'var(--info)',
  safe:     'var(--success)',
}

function scoreAccent(score) {
  if (score === null || score === undefined) return 'default'
  if (score >= 80) return 'success'
  if (score >= 60) return 'warning'
  return 'danger'
}

function topType(byType) {
  const entries = Object.entries(byType).filter(([, n]) => n > 0)
  if (!entries.length) return 'None'
  entries.sort((a, b) => b[1] - a[1])
  return TYPE_LABEL[entries[0][0]] ?? entries[0][0]
}

function BarRow({ label, count, total, color }) {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0
  return (
    <div className="rp-bar-row">
      <span className="rp-bar-label">{label}</span>
      <div className="rp-bar-track">
        <div className="rp-bar-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="rp-bar-count">{count}</span>
    </div>
  )
}

function downloadCSV(report) {
  const rows = [
    ['Category', 'Subcategory', 'Count'],
    ...Object.entries(report.by_type).map(([k, v]) => ['Type', TYPE_LABEL[k] ?? k, v]),
    ...RISK_ORDER.map(r => ['Risk', r.charAt(0).toUpperCase() + r.slice(1), report.by_risk[r] ?? 0]),
    ['Summary', 'Total scans', report.total_scans],
    ['Summary', 'Security score', report.score !== null && report.score !== undefined ? report.score : 'N/A'],
  ]
  const csv = rows.map(r => r.map(c => `"${c}"`).join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href     = url
  a.download = `aegis-report-${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

export default function ReportsPage() {
  const [report,  setReport]  = useState(null)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)

  const load = useCallback(() => {
    setLoading(true)
    setError(null)
    reports.list()
      .then(data => { setReport(data); setLoading(false) })
      .catch(err  => { setError(err.message ?? 'Failed to load report.'); setLoading(false) })
  }, [])

  useEffect(() => { load() }, [load])

  return (
    <div className="rp-page">
      <div className="rp-header">
        <div>
          <h1 className="rp-title">Security Report</h1>
          {!loading && report && (
            <p className="rp-subtitle">
              Generated {new Date(report.generated_at).toLocaleString()}
            </p>
          )}
        </div>
        <div className="rp-header-actions">
          <button className="rp-refresh-btn" onClick={load} disabled={loading}>Refresh</button>
          {report && report.total_scans > 0 && (
            <button className="rp-download-btn" onClick={() => downloadCSV(report)}>
              Download CSV
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="rp-error" role="alert">
          {error}
          <button className="rp-error-retry" onClick={load}>Retry</button>
        </div>
      )}

      {loading && (
        <div className="rp-skeleton-grid">
          {[1, 2, 3].map(i => <div key={i} className="rp-skeleton-card" />)}
        </div>
      )}

      {!loading && report && report.total_scans === 0 && (
        <div className="rp-empty">
          No scan data yet. Run some analyses to generate a report.
        </div>
      )}

      {!loading && report && report.total_scans > 0 && (
        <>
          <section className="rp-metrics">
            <DashboardCard
              title="Total Scans"
              value={report.total_scans}
              subtitle={`${topType(report.by_type)} most common`}
              accent="info"
            />
            <DashboardCard
              title="Security Score"
              value={report.score !== null && report.score !== undefined ? `${report.score}/100` : 'N/A'}
              subtitle={
                report.score === null || report.score === undefined ? 'No data'
                : report.score >= 80 ? 'Good'
                : report.score >= 60 ? 'Fair'
                : report.score >= 40 ? 'Poor'
                : 'Critical'
              }
              accent={scoreAccent(report.score)}
            />
            <DashboardCard
              title="High Risk Findings"
              value={(report.by_risk.critical ?? 0) + (report.by_risk.high ?? 0)}
              subtitle={`${report.by_risk.critical ?? 0} critical, ${report.by_risk.high ?? 0} high`}
              accent={(report.by_risk.critical ?? 0) + (report.by_risk.high ?? 0) > 0 ? 'danger' : 'success'}
            />
          </section>

          <section className="rp-charts">
            <DashboardCard title="By Scan Type">
              <div className="rp-bars">
                {Object.entries(report.by_type).map(([type, count]) => (
                  <BarRow
                    key={type}
                    label={TYPE_LABEL[type] ?? type}
                    count={count}
                    total={report.total_scans}
                    color="var(--accent)"
                  />
                ))}
              </div>
            </DashboardCard>

            <DashboardCard title="By Risk Level">
              <div className="rp-bars">
                {RISK_ORDER.map(risk => (
                  <BarRow
                    key={risk}
                    label={risk.charAt(0).toUpperCase() + risk.slice(1)}
                    count={report.by_risk[risk] ?? 0}
                    total={report.total_scans}
                    color={RISK_COLORS[risk]}
                  />
                ))}
              </div>
            </DashboardCard>
          </section>
        </>
      )}
    </div>
  )
}
