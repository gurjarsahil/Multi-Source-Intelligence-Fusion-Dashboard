import React, { useState, useEffect } from 'react'
import { intelAPI, alertsAPI } from '../services/api'
import { BarChart, Bar, LineChart, Line, AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, PieChart, Pie } from 'recharts'
import './DashboardPage.css'

const COLORS = {
  critical: '#ff3860', high: '#ff8c42', medium: '#ffd700',
  low: '#00ff88', safe: '#00ff88', threat: '#ff3860', suspicious: '#ffd700',
  SIGINT: '#00d4ff', HUMINT: '#a855f7', OSINT: '#00ff88', GEOINT: '#ff8c42', CYBINT: '#ff3860',
}

function StatCard({ label, value, sub, accent, icon }) {
  return (
    <div className="stat-card" style={{ '--accent-line': accent || 'var(--accent-cyan)' }}>
      <div className="stat-header">
        <span className="stat-label">{label}</span>
        <span className="stat-icon-badge">{icon}</span>
      </div>
      <div className="stat-value" style={{ color: accent || 'var(--accent-cyan)' }}>{value}</div>
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  )
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="chart-tooltip glass">
      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color || 'var(--accent-cyan)', fontSize: 13, fontWeight: 600 }}>
          {p.name}: {p.value}
        </div>
      ))}
    </div>
  )
}

export default function DashboardPage() {
  const [stats, setStats] = useState(null)
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)

  const fetchData = async () => {
    try {
      const [s, a] = await Promise.all([intelAPI.getStats(), alertsAPI.getAlerts({ limit: 8 })])
      setStats(s.data)
      setAlerts(a.data)
    } catch {}
    setLoading(false)
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 15000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="page-loading">
        <div className="spinner" style={{ width: 40, height: 40 }} />
        <div style={{ color: 'var(--text-muted)', marginTop: 16 }}>Loading intelligence feed...</div>
      </div>
    )
  }

  const typeChartData = Object.entries(stats?.data_by_type || {}).map(([k, v]) => ({
    name: k, value: v, fill: COLORS[k] || 'var(--accent-cyan)',
  }))

  const severityChartData = Object.entries(stats?.alerts_by_severity || {}).map(([k, v]) => ({
    name: k.charAt(0).toUpperCase() + k.slice(1), value: v, fill: COLORS[k],
  }))

  const recentActivity = stats?.recent_activity || []

  return (
    <div className="dashboard-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Intelligence Dashboard</h1>
          <p className="page-sub">Real-time multi-source threat fusion and analysis</p>
        </div>
        <button className="btn btn-ghost btn-sm" onClick={fetchData}>↺ Refresh</button>
      </div>

      {/* Stat Cards */}
      <div className="stats-grid">
        <StatCard label="Total Intelligence" value={stats?.total_intelligence ?? 0}
          sub="Records ingested" accent="var(--accent-cyan)" icon="◈" />
        <StatCard label="Active Threats" value={stats?.active_threats ?? 0}
          sub="Unacknowledged alerts" accent="var(--accent-red)" icon="⚡" />
        <StatCard label="Critical Alerts" value={stats?.critical_alerts ?? 0}
          sub="Highest priority" accent="var(--severity-critical)" icon="⚠" />
        <StatCard label="Avg Risk Score" value={((stats?.avg_risk_score || 0) * 100).toFixed(1) + '%'}
          sub="Weighted ensemble" accent="var(--accent-orange)" icon="⬡" />
      </div>

      {/* Charts Row */}
      <div className="charts-row">
        {/* Intelligence by Type */}
        <div className="chart-card glass">
          <div className="chart-header">
            <span className="chart-title">Intelligence by Source Type</span>
            <span className="badge badge-low">{typeChartData.length} Types</span>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={typeChartData} margin={{ top: 5, right: 10, bottom: 5, left: -20 }}>
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#4a6fa5' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 10, fill: '#4a6fa5' }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                {typeChartData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Alerts by Severity */}
        <div className="chart-card glass">
          <div className="chart-header">
            <span className="chart-title">Alert Severity Distribution</span>
            <span className="badge badge-threat">{stats?.total_alerts ?? 0} Total</span>
          </div>
          <div className="pie-wrapper">
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={severityChartData} dataKey="value" cx="50%" cy="50%"
                  outerRadius={75} innerRadius={40} paddingAngle={3}
                  label={({ name, value }) => `${name}: ${value}`}
                  labelLine={false}
                >
                  {severityChartData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Bottom Row */}
      <div className="bottom-row">
        {/* Recent Alerts */}
        <div className="panel glass">
          <div className="panel-header">
            <span className="panel-title">⚡ Recent Alerts</span>
            <a href="/alerts" className="panel-link">View All →</a>
          </div>
          <div className="alerts-list">
            {alerts.length === 0 && <div className="empty-state">No alerts detected</div>}
            {alerts.map(alert => (
              <div key={alert.id} className={`alert-row sev-border-${alert.severity}`}>
                <div className="alert-row-left">
                  <span className={`badge badge-${alert.severity}`}>{alert.severity}</span>
                  <span className="alert-title truncate">{alert.title}</span>
                </div>
                <div className="alert-meta">
                  <span className="mono" style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                    {alert.risk_score ? (alert.risk_score * 100).toFixed(0) + '%' : '—'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="panel glass">
          <div className="panel-header">
            <span className="panel-title">◈ Recent Ingestion</span>
            <a href="/intel" className="panel-link">View All →</a>
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th><th>Source</th><th>Type</th><th>Status</th>
              </tr>
            </thead>
            <tbody>
              {recentActivity.map(r => (
                <tr key={r.id}>
                  <td className="mono text-muted" style={{ fontSize: 11 }}>#{r.id}</td>
                  <td>{r.source}</td>
                  <td><span className="badge" style={{ background: `${COLORS[r.type]}22`, color: COLORS[r.type], border: `1px solid ${COLORS[r.type]}44` }}>{r.type}</span></td>
                  <td><span className={`badge badge-${r.status === 'processed' ? 'low' : 'medium'}`}>{r.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
