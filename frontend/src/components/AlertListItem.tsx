'use client';

export interface AlertItem {
  id?: number;
  type: string;
  title: string;
  message: string;
  created_at?: string;
  status?: string;
}

const TYPE_META: Record<string, { label: string; border: string }> = {
  risk_rise: { label: '위험 경보', border: 'border-l-red-600' },
  rain_before_spray: { label: '강우 전 방제', border: 'border-l-sky-600' },
  high_humidity: { label: '고습/결로', border: 'border-l-cyan-600' },
  nearby_pest: { label: '주변 발생', border: 'border-l-amber-500' },
  weekly_report: { label: '주간 리포트', border: 'border-l-rda-600' },
};

const DEFAULT_META = { label: '알림', border: 'border-l-portal-muted' };

function stripEmoji(text: string) {
  return text.replace(/[\u{1F300}-\u{1FAFF}\u2600-\u27BF]/gu, '').replace(/\s+/g, ' ').trim();
}

function formatDate(iso?: string) {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleString('ko-KR', {
      month: 'numeric',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return iso.slice(0, 16);
  }
}

interface ParsedReport {
  meta: string[];
  sections: { title: string; items: string[] }[];
  footer?: string;
}

function parseWeeklyReport(text: string): ParsedReport {
  let raw = text.trim();
  if (!raw.includes('\n') && (raw.includes('【') || raw.includes(', '))) {
    raw = raw
      .replace(/\s*【/g, '\n【')
      .replace(/\s*, \s*/g, '\n• ');
  }

  const lines = raw.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
  const meta: string[] = [];
  const sections: { title: string; items: string[] }[] = [];
  let current: { title: string; items: string[] } | null = null;
  let footer: string | undefined;

  for (const line of lines) {
    if (line.startsWith('—')) {
      footer = line.replace(/^—\s*/, '');
      continue;
    }
    const section = line.match(/^【(.+?)】/);
    if (section) {
      if (current) sections.push(current);
      current = { title: section[1], items: [] };
      continue;
    }
    if (line.startsWith('•') || /^\d+\./.test(line)) {
      const item = line.replace(/^•\s*/, '').replace(/^\d+\.\s*/, '');
      if (current) current.items.push(item);
      else meta.push(item);
      continue;
    }
    if (line.includes('주간 리포트') || /^[🌾📍🌱]/.test(line)) {
      meta.push(stripEmoji(line));
      continue;
    }
    if (current) current.items.push(line);
    else meta.push(line);
  }
  if (current) sections.push(current);

  return { meta, sections, footer };
}

function WeeklyReportBody({ message }: { message: string }) {
  const { meta, sections, footer } = parseWeeklyReport(message);

  return (
    <div className="mt-3 space-y-3 text-sm">
      {meta.length > 0 && (
        <div className="space-y-1 text-xs text-ink-secondary">
          {meta.map((m, i) => (
            <p key={i}>{m}</p>
          ))}
        </div>
      )}
      {sections.map((sec) => (
        <div key={sec.title} className="rounded-portal border border-border-light bg-surface-muted p-3">
          <p className="text-xs font-bold text-rda-700 mb-2 pb-1 border-b border-rda-100">{sec.title}</p>
          <ul className="space-y-1.5 text-xs text-ink-secondary leading-relaxed">
            {sec.items.map((item, i) => (
              <li key={i} className="flex gap-2">
                <span className="text-rda-600 shrink-0">›</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      ))}
      {footer && (
        <p className="text-[10px] text-ink-muted text-right pt-1">{footer}</p>
      )}
    </div>
  );
}

export default function AlertListItem({ alert }: { alert: AlertItem }) {
  const meta = TYPE_META[alert.type] || DEFAULT_META;
  const isWeekly = alert.type === 'weekly_report';

  return (
    <article
      className={`alert-item border border-border bg-white rounded-portal border-l-4 ${meta.border} shadow-card overflow-hidden`}
    >
      <div className="px-4 py-3 border-b border-border-light flex flex-wrap items-center justify-between gap-2">
        <span className="text-xs font-semibold text-ink-secondary">{meta.label}</span>
        {alert.created_at && (
          <time className="text-[11px] text-ink-muted tabular-nums">{formatDate(alert.created_at)}</time>
        )}
      </div>

      <div className="px-4 py-4">
        <h3 className="font-bold text-sm text-ink leading-snug">{alert.title}</h3>

        {isWeekly ? (
          <WeeklyReportBody message={alert.message} />
        ) : (
          <p className="text-sm text-ink-secondary mt-2 leading-relaxed">{alert.message}</p>
        )}
      </div>
    </article>
  );
}

export function AlertList({ alerts, emptyText = '발송된 알림이 없습니다' }: {
  alerts: AlertItem[];
  emptyText?: string;
}) {
  if (alerts.length === 0) {
    return <p className="text-ink-muted text-sm py-8 text-center bg-surface-muted rounded-portal">{emptyText}</p>;
  }

  return (
    <div className="space-y-3">
      {alerts.map((a) => (
        <AlertListItem key={a.id ?? `${a.type}-${a.title}`} alert={a} />
      ))}
    </div>
  );
}
