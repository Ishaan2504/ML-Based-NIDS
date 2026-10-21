import { Activity, LayoutDashboard, ShieldAlert, Workflow } from 'lucide-react'

export const pages = [
  { name: 'Security Overview', icon: LayoutDashboard, key: 'overview' as const },
  { name: 'Traffic Analysis Lab', icon: Workflow, key: 'lab' as const },
]

export const stats = [
  { label: 'Flows analysed', icon: Activity, hint: 'Rows scored', color: 'blue' },
  { label: 'Predicted malicious', icon: ShieldAlert, hint: 'Model flagged', color: 'red' },
  { label: 'Predicted benign', icon: Activity, hint: 'Model classified', color: 'green' },
]
