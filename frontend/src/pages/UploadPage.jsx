import React, { useState, useRef } from 'react'
import { uploadAPI, aiAPI } from '../services/api'
import './UploadPage.css'

export default function UploadPage() {
  const [dragActive, setDragActive] = useState(false)
  const [uploadResults, setUploadResults] = useState([])
  const [uploading, setUploading] = useState(false)
  const [nlpText, setNlpText] = useState('')
  const [nlpResult, setNlpResult] = useState(null)
  const [nlpLoading, setNlpLoading] = useState(false)
  const fileInput = useRef(null)

  const handleFiles = async (files) => {
    setUploading(true)
    const results = []
    for (const file of files) {
      try {
        let res
        const ext = file.name.split('.').pop().toLowerCase()
        if (ext === 'csv') res = await uploadAPI.uploadCSV(file)
        else if (ext === 'json') res = await uploadAPI.uploadJSON(file)
        else if (['jpg', 'jpeg', 'png', 'bmp', 'tiff'].includes(ext)) res = await uploadAPI.uploadImage(file)
        else { results.push({ name: file.name, status: 'error', message: 'Unsupported format' }); continue }
        results.push({ name: file.name, status: 'success', data: res.data })
      } catch (err) {
        results.push({ name: file.name, status: 'error', message: err.response?.data?.detail || 'Upload failed' })
      }
    }
    setUploadResults(prev => [...results, ...prev])
    setUploading(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragActive(false)
    if (e.dataTransfer.files.length) handleFiles(Array.from(e.dataTransfer.files))
  }

  const handleNlpAnalyze = async () => {
    if (!nlpText.trim()) return
    setNlpLoading(true)
    try {
      const { data } = await aiAPI.analyzeText(nlpText)
      setNlpResult(data)
    } catch { setNlpResult({ error: 'Analysis failed' }) }
    setNlpLoading(false)
  }

  return (
    <div className="upload-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">↑ Data Ingestion</h1>
          <p className="page-sub">Upload intelligence data and run AI analysis</p>
        </div>
      </div>

      <div className="upload-grid">
        {/* File Upload Zone */}
        <div className="upload-section glass">
          <div className="section-title">◈ File Upload</div>
          <div className="section-sub">Supports CSV, JSON, and Image files</div>

          <div
            className={`dropzone ${dragActive ? 'active' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setDragActive(true) }}
            onDragLeave={() => setDragActive(false)}
            onDrop={handleDrop}
            onClick={() => fileInput.current?.click()}
          >
            <div className="dropzone-icon">{uploading ? '⟳' : '↑'}</div>
            <div className="dropzone-text">
              {uploading ? 'Uploading...' : 'Drop files here or click to browse'}
            </div>
            <div className="dropzone-hint">CSV · JSON · JPG · PNG · BMP</div>
            <input
              ref={fileInput}
              type="file"
              multiple
              accept=".csv,.json,.jpg,.jpeg,.png,.bmp,.tiff"
              style={{ display: 'none' }}
              onChange={(e) => e.target.files.length && handleFiles(Array.from(e.target.files))}
            />
          </div>

          {/* Upload Results */}
          {uploadResults.length > 0 && (
            <div className="upload-results">
              <div className="results-title">Upload Results</div>
              {uploadResults.map((r, i) => (
                <div key={i} className={`result-row ${r.status}`}>
                  <span className="result-icon">{r.status === 'success' ? '✓' : '✕'}</span>
                  <span className="result-name truncate">{r.name}</span>
                  <span className={`badge badge-${r.status === 'success' ? 'low' : 'critical'}`}>
                    {r.status}
                  </span>
                  {r.data?.record_count && (
                    <span className="mono text-muted" style={{ fontSize: 11 }}>
                      {r.data.record_count} records
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* NLP Analysis */}
        <div className="upload-section glass">
          <div className="section-title">⟁ NLP Threat Analysis</div>
          <div className="section-sub">Analyze text with DistilBERT for threat classification</div>

          <textarea
            className="input nlp-textarea"
            value={nlpText}
            onChange={e => setNlpText(e.target.value)}
            placeholder="Enter intelligence text to analyze...&#10;&#10;Example: Suspicious communications intercepted near the eastern checkpoint. Encrypted radio traffic increased by 300% in the last 24 hours."
            rows={6}
          />
          <button
            className="btn btn-primary"
            onClick={handleNlpAnalyze}
            disabled={nlpLoading || !nlpText.trim()}
            style={{ marginTop: 12 }}
          >
            {nlpLoading ? <><span className="spinner" style={{ width: 14, height: 14 }} /> Analyzing...</> : '⟁ Analyze Threat Level'}
          </button>

          {nlpResult && !nlpResult.error && (
            <div className="nlp-result">
              <div className="nlp-result-header">
                <span className={`badge badge-${nlpResult.label}`} style={{ fontSize: 13, padding: '4px 14px' }}>
                  {nlpResult.label?.toUpperCase()}
                </span>
                <span className="nlp-confidence mono" style={{
                  color: nlpResult.confidence > 0.6 ? 'var(--accent-red)' : nlpResult.confidence > 0.4 ? 'var(--accent-orange)' : 'var(--accent-green)',
                  fontSize: 20, fontWeight: 800,
                }}>
                  {(nlpResult.confidence * 100).toFixed(1)}%
                </span>
              </div>
              <div className="nlp-details">
                <div className="nlp-detail-row">
                  <span className="text-muted">Severity</span>
                  <span className={`badge badge-${nlpResult.severity}`}>{nlpResult.severity}</span>
                </div>
                <div className="nlp-detail-row">
                  <span className="text-muted">Model</span>
                  <span className="mono">{nlpResult.model}</span>
                </div>
                {nlpResult.details?.matched_keywords?.length > 0 && (
                  <div className="nlp-detail-row">
                    <span className="text-muted">Keywords</span>
                    <span className="nlp-keywords">
                      {nlpResult.details.matched_keywords.map(k => (
                        <span key={k} className="keyword-tag">{k}</span>
                      ))}
                    </span>
                  </div>
                )}
                <div className="nlp-scores">
                  <div className="score-bar-group">
                    <span className="score-label">Keyword Score</span>
                    <div className="score-bar">
                      <div className="score-bar-fill" style={{
                        width: `${(nlpResult.details?.keyword_score || 0) * 100}%`,
                        background: 'var(--accent-purple)',
                      }} />
                    </div>
                    <span className="score-val mono">{((nlpResult.details?.keyword_score || 0) * 100).toFixed(0)}%</span>
                  </div>
                  <div className="score-bar-group">
                    <span className="score-label">ML Score</span>
                    <div className="score-bar">
                      <div className="score-bar-fill" style={{
                        width: `${(nlpResult.details?.ml_score || 0) * 100}%`,
                        background: 'var(--accent-cyan)',
                      }} />
                    </div>
                    <span className="score-val mono">{((nlpResult.details?.ml_score || 0) * 100).toFixed(0)}%</span>
                  </div>
                  <div className="score-bar-group">
                    <span className="score-label">Combined</span>
                    <div className="score-bar">
                      <div className="score-bar-fill" style={{
                        width: `${(nlpResult.details?.combined_score || 0) * 100}%`,
                        background: nlpResult.confidence > 0.6 ? 'var(--accent-red)' : 'var(--accent-green)',
                      }} />
                    </div>
                    <span className="score-val mono">{((nlpResult.details?.combined_score || 0) * 100).toFixed(0)}%</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
