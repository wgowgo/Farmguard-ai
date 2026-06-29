'use client';

export interface WeatherTimelinePoint {
  time: string;
  label: string;
  temp: number;
  humidity: number;
  rain_mm: number;
  rain_prob: number;
  wind_speed?: number | null;
  dew_time?: number | null;
  dew_risk: 'low' | 'medium' | 'high';
  period: 'observed' | 'forecast';
  source: string;
}

export interface WeatherTimeline {
  hours: number;
  points: WeatherTimelinePoint[];
  summary: {
    high_dew_hours: number;
    rain_risk_hours: number;
    next_rain?: WeatherTimelinePoint | null;
    peak_humidity: number;
  };
  highlights: string[];
}

const DEW_COLOR = {
  low: 'bg-emerald-50',
  medium: 'bg-amber-50',
  high: 'bg-red-50',
};

export default function WeatherTimelineCard({ data }: { data: WeatherTimeline }) {
  const maxHum = Math.max(...data.points.map((p) => p.humidity), 1);

  return (
    <div className="card">
      <div className="flex flex-wrap items-start justify-between gap-3 mb-4">
        <div>
          <p className="section-label">기상 타임라인 (72h)</p>
          <p className="text-sm text-ink-secondary mt-1">
            {data.highlights.join(', ') || '팜맵 관측 + 기상청 예보'}
          </p>
        </div>
        <div className="text-xs text-ink-muted text-right">
          <p>고습, 결로 {data.summary.high_dew_hours}h</p>
          <p>강수 위험 {data.summary.rain_risk_hours}h</p>
        </div>
      </div>

      <div className="space-y-1 max-h-80 overflow-y-auto pr-1">
        {data.points.map((p) => (
          <div
            key={p.time}
            className={`flex items-center gap-3 p-2 rounded-lg text-xs ${DEW_COLOR[p.dew_risk]}`}
          >
            <span className="w-24 shrink-0 font-mono text-ink-muted">{p.label}</span>
            <span className="w-12 tabular-nums">{p.temp}°</span>
            <div className="flex-1 h-2 bg-white/80 rounded-full overflow-hidden">
              <div
                className="h-full bg-sky-400/70 rounded-full"
                style={{ width: `${(p.humidity / maxHum) * 100}%` }}
              />
            </div>
            <span className="w-10 text-right tabular-nums">{p.humidity}%</span>
            <span className="w-14 text-right tabular-nums text-ink-muted">
              {p.rain_prob > 0 ? `${p.rain_prob}%` : `${p.rain_mm}mm`}
            </span>
            <span className="w-12 text-right text-[10px] uppercase text-ink-muted">
              {p.period === 'observed' ? '관측' : '예보'}
            </span>
          </div>
        ))}
      </div>

      <div className="flex gap-4 mt-4 text-[10px] text-ink-muted">
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-emerald-50 ring-1 ring-emerald-200" /> 낮음</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-amber-50 ring-1 ring-amber-200" /> 보통</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-red-50 ring-1 ring-red-200" /> 결로주의</span>
      </div>
    </div>
  );
}
