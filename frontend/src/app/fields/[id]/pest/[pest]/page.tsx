'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import RiskBadge from '@/components/RiskBadge';
import SprayPrescriptionCard, { SprayPrescription } from '@/components/SprayPrescriptionCard';
import PageHeader from '@/components/PageHeader';

export default function PestDetailPage() {
  const params = useParams();
  const fieldId = Number(params.id);
  const pestName = decodeURIComponent(params.pest as string);
  const [data, setData] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    import('@/lib/api').then(({ api }) =>
      api.getPestDetail(fieldId, pestName).then(setData).catch(console.error)
    );
  }, [fieldId, pestName]);

  if (!data) {
    return (
      <div className="flex items-center justify-center py-32">
        <div className="spinner" />
      </div>
    );
  }

  const rec = data.recommendation as Record<string, unknown> | null;
  const occurrences = data.occurrences as Record<string, unknown>[];
  const knowledge = data.knowledge as Record<string, unknown> | null;
  const prescriptions = (data.spray_prescriptions as SprayPrescription[])
    || (knowledge?.spray_prescriptions as SprayPrescription[])
    || [];
  const news = (knowledge?.nongsaro_occurrence as Record<string, unknown>[]) || [];

  return (
    <div className="space-y-6 max-w-2xl">
      <PageHeader
        title={pestName}
        desc="병해충 위험 상세"
        breadcrumb={[
          { label: '대시보드', href: '/' },
          { label: '필지', href: `/fields/${fieldId}` },
          { label: pestName },
        ]}
        actions={<Link href={`/fields/${fieldId}`} className="btn-secondary no-underline">← 필지</Link>}
      />

      <div className="card">
        <RiskBadge score={data.final_risk as number} level={data.risk_level as string} />
        <div className="grid grid-cols-3 gap-3 mt-6">
          {[
            { label: '기상', value: data.weather_risk },
            { label: '예찰', value: data.pest_risk },
            { label: '토양', value: data.soil_risk },
          ].map((item) => (
            <div key={item.label} className="p-4 bg-surface-muted rounded-xl text-center">
              <p className="text-xs text-ink-muted mb-1">{item.label}</p>
              <p className="text-2xl font-semibold tabular-nums">{Math.round(item.value as number)}</p>
            </div>
          ))}
        </div>
      </div>

      {knowledge?.symptoms ? (
        <div className="card">
          <p className="section-label">병해충 정보</p>
          <p className="text-sm text-ink-secondary mb-2">
            <span className="text-ink-muted">증상, </span>{String(knowledge.symptoms)}
          </p>
          {knowledge.environment ? (
            <p className="text-sm text-ink-secondary">
              <span className="text-ink-muted">발생환경, </span>{String(knowledge.environment)}
            </p>
          ) : null}
        </div>
      ) : null}

      {rec && (
        <div className="card">
          <p className="section-label">위험 원인</p>
          <p className="text-sm text-ink-secondary whitespace-pre-line mb-6 leading-relaxed">{rec.reason as string}</p>
          <p className="section-label">권장 행동</p>
          <ol className="space-y-2">
            {(rec.action_list as string[])?.map((a, i) => (
              <li key={i} className="flex gap-3 text-sm text-ink-secondary">
                <span className="text-ink-muted font-mono text-xs">{String(i + 1).padStart(2, '0')}</span>
                {a}
              </li>
            ))}
          </ol>
        </div>
      )}

      <SprayPrescriptionCard items={prescriptions} />

      <div className="card">
        <p className="section-label">주변 발생 (팜맵)</p>
        {occurrences?.length ? (
          <div className="space-y-2">
            {occurrences.map((o, i) => (
              <div key={i} className="flex justify-between text-sm p-3 bg-surface-muted rounded-xl">
                <span>{o.distance_km as number}km</span>
                <span>강도 {o.value as number}</span>
                <span className="text-ink-muted">{o.report_date as string}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-ink-muted text-sm">기록 없음</p>
        )}
      </div>

      {news.length > 0 && (
        <div className="card">
          <p className="section-label">농사로 발생 뉴스</p>
          <ul className="text-sm space-y-2">
            {news.slice(0, 3).map((n, i) => (
              <li key={i} className="p-3 bg-surface-muted rounded-xl">{String(n.cntntsSj || n.title)}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="card-flat">
        <p className="text-xs text-ink-muted">
          팜맵, 기상청, 농사로, 토양/비료 API 연동
        </p>
      </div>
    </div>
  );
}
