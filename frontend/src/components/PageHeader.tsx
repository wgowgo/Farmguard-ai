import Link from 'next/link';
import { ReactNode } from 'react';

interface Props {
  title: string;
  desc?: string;
  breadcrumb?: { label: string; href?: string }[];
  actions?: ReactNode;
}

export default function PageHeader({ title, desc, breadcrumb, actions }: Props) {
  return (
    <div className="page-header">
      {breadcrumb && breadcrumb.length > 0 && (
        <nav className="page-breadcrumb" aria-label="breadcrumb">
          <Link href="/">홈</Link>
          {breadcrumb.map((b, i) => (
            <span key={i} className="flex items-center gap-1.5">
              <span aria-hidden className="text-border">›</span>
              {b.href ? (
                <Link href={b.href}>{b.label}</Link>
              ) : (
                <span className="text-ink-secondary">{b.label}</span>
              )}
            </span>
          ))}
        </nav>
      )}
      <div className="page-header-body">
        <div>
          <h2 className="page-title">{title}</h2>
          {desc && <p className="page-desc">{desc}</p>}
        </div>
        {actions && <div className="flex flex-wrap gap-2 shrink-0">{actions}</div>}
      </div>
    </div>
  );
}
