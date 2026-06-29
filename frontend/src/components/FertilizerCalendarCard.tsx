'use client';

export interface FertilizerEvent {
  id: string;
  label: string;
  timing_label: string;
  date: string;
  offset_days: number;
  nitrogen: number;
  phosphate: number;
  potassium: number;
  unit: string;
  status: 'past' | 'today' | 'upcoming' | 'scheduled';
  notes: string;
}

export interface FertilizerCalendar {
  crop_name: string;
  planting_date?: string | null;
  source: string;
  unit: string;
  total: { nitrogen: number; phosphate: number; potassium: number };
  next_event?: FertilizerEvent | null;
  events: FertilizerEvent[];
  summary: string;
}

const STATUS_STYLE: Record<string, string> = {
  past: 'opacity-50',
  today: 'ring-2 ring-orange-400 bg-orange-50',
  upcoming: 'ring-1 ring-ink/20 bg-white',
  scheduled: 'bg-surface-muted',
};

export default function FertilizerCalendarCard({ data }: { data: FertilizerCalendar }) {
  return (
    <div className="card">
      <div className="flex flex-wrap items-start justify-between gap-3 mb-4">
        <div>
          <p className="section-label">시비 캘린더</p>
          <p className="text-sm text-ink-secondary mt-1">{data.summary}</p>
        </div>
        <span className="text-[10px] uppercase tracking-wide text-ink-muted px-2 py-1 rounded-full bg-surface-muted">
          {data.source === 'soil_api' ? '흙토람 처방' : '추정 처방'}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-2 mb-6 text-center text-xs">
        {[
          { label: '질소 합계', value: data.total.nitrogen },
          { label: '인산 합계', value: data.total.phosphate },
          { label: '칼리 합계', value: data.total.potassium },
        ].map((t) => (
          <div key={t.label} className="p-3 rounded-xl bg-surface-muted">
            <p className="text-ink-muted mb-1">{t.label}</p>
            <p className="font-semibold tabular-nums">{t.value}</p>
            <p className="text-ink-muted">{data.unit}</p>
          </div>
        ))}
      </div>

      <div className="space-y-2">
        {data.events.map((e) => (
          <div
            key={e.id}
            className={`p-4 rounded-xl flex flex-wrap items-center justify-between gap-3 ${STATUS_STYLE[e.status] || ''}`}
          >
            <div>
              <p className="font-medium text-sm">{e.label}</p>
              <p className="text-xs text-ink-muted mt-0.5">{e.timing_label}, {e.date}</p>
            </div>
            <div className="text-right text-xs tabular-nums">
              <p>N {e.nitrogen}, P {e.phosphate}, K {e.potassium}</p>
              <p className="text-ink-muted">{e.unit}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
