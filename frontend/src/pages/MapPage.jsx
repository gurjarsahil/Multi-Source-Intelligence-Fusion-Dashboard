import React, { useState, useEffect, useRef } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup, LayersControl, useMap } from 'react-leaflet'
import { intelAPI, alertsAPI, aiAPI } from '../services/api'
import 'leaflet/dist/leaflet.css'
import './MapPage.css'

const SEV_COLORS = {
  critical: '#ff3860', high: '#ff8c42', medium: '#ffd700',
  low: '#00ff88', threat: '#ff3860', safe: '#00ff88', suspicious: '#ffd700',
}

function getRiskColor(score) {
  if (score >= 0.75) return '#ff3860'
  if (score >= 0.55) return '#ff8c42'
  if (score >= 0.35) return '#ffd700'
  return '#00ff88'
}

export default function MapPage() {
  const [points, setPoints] = useState([])
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')
  const [clustering, setClustering] = useState(null)
  const [clusterLoading, setClusterLoading] = useState(false)

  useEffect(() => {
    const load = async () => {
      try {
        const { data } = await intelAPI.getMapData()
        setPoints(data.points || [])
        setAlerts(data.alerts || [])
      } catch {}
      setLoading(false)
    }
    load()
    const t = setInterval(load, 20000)
    return () => clearInterval(t)
  }, [])

  const runClustering = async () => {
    const coords = points.filter(p => p.lat && p.lon).map(p => [p.lat, p.lon])
    if (coords.length < 2) return
    setClusterLoading(true)
    try {
      const { data } = await aiAPI.cluster(coords, 'dbscan')
      setClustering(data)
    } catch {}
    setClusterLoading(false)
  }

  const filtered = filter === 'all' ? points
    : filter === 'threat' ? points.filter(p => p.risk_score > 0.6)
    : points.filter(p => p.type === filter)

  return (
    <div className="map-page">
      {/* Controls */}
      <div className="map-controls glass">
        <div className="map-ctrl-title">⬡ Geospatial Intelligence</div>
        <div className="map-filter-row">
          {['all', 'threat', 'SIGINT', 'HUMINT', 'OSINT', 'GEOINT', 'CYBINT'].map(f => (
            <button key={f} className={`btn btn-xs ${filter === f ? 'btn-primary' : 'btn-ghost'}`}
              onClick={() => setFilter(f)}>
              {f}
            </button>
          ))}
        </div>
        <div className="map-stats">
          <span className="mono" style={{ fontSize: 11, color: 'var(--text-muted)' }}>
            {filtered.length} points · {alerts.length} alerts
          </span>
          <button className={`btn btn-ghost btn-xs ${clusterLoading ? '' : ''}`}
            onClick={runClustering} disabled={clusterLoading}>
            {clusterLoading ? '...' : '⟁ Run DBSCAN'}
          </button>
        </div>

        {/* Legend */}
        <div className="map-legend">
          {Object.entries(SEV_COLORS).slice(0, 4).map(([k, v]) => (
            <div key={k} className="legend-item">
              <div className="legend-dot" style={{ background: v, boxShadow: `0 0 6px ${v}` }} />
              <span>{k}</span>
            </div>
          ))}
        </div>

        {/* Cluster Results */}
        {clustering && (
          <div className="cluster-panel">
            <div className="cluster-panel-title">DBSCAN Results</div>
            <div className="cluster-stats">
              <span>{clustering.total_clusters} clusters</span>
              <span>{clustering.hotspots?.length || 0} hotspots</span>
            </div>
            {clustering.hotspots?.map(h => (
              <div key={h.cluster_id} className={`hotspot-row risk-${h.risk_level}`}>
                <span>Hotspot #{h.cluster_id}</span>
                <span className={`badge badge-${h.risk_level}`}>{h.risk_level}</span>
                <span className="mono" style={{ fontSize: 10 }}>{h.point_count} pts</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Map */}
      <div className="map-container">
        {loading ? (
          <div className="map-loading">
            <div className="spinner" style={{ width: 40, height: 40 }} />
            <div style={{ color: 'var(--text-muted)', marginTop: 12 }}>Loading geospatial data...</div>
          </div>
        ) : (
          <MapContainer
            center={[20, 0]}
            zoom={2}
            style={{ height: '100%', width: '100%' }}
            zoomControl={true}
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; OpenStreetMap contributors'
            />

            {/* Intelligence points */}
            {filtered.map(p => (
              <CircleMarker
                key={p.id}
                center={[p.lat, p.lon]}
                radius={Math.max(5, (p.risk_score || 0.3) * 12)}
                pathOptions={{
                  color: getRiskColor(p.risk_score || 0),
                  fillColor: getRiskColor(p.risk_score || 0),
                  fillOpacity: 0.6,
                  weight: 1,
                }}
              >
                <Popup>
                  <div className="map-popup">
                    <div className="popup-type">{p.type} — {p.source}</div>
                    <div className="popup-row">
                      <span>Risk Score</span>
                      <span style={{ color: getRiskColor(p.risk_score || 0), fontWeight: 700 }}>
                        {((p.risk_score || 0) * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="popup-row">
                      <span>Prediction</span>
                      <span>{p.prediction || 'Pending'}</span>
                    </div>
                    <div className="popup-row">
                      <span>Coords</span>
                      <span>{p.lat?.toFixed(3)}, {p.lon?.toFixed(3)}</span>
                    </div>
                    <div className="popup-time">{p.timestamp?.slice(0, 19)}</div>
                  </div>
                </Popup>
              </CircleMarker>
            ))}

            {/* Alert markers */}
            {alerts.map(a => (
              <CircleMarker
                key={`alert-${a.id}`}
                center={[a.lat, a.lon]}
                radius={9}
                pathOptions={{
                  color: SEV_COLORS[a.severity] || '#ff3860',
                  fillColor: SEV_COLORS[a.severity] || '#ff3860',
                  fillOpacity: 0.85,
                  weight: 2,
                }}
              >
                <Popup>
                  <div className="map-popup">
                    <div className="popup-type alert-label">⚡ ALERT</div>
                    <div className="popup-title">{a.title}</div>
                    <div className="popup-row">
                      <span>Severity</span>
                      <span style={{ color: SEV_COLORS[a.severity], textTransform: 'uppercase', fontWeight: 700 }}>{a.severity}</span>
                    </div>
                    <div className="popup-row">
                      <span>Risk</span>
                      <span>{a.risk_score ? (a.risk_score * 100).toFixed(1) + '%' : '—'}</span>
                    </div>
                  </div>
                </Popup>
              </CircleMarker>
            ))}

            {/* Cluster hotspot circles */}
            {clustering?.hotspots?.map(h => (
              <CircleMarker
                key={`cluster-${h.cluster_id}`}
                center={[h.center.lat, h.center.lon]}
                radius={30}
                pathOptions={{
                  color: SEV_COLORS[h.risk_level] || '#ffd700',
                  fillColor: SEV_COLORS[h.risk_level] || '#ffd700',
                  fillOpacity: 0.1,
                  weight: 2,
                  dashArray: '6 4',
                }}
              >
                <Popup>
                  <div className="map-popup">
                    <div className="popup-type">⬡ HOTSPOT #{h.cluster_id}</div>
                    <div className="popup-row"><span>Density</span><span>{(h.density * 100).toFixed(1)}%</span></div>
                    <div className="popup-row"><span>Points</span><span>{h.point_count}</span></div>
                    <div className="popup-row"><span>Risk</span><span style={{ color: SEV_COLORS[h.risk_level], textTransform: 'uppercase' }}>{h.risk_level}</span></div>
                  </div>
                </Popup>
              </CircleMarker>
            ))}
          </MapContainer>
        )}
      </div>
    </div>
  )
}
