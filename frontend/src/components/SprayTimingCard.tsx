'use client';

export interface SprayTiming {
  date: string;
  best_window?: { from: number; to: number; label: string };
  all_windows: { from: number; to: number; label: string }[];
  rain_warning: string;
  rain_start_hour?: number;
  summary: string;
  hourly: { hour: number; label: string; rain_prob: number; suitable: boolean }[];
}

export default function SprayTimingCard({ data }: { data: SprayTiming }) {
  return (
    <div className="card">
      <p className="section-label">방제 가능 시간</p>
      <p className="text-sm text-ink font-medium mb-4 leading-relaxed">{data.summary}</p>

      {data.best_window && (
        <div className="bg-surface-muted rounded-xl p-4 mb-4 border border-border-light">
          <p className="text-xs text-ink-muted mb-1">오늘 최적 시간</p>
          <p className="text-xl font-semibold tracking-tight">{data.best_window.label}</p>
        </div>
      )}

      <p className="text-xs text-orange-600 mb-4">{data.rain_warning}</p>

      <div className="flex flex-wrap gap-1">
        {data.hourly.map((h) => (
          <div
            key={h.hour}
            title={`강수확률 ${h.rain_prob}%`}
            className={`text-xs px-2 py-2.5 rounded-lg text-center min-w-[36px] font-medium ${
              h.suitable
                ? 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-100'
                : h.rain_prob >= 50
                  ? 'bg-sky-50 text-sky-700 ring-1 ring-sky-100'
                  : 'bg-surface-subtle text-ink-muted'
            }`}
          >
            {h.hour}
          </div>
        ))}
      </div>
      <p className="text-xs text-ink-muted mt-3">초록=방제 적합, 파랑=강수 예보</p>
    </div>
  );
}
