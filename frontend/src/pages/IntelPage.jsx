import React, { useState, useEffect } from 'react'
import { intelAPI, aiAPI } from '../services/api'
import './IntelPage.css'

const TYPE_COLORS = {
  SIGINT: '#00d4ff', HUMINT: '#a855f7', OSINT: '#00ff88', GEOINT: '#ff8c42', CYBINT: '#ff3860',
}

export default function IntelPage() {
  const [records, setRecords] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(0)
  const [typeFilter, setTypeFilter] = useState('')
  const [processing, setProcessing] = useState(null)

  const fetchData = async () => {
    setLoading(true)
    try {
      const { data } = await intelAPI.getData({ limit: 20, offset: page * 20, type: typeFilter || undefined })
      setRecords(data.records || [])
      setTotal(data.total || 0)
    } catch {}
    setLoading(false)
  }

  useEffect(() => { fetchData() }, [page, typeFilter])

  const handleProcess = async (id) => {
    setProcessing(id)
    try {
      await aiAPI.processRecord(id)
      fetchData()
    } catch {}
    setProcessing(null)
  }

  const totalPages = Math.ceil(total / 20)

  return (
    <div className="intel-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">◈ Intelligence Records</h1>
          <p className="page-sub">{total} records in database</p>
        </div>
        <button className="btn btn-ghost btn-sm" onClick={fetchData}>↺ Refresh</button>
      </div>

      {/* Type filter */}
      <div className="intel-filter-row">
        <button className={`btn btn-xs ${!typeFilter ? 'btn-primary' : 'btn-ghost'}`}
          onClick={() => { setTypeFilter(''); setPage(0) }}>All</button>
        {['SIGINT', 'HUMINT', 'OSINT', 'GEOINT', 'CYBINT'].map(t => (
          <button key={t}
            className={`btn btn-xs ${typeFilter === t ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => { setTypeFilter(t); setPage(0) }}
            style={typeFilter === t ? {} : { borderColor: TYPE_COLORS[t] + '44', color: TYPE_COLORS[t] }}>
            {t}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="intel-table-wrap glass">
        {loading ? (
          <div className="page-loading" style={{ minHeight: 200 }}>
            <div className="spinner" />
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th><th>Source</th><th>Type</th><th>Coords</th><th>Description</th><th>Status</th><th>Time</th><th>Action</th>
              </tr>
            </thead>
            <tbody>
              {records.map(r => {
                const desc = typeof r.data === 'object' ? (r.data?.description || r.data?.report_type || '—') : String(r.data || '—')
                return (
                  <tr key={r.id}>
                    <td className="mono text-muted" style={{ fontSize: 11 }}>#{r.id}</td>
                    <td className="mono" style={{ fontSize: 11 }}>{r.source}</td>
                    <td>
                      <span className="badge" style={{
                        background: (TYPE_COLORS[r.type] || '#00d4ff') + '18',
                        color: TYPE_COLORS[r.type] || '#00d4ff',
                        border: `1px solid ${(TYPE_COLORS[r.type] || '#00d4ff')}40`,
                      }}>{r.type}</span>
                    </td>
                    <td className="mono" style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                      {r.latitude && r.longitude ? `${r.latitude.toFixed(2)}, ${r.longitude.toFixed(2)}` : '—'}
                    </td>
                    <td className="truncate" style={{ maxWidth: 220, fontSize: 12 }}>{desc}</td>
                    <td>
                      <span className={`badge badge-${r.status === 'processed' ? 'low' : 'medium'}`}>{r.status}</span>
                    </td>
                    <td className="mono" style={{ fontSize: 10, color: 'var(--text-dim)' }}>
                      {r.timestamp?.slice(0, 16)}
                    </td>
                    <td>
                      <button
                        className="btn btn-ghost btn-xs"
                        onClick={() => handleProcess(r.id)}
                        disabled={processing === r.id}
                      >
                        {processing === r.id ? '...' : '⟁ Process'}
                      </button>
                    </td>
                  </tr>
                )
              })}
              {records.length === 0 && (
                <tr><td colSpan={8} className="empty-state">No records found</td></tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="pagination">
          <button className="btn btn-ghost btn-xs" disabled={page === 0}
            onClick={() => setPage(p => p - 1)}>← Prev</button>
          <span className="mono text-muted" style={{ fontSize: 12 }}>
            Page {page + 1} of {totalPages}
          </span>
          <button className="btn btn-ghost btn-xs" disabled={page >= totalPages - 1}
            onClick={() => setPage(p => p + 1)}>Next →</button>
        </div>
      )}
    </div>
  )
}
