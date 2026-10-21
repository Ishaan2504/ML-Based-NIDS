import { useEffect, useState } from 'react'
import { Activity, AlertTriangle, Database, Fingerprint, PanelLeftClose, Shield, Upload } from 'lucide-react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Button } from '@/components/ui/button'
import { pages } from '@/lib/dashboard-data'
import '@/styles/analysis-results.css'
import { analyzeCsv, getApiHealth, getModelInfo, type ApiHealth, type CsvAnalysis, type ModelInfo } from '@/lib/api'

type PageKey = 'overview' | 'lab'
const MAX_UPLOAD_BYTES = 500 * 1024 * 1024

function AnalysisSummary({ analysis }: { analysis: CsvAnalysis }) {
  const breakdown = analysis.prediction_breakdown ?? Object.values(
    analysis.preview.reduce<Record<string, { prediction: string; category: string; count: number }>>((groups, row) => {
      const key = `${row.predicted_label}\u0000${row.attack_family}`
      groups[key] ??= { prediction: row.predicted_label, category: row.attack_family, count: 0 }
      groups[key].count += 1
      return groups
    }, {}),
  ).sort((left, right) => right.count - left.count || left.prediction.localeCompare(right.prediction))
  const threatRatio = analysis.total_flows
    ? (analysis.malicious_count / analysis.total_flows) * 100
    : 0

  return (
    <div className="analysis-summary" role="status">
      <div className="analysis-summary-heading">
        <div><span className="eyebrow"><span className="eyebrow-dot" /> FILE ANALYSIS</span><h3>Traffic results</h3></div>
        <span className="analysis-file-pill">{analysis.source_file}</span>
      </div>
      <p className="analysis-summary-meta">{analysis.total_flows.toLocaleString()} network flows · {analysis.feature_count} input features · {analysis.model_id}</p>
      <div className="analysis-kpis">
        <article><span>Normal traffic</span><strong>{analysis.benign_count.toLocaleString()}</strong><small>predicted benign</small></article>
        <article><span>Threats detected</span><strong>{analysis.malicious_count.toLocaleString()}</strong><small>predicted malicious</small></article>
        <article><span>Threat ratio</span><strong>{threatRatio.toFixed(1)}%</strong><small>of uploaded flows</small></article>
      </div>
      <div className="analysis-breakdown-grid">
        <section className="analysis-chart-panel" aria-label="Detection summary chart">
          <div className="analysis-panel-heading"><h4>Detection summary</h4><span>{analysis.prediction_breakdown ? 'All predicted flows' : 'Preview rows only'}</span></div>
          <div className="analysis-chart">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={breakdown} layout="vertical" margin={{ top: 8, right: 14, bottom: 4, left: 4 }}>
                <CartesianGrid stroke="#252c32" horizontal={false} />
                <XAxis type="number" allowDecimals={false} tick={{ fill: '#8392a0', fontSize: 10 }} axisLine={{ stroke: '#30383e' }} tickLine={false} />
                <YAxis type="category" dataKey="prediction" width={105} tick={{ fill: '#b6c3cd', fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip cursor={{ fill: 'rgba(80,195,231,.08)' }} contentStyle={{ background: '#11191d', border: '1px solid #34424a', borderRadius: 6, color: '#e5edf2', fontSize: 11 }} />
                <Bar dataKey="count" name="Flows" fill="#54bce8" radius={[0, 4, 4, 0]} barSize={20} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
        <section className="analysis-table-panel">
          <div className="analysis-panel-heading"><h4>Prediction breakdown</h4><span>{breakdown.length} classes</span></div>
          <div className="analysis-table-scroll"><table className="analysis-breakdown-table"><thead><tr><th>Prediction</th><th>Count</th><th>Category</th></tr></thead>
            <tbody>{breakdown.map(row => <tr key={`${row.prediction}-${row.category}`}><td>{row.prediction}</td><td>{row.count.toLocaleString()}</td><td><span className={`category-tag ${row.category.toLowerCase() === 'normal' ? 'normal' : 'threat'}`}>{row.category}</span></td></tr>)}</tbody>
          </table></div>
        </section>
      </div>
      <p className="analysis-footnote">Predictions are model outputs for triage, not confirmed attacks. Scores are not calibrated probabilities.</p>
    </div>
  )
}

function BatchAnalysisSummary({ analyses }: { analyses: CsvAnalysis[] }) {
  const totals = analyses.reduce((sum, result) => ({
    flows: sum.flows + result.total_flows,
    benign: sum.benign + result.benign_count,
    threats: sum.threats + result.malicious_count,
  }), { flows: 0, benign: 0, threats: 0 })
  const threatRatio = totals.flows ? (totals.threats / totals.flows) * 100 : 0

  return (
    <div className="batch-report" role="status">
      <div className="analysis-summary-heading"><div><span className="eyebrow"><span className="eyebrow-dot" /> BATCH ANALYSIS</span><h3>File comparison</h3></div><span className="analysis-file-pill">{analyses.length} files analyzed separately</span></div>
      <p className="analysis-summary-meta">Each file has its own predictions below. Batch totals summarize all analyzed flows.</p>
      <div className="analysis-kpis batch-kpis">
        <article><span>Files analyzed</span><strong>{analyses.length}</strong><small>separate results</small></article>
        <article><span>Total flows</span><strong>{totals.flows.toLocaleString()}</strong><small>across selected files</small></article>
        <article><span>Threat ratio</span><strong>{threatRatio.toFixed(1)}%</strong><small>{totals.threats.toLocaleString()} predicted malicious</small></article>
      </div>
      <div className="batch-table-wrap"><table className="batch-table"><thead><tr><th>File</th><th>Flows</th><th>Normal</th><th>Threats</th><th>Threat ratio</th></tr></thead>
        <tbody>{analyses.map(result => <tr key={result.source_file}><td>{result.source_file}</td><td>{result.total_flows.toLocaleString()}</td><td>{result.benign_count.toLocaleString()}</td><td>{result.malicious_count.toLocaleString()}</td><td>{result.total_flows ? `${((result.malicious_count / result.total_flows) * 100).toFixed(1)}%` : '0.0%'}</td></tr>)}</tbody>
      </table></div>
      <div className="batch-file-results">
        {analyses.map((result, index) => (
          <details className="batch-file-detail" key={`${result.source_file}-${index}`}>
            <summary><span>{result.source_file}</span><small>{result.total_flows.toLocaleString()} flows · {(result.total_flows ? (result.malicious_count / result.total_flows) * 100 : 0).toFixed(1)}% threat ratio</small></summary>
            <AnalysisSummary analysis={result} />
          </details>
        ))}
      </div>
      <p className="analysis-footnote">Predictions are model outputs for triage, not confirmed attacks. The combined figures are descriptive totals, not a model accuracy score.</p>
    </div>
  )
}

export default function App() {
  const [active, setActive] = useState<PageKey>('overview')
  const [collapsed, setCollapsed] = useState(false)
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [analysisResults, setAnalysisResults] = useState<CsvAnalysis[]>([])
  const [analysisError, setAnalysisError] = useState('')
  const [analyzing, setAnalyzing] = useState(false)
  const [analysisProgress, setAnalysisProgress] = useState('')
  const [apiHealth, setApiHealth] = useState<ApiHealth | null>(null)
  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null)
  const [apiChecked, setApiChecked] = useState(false)

  useEffect(() => {
    let mounted = true
    const refreshStatus = async () => {
      try {
        const health = await getApiHealth()
        if (!mounted) return
        setApiHealth(health)
        setModelInfo(await getModelInfo().catch(() => null))
      } catch {
        if (mounted) {
          setApiHealth(null)
          setModelInfo(null)
        }
      } finally {
        if (mounted) setApiChecked(true)
      }
    }
    void refreshStatus()
    const timer = window.setInterval(() => void refreshStatus(), 15_000)
    return () => {
      mounted = false
      window.clearInterval(timer)
    }
  }, [])

  const apiLabel = !apiChecked ? 'Checking API' : apiHealth?.status === 'online' ? 'API online' : apiHealth ? 'API degraded' : 'API offline'
  const apiDot = apiHealth?.status === 'online' ? 'online' : 'offline'

  const runAnalysis = async () => {
    if (!selectedFiles.length) return
    setAnalyzing(true)
    setAnalysisError('')
    setAnalysisResults([])
    const results: CsvAnalysis[] = []
    const errors: string[] = []
    for (let index = 0; index < selectedFiles.length; index += 1) {
      const file = selectedFiles[index]
      setAnalysisProgress(`Analyzing file ${index + 1} of ${selectedFiles.length}: ${file.name}`)
      try {
        results.push(await analyzeCsv(file))
      } catch (error) {
        errors.push(`${file.name}: ${error instanceof Error ? error.message : 'analysis failed'}`)
      }
    }
    setAnalysisResults(results)
    setAnalysisError(errors.length ? `Some files could not be analyzed: ${errors.join(' · ')}` : '')
    setAnalysisProgress('')
    setAnalyzing(false)
  }

  const selectFiles = (fileList: FileList | null) => {
    setAnalysisResults([])
    setAnalysisError('')
    setAnalysisProgress('')
    const files = Array.from(fileList ?? [])
    if (!files.length) {
      setSelectedFiles([])
      return
    }
    if (files.length > 10) {
      setSelectedFiles([])
      setAnalysisError('Choose up to 10 files per batch.')
      return
    }
    const invalidType = files.find(file => !/\.(csv|txt)$/i.test(file.name))
    if (invalidType) {
      setSelectedFiles([])
      setAnalysisError(`${invalidType.name} is not a CSV or TXT file. Choose only .csv or .txt NSL-KDD files.`)
      return
    }
    const oversized = files.find(file => file.size > MAX_UPLOAD_BYTES)
    if (oversized) {
      setSelectedFiles([])
      setAnalysisError(`${oversized.name} exceeds the 500 MB per-file upload limit.`)
      return
    }
    setSelectedFiles(files)
  }

  const modelMetrics = [
    { label: 'Model', value: modelInfo?.model_name ?? 'XGBoost' },
    { label: 'Selected features', value: modelInfo?.selected_feature_count?.toString() ?? '—' },
    { label: 'Supported labels', value: modelInfo?.class_count?.toString() ?? '—' },
    { label: 'Test accuracy', value: modelInfo?.test_accuracy == null ? 'Not available' : `${(modelInfo.test_accuracy * 100).toFixed(1)}%` },
  ]

  return (
    <div className={`app-shell ${collapsed ? 'sidebar-collapsed' : ''}`}>
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><Fingerprint size={21} /></div>
          <div className="brand-copy"><strong>sentinel<span>.</span></strong><small>NETWORK DEFENSE</small></div>
          <button className="collapse-button" onClick={() => setCollapsed(!collapsed)} aria-label="Collapse sidebar"><PanelLeftClose size={16} /></button>
        </div>
        <div className="nav-label">WORKSPACE</div>
        <nav className="nav-list" aria-label="Main navigation">
          {pages.map(({ name, icon: Icon, key }) => (
            <button key={key} onClick={() => setActive(key)} className={`nav-item ${active === key ? 'active' : ''}`} title={name} aria-current={active === key ? 'page' : undefined}>
              <Icon size={17} /><span>{name}</span>
            </button>
          ))}
        </nav>
        <div className="sidebar-spacer" />
        <div className="pipeline-card">
          <div className="pipeline-card-top"><span className={`status-dot ${apiDot}`} /><span>MODEL STATUS</span><span className="live-label">{apiHealth?.model_loaded ? 'READY' : 'OFFLINE'}</span></div>
          <div className="pipeline-card-title">{apiHealth?.model_loaded ? 'Ready for local analysis' : 'Model unavailable'}</div>
          <div className="pipeline-line"><span /></div>
          <div className="pipeline-foot"><span>Active model</span><span>NSL-KDD</span></div>
        </div>
      </aside>

      <main className="main-panel">
        <header className="topbar">
          <div className="breadcrumbs"><span>Workspace</span><span className="crumb-slash">/</span><strong>{active === 'overview' ? 'Overview' : 'Analysis Lab'}</strong></div>
          <div className="topbar-actions">
            <div className="api-pill" title={apiHealth?.message ?? undefined}><span className={`status-dot ${apiDot}`} />{apiLabel}</div>
            <div className="top-divider" />
            <div className="model-chip"><span className="model-chip-icon"><Database size={14} /></span><span><small>ACTIVE MODEL</small><strong>{modelInfo?.model_name ?? 'Unavailable'}</strong></span></div>
          </div>
        </header>

        <div className="content-wrap">
          <div className="notice-banner"><span className="notice-icon"><AlertTriangle size={15} /></span><span><strong>Offline analysis</strong><i> · Only uploaded, recorded NSL-KDD flow data is analyzed.</i></span></div>
          <div className="page-heading">
            <div><div className="eyebrow"><span className="eyebrow-dot" /> NIDS · LOCAL SYSTEM</div><h1>{active === 'overview' ? 'SECURITY OVERVIEW' : 'TRAFFIC ANALYSIS LAB'}</h1><p className="page-subtitle">Local network intrusion predictions using the NSL-KDD model.</p></div>
            {active === 'overview' && <div className="heading-actions"><Button variant="primary" onClick={() => setActive('lab')}><Upload size={15} />Analyze a CSV</Button></div>}
          </div>

          {active === 'overview' ? (
            <>
            <section className="model-metrics" aria-label="Model performance summary">
              {modelMetrics.map(metric => <article className="model-metric" key={metric.label}><span>{metric.label}</span><strong>{metric.value}</strong></article>)}
            </section>
            {modelInfo?.test_accuracy != null && <p className="model-metric-note">Accuracy measured on {modelInfo.test_rows?.toLocaleString()} KDDTest+ rows from the model’s supported classes. Full test split: {modelInfo.full_test_accuracy == null ? '—' : `${(modelInfo.full_test_accuracy * 100).toFixed(1)}%`} over {modelInfo.full_test_rows?.toLocaleString()} rows, including attack labels this model does not support.</p>}
            <section className="bottom-grid">
              <article className="panel health-panel">
                <div className="panel-header"><div><h2>Analysis status</h2><p>Results from the current session</p></div><span className="health-tag">{analysisResults.length ? 'COMPLETE' : 'READY'}</span></div>
                {analysisResults.length ? (
                  <>
                    <div className="health-row"><div className="health-icon blue"><Activity size={16} /></div><div><strong>{analysisResults.length === 1 ? analysisResults[0].source_file : `${analysisResults.length} files analyzed`}</strong><span>{analysisResults[0].model_id}</span></div><span className="health-state">{analysisResults.reduce((sum, result) => sum + result.total_flows, 0).toLocaleString()} rows</span></div>
                    {analysisResults.length === 1 ? <AnalysisSummary analysis={analysisResults[0]} /> : <BatchAnalysisSummary analyses={analysisResults} />}
                  </>
                ) : (
                  <div className="health-row"><div className="health-icon blue"><Activity size={16} /></div><div><strong>No analysis yet</strong><span>Upload an NSL-KDD CSV or TXT file in the Analysis Lab to get predictions.</span></div></div>
                )}
                <div className="health-note"><Shield size={14} /><span>Predictions are model outputs, not confirmed attacks.</span></div>
              </article>
            </section>
            </>
          ) : (
            <section className="panel lab-panel upload-content">
              <h2>Analyze network traffic CSV</h2>
              <p>Upload NSL-KDD traffic. Headerless 41-, 42-, and 43-column files and headed CSV files are supported.</p>
              <div className="format-callout">Accepted inputs: NSL-KDD connection features, optionally followed by label and difficulty columns.</div>
              <label className="field-label" htmlFor="flow-file">Select network traffic CSV or TXT files</label>
              <div className="file-picker">
                <input id="flow-file" type="file" accept=".csv,.txt,text/csv,text/plain" multiple onChange={event => selectFiles(event.currentTarget.files)} />
                <span>Up to 10 files · 500 MB per file · analyzed separately</span>
              </div>
              {selectedFiles.length > 0 && <p className="selected-file">Selected {selectedFiles.length} {selectedFiles.length === 1 ? 'file' : 'files'}: {selectedFiles.map(file => file.name).join(', ')}</p>}
              {!apiHealth?.model_loaded && <p className="analysis-error" role="status">The prediction API or model is offline. Start the backend before analyzing a file.</p>}
              {analysisError && <p className="analysis-error" role="alert">{analysisError}</p>}
              {analysisProgress && <p className="analysis-progress" role="status">{analysisProgress}</p>}
              <Button variant="primary" disabled={!selectedFiles.length || !apiHealth?.model_loaded || analyzing} onClick={() => void runAnalysis()}><Upload size={14} />{analyzing ? 'Analyzing files…' : `Analyze ${selectedFiles.length || ''} ${selectedFiles.length === 1 ? 'file' : 'files'}`}</Button>
              {analysisResults.length > 0 && (
                <div className="analysis-result">
                  {analysisResults.length === 1 ? (
                    <>
                      <AnalysisSummary analysis={analysisResults[0]} />
                      <details className="analysis-preview-details">
                        <summary>View first {Math.min(analysisResults[0].preview.length, 10)} row predictions</summary>
                        <table className="analysis-preview"><thead><tr><th>Row</th><th>Prediction</th><th>Score</th></tr></thead><tbody>{analysisResults[0].preview.slice(0, 10).map(row => <tr key={row.row_index}><td>{row.row_index + 1}</td><td>{row.predicted_label}</td><td>{row.score.toFixed(4)}</td></tr>)}</tbody></table>
                      </details>
                    </>
                  ) : <BatchAnalysisSummary analyses={analysisResults} />}
                </div>
              )}
            </section>
          )}

          <footer className="app-footer"><span><Shield size={13} /> Predictions are model outputs, not confirmed attacks.</span><span>Model trained on NSL-KDD data; results may not transfer to other networks.</span></footer>
        </div>
      </main>
    </div>
  )
}
