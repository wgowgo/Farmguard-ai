'use client';

interface Props {
  score: number;
  level: string;
  showBar?: boolean;
}

function riskBarColor(score: number): string {
  if (score < 40) return '#007a3d';
  if (score < 70) return '#d97706';
  if (score < 85) return '#ea580c';
  return '#dc2626';
}

export default function RiskBadge({ score, level, showBar = true }: Props) {
  const badgeClass = {
    '낮음': 'risk-badge-low',
    '주의': 'risk-badge-caution',
    '위험': 'risk-badge-danger',
    '매우 위험': 'risk-badge-critical',
  }[level] || 'bg-surface-subtle text-ink-secondary border border-border';

  return (
    <div className="flex items-center gap-4">
      <span className={`risk-badge ${badgeClass}`}>{level}</span>
      <span className="text-3xl font-semibold tracking-tight tabular-nums">{Math.round(score)}</span>
      {showBar && (
        <div className="flex-1 h-1.5 bg-surface-subtle rounded-full overflow-hidden max-w-[140px]">
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{ width: `${Math.min(score, 100)}%`, backgroundColor: riskBarColor(score) }}
          />
        </div>
      )}
    </div>
  );
}
