import { Activity, FileSearch, Gauge, LayoutDashboard, Network, Shield, ShieldAlert, SlidersHorizontal, Workflow } from 'lucide-react'

export const pages = [
  { name: 'Security Overview', icon: LayoutDashboard, key: 'overview' },
  { name: 'Threat Alerts', icon: ShieldAlert, key: 'alerts', badge: '—' },
  { name: 'Traffic Investigation', icon: FileSearch, key: 'investigation' },
  { name: 'Network Activity', icon: Network, key: 'network' },
  { name: 'Model Performance', icon: Gauge, key: 'performance' },
  { name: 'Traffic Analysis Lab', icon: Workflow, key: 'lab' },
]

export const stats = [
  { label: 'Flows analysed', icon: Activity, hint: 'Total records scored', color: 'blue' },
  { label: 'Predicted malicious', icon: ShieldAlert, hint: 'Model score ≥ threshold', color: 'red' },
  { label: 'Predicted benign', icon: Shield, hint: 'Below operating threshold', color: 'green' },
  { label: 'Operating threshold', icon: SlidersHorizontal, hint: 'Chosen on validation data', color: 'amber' },
]
