'use client';

import FertilizerCalendarCard, { FertilizerCalendar } from './FertilizerCalendarCard';

export default function WeekPlanCard({
  weekPlan,
  fertilizerCalendar,
}: {
  weekPlan?: {
    spray_summary?: string;
    spray_best_window?: { label?: string };
    fertilizer_summary?: string | null;
    fertilizer_next?: { label?: string; timing_label?: string } | null;
    top_pest?: string;
  };
  fertilizerCalendar?: FertilizerCalendar | null;
}) {
  if (!weekPlan && !fertilizerCalendar) return null;

  return (
    <div className="card">
      <p className="section-label">이번 주 농작업</p>
      <div className="grid md:grid-cols-2 gap-4 mt-2">
        <div className="p-4 rounded-xl bg-surface-muted">
          <p className="text-xs text-ink-muted uppercase tracking-wider mb-2">방제</p>
          <p className="text-sm font-medium">{weekPlan?.top_pest ? `${weekPlan.top_pest} 주의` : '병해충 모니터링'}</p>
          <p className="text-xs text-ink-secondary mt-2 leading-relaxed">
            {weekPlan?.spray_summary || '방제 타이밍을 확인하세요.'}
          </p>
          {weekPlan?.spray_best_window?.label && (
            <p className="text-xs font-mono mt-2 text-ink-muted">적기 {weekPlan.spray_best_window.label}</p>
          )}
        </div>
        <div className="p-4 rounded-xl bg-surface-muted">
          <p className="text-xs text-ink-muted uppercase tracking-wider mb-2">시비</p>
          <p className="text-sm font-medium">
            {weekPlan?.fertilizer_next?.label || fertilizerCalendar?.next_event?.label || '시비 일정'}
          </p>
          <p className="text-xs text-ink-secondary mt-2 leading-relaxed">
            {weekPlan?.fertilizer_summary || fertilizerCalendar?.summary || '흙토람 비료처방 기준'}
          </p>
        </div>
      </div>
    </div>
  );
}

export { FertilizerCalendarCard };
