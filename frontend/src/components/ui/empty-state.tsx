import { Database, type LucideIcon } from 'lucide-react'

type EmptyStateProps = { icon?: LucideIcon; title?: string }

export function EmptyState({ icon: Icon = Database, title = 'No generated results yet' }: EmptyStateProps) {
  return <div className="empty-state"><div className="empty-icon"><Icon size={19} /></div><div><div className="empty-title">{title}</div><p>Not yet generated. Run the pipeline.</p></div></div>
}
