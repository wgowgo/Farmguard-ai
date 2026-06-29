const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    cache: 'no-store',
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export interface Field {
  field_id: number;
  fmap_innb: string;
  pnu_code?: string;
  crop_name: string;
  land_type?: string;
  address?: string;
  lat?: number;
  lng?: number;
  planting_date?: string;
}

export interface RiskSummary {
  pest_name: string;
  final_risk: number;
  risk_level: string;
  weather_risk: number;
  pest_risk: number;
  soil_risk: number;
}

export interface CropProfile {
  id: string;
  name_ko: string;
  soil_code: string;
  category: string;
  season: string;
  target_pests: string[];
}

export interface DisasterCenter {
  crop_name: string;
  season: string;
  summary: string;
  priority_alert?: {
    title: string;
    message: string;
    level: string;
    type: string;
    date: string;
    label: string;
  };
  weather_hazards: {
    date: string;
    label: string;
    type: string;
    title: string;
    level: string;
    message: string;
  }[];
  checklists: { id: string; title: string; actions: string }[];
  articles: { title: string; body: string; source: string; category: string }[];
}

export interface AdminDashboard {
  system: {
    demo_mode: boolean;
    model_version: string;
    supported_crops: number;
    crop_names: string[];
    database: string;
  };
  stats: {
    field_count: number;
    api_log_count: number;
    alert_count: number;
    weather_records: number;
    soil_records: number;
    pest_records: number;
    risk_scores: number;
    recommendations: number;
    high_risk_today: number;
  };
  pipeline: {
    api_connected: string;
    last_collection: string | null;
    data_layers: { name: string; status: string }[];
  };
  sources: {
    source_name: string;
    license_type?: string;
    last_called_at?: string;
    last_status: string;
    commercial_allowed?: boolean;
  }[];
}

export interface AdminField {
  field_id: number;
  fmap_innb: string;
  crop_name: string;
  land_type?: string;
  address?: string;
  created_at?: string;
  weather_records: number;
  top_risk?: {
    pest_name: string;
    final_risk: number;
    risk_level: string;
  };
}

export interface RiskLog {
  id: number;
  field_id: number;
  address?: string;
  date: string;
  pest_name: string;
  weather_risk?: number;
  pest_risk?: number;
  soil_risk?: number;
  final_risk?: number;
  risk_level: string;
  model_version?: string;
}

export interface ApiLog {
  id: number;
  source_name?: string;
  endpoint: string;
  status_code: number;
  created_at: string;
  field_id?: number;
}

export interface FieldInsights {
  forecast_14d: { date: string; avg_risk: number; type: string; label?: string; rain_forecast_mm?: number; source?: string }[];
  spray_timing: {
    summary: string;
    rain_warning: string;
    best_window?: { label: string };
    hourly: { hour: number; rain_prob: number; suitable: boolean }[];
    all_windows: { label: string }[];
  };
  map_layers: {
    field: { lat: number; lng: number };
    circles: {
      center: { lat: number; lng: number };
      radius_m: number;
      pest_name: string;
      intensity?: number;
      distance_km: number;
    }[];
    pest_markers: { lat: number; lng: number; pest_name: string; value?: number; distance_km?: number }[];
  };
  weekly_report: { title: string; text: string; generated_at: string };
  fertilizer_calendar?: import('@/components/FertilizerCalendarCard').FertilizerCalendar;
  week_plan?: {
    spray_summary?: string;
    spray_best_window?: { label?: string };
    fertilizer_summary?: string | null;
    fertilizer_next?: { label?: string; timing_label?: string } | null;
    top_pest?: string;
  };
  weather_timeline?: import('@/components/WeatherTimelineCard').WeatherTimeline;
}

export interface Dashboard {
  field: Field;
  today_risks: RiskSummary[];
  top_pests: RiskSummary[];
  trend_7d: { date: string; avg_risk: number }[];
  alerts: { id: number; type: string; title: string; message: string; status: string; created_at?: string }[];
  recommendation?: {
    title: string;
    reason: string;
    action_list: string[];
    pest_name: string;
    risk_score: number;
  };
}

export const api = {
  getCrops: () => fetchApi<{ crops: CropProfile[]; count: number }>('/api/crops'),
  getCrop: (idOrName: string) => fetchApi<CropProfile>(`/api/crops/${encodeURIComponent(idOrName)}`),
  getFields: () => fetchApi<Field[]>('/api/fields'),
  getField: (id: number) => fetchApi<Field>(`/api/fields/${id}`),
  getDashboard: (id: number) => fetchApi<Dashboard>(`/api/fields/${id}/dashboard`),
  getInsights: (id: number) => fetchApi<FieldInsights>(`/api/fields/${id}/insights`),
  getFieldDetail: (id: number) => fetchApi<Record<string, unknown>>(`/api/fields/${id}/detail`),
  getDisasters: (fieldId?: number, cropName = '고추') => {
    const qs = fieldId ? `?field_id=${fieldId}` : `?crop_name=${encodeURIComponent(cropName)}`;
    return fetchApi<DisasterCenter>(`/api/disasters${qs}`);
  },
  getFertilizerCalendar: (id: number) =>
    fetchApi<import('@/components/FertilizerCalendarCard').FertilizerCalendar>(`/api/fields/${id}/fertilizer-calendar`),
  getPestDetail: (fieldId: number, pestName: string) =>
    fetchApi<Record<string, unknown>>(`/api/fields/${fieldId}/pest/${encodeURIComponent(pestName)}`),
  registerField: (data: { lat: number; lng: number; crop_name: string; planting_date?: string }) =>
    fetchApi<Field>('/api/fields', { method: 'POST', body: JSON.stringify(data) }),
  collect: (id: number) => fetchApi<Record<string, unknown>>(`/api/fields/${id}/collect`, { method: 'POST' }),
  getApiStatus: () => fetchApi<{ source_name: string; last_called_at?: string; last_status: string }[]>('/api/admin/api-status'),
  getStats: () => fetchApi<{ field_count: number; api_log_count: number; alert_count: number; high_risk_today?: number; demo_mode?: boolean }>('/api/admin/stats'),
  getLogs: () => fetchApi<ApiLog[]>('/api/admin/logs'),
  getAdminDashboard: () => fetchApi<AdminDashboard>('/api/admin/dashboard'),
  getAdminFields: () => fetchApi<AdminField[]>('/api/admin/fields'),
  getRiskLogs: () => fetchApi<RiskLog[]>('/api/admin/risk-logs'),
  collectAll: () => fetchApi<{ collected: number; results: Record<string, unknown>[] }>('/api/admin/collect-all', { method: 'POST' }),
  setDemoMode: (enabled: boolean) =>
    fetchApi<{ demo_mode: boolean; message: string }>(`/api/admin/demo-mode?enabled=${enabled}`, { method: 'POST' }),
  getAlerts: (fieldId?: number) =>
    fetchApi<Record<string, unknown>[]>(fieldId ? `/api/alerts?field_id=${fieldId}` : '/api/alerts'),
  getAlertSettings: () => fetchApi<Record<string, boolean>>('/api/alerts/settings'),
  updateAlertSettings: (settings: Record<string, boolean>) =>
    fetchApi<{ status: string }>('/api/alerts/settings', { method: 'PUT', body: JSON.stringify(settings) }),
  getKnowledgeServices: () => fetchApi<Record<string, unknown>>('/api/knowledge/services'),
  knowledgeSearch: (q: string, crop_name = '고추') =>
    fetchApi<Record<string, unknown>>(`/api/knowledge/search?q=${encodeURIComponent(q)}&crop_name=${encodeURIComponent(crop_name)}`),
  getNongsaroDbyhs: (year = '', search_text = '') => {
    const qs = new URLSearchParams();
    if (year) qs.set('year', year);
    if (search_text) qs.set('search_text', search_text);
    return fetchApi<Record<string, unknown>>(`/api/knowledge/nongsaro/dbyhs?${qs}`);
  },
  nongsaroCall: (service: string, operation = '', params: Record<string, string> = {}) => {
    const qs = new URLSearchParams({ service, ...params });
    if (operation) qs.set('operation', operation);
    return fetchApi<Record<string, unknown>>(`/api/knowledge/nongsaro/call?${qs}`);
  },
  getNongsaroPesticide: (crop_name = '고추', pest_name = '') =>
    fetchApi<Record<string, unknown>>(
      `/api/knowledge/nongsaro/pesticide?crop_name=${encodeURIComponent(crop_name)}&pest_name=${encodeURIComponent(pest_name)}`
    ),
  getFieldEnrichment: (field_id: number) =>
    fetchApi<Record<string, unknown>>(`/api/knowledge/field/${field_id}/enrichment`),
};

export function riskColor(level: string): string {
  switch (level) {
    case '낮음': return 'risk-badge-low';
    case '주의': return 'risk-badge-caution';
    case '위험': return 'risk-badge-danger';
    case '매우 위험': return 'risk-badge-critical';
    default: return 'bg-surface-subtle text-ink-secondary border border-border';
  }
}

export function riskBarColor(score: number): string {
  if (score < 40) return '#007a3d';
  if (score < 70) return '#d97706';
  if (score < 85) return '#ea580c';
  return '#dc2626';
}
