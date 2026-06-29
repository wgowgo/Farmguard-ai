'use client';

import { useEffect, useState, Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import dynamic from 'next/dynamic';
import { api, Dashboard, Field, FieldInsights, riskColor } from '@/lib/api';
import RiskBadge from '@/components/RiskBadge';
import Forecast14dChart from '@/components/Forecast14dChart';
import SprayTimingCard from '@/components/SprayTimingCard';
import WeekPlanCard from '@/components/WeekPlanCard';
import WeatherTimelineCard, { WeatherTimeline } from '@/components/WeatherTimelineCard';
import ShareReportModal from '@/components/ShareReportModal';
import PageHeader from '@/components/PageHeader';
import { AlertList } from '@/components/AlertListItem';

const RiskMapView = dynamic(() => import('@/components/RiskMapView'), { ssr: false });

export default function DashboardPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center py-32">
        <div className="spinner" />
      </div>
    }>
      <DashboardContent />
    </Suspense>
  );
}

function DashboardContent() {
  const searchParams = useSearchParams();
  const [fields, setFields] = useState<Field[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [insights, setInsights] = useState<FieldInsights | null>(null);
  const [showShare, setShowShare] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getFields().then((f) => {
      setFields(f);
      const q = searchParams.get('field');
      const preferred = q ? Number(q) : null;
      if (preferred && f.some((x) => x.field_id === preferred)) {
        setSelectedId(preferred);
      } else if (f.length > 0) {
        setSelectedId(f[0].field_id);
      } else {
        setLoading(false);
      }
    }).catch(() => setLoading(false));
  }, [searchParams]);

  useEffect(() => {
    if (!selectedId) return;
    setLoading(true);
    Promise.all([api.getDashboard(selectedId), api.getInsights(selectedId)])
      .then(([d, ins]) => { setDashboard(d); setInsights(ins); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [selectedId]);

  if (loading && !dashboard) {
    return (
      <div className="flex items-center justify-center py-32">
        <div className="spinner" />
      </div>
    );
  }

  if (fields.length === 0) {
    return (
      <>
        <PageHeader title="대시보드" desc="필지를 등록하면 위험도, 예보, 방제 정보를 확인할 수 있습니다" breadcrumb={[{ label: '대시보드' }]} />
        <div className="empty-state">
          <p className="text-ink-secondary mb-6">등록된 필지가 없습니다</p>
          <Link href="/fields/register" className="btn-primary">필지 등록하기</Link>
        </div>
      </>
    );
  }

  const maxRisk = dashboard?.today_risks.reduce((m, r) => Math.max(m, r.final_risk), 0) ?? 0;
  const urgent = maxRisk >= 70;
  const forecastFuture = insights?.forecast_14d.filter((f) => f.type === 'forecast') ?? [];
  const peakForecast = forecastFuture.length
    ? forecastFuture.reduce((a, b) => (a.avg_risk > b.avg_risk ? a : b))
    : null;

  return (
    <div className="space-y-6">
      <PageHeader
        title="대시보드"
        desc="7일 예보, 방제 타이밍, 주변 위험 지도"
        breadcrumb={[{ label: '대시보드' }]}
        actions={
          <>
            {urgent && <span className="alert-banner">긴급 알림</span>}
            {insights?.weekly_report && (
              <button onClick={() => setShowShare(true)} className="btn-primary text-sm">
                리포트 공유
              </button>
            )}
          </>
        }
      />

      <div className="flex gap-2 flex-wrap">
        {fields.map((f) => (
          <button
            key={f.field_id}
            onClick={() => setSelectedId(f.field_id)}
            className={selectedId === f.field_id ? 'chip-active' : 'chip'}
          >
            {f.crop_name}, {f.address?.slice(0, 12) || `#${f.field_id}`}
          </button>
        ))}
      </div>

      {dashboard && insights && (
        <>
          <div className="grid md:grid-cols-3 gap-5">
            <div className="card md:col-span-1">
              <p className="section-label">오늘 위험도</p>
              {dashboard.top_pests[0] ? (
                <RiskBadge score={dashboard.top_pests[0].final_risk} level={dashboard.top_pests[0].risk_level} />
              ) : (
                <p className="text-ink-muted text-sm">데이터 없음</p>
              )}
              {peakForecast && (
                <p className="text-xs text-ink-secondary mt-4 pt-4 border-t border-border-light">
                  이번 주 최고 예보, {peakForecast.label}, {peakForecast.avg_risk}점
                </p>
              )}
              <p className="text-xs text-ink-muted mt-2">
                {dashboard.field.crop_name}, {dashboard.field.land_type}, {dashboard.field.address}
              </p>
            </div>

            <div className="card md:col-span-2">
              <p className="section-label">7일 관측 + 7일 예보</p>
              <Forecast14dChart data={insights.forecast_14d as Parameters<typeof Forecast14dChart>[0]['data']} />
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-5">
            <SprayTimingCard data={insights.spray_timing as Parameters<typeof SprayTimingCard>[0]['data']} />
            <WeekPlanCard
              weekPlan={insights.week_plan as Parameters<typeof WeekPlanCard>[0]['weekPlan']}
              fertilizerCalendar={insights.fertilizer_calendar as Parameters<typeof WeekPlanCard>[0]['fertilizerCalendar']}
            />
          </div>

          <div className="card">
            <p className="section-label">주변 병해충 지도</p>
            <RiskMapView layers={insights.map_layers} />
            <p className="text-xs text-ink-muted mt-3">원 = 발생 거리, 점 = 예찰 위치</p>
          </div>

          {insights.weather_timeline && (insights.weather_timeline as WeatherTimeline).points?.length > 0 && (
            <WeatherTimelineCard data={insights.weather_timeline as WeatherTimeline} />
          )}

          <div className="grid md:grid-cols-2 gap-5">
            <div className="card">
              <p className="section-label">병해충 Top 3</p>
              <div className="space-y-1">
                {dashboard.top_pests.map((p, i) => (
                  <Link
                    key={p.pest_name}
                    href={`/fields/${selectedId}/pest/${encodeURIComponent(p.pest_name)}`}
                    className="flex items-center justify-between p-3 -mx-2 rounded-xl hover:bg-surface-muted transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <span className="w-7 h-7 rounded-lg bg-surface-subtle text-ink-secondary text-xs flex items-center justify-center font-medium">
                        {i + 1}
                      </span>
                      <span className="font-medium text-sm">{p.pest_name}</span>
                    </div>
                    <span className={`risk-badge ${riskColor(p.risk_level)}`}>
                      {Math.round(p.final_risk)}, {p.risk_level}
                    </span>
                  </Link>
                ))}
              </div>
            </div>

            {dashboard.recommendation && (
              <div className="card">
                <p className="section-label">행동 권고</p>
                <p className="font-medium text-ink mb-2">{dashboard.recommendation.title}</p>
                <p className="text-sm text-ink-secondary whitespace-pre-line mb-4 leading-relaxed">
                  {dashboard.recommendation.reason}
                </p>
                <ol className="space-y-2">
                  {dashboard.recommendation.action_list?.map((a, i) => (
                    <li key={i} className="flex gap-3 text-sm text-ink-secondary">
                      <span className="text-ink-muted font-mono text-xs mt-0.5">{String(i + 1).padStart(2, '0')}</span>
                      {a}
                    </li>
                  ))}
                </ol>
              </div>
            )}
          </div>

          {dashboard.alerts.length > 0 && (
            <div className="card">
              <p className="card-title">최근 알림</p>
              <AlertList alerts={dashboard.alerts} emptyText="최근 알림이 없습니다" />
            </div>
          )}

          <div className="flex gap-3 flex-wrap pt-2">
            <Link href={`/fields/${selectedId}`} className="btn-primary">필지 상세</Link>
            <button
              onClick={() => selectedId && Promise.all([
                api.collect(selectedId),
                api.getDashboard(selectedId),
                api.getInsights(selectedId),
              ]).then(([, d, ins]) => { setDashboard(d); setInsights(ins); })}
              className="btn-secondary"
            >
              새로고침
            </button>
          </div>
        </>
      )}

      {showShare && insights?.weekly_report && selectedId && (
        <ShareReportModal report={insights.weekly_report} fieldId={selectedId} onClose={() => setShowShare(false)} />
      )}
    </div>
  );
}
