'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';
import { api, CropProfile } from '@/lib/api';
import { FALLBACK_CROPS, loadCrops } from '@/lib/crops';
import PageHeader from '@/components/PageHeader';

const FieldMap = dynamic(() => import('@/components/FieldMap'), { ssr: false });

export default function RegisterFieldPage() {
  const router = useRouter();
  const [lat, setLat] = useState<number | null>(null);
  const [lng, setLng] = useState<number | null>(null);
  const [crop, setCrop] = useState('고추');
  const [crops, setCrops] = useState<CropProfile[]>(FALLBACK_CROPS);
  const [plantingDate, setPlantingDate] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadCrops(() => api.getCrops()).then(setCrops).catch(() => setCrops(FALLBACK_CROPS));
  }, []);

  const selected = crops.find((c) => c.name_ko === crop);

  const handleSubmit = async () => {
    if (lat === null || lng === null) {
      setError('지도에서 필지 위치를 선택해주세요');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const field = await api.registerField({
        lat, lng, crop_name: crop,
        planting_date: plantingDate || undefined,
      });
      router.push(`/dashboard?field=${field.field_id}`);
    } catch {
      setError('필지 등록에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto space-y-6">
      <PageHeader
        title="필지 등록"
        desc="지도에서 위치를 선택하면 팜맵 API로 필지 정보를 자동 조회합니다"
        breadcrumb={[{ label: '필지등록' }]}
      />

      <div className="card space-y-5">
        <FieldMap onSelect={(la, ln) => { setLat(la); setLng(ln); }} marker={lat && lng ? [lat, lng] : null} />
        {lat && lng && (
          <p className="text-xs text-ink-muted font-mono">{lat.toFixed(5)}, {lng.toFixed(5)}</p>
        )}

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-ink-muted mb-2 uppercase tracking-wider">작물</label>
            <select value={crop} onChange={(e) => setCrop(e.target.value)} className="input-field">
              {crops.map((c) => (
                <option key={c.id} value={c.name_ko}>{c.name_ko} ({c.category})</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-ink-muted mb-2 uppercase tracking-wider">재배 시작일</label>
            <input type="date" value={plantingDate} onChange={(e) => setPlantingDate(e.target.value)} className="input-field" />
          </div>
        </div>

        {selected && (
          <div className="rounded-xl bg-surface-muted p-4 text-sm">
            <p className="text-xs text-ink-muted uppercase tracking-wider mb-2">모니터링 병해충</p>
            <div className="flex flex-wrap gap-2">
              {selected.target_pests.map((p) => (
                <span key={p} className="px-2.5 py-1 rounded-full bg-white text-xs ring-1 ring-border-light">{p}</span>
              ))}
            </div>
          </div>
        )}

        {error && <p className="text-red-600 text-sm">{error}</p>}

        <button onClick={handleSubmit} disabled={loading} className="btn-primary w-full disabled:opacity-40">
          {loading ? '등록 중...' : '필지 등록'}
        </button>
      </div>

      <div className="card-flat">
        <p className="section-label">자동 수집 데이터</p>
        <ul className="text-sm text-ink-secondary space-y-2">
          <li>팜맵 조회: fmapInnb, PNU, 논/밭</li>
          <li>농업기상: 온도, 습도, 강수, 결로</li>
          <li>토양검정: 산도, 유기물, EC</li>
          <li>작물별 병해충 위험도: {selected?.target_pests.length ?? 3}종</li>
        </ul>
      </div>
    </div>
  );
}
