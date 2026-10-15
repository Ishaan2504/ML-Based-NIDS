import { useState } from 'react'
import { Activity, AlertTriangle, ArrowDownToLine, ArrowUpRight, Bell, ChevronDown, CircleHelp, Clock3, Command, Database, Fingerprint, Layers3, PanelLeftClose, Search, Shield, ShieldAlert, Sparkles, Upload } from 'lucide-react'
import BentoItem from '@/components/ui/terminal-bento-grid'
import { Button } from '@/components/ui/button'
import { EmptyState } from '@/components/ui/empty-state'
import { pages, stats } from '@/lib/dashboard-data'

export default function App() {
  const [active, setActive] = useState('overview')
  const [collapsed, setCollapsed] = useState(false)
  const [selectedFile, setSelectedFile] = useState('')
  const activePage = pages.find(p => p.key === active) ?? pages[0]

  return <div className={`app-shell ${collapsed ? 'sidebar-collapsed' : ''}`}>
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark"><Fingerprint size={21} /></div><div className="brand-copy"><strong>sentinel<span>.</span></strong><small>NETWORK DEFENSE</small></div><button className="collapse-button" onClick={() => setCollapsed(!collapsed)} aria-label="Collapse sidebar"><PanelLeftClose size={16} /></button></div>
      <div className="workspace-switch"><div className="workspace-icon"><Command size={15} /></div><div className="workspace-copy"><strong>Security workspace</strong><small>LOCAL ENVIRONMENT</small></div><ChevronDown size={14} /></div>
      <div className="nav-label">WORKSPACE</div>
      <nav className="nav-list">{pages.map(({ name, icon: Icon, key, badge }) => <button key={key} onClick={() => setActive(key)} className={`nav-item ${active === key ? 'active' : ''}`} title={name}><Icon size={17} /><span>{name}</span>{badge && <small>{badge}</small>}</button>)}</nav>
      <div className="sidebar-spacer" />
      <div className="pipeline-card"><div className="pipeline-card-top"><span className="status-dot offline" /> <span>PIPELINE STATUS</span><span className="live-label">IDLE</span></div><div className="pipeline-card-title">Awaiting first run</div><div className="pipeline-line"><span /></div><div className="pipeline-foot"><span>Dataset</span><span>CIC-IDS2017</span></div></div>
      <div className="sidebar-bottom"><button className="nav-item"><CircleHelp size={17}/><span>Documentation</span></button><div className="user-row"><div className="avatar">AD</div><div><strong>Analyst workspace</strong><small>Local · offline</small></div><ChevronDown size={14}/></div></div>
    </aside>

    <main className="main-panel">
      <header className="topbar"><div className="breadcrumbs"><span>Workspace</span><span className="crumb-slash">/</span><strong>{activePage.name}</strong></div><div className="topbar-actions"><div className="api-pill"><span className="status-dot offline"/>API offline</div><button className="icon-button" aria-label="Search"><Search size={17}/></button><button className="icon-button notification" aria-label="Notifications"><Bell size={17}/><i/></button><div className="top-divider"/><div className="model-chip"><span className="model-chip-icon"><Layers3 size={14}/></span><span><small>ACTIVE MODEL</small><strong>Not yet generated</strong></span><ChevronDown size={13}/></div></div></header>

      <div className="content-wrap">
        <div className="notice-banner"><span className="notice-icon"><AlertTriangle size={15}/></span><span><strong>Offline analysis workspace</strong><i> · This dashboard analyses recorded flow data. No live traffic is collected.</i></span><button aria-label="Dismiss" onClick={e => e.currentTarget.parentElement?.remove()}>×</button></div>
        <div className="page-heading"><div><div className="eyebrow"><span className="eyebrow-dot"/> NIDS · LOCAL SYSTEM</div><h1>SYSTEM DASHBOARD</h1><p className="page-subtitle">{active === 'overview' ? 'Recorded network flow analysis · offline mode' : activePage.name}</p></div><div className="heading-actions"><Button><Clock3 size={15}/>No analysis run<ChevronDown size={14}/></Button><Button variant="primary" onClick={() => setActive('lab')}><Upload size={15}/>Analyze a CSV</Button></div></div>

        <div className="run-banner"><div className="run-banner-icon"><Database size={17}/></div><div><strong>No analysis run selected</strong><span>Upload a labelled-flow CSV or run the offline pipeline to populate this workspace.</span></div><button onClick={() => setActive('lab')}>Open Analysis Lab <ArrowUpRight size={14}/></button></div>

        {active === 'overview' ? <>
        <section className="stats-grid">{stats.map(({label, icon: Icon, hint, color}) => <article className="stat-card" key={label}><div className="stat-head"><span>{label}</span><span className={`stat-icon ${color}`}><Icon size={16}/></span></div><div className="stat-value">—</div><div className="stat-foot"><span>{hint}</span><span className="not-generated">Not generated</span></div></article>)}</section>

        <section className="overview-grid">
          <article className="panel traffic-panel"><div className="panel-header"><div><h2>Traffic over time</h2><p>Predicted benign and malicious flows by time bucket</p></div><Button><span className="tiny-dot blue-dot"/>Timeline unavailable<ChevronDown size={13}/></Button></div><div className="chart-empty"><div className="chart-grid"><div className="chart-axis"><span>—</span><span>—</span><span>—</span><span>—</span></div><div className="chart-main"><div className="chart-lines"><i/><i/><i/><i/></div><div className="chart-zero"><Activity size={19}/><span>Run an analysis to see traffic patterns</span></div><div className="chart-xaxis"><span>—</span><span>—</span><span>—</span><span>—</span><span>—</span></div></div></div></div><div className="chart-legend"><span><i className="legend-benign"/>Predicted benign</span><span><i className="legend-malicious"/>Predicted malicious</span><small>Counts are loaded from generated run artifacts.</small></div></article>
          <article className="panel distribution-panel"><div className="panel-header"><div><h2>Threat distribution</h2><p>Predicted attack families</p></div><button className="more-button">···</button></div><div className="donut-wrap"><div className="donut"><div className="donut-center"><Shield size={21}/><span>—</span><small>alerts</small></div></div></div><div className="distribution-empty">No generated predictions</div><div className="distribution-foot"><span>Family breakdown</span><span>Not generated</span></div></article>
        </section>

        <section className="bottom-grid">
          <article className="panel alerts-panel"><div className="panel-header"><div><h2>Recent alerts</h2><p>Latest model-flagged flows from the selected run</p></div><button className="text-link" onClick={() => setActive('alerts')}>View all <ArrowUpRight size={14}/></button></div><div className="table-head"><span>FLOW</span><span>PREDICTED FAMILY</span><span>MODEL SCORE</span><span>SEVERITY</span></div><EmptyState icon={ShieldAlert} title="No alerts to display"/><div className="table-bottom"><span>Showing 0 alerts</span><button disabled><ArrowDownToLine size={14}/>Export CSV</button></div></article>
          <article className="panel health-panel"><div className="panel-header"><div><h2>System health</h2><p>Local analysis services</p></div><span className="health-tag">DEGRADED</span></div><div className="health-row"><div className="health-icon red"><Activity size={16}/></div><div><strong>Prediction API</strong><span>Start the local API to enable analysis.</span></div><span className="health-state">Offline</span></div><div className="health-row"><div className="health-icon blue"><Database size={16}/></div><div><strong>Run storage</strong><span>File-based · local workspace</span></div><span className="health-state muted">Empty</span></div><div className="health-note"><Sparkles size={14}/><span>Results and metrics appear here after the pipeline generates reports.</span></div></article>
        </section>

        <section className="terminal-section"><div className="terminal-section-head"><div><span className="terminal-label"><span/> WORKSPACE DIAGNOSTICS</span><h2>Pipeline monitor</h2></div><span className="terminal-status"><span className="status-dot offline"/>WAITING FOR DATA</span></div><div className="bento-grid"><BentoItem className="col-span-2"><h3>&gt; DATASET: CIC-IDS2017</h3><p>Recorded flow analysis · Dataset files not detected</p></BentoItem><BentoItem><h3>&gt; MODEL STATUS</h3><p>Not yet generated</p></BentoItem><BentoItem><h3>&gt; API STATUS</h3><p>Offline · local service</p></BentoItem><BentoItem className="col-span-2"><h3>&gt; REPORTS</h3><p>Not yet generated. Run the pipeline.</p></BentoItem></div></section>
        <footer className="app-footer"><span><Shield size={13}/> Predictions are model outputs, not confirmed attacks. Scores are uncalibrated.</span><span>Trained on lab-generated 2017 data; results may not transfer to other networks.</span></footer>
        </> : <section className="page-placeholder">
          {active === 'lab' ? <article className="panel lab-upload"><div className="upload-art"><Upload size={22}/></div><h2>Upload recorded flow data</h2><p>Choose a CSV file containing flow feature columns for offline analysis. Files stay in this local workspace.</p><label className="upload-drop"><input type="file" accept=".csv,text/csv" onChange={e => setSelectedFile(e.currentTarget.files?.[0]?.name ?? '')}/><span className="upload-drop-title">{selectedFile || <>Drop a CSV here or <b>browse files</b></>}</span><span className="upload-drop-note">CSV format · Maximum 200 MB · Decimal commas are not supported</span></label><div className="upload-empty"><AlertTriangle size={14}/> Analysis requires the local prediction API and a generated model bundle.</div><Button variant="primary" disabled><Sparkles size={14}/>Analyze file</Button></article> : <article className="panel placeholder-panel"><div className="placeholder-icon"><activePage.icon size={21}/></div><h2>{activePage.name}</h2><p>{active === 'alerts' ? 'Model-flagged flows, filters, and safe CSV export.' : active === 'investigation' ? 'Inspect a selected flow, its features, and model explanation.' : active === 'network' ? 'Explore protocol, port, timeline, and endpoint summaries.' : 'Review saved evaluation reports and model limitations.'}</p><EmptyState icon={activePage.icon} title="No generated results yet"/><div className="placeholder-foot">Not yet generated. Run the pipeline.</div></article>}
        </section>}
        <footer className="app-footer"><span><Shield size={13}/> Predictions are model outputs, not confirmed attacks. Scores are uncalibrated.</span><span>Trained on lab-generated 2017 data; results may not transfer to other networks.</span></footer>
      </div>
    </main>
  </div>
}
