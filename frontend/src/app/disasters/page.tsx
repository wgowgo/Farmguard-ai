'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api, CropProfile, DisasterCenter, Field } from '@/lib/api';
import { FALLBACK_CROPS, loadCrops } from '@/lib/crops';
import PageHeader from '@/components/PageHeader';

const LEVEL_STYLE: Record<string, string> = {
  경보: 'bg-red-100 text-red-800 ring-red-200',
  주의: 'bg-amber-100 text-amber-900 ring-amber-200',
};

export default function DisastersPage() {
  const [fields, setFields] = useState<Field[]>([]);
  const [crops, setCrops] = useState<CropProfile[]>(FALLBACK_CROPS);
  const [fieldId, setFieldId] = useState<number | ''>('');
  const [crop, setCrop] = useState('고추');
  const [data, setData] = useState<DisasterCenter | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.getFields(), loadCrops(() => api.getCrops())]).then(([f, c]) => {
      setFields(f);
      setCrops(c);
      if (f.length > 0) setFieldId(f[0].field_id);
    }).catch(console.error);
  }, []);

  useEffect(() => {
    setLoading(true);
    const p = fieldId
      ? api.getDisasters(fieldId as number)
      : api.getDisasters(undefined, crop);
    p.then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [fieldId, crop]);

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <PageHeader
        title="재해 예방 센터"
        desc="기상청 예보 + 작물별 재해 대비 체크리스트"
        breadcrumb={[{ label: '재해예방' }]}
      />

      <div className="card flex flex-wrap gap-4">
        <div className="flex-1 min-w-[140px]">
          <label className="block text-xs text-ink-muted mb-2">필지 (KMA 연동)</label>
          <select
            className="input-field"
            value={fieldId}
            onChange={(e) => setFieldId(e.target.value ? Number(e.target.value) : '')}
          >
            <option value="">필지 없음</option>
            {fields.map((f) => (
              <option key={f.field_id} value={f.field_id}>{f.crop_name}, {f.address?.slice(0, 14)}</option>
            ))}
          </select>
        </div>
        <div className="flex-1 min-w-[140px]">
          <label className="block text-xs text-ink-muted mb-2">작물</label>
          <select className="input-field" value={crop} onChange={(e) => setCrop(e.target.value)} disabled={!!fieldId}>
            {crops.map((c) => <option key={c.id} value={c.name_ko}>{c.name_ko}</option>)}
          </select>
        </div>
      </div>

      {loading || !data ? (
        <div className="flex justify-center py-20">
          <div className="spinner" />
        </div>
      ) : (
        <>
          <div className="card">
            <p className="section-label">요약</p>
            <p className="text-sm text-ink-secondary leading-relaxed">{data.summary}</p>
            {data.priority_alert && (
              <div className="mt-4 p-4 rounded-xl bg-amber-50 border border-amber-100">
                <div className="flex justify-between gap-2">
                  <p className="font-medium text-sm">{data.priority_alert.title}</p>
                  <span className={`text-[10px] px-2 py-0.5 rounded-full ring-1 ${LEVEL_STYLE[data.priority_alert.level] || ''}`}>
                    {data.priority_alert.level}
                  </span>
                </div>
                <p className="text-xs text-ink-secondary mt-1">{data.priority_alert.message}</p>
              </div>
            )}
          </div>

          {data.weather_hazards.length > 0 && (
            <div className="card">
              <p className="section-label">기상청 재해 예보 (5일)</p>
              <div className="space-y-2">
                {data.weather_hazards.map((h, i) => (
                  <div key={i} className="flex justify-between items-center p-3 rounded-xl bg-surface-muted text-sm">
                    <div>
                      <p className="font-medium">{h.title} <span className="text-ink-muted font-normal">({h.label})</span></p>
                      <p className="text-xs text-ink-secondary mt-0.5">{h.message}</p>
                    </div>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full ring-1 shrink-0 ${LEVEL_STYLE[h.level] || ''}`}>
                      {h.level}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="card">
            <p className="section-label">{data.crop_name} 재해 체크리스트</p>
            <div className="space-y-3">
              {data.checklists.map((c) => (
                <div key={c.id} className="p-4 rounded-xl border border-border-light">
                  <p className="font-medium text-sm">{c.title}</p>
                  <p className="text-xs text-ink-secondary mt-1 leading-relaxed">{c.actions}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="card">
            <p className="section-label">재해 예방 자료</p>
            <ul className="space-y-2">
              {data.articles.map((a, i) => (
                <li key={i} className="p-3 rounded-xl bg-surface-muted text-sm">
                  <p className="font-medium">{a.title}</p>
                  <p className="text-xs text-ink-secondary mt-1">{a.body}</p>
                </li>
              ))}
            </ul>
          </div>
        </>
      )}

      <Link href="/dashboard" className="btn-secondary inline-block">← 대시보드</Link>
    </div>
  );
}
