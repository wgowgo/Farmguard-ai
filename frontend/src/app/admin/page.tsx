'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { api, AdminDashboard, AdminField, RiskLog, ApiLog, riskColor, CropProfile } from '@/lib/api';
import { FALLBACK_CROPS, loadCrops } from '@/lib/crops';
import PageHeader from '@/components/PageHeader';

type Tab = 'overview' | 'api' | 'fields' | 'risk' | 'logs';

const TABS: { id: Tab; label: string }[] = [
  { id: 'overview', label: '개요' },
  { id: 'api', label: 'API 연동' },
  { id: 'fields', label: '필지 관리' },
  { id: 'risk', label: '위험도 로그' },
  { id: 'logs', label: '호출 로그' },
];

function StatusDot({ status }: { status: string }) {
  const color =
    status === 'success' ? 'bg-green-500' :
    status === 'error' ? 'bg-red-500' :
    'bg-gray-300';
  return <span className={`inline-block w-2.5 h-2.5 rounded-full ${color}`} />;
}

export default function AdminPage() {
  const [tab, setTab] = useState<Tab>('overview');
  const [dashboard, setDashboard] = useState<AdminDashboard | null>(null);
  const [fields, setFields] = useState<AdminField[]>([]);
  const [riskLogs, setRiskLogs] = useState<RiskLog[]>([]);
  const [logs, setLogs] = useState<ApiLog[]>([]);
  const [crops, setCrops] = useState<CropProfile[]>(FALLBACK_CROPS);
  const [loading, setLoading] = useState(true);
  const [collecting, setCollecting] = useState(false);
  const [message, setMessage] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [d, f, r, l, cropList] = await Promise.all([
        api.getAdminDashboard(),
        api.getAdminFields(),
        api.getRiskLogs(),
        api.getLogs(),
        loadCrops(() => api.getCrops()),
      ]);
      setDashboard(d);
      setFields(f);
      setRiskLogs(r);
      setLogs(l);
      setCrops(cropList);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleCollectAll = async () => {
    setCollecting(true);
    setMessage('');
    try {
      const r = await api.collectAll();
      setMessage(`${r.collected}개 필지 데이터 수집 완료`);
      await load();
    } catch {
      setMessage('수집 중 오류 발생');
    } finally {
      setCollecting(false);
    }
  };

  const handleCollectOne = async (fieldId: number) => {
    try {
      await api.collect(fieldId);
      setMessage(`필지 #${fieldId} 수집 완료`);
      await load();
    } catch {
      setMessage(`필지 #${fieldId} 수집 실패`);
    }
  };

  const handleDemoToggle = async (enabled: boolean) => {
    try {
      const r = await api.setDemoMode(enabled);
      setMessage(r.message);
      await load();
    } catch {
      setMessage('모드 전환 실패');
    }
  };

  if (loading && !dashboard) {
    return (
      <div className="flex items-center justify-center py-32">
        <div className="spinner" />
      </div>
    );
  }

  const stats = dashboard?.stats;
  const system = dashboard?.system;
  const cropNames = system?.crop_names?.length
    ? system.crop_names
    : crops.map((c) => c.name_ko);
  const cropCount = system?.supported_crops ?? crops.length;
  const cropPreview = cropNames.slice(0, 4).join(', ');
  const cropSuffix = cropNames.length > 4 ? '…' : '';

  return (
    <div className="space-y-6">
      <PageHeader
        title="관리"
        desc="API 연동, 파이프라인, 위험도 모니터링"
        breadcrumb={[{ label: '관리' }]}
        actions={
          <>
            <button onClick={load} className="btn-secondary text-sm">새로고침</button>
            <button
              onClick={handleCollectAll}
              disabled={collecting || fields.length === 0}
              className="btn-primary text-sm disabled:opacity-40"
            >
              {collecting ? '수집 중...' : '전체 수집'}
            </button>
          </>
        }
      />

      {message && <div className="info-banner">{message}</div>}

      {system && (
        <div className="card flex flex-wrap items-center justify-between gap-6">
          <div className="flex flex-wrap gap-8 text-sm">
            {[
              { label: '모드', value: system.demo_mode ? '데모' : '실 API' },
              { label: 'DB', value: system.database },
              { label: '모델', value: system.model_version },
              { label: '지원 작물', value: `${cropCount}종, ${cropPreview}${cropSuffix}` },
              { label: 'API', value: dashboard?.pipeline.api_connected },
            ].map((item) => (
              <div key={item.label}>
                <p className="text-xs text-ink-muted uppercase tracking-wider">{item.label}</p>
                <p className="font-medium mt-0.5">{item.value}</p>
              </div>
            ))}
          </div>
          <div className="flex gap-2 p-1 bg-surface-muted rounded-xl">
            <button
              onClick={() => handleDemoToggle(true)}
              className={`px-4 py-2 rounded-lg text-xs font-medium transition ${
                system.demo_mode ? 'bg-white shadow-sm text-ink' : 'text-ink-muted hover:text-ink'
              }`}
            >
              데모
            </button>
            <button
              onClick={() => handleDemoToggle(false)}
              className={`px-4 py-2 rounded-lg text-xs font-medium transition ${
                !system.demo_mode ? 'bg-white shadow-sm text-ink' : 'text-ink-muted hover:text-ink'
              }`}
            >
              실 API
            </button>
          </div>
        </div>
      )}

      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {[
            { label: '등록 필지', value: stats.field_count },
            { label: 'API 호출', value: stats.api_log_count },
            { label: '기상', value: stats.weather_records },
            { label: '토양', value: stats.soil_records },
            { label: '병해충', value: stats.pest_records },
            { label: '고위험', value: stats.high_risk_today },
          ].map((k) => (
            <div key={k.label} className="card py-5 text-center">
              <p className="stat-value">{k.value}</p>
              <p className="stat-label">{k.label}</p>
            </div>
          ))}
        </div>
      )}

      <div className="portal-tabs">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={tab === t.id ? 'portal-tab-active' : 'portal-tab'}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab: Overview */}
      {tab === 'overview' && dashboard && (
        <div className="grid md:grid-cols-2 gap-4">
          <div className="card">
            <h3 className="font-semibold mb-4">데이터 파이프라인</h3>
            <div className="space-y-3">
              {['필지 등록', '공공 API 수집', '정규화, Feature', '위험도 산출', '설명 카드 생성'].map((step, i) => (
                <div key={step} className="flex items-center gap-3">
                  <span className="w-7 h-7 rounded-lg bg-surface-subtle text-ink-secondary text-xs flex items-center justify-center font-medium">
                    {i + 1}
                  </span>
                  <span className="text-sm">{step}</span>
                  <StatusDot status={i < 3 && stats && stats.field_count > 0 ? 'success' : 'unknown'} />
                </div>
              ))}
            </div>
          </div>

          <div className="card">
            <h3 className="font-semibold mb-4">API 레이어 상태</h3>
            <div className="space-y-2">
              {dashboard.pipeline.data_layers.map((layer) => (
                <div key={layer.name} className="flex items-center justify-between p-3 bg-surface-muted rounded-xl text-sm">
                  <div className="flex items-center gap-2">
                    <StatusDot status={layer.status} />
                    <span>{layer.name}</span>
                  </div>
                  <span className={`text-xs font-medium ${
                    layer.status === 'success' ? 'text-emerald-600' : 'text-ink-muted'
                  }`}>
                    {layer.status === 'success' ? '연동됨' : layer.status === 'unknown' ? '대기' : layer.status}
                  </span>
                </div>
              ))}
            </div>
            {dashboard.pipeline.last_collection && (
              <p className="text-xs text-ink-muted mt-3">
                마지막 수집: {new Date(dashboard.pipeline.last_collection).toLocaleString('ko-KR')}
              </p>
            )}
          </div>

          <div className="card md:col-span-2">
            <h3 className="font-semibold mb-3">지원 작물 ({cropCount}종)</h3>
            <div className="flex flex-wrap gap-2">
              {cropNames.map((name) => (
                <span key={name} className="px-2.5 py-1 rounded-full bg-surface-muted text-xs ring-1 ring-border-light">
                  {name}
                </span>
              ))}
            </div>
          </div>

          <div className="card md:col-span-2">
            <h3 className="font-semibold mb-3">데이터 출처 (심사 증빙)</h3>
            <div className="grid md:grid-cols-2 gap-4 text-sm text-ink-secondary">
              <ul className="space-y-1">
                <li>• 팜맵 조회 서비스: 필지 식별 (fmapInnb)</li>
                <li>• 팜맵기반 농업기상: 시간별 기상 피처</li>
                <li>• 팜맵기반 토양검정: 토양 취약성</li>
              </ul>
              <ul className="space-y-1">
                <li>• 팜맵기반 병해충발생: 예찰 prior</li>
                <li>• 기상청 단기예보: 알림 보강</li>
                <li>• 제공: 농림축산식품부, 기상청 / data.go.kr</li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Tab: API */}
      {tab === 'api' && dashboard && (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="table-head">
                <th className="pb-3 pr-4">API</th>
                <th className="pb-3 pr-4">라이선스</th>
                <th className="pb-3 pr-4">상업 이용</th>
                <th className="pb-3 pr-4">마지막 호출</th>
                <th className="pb-3">상태</th>
              </tr>
            </thead>
            <tbody>
              {dashboard.sources.map((s) => (
                <tr key={s.source_name} className="border-b border-border-light">
                  <td className="py-3 pr-4 font-medium">{s.source_name}</td>
                  <td className="py-3 pr-4 text-ink-muted">{s.license_type || '-'}</td>
                  <td className="py-3 pr-4">{s.commercial_allowed ? '✓ 가능' : '✗ 제한'}</td>
                  <td className="py-3 pr-4 text-xs text-ink-muted">
                    {s.last_called_at ? new Date(s.last_called_at).toLocaleString('ko-KR') : '미호출'}
                  </td>
                  <td className="py-3">
                    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-semibold ${
                      s.last_status === 'success' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-surface-subtle text-ink-secondary border border-border'
                    }`}>
                      <StatusDot status={s.last_status} />
                      {s.last_status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Tab: Fields */}
      {tab === 'fields' && (
        <div className="card overflow-x-auto">
          {fields.length === 0 ? (
            <div className="text-center py-10">
              <p className="text-ink-muted mb-3">등록된 필지가 없습니다</p>
              <Link href="/fields/register" className="btn-primary inline-block text-sm">필지 등록</Link>
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="table-head">
                  <th className="pb-3 pr-4">ID</th>
                  <th className="pb-3 pr-4">주소</th>
                  <th className="pb-3 pr-4">작물</th>
                  <th className="pb-3 pr-4">팜맵 ID</th>
                  <th className="pb-3 pr-4">기상</th>
                  <th className="pb-3 pr-4">최고 위험</th>
                  <th className="pb-3">액션</th>
                </tr>
              </thead>
              <tbody>
                {fields.map((f) => (
                  <tr key={f.field_id} className="border-b border-border-light">
                    <td className="py-3 pr-4 font-mono text-xs">#{f.field_id}</td>
                    <td className="py-3 pr-4">{f.address?.slice(0, 20) || '-'}</td>
                    <td className="py-3 pr-4">{f.crop_name}</td>
                    <td className="py-3 pr-4 font-mono text-xs">{f.fmap_innb}</td>
                    <td className="py-3 pr-4">{f.weather_records}건</td>
                    <td className="py-3 pr-4">
                      {f.top_risk ? (
                        <span className={`px-2 py-0.5 rounded text-xs font-semibold ${riskColor(f.top_risk.risk_level)}`}>
                          {f.top_risk.pest_name} {Math.round(f.top_risk.final_risk)}점
                        </span>
                      ) : '-'}
                    </td>
                    <td className="py-3 flex gap-2">
                      <button
                        onClick={() => handleCollectOne(f.field_id)}
                        className="text-xs text-ink hover:underline"
                      >
                        수집
                      </button>
                      <Link href={`/fields/${f.field_id}`} className="text-xs text-ink-secondary hover:underline">
                        상세
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Tab: Risk logs */}
      {tab === 'risk' && (
        <div className="card overflow-x-auto">
          <h3 className="font-semibold mb-4">위험도 계산 로그</h3>
          {riskLogs.length === 0 ? (
            <p className="text-ink-muted text-sm py-6 text-center">위험도 계산 기록 없음</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="table-head">
                  <th className="pb-3 pr-3">날짜</th>
                  <th className="pb-3 pr-3">필지</th>
                  <th className="pb-3 pr-3">병해충</th>
                  <th className="pb-3 pr-3">기상</th>
                  <th className="pb-3 pr-3">예찰</th>
                  <th className="pb-3 pr-3">토양</th>
                  <th className="pb-3 pr-3">최종</th>
                  <th className="pb-3">단계</th>
                </tr>
              </thead>
              <tbody>
                {riskLogs.map((r) => (
                  <tr key={r.id} className="border-b border-border-light">
                    <td className="py-2.5 pr-3 text-xs">{r.date}</td>
                    <td className="py-2.5 pr-3 text-xs truncate max-w-[120px]">{r.address || `#${r.field_id}`}</td>
                    <td className="py-2.5 pr-3 font-medium">{r.pest_name}</td>
                    <td className="py-2.5 pr-3">{Math.round(r.weather_risk ?? 0)}</td>
                    <td className="py-2.5 pr-3">{Math.round(r.pest_risk ?? 0)}</td>
                    <td className="py-2.5 pr-3">{Math.round(r.soil_risk ?? 0)}</td>
                    <td className="py-2.5 pr-3 font-bold">{Math.round(r.final_risk ?? 0)}</td>
                    <td className="py-2.5">
                      <span className={`px-2 py-0.5 rounded text-xs font-semibold ${riskColor(r.risk_level)}`}>
                        {r.risk_level}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Tab: API logs */}
      {tab === 'logs' && (
        <div className="card">
          <h3 className="font-semibold mb-4">API 호출 로그</h3>
          {logs.length === 0 ? (
            <p className="text-ink-muted text-sm py-6 text-center">호출 로그 없음</p>
          ) : (
            <div className="space-y-2">
              {logs.map((l) => (
                <div key={l.id} className="flex flex-wrap items-center gap-3 p-3 bg-surface-muted rounded-xl text-sm">
                  <StatusDot status={l.status_code === 200 ? 'success' : 'error'} />
                  <span className="font-medium text-xs w-24">{l.source_name}</span>
                  <span className="font-mono text-xs text-ink-secondary flex-1 truncate">{l.endpoint}</span>
                  <span className="text-xs text-ink-muted">field #{l.field_id ?? '-'}</span>
                  <span className={`px-2 py-0.5 rounded-lg text-xs font-medium ${
                    l.status_code === 200 ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'
                  }`}>
                    {l.status_code}
                  </span>
                  <span className="text-xs text-gray-400">
                    {l.created_at ? new Date(l.created_at).toLocaleString('ko-KR') : '-'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
