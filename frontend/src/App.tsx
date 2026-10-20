import { useEffect, useState } from 'react'
import { Activity, AlertTriangle, ArrowDownToLine, ArrowUpRight, Bell, ChevronDown, CircleHelp, Clock3, Command, Database, Fingerprint, Layers3, PanelLeftClose, Search, Shield, ShieldAlert, Sparkles, Upload } from 'lucide-react'
import BentoItem from '@/components/ui/terminal-bento-grid'
import { Button } from '@/components/ui/button'
import { EmptyState } from '@/components/ui/empty-state'
import { pages, stats } from '@/lib/dashboard-data'
import '@/styles/analysis-results.css'
import { analyzeCsv, getApiHealth, getBenchmark, getModelInfo, type ApiHealth, type BenchmarkReport, type CsvAnalysis, type ModelInfo } from '@/lib/api'

export default function App() {
  const [active, setActive] = useState('overview')
  const [collapsed, setCollapsed] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [analysis, setAnalysis] = useState<CsvAnalysis | null>(null)
  const [analysisError, setAnalysisError] = useState('')
  const [analyzing, setAnalyzing] = useState(false)
  const [apiHealth, setApiHealth] = useState<ApiHealth | null>(null)
  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null)
  const [benchmark, setBenchmark] = useState<BenchmarkReport | null>(null)
  const [apiChecked, setApiChecked] = useState(false)
  const activePage = pages.find(p => p.key === active) ?? pages[0]

  useEffect(() => {
    let mounted = true
    const refreshStatus = async () => {
      try {
        const health = await getApiHealth()
        if (!mounted) return
        setApiHealth(health)
        try {
          setModelInfo(await getModelInfo())
        } catch {
          setModelInfo(null)
        }
        try {
          setBenchmark(await getBenchmark())
        } catch {
          setBenchmark(null)
        }
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
    if (!selectedFile) return
    setAnalyzing(true)
    setAnalysisError('')
    setAnalysis(null)
    try {
      setAnalysis(await analyzeCsv(selectedFile))
    } catch (error) {
      setAnalysisError(error instanceof Error ? error.message : 'CSV analysis failed.')
    } finally {
      setAnalyzing(false)
    }
  }

  return <div className={`app-shell ${collapsed ? 'sidebar-collapsed' : ''}`}>
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark"><Fingerprint size={21} /></div><div className="brand-copy"><strong>sentinel<span>.</span></strong><small>NETWORK DEFENSE</small></div><button className="collapse-button" onClick={() => setCollapsed(!collapsed)} aria-label="Collapse sidebar"><PanelLeftClose size={16} /></button></div>
      <div className="workspace-switch"><div className="workspace-icon"><Command size={15} /></div><div className="workspace-copy"><strong>Security workspace</strong><small>LOCAL ENVIRONMENT</small></div><ChevronDown size={14} /></div>
      <div className="nav-label">WORKSPACE</div>
      <nav className="nav-list">{pages.map(({ name, icon: Icon, key, badge }) => <button key={key} onClick={() => setActive(key)} className={`nav-item ${active === key ? 'active' : ''}`} title={name}><Icon size={17} /><span>{name}</span>{badge && <small>{badge}</small>}</button>)}</nav>
      <div className="sidebar-spacer" />
      <div className="pipeline-card"><div className="pipeline-card-top"><span className={`status-dot ${apiDot}`} /> <span>PIPELINE STATUS</span><span className="live-label">{apiHealth?.model_loaded ? 'READY' : 'IDLE'}</span></div><div className="pipeline-card-title">{apiHealth?.model_loaded ? 'Model ready for inference' : 'Awaiting verified model'}</div><div className="pipeline-line"><span /></div><div className="pipeline-foot"><span>Dataset</span><span>CIC-IDS2017</span></div></div>
      <div className="sidebar-bottom"><button className="nav-item"><CircleHelp size={17}/><span>Documentation</span></button><div className="user-row"><div className="avatar">AD</div><div><strong>Analyst workspace</strong><small>Local · offline</small></div><ChevronDown size={14}/></div></div>
    </aside>

    <main className="main-panel">
      <header className="topbar"><div className="breadcrumbs"><span>Workspace</span><span className="crumb-slash">/</span><strong>{activePage.name}</strong></div><div className="topbar-actions"><div className="api-pill" title={apiHealth?.message ?? undefined}><span className={`status-dot ${apiDot}`}/>{apiLabel}</div><button className="icon-button" aria-label="Search"><Search size={17}/></button><button className="icon-button notification" aria-label="Notifications"><Bell size={17}/><i/></button><div className="top-divider"/><div className="model-chip"><span className="model-chip-icon"><Layers3 size={14}/></span><span><small>ACTIVE MODEL</small><strong>{modelInfo?.model_id ?? 'Not yet generated'}</strong></span><ChevronDown size={13}/></div></div></header>

      <div className="content-wrap">
        <div className="notice-banner"><span className="notice-icon"><AlertTriangle size={15}/></span><span><strong>Offline analysis workspace</strong><i> · This dashboard analyses recorded flow data. No live traffic is collected.</i></span><button aria-label="Dismiss" onClick={e => e.currentTarget.parentElement?.remove()}>×</button></div>
        <div className="page-heading"><div><div className="eyebrow"><span className="eyebrow-dot"/> NIDS · LOCAL SYSTEM</div><h1>SYSTEM DASHBOARD</h1><p className="page-subtitle">{active === 'overview' ? 'Recorded network flow analysis · offline mode' : activePage.name}</p></div><div className="heading-actions"><Button><Clock3 size={15}/>No analysis run<ChevronDown size={14}/></Button><Button variant="primary" onClick={() => setActive('lab')}><Upload size={15}/>Analyze a CSV</Button></div></div>

        <div className="run-banner"><div className="run-banner-icon"><Database size={17}/></div><div><strong>{analysis ? 'Analysis complete' : 'No analysis run selected'}</strong><span>{analysis ? `${analysis.total_flows.toLocaleString()} flows scored with ${analysis.model_id}.` : 'Upload a labelled-flow CSV to populate this workspace.'}</span></div><button onClick={() => setActive('lab')}>{analysis ? 'View Analysis' : 'Open Analysis Lab'} <ArrowUpRight size={14}/></button></div>

        {active === 'overview' ? <>
        <section className="stats-grid">{stats.map(({label, icon: Icon, hint, color}, index) => { const values = analysis ? [analysis.total_flows, analysis.malicious_count, analysis.benign_count, modelInfo?.threshold ?? '—'] : null; return <article className="stat-card" key={label}><div className="stat-head"><span>{label}</span><span className={`stat-icon ${color}`}><Icon size={16}/></span></div><div className="stat-value">{values ? (typeof values[index] === 'number' && index === 3 ? Number(values[index]).toFixed(4) : Number(values[index]).toLocaleString()) : '—'}</div><div className="stat-foot"><span>{hint}</span><span className="not-generated">{analysis ? 'Generated' : 'Not generated'}</span></div></article>})}</section>

        <section className="overview-grid">
          <article className="panel traffic-panel"><div className="panel-header"><div><h2>Traffic over time</h2><p>Predicted benign and malicious flows by time bucket</p></div><Button><span className="tiny-dot blue-dot"/>Timeline unavailable<ChevronDown size={13}/></Button></div><div className="chart-empty"><div className="chart-grid"><div className="chart-axis"><span>—</span><span>—</span><span>—</span><span>—</span></div><div className="chart-main"><div className="chart-lines"><i/><i/><i/><i/></div><div className="chart-zero"><Activity size={19}/><span>Run an analysis to see traffic patterns</span></div><div className="chart-xaxis"><span>—</span><span>—</span><span>—</span><span>—</span><span>—</span></div></div></div></div><div className="chart-legend"><span><i className="legend-benign"/>Predicted benign</span><span><i className="legend-malicious"/>Predicted malicious</span><small>Counts are loaded from generated run artifacts.</small></div></article>
          <article className="panel distribution-panel"><div className="panel-header"><div><h2>Threat distribution</h2><p>Predicted attack families</p></div><button className="more-button">···</button></div><div className="donut-wrap"><div className="donut"><div className="donut-center"><Shield size={21}/><span>—</span><small>alerts</small></div></div></div><div className="distribution-empty">No generated predictions</div><div className="distribution-foot"><span>Family breakdown</span><span>Not generated</span></div></article>
        </section>

        <section className="bottom-grid">
          <article className="panel alerts-panel"><div className="panel-header"><div><h2>Recent alerts</h2><p>Latest model-flagged flows from the selected run</p></div><button className="text-link" onClick={() => setActive('alerts')}>View all <ArrowUpRight size={14}/></button></div><div className="table-head"><span>FLOW</span><span>PREDICTED FAMILY</span><span>MODEL SCORE</span><span>SEVERITY</span></div><EmptyState icon={ShieldAlert} title="No alerts to display"/><div className="table-bottom"><span>Showing 0 alerts</span><button disabled><ArrowDownToLine size={14}/>Export CSV</button></div></article>
          <article className="panel health-panel"><div className="panel-header"><div><h2>System health</h2><p>Local analysis services</p></div><span className="health-tag">{!apiChecked ? 'CHECKING' : apiHealth?.status === 'online' ? 'API ONLINE' : apiHealth ? 'DEGRADED' : 'OFFLINE'}</span></div><div className="health-row"><div className="health-icon red"><Activity size={16}/></div><div><strong>Prediction API</strong><span>{apiHealth?.model_loaded ? 'Verified model bundle loaded.' : apiHealth ? 'API is responding; no model bundle is loaded.' : 'Start the local API to enable analysis.'}</span></div><span className="health-state">{apiHealth?.model_loaded ? 'Ready' : apiHealth ? 'Degraded' : 'Offline'}</span></div><div className="health-row"><div className="health-icon blue"><Database size={16}/></div><div><strong>Run storage</strong><span>Analysis runs are not persisted yet.</span></div><span className="health-state muted">Not configured</span></div><div className="health-note"><Sparkles size={14}/><span>Results and metrics appear here after the pipeline generates reports.</span></div></article>
        </section>

        <section className="terminal-section"><div className="terminal-section-head"><div><span className="terminal-label"><span/> WORKSPACE DIAGNOSTICS</span><h2>Pipeline monitor</h2></div><span className="terminal-status"><span className={`status-dot ${apiDot}`}/>{apiHealth?.model_loaded ? 'MODEL READY' : apiHealth ? 'WAITING FOR MODEL' : 'API OFFLINE'}</span></div><div className="bento-grid"><BentoItem className="col-span-2"><h3>&gt; DATASET: CIC-IDS2017</h3><p>Recorded flows · Place CSV files in data/raw/cicids2017/</p></BentoItem><BentoItem><h3>&gt; MODEL STATUS</h3><p>{modelInfo?.model_id ?? 'Not yet generated'}</p></BentoItem><BentoItem><h3>&gt; API STATUS</h3><p>{apiLabel}</p></BentoItem><BentoItem className="col-span-2"><h3>&gt; REPORTS</h3><p>Not yet generated. Run the pipeline.</p></BentoItem></div></section>
        <footer className="app-footer"><span><Shield size={13}/> Predictions are model outputs, not confirmed attacks. Scores are uncalibrated.</span><span>Trained on CIC-IDS2017 benchmark data; results may not transfer to other networks.</span></footer>
        </> : <section className="page-placeholder">
          {active === 'lab' ? <article className="panel lab-upload"><div className="upload-art"><Upload size={22}/></div><h2>Upload recorded flow data</h2><p>Choose a CSV of network flow feature columns. The file is scored locally by the active model.</p><label className="upload-drop"><input type="file" accept=".csv,text/csv" onChange={e => { setSelectedFile(e.currentTarget.files?.[0] ?? null); setAnalysis(null); setAnalysisError('') }}/><span className="upload-drop-title">{selectedFile?.name || <>Drop a CSV here or <b>browse files</b></>}</span><span className="upload-drop-note">CSV format · Maximum 500 MB · Numeric feature columns</span></label><div className="upload-empty"><AlertTriangle size={14}/>{apiHealth?.model_loaded ? 'Predictions are model scores, not confirmed attacks.' : 'Analysis requires the local prediction API and a trained model bundle.'}</div>{analysisError && <p className="analysis-error" role="alert">{analysisError}</p>}<Button variant="primary" disabled={!selectedFile || !apiHealth?.model_loaded || analyzing} onClick={() => void runAnalysis()}><Sparkles size={14}/>{analyzing ? 'Analyzing…' : 'Analyze file'}</Button>{analysis && <div className="analysis-result" role="status"><h3>Analysis complete</h3><p>{analysis.source_file} · {analysis.total_flows.toLocaleString()} flows · model {analysis.model_id}</p><div className="analysis-counts"><span>Predicted benign <b>{analysis.benign_count.toLocaleString()}</b></span><span>Predicted malicious <b>{analysis.malicious_count.toLocaleString()}</b></span></div><p className="analysis-footnote">Showing {analysis.preview.length} preview rows. Scores are not calibrated probabilities.</p><table className="analysis-preview"><thead><tr><th>Row</th><th>Prediction</th><th>Score</th></tr></thead><tbody>{analysis.preview.slice(0, 10).map(row => <tr key={row.row_index}><td>{row.row_index + 1}</td><td>{row.is_malicious_prediction ? "Malicious" : "Benign"}</td><td>{row.score.toFixed(4)}</td></tr>)}</tbody></table></div>}</article> : active === 'performance' ? <article className="panel performance-results"><div className="placeholder-icon"><activePage.icon size={21}/></div><h2>Model comparison</h2><p>Held-out test metrics · {benchmark?.dataset ?? 'CIC-IDS2017'} · {benchmark?.rows.toLocaleString() ?? '—'} flows</p>{benchmark ? <><div className="placeholder-foot">Selected by {benchmark.selection_metric}: <strong>{benchmark.selected_model}</strong>. Test partition was not used to select the model.</div><div className="table-scroll"><table className="analysis-preview"><thead><tr><th>Model</th><th>Precision</th><th>Recall</th><th>F1</th><th>PR-AUC</th><th>ROC-AUC</th></tr></thead><tbody>{Object.entries(benchmark.models).map(([name, scores]) => <tr key={name}><td>{name}{name === benchmark.selected_model ? ' · Active' : ''}</td><td>{(scores.test.precision * 100).toFixed(2)}%</td><td>{(scores.test.recall * 100).toFixed(2)}%</td><td>{(scores.test.f1 * 100).toFixed(2)}%</td><td>{scores.test.pr_auc.toFixed(4)}</td><td>{scores.test.roc_auc.toFixed(4)}</td></tr>)}</tbody></table></div><p className="analysis-footnote">Warning: this report uses a stratified random row split; repeated or adjacent flows may cross partitions and inflate test scores.</p></> : <div className="placeholder-foot">No benchmark report is available from the API.</div>}</article>: <article className="panel placeholder-panel"><div className="placeholder-icon"><activePage.icon size={21}/></div><h2>{activePage.name}</h2><p>{active === 'alerts' ? 'Model-flagged flows, filters, and safe CSV export.' : active === 'investigation' ? 'Inspect a selected flow, its features, and model explanation.' : active === 'network' ? 'Explore protocol, port, timeline, and endpoint summaries.' : 'Review saved evaluation reports and model limitations.'}</p><EmptyState icon={activePage.icon} title="No generated results yet"/><div className="placeholder-foot">Not yet generated. Run the pipeline.</div></article>}
        </section>}
        <footer className="app-footer"><span><Shield size={13}/> Predictions are model outputs, not confirmed attacks. Scores are uncalibrated.</span><span>Trained on CIC-IDS2017 benchmark data; results may not transfer to other networks.</span></footer>
      </div>
    </main>
  </div>
}
