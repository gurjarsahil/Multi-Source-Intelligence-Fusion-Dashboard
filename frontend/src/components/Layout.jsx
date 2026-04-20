import React, { useState, useEffect } from 'react'
import { Outlet, NavLink, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { IntelWebSocket, alertsAPI } from '../services/api'
import './Layout.css'

const NAV = [
  { path: '/dashboard', icon: '⬡', label: 'Dashboard' },
  { path: '/map',       icon: '◈', label: 'Intel Map' },
  { path: '/intel',     icon: '⟁', label: 'Intelligence' },
  { path: '/alerts',    icon: '⚡', label: 'Alerts' },
  { path: '/upload',    icon: '↑', label: 'Upload Data' },
]

export default function Layout() {
  const { user, logout } = useAuth()
  const location = useLocation()
  const [liveAlerts, setLiveAlerts] = useState([])
  const [unread, setUnread] = useState(0)
  const [wsConnected, setWsConnected] = useState(false)
  const [toast, setToast] = useState(null)
  const [time, setTime] = useState(new Date())

  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(t)
  }, [])

  useEffect(() => {
    const ws = new IntelWebSocket((msg) => {
      if (msg.event === 'connected') setWsConnected(true)
      if (msg.event === 'new_alerts' && msg.data?.length > 0) {
        setUnread(u => u + msg.data.length)
        const a = msg.data[0]
        setToast(a)
        setTimeout(() => setToast(null), 5000)
      }
    })
    ws.connect()
    const ping = setInterval(() => ws.ping(), 30000)
    return () => { ws.disconnect(); clearInterval(ping) }
  }, [])

  useEffect(() => {
    if (location.pathname === '/alerts') setUnread(0)
  }, [location.pathname])

  return (
    <div className="layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <div className="logo-icon">⬡</div>
          <div>
            <div className="logo-title">NEXUS</div>
            <div className="logo-sub">Intelligence Fusion</div>
          </div>
        </div>

        <div className="sidebar-status">
          <div className={`status-dot ${wsConnected ? 'live' : 'offline'}`} />
          <span>{wsConnected ? 'LIVE FEED' : 'CONNECTING...'}</span>
        </div>

        <nav className="sidebar-nav">
          {NAV.map(n => (
            <NavLink key={n.path} to={n.path} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              <span className="nav-icon">{n.icon}</span>
              <span className="nav-label">{n.label}</span>
              {n.path === '/alerts' && unread > 0 && (
                <span className="nav-badge">{unread}</span>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-clock mono">{time.toUTCString().slice(17, 25)} UTC</div>
          <div className="user-info">
            <div className="user-avatar">{user?.name?.[0]?.toUpperCase() || 'U'}</div>
            <div>
              <div className="user-name">{user?.name}</div>
              <div className={`user-role role-${user?.role}`}>{user?.role?.toUpperCase()}</div>
            </div>
          </div>
          <button className="btn btn-ghost btn-sm w-full" onClick={logout} style={{ marginTop: 8 }}>
            ⏻ Logout
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="main-content">
        <Outlet />
      </main>

      {/* Toast notification */}
      {toast && (
        <div className={`toast toast-${toast.severity}`}>
          <div className="toast-icon">⚡</div>
          <div>
            <div className="toast-title">{toast.title}</div>
            <div className="toast-desc">{toast.description?.slice(0, 100)}...</div>
          </div>
          <button className="toast-close" onClick={() => setToast(null)}>✕</button>
        </div>
      )}
    </div>
  )
}
