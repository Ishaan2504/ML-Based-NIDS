import type { HTMLAttributes, PropsWithChildren } from 'react'

type BentoItemProps = PropsWithChildren<HTMLAttributes<HTMLDivElement>>

export default function BentoItem({ className = '', children, ...props }: BentoItemProps) {
  return <div className={`bento-item ${className}`} {...props}>{children}</div>
}
