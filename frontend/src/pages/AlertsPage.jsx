import React, { useState, useEffect } from 'react'
import { alertsAPI } from '../services/api'
import './AlertsPage.css'

const SEV_ORDER = { critical: 0, high: 1, medium: 2, low: 3 }

export default function AlertsPage() {
  const [alerts, setAlerts] = useState([])
  const [summary, setSummary] = useState({})
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')

  const fetchData = async () => {
    try {
      const [a, s] = await Promise.all([
        alertsAPI.getAlerts({ limit: 100 }),
        alertsAPI.getSummary(),
      ])
      setAlerts(a.data)
      setSummary(s.data)
    } catch {}
    setLoading(false)
  }

  useEffect(() => { fetchData() }, [])

  const handleAck = async (id) => {
    try {
      await alertsAPI.acknowledge(id)
      setAlerts(prev => prev.map(a => a.id === id ? { ...a, acknowledged: true } : a))
    } catch {}
  }

  const filtered = filter === 'all' ? alerts : alerts.filter(a => a.severity === filter)

  const sevCounts = { critical: 0, high: 0, medium: 0, low: 0 }
  alerts.forEach(a => { if (sevCounts[a.severity] !== undefined) sevCounts[a.severity]++ })

  if (loading) {
    return (
      <div className="page-loading">
        <div className="spinner" style={{ width: 40, height: 40 }} />
        <div style={{ color: 'var(--text-muted)', marginTop: 16 }}>Loading alerts...</div>
      </div>
    )
  }

  return (
    <div className="alerts-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">⚡ Alert Center</h1>
          <p className="page-sub">Real-time threat alerts and intelligence notifications</p>
        </div>
        <button className="btn btn-ghost btn-sm" onClick={fetchData}>↺ Refresh</button>
      </div>

      {/* Summary cards */}
      <div className="alert-summary-grid">
        {['critical', 'high', 'medium', 'low'].map(sev => (
          <div key={sev} className={`alert-summary-card sev-card-${sev}`}
            onClick={() => setFilter(filter === sev ? 'all' : sev)}
            style={{ cursor: 'pointer', opacity: filter === 'all' || filter === sev ? 1 : 0.4 }}>
            <div className="asc-label">{sev}</div>
            <div className="asc-value">{sevCounts[sev]}</div>
            <div className="asc-bar">
              <div className="asc-bar-fill" style={{
                width: `${Math.min((sevCounts[sev] / Math.max(alerts.length, 1)) * 100, 100)}%`,
                background: `var(--severity-${sev})`,
              }} />
            </div>
          </div>
        ))}
      </div>

      {/* Filter tabs */}
      <div className="alert-filter-row">
        {['all', 'critical', 'high', 'medium', 'low'].map(f => (
          <button key={f}
            className={`btn btn-xs ${filter === f ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setFilter(f)}>
            {f === 'all' ? `All (${alerts.length})` : `${f} (${sevCounts[f]})`}
          </button>
        ))}
      </div>

      {/* Alerts list */}
      <div className="alerts-container">
        {filtered.length === 0 && (
          <div className="empty-state">No alerts match the current filter</div>
        )}
        {filtered.map((alert, idx) => (
          <div key={alert.id}
            className={`alert-card glass animate-fadein sev-left-${alert.severity} ${alert.acknowledged ? 'acked' : ''}`}
            style={{ animationDelay: `${idx * 30}ms` }}>
            <div className="alert-card-top">
              <div className="alert-card-left">
                <span className={`badge badge-${alert.severity}`}>{alert.severity}</span>
                <span className={`badge badge-${alert.type}`}>{alert.type}</span>
                <span className="alert-card-title">{alert.title}</span>
              </div>
              <div className="alert-card-right">
                {alert.risk_score && (
                  <span className="alert-risk mono" style={{
                    color: alert.risk_score > 0.7 ? 'var(--accent-red)' : alert.risk_score > 0.5 ? 'var(--accent-orange)' : 'var(--accent-green)',
                  }}>
                    {(alert.risk_score * 100).toFixed(1)}%
                  </span>
                )}
                {!alert.acknowledged && (
                  <button className="btn btn-ghost btn-xs" onClick={() => handleAck(alert.id)}>
                    ✓ ACK
                  </button>
                )}
                {alert.acknowledged && (
                  <span className="badge badge-low" style={{ opacity: 0.6 }}>ACKED</span>
                )}
              </div>
            </div>
            {alert.description && (
              <div className="alert-card-desc">{alert.description}</div>
            )}
            <div className="alert-card-meta">
              {alert.latitude && alert.longitude && (
                <span className="mono">📍 {alert.latitude?.toFixed(3)}, {alert.longitude?.toFixed(3)}</span>
              )}
              <span className="mono">{alert.created_at?.slice(0, 19)}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
