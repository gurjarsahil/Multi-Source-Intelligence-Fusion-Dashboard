import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import './LoginPage.css'

export default function LoginPage() {
  const { login, loading } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: 'admin@intel.local', password: 'admin123' })
  const [error, setError] = useState('')
  const [animating, setAnimating] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setAnimating(true)
    const result = await login(form.email, form.password)
    if (result.success) {
      navigate('/dashboard')
    } else {
      setError(result.error)
      setAnimating(false)
    }
  }

  return (
    <div className="login-page">
      {/* Animated background orbs */}
      <div className="orb orb-1" />
      <div className="orb orb-2" />
      <div className="orb orb-3" />

      {/* Scan line */}
      <div className="scan-line" />

      <div className="login-container">
        {/* Logo */}
        <div className="login-logo">
          <div className="login-logo-icon">⬡</div>
          <div className="login-logo-text">NEXUS</div>
          <div className="login-logo-sub">INTELLIGENCE FUSION SYSTEM</div>
        </div>

        {/* Status line */}
        <div className="login-status">
          <span className="status-dot live" />
          <span className="mono" style={{ fontSize: 10 }}>SYSTEM ONLINE · SECURE CONNECTION ESTABLISHED</span>
        </div>

        {/* Card */}
        <div className="login-card glass">
          <div className="login-card-header">
            <div className="login-card-title">Operator Authentication</div>
            <div className="login-card-sub">Restricted Access — Authorized Personnel Only</div>
          </div>

          <form onSubmit={handleSubmit} className="login-form">
            <div className="form-group">
              <label className="label">Email Address</label>
              <input
                type="email"
                className="input"
                value={form.email}
                onChange={e => setForm({ ...form, email: e.target.value })}
                placeholder="operator@intel.local"
                required
              />
            </div>
            <div className="form-group">
              <label className="label">Access Code</label>
              <input
                type="password"
                className="input"
                value={form.password}
                onChange={e => setForm({ ...form, password: e.target.value })}
                placeholder="••••••••"
                required
              />
            </div>

            {error && (
              <div className="login-error">
                ⚠ {error}
              </div>
            )}

            <button type="submit" className={`btn btn-primary w-full login-btn ${animating ? 'loading' : ''}`} disabled={loading}>
              {loading ? <><span className="spinner" style={{ width: 16, height: 16 }} /> Authenticating...</> : '→ Access Intelligence Dashboard'}
            </button>
          </form>

          <div className="login-hint">
            <span className="mono text-muted" style={{ fontSize: 11 }}>DEFAULT: admin@intel.local / admin123</span>
          </div>
        </div>

        <div className="login-footer">
          <span>CLASSIFICATION: UNCLASSIFIED // FOR DEMONSTRATION ONLY</span>
        </div>
      </div>
    </div>
  )
}
