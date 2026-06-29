'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { api } from '@/lib/api';
import FertilizerCalendarCard, { FertilizerCalendar } from '@/components/FertilizerCalendarCard';
import WeatherTimelineCard, { WeatherTimeline } from '@/components/WeatherTimelineCard';
import PageHeader from '@/components/PageHeader';

export default function FieldDetailPage() {
  const params = useParams();
  const fieldId = Number(params.id);
  const [detail, setDetail] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    api.getFieldDetail(fieldId).then(setDetail).catch(console.error);
  }, [fieldId]);

  if (!detail) {
    return (
      <div className="flex items-center justify-center py-32">
        <div className="spinner" />
      </div>
    );
  }

  const field = detail.field as Record<string, unknown>;
  const soil = detail.soil as Record<string, unknown> | null;
  const enrichment = detail.enrichment as Record<string, unknown> | null;
  const soilV2 = (enrichment?.soil_chem_v2 as Record<string, unknown>[])?.[0];
  const fertilizer = enrichment?.fertilizer as Record<string, unknown> | null;
  const weather = detail.weather_summary as Record<string, unknown>[];
  const pests = detail.pests as Record<string, unknown>[];
  const fertilizerCalendar = detail.fertilizer_calendar as FertilizerCalendar | null;
  const weatherTimeline = detail.weather_timeline as WeatherTimeline | null;

  return (
    <div className="space-y-6">
      <PageHeader
        title="필지 상세"
        desc={field.address as string}
        breadcrumb={[{ label: '대시보드', href: '/' }, { label: '필지 상세' }]}
        actions={<Link href="/dashboard" className="btn-secondary no-underline">← 대시보드</Link>}
      />

      <div className="grid md:grid-cols-2 gap-5">
        <div className="card">
          <p className="section-label">필지 정보</p>
          <dl className="space-y-3 text-sm">
            {([
              ['작물', field.crop_name],
              ['논/밭', field.land_type],
              ['팜맵 ID', field.fmap_innb],
            ] as [string, unknown][]).map(([label, val]) => (
              <div key={String(label)} className="flex justify-between py-2 border-b border-border-light last:border-0">
                <dt className="text-ink-muted">{label}</dt>
                <dd className="font-medium font-mono text-xs">{String(val)}</dd>
              </div>
            ))}
          </dl>
        </div>

        <div className="card">
          <p className="section-label">토양</p>
          {soil ? (
            <dl className="space-y-3 text-sm">
              {([
                ['검정년도', `${soil.year}년`],
                ['산도', soil.acidity],
                ['유기물', `${soil.organic_matter}%`],
                ['EC', soil.ec],
                ['유효인산', `${soil.phosphate} mg/kg`],
              ] as [string, unknown][]).map(([label, val]) => (
                <div key={String(label)} className="flex justify-between py-2 border-b border-border-light last:border-0">
                  <dt className="text-ink-muted">{label}</dt>
                  <dd className="font-medium tabular-nums">{String(val)}</dd>
                </div>
              ))}
            </dl>
          ) : (
            <p className="text-ink-muted text-sm">데이터 없음</p>
          )}
        </div>
      </div>

      {(soilV2 || (fertilizer && Object.keys(fertilizer).length > 0)) && (
        <div className="card">
          <p className="section-label">흙토람 토양, 비료 (실시간 API)</p>
          <div className="grid md:grid-cols-2 gap-6 text-sm">
            {soilV2 && (
              <dl className="space-y-2">
                <p className="text-xs text-ink-muted mb-2">토양검정 V2</p>
                {([
                  ['검정연도', soilV2.Any_Year],
                  ['산도 pH', soilV2.ACID],
                  ['유기물', soilV2.OM],
                  ['유효인산', soilV2.VLDPHA],
                ] as [string, unknown][]).map(([label, val]) => (
                  <div key={String(label)} className="flex justify-between py-1">
                    <dt className="text-ink-muted">{label}</dt>
                    <dd className="font-medium tabular-nums">{String(val ?? '-')}</dd>
                  </div>
                ))}
              </dl>
            )}
            {fertilizer && Object.keys(fertilizer).length > 0 && (
              <dl className="space-y-2">
                <p className="text-xs text-ink-muted mb-2">비료사용처방</p>
                {([
                  ['작물', fertilizer.crop_Nm],
                  ['질소(기비)', fertilizer.pre_Fert_N],
                  ['인산(기비)', fertilizer.pre_Fert_P],
                  ['칼리(기비)', fertilizer.pre_Fert_K],
                ] as [string, unknown][]).filter(([, v]) => v != null && v !== '').map(([label, val]) => (
                  <div key={String(label)} className="flex justify-between py-1">
                    <dt className="text-ink-muted">{label}</dt>
                    <dd className="font-medium tabular-nums">{String(val)}</dd>
                  </div>
                ))}
              </dl>
            )}
          </div>
        </div>
      )}

      {weatherTimeline && weatherTimeline.points?.length > 0 && (
        <WeatherTimelineCard data={weatherTimeline} />
      )}

      {fertilizerCalendar && (
        <FertilizerCalendarCard data={fertilizerCalendar} />
      )}

      <div className="card overflow-x-auto">
        <p className="section-label">기상 스냅샷 (6시간)</p>
        <table className="w-full text-sm">
          <thead>
            <tr className="table-head">
              <th className="pr-4">시간</th>
              <th className="pr-4">기온</th>
              <th className="pr-4">습도</th>
              <th className="pr-4">강수</th>
              <th className="pr-4">토양수분</th>
              <th>결로</th>
            </tr>
          </thead>
          <tbody>
            {weather?.map((w, i) => (
              <tr key={i} className="table-cell">
                <td className="pr-4">{String(w.time).slice(11, 16)}</td>
                <td className="pr-4">{w.temp as number}°</td>
                <td className="pr-4">{w.humidity as number}%</td>
                <td className="pr-4">{w.rain as number}mm</td>
                <td className="pr-4">{w.soil_moisture as number}%</td>
                <td>{w.dew_time as number}h</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <p className="section-label">병해충 발생</p>
        <div className="space-y-1">
          {pests?.map((p, i) => (
            <Link
              key={i}
              href={`/fields/${fieldId}/pest/${encodeURIComponent(p.name as string)}`}
              className="flex justify-between items-center p-4 -mx-2 rounded-xl hover:bg-surface-muted transition-colors"
            >
              <span className="font-medium text-sm">{p.name as string}</span>
              <span className="text-xs text-ink-muted">
                {p.distance_km as number}km, {p.value as number}
              </span>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
