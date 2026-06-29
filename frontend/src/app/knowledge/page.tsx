'use client';

import { useCallback, useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { FALLBACK_CROPS, loadCrops } from '@/lib/crops';
import PageHeader from '@/components/PageHeader';

const NONGSARO_DEFAULTS = [
  { code: 'dbyhsCccrrncInfo', name: '병해충발생정보' },
  { code: 'healthEduGymMovInfo', name: '건강안전정보' },
  { code: 'openApiData', name: '공공데이터' },
  { code: 'relatedSite', name: '관련 사이트' },
  { code: 'agchmQltinsp', name: '농약 품질검사' },
  { code: 'pesticideRegStatus', name: '농약등록현황' },
  { code: 'agchmSafeManual', name: '농약안전사용지침' },
  { code: 'frcDsstrPrevnt', name: '농작물재해예방정보' },
];

export default function KnowledgePage() {
  const [query, setQuery] = useState('탄저병');
  const [crop, setCrop] = useState('고추');
  const [cropOptions, setCropOptions] = useState<string[]>(FALLBACK_CROPS.map((c) => c.name_ko));
  const [searchResult, setSearchResult] = useState<Record<string, unknown> | null>(null);
  const [nongsaro, setNongsaro] = useState<Record<string, unknown> | null>(null);
  const [nongsaroSvc, setNongsaroSvc] = useState('dbyhsCccrrncInfo');
  const [nongsaroResult, setNongsaroResult] = useState<Record<string, unknown> | null>(null);
  const [services, setServices] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.getKnowledgeServices().then(setServices).catch(console.error);
    api.getNongsaroDbyhs('', '고추').then(setNongsaro).catch(console.error);
    loadCrops(() => api.getCrops()).then((list) => setCropOptions(list.map((c) => c.name_ko))).catch(console.error);
  }, []);

  const handleSearch = useCallback(async () => {
    setLoading(true);
    try {
      const r = await api.knowledgeSearch(query, crop);
      setSearchResult(r);
    } finally {
      setLoading(false);
    }
  }, [query, crop]);

  const handleNongsaroCall = async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (nongsaroSvc === 'dbyhsCccrrncInfo') params.sText = query;
      if (nongsaroSvc === 'pesticideRegStatus') {
        params.cropName = crop;
        params.diseaseWeedName = query;
      }
      if (nongsaroSvc === 'agchmSafeManual') params.sCropNm = crop;
      const r = await api.nongsaroCall(nongsaroSvc, '', params);
      setNongsaroResult(r);
    } finally {
      setLoading(false);
    }
  };

  const svcList = (services?.nongsaro as { code: string; name: string }[]) || NONGSARO_DEFAULTS;

  return (
    <div className="space-y-6 max-w-4xl">
      <PageHeader
        title="농업 지식 허브"
        desc="농사로 8종, 토양/비료, 팜맵, 기상청 연동"
        breadcrumb={[{ label: '지식허브' }]}
      />

      <div className="card space-y-4">
        <p className="section-label">통합 검색</p>
        <div className="flex flex-wrap gap-2">
          <select className="input-field flex-1 min-w-[120px]" value={crop} onChange={(e) => setCrop(e.target.value)}>
            {cropOptions.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
          <input className="input-field flex-[2] min-w-[160px]" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="병해충, 키워드" />
          <button onClick={handleSearch} disabled={loading} className="btn-primary text-sm">검색</button>
        </div>
        {searchResult && (
          <div className="grid md:grid-cols-2 gap-4 mt-4">
            <div className="p-4 bg-surface-muted rounded-xl">
              <p className="text-xs font-medium text-ink-muted mb-2">농사로 발생정보</p>
              <ul className="text-sm space-y-1">
                {((searchResult.nongsaro_occurrence as Record<string, unknown>[]) || []).slice(0, 5).map((item, i) => (
                  <li key={i}>{String(item.cntntsSj || item.title || '-')}</li>
                ))}
              </ul>
            </div>
            <div className="p-4 bg-surface-muted rounded-xl">
              <p className="text-xs font-medium text-ink-muted mb-2">농약 등록현황</p>
              <ul className="text-sm space-y-1">
                {((searchResult.pesticide_registration as Record<string, unknown>[]) || []).slice(0, 5).map((item, i) => (
                  <li key={i}>
                    {String(item.pestiBrandName || item.cropName || '-')}
                    {item.diseaseWeedName ? `, ${String(item.diseaseWeedName)}` : ''}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>

      <div className="card space-y-4">
        <p className="section-label">농사로 API (8종)</p>
        <select className="input-field w-full" value={nongsaroSvc} onChange={(e) => setNongsaroSvc(e.target.value)}>
          {svcList.map((s) => (
            <option key={s.code} value={s.code}>{s.name}</option>
          ))}
        </select>
        <button onClick={handleNongsaroCall} disabled={loading} className="btn-secondary text-sm">API 호출</button>
        {nongsaroResult && (
          <pre className="text-xs bg-surface-muted p-4 rounded-xl overflow-auto max-h-64">
            {JSON.stringify(nongsaroResult, null, 2)}
          </pre>
        )}
      </div>

      <div className="card">
        <p className="section-label">최근 병해충 발생 뉴스</p>
        <ul className="text-sm space-y-2">
          {((nongsaro?.items as Record<string, unknown>[]) || []).slice(0, 8).map((item, i) => (
            <li key={i} className="flex justify-between p-3 bg-surface-muted rounded-xl">
              <span>{String(item.cntntsSj || '-')}</span>
              <span className="text-ink-muted text-xs">{String(item.registDt || '')}</span>
            </li>
          ))}
        </ul>
      </div>

      {services && (
        <div className="card-flat text-xs text-ink-muted">
          연동: 농사로 {svcList.length}종, 토양/비료 {((services.soil as unknown[]) || []).length}종 , 
          팜맵 {((services.farmmap as unknown[]) || []).length}종, 기상청 {((services.kma as unknown[]) || []).length}종
        </div>
      )}
    </div>
  );
}
