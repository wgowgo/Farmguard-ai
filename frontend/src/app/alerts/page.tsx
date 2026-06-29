'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import PageHeader from '@/components/PageHeader';
import { AlertList, AlertItem } from '@/components/AlertListItem';

const ALERT_TYPES = [
  { key: 'risk_rise', label: '위험도 상승', desc: '70점 이상 시 알림' },
  { key: 'rain_before_spray', label: '강우 전 방제', desc: '비 예보 6시간 전' },
  { key: 'high_humidity', label: '고습 / 결로', desc: '습도 80% 이상' },
  { key: 'nearby_pest', label: '주변 발생', desc: '2km 이내 신규' },
  { key: 'weekly_report', label: '주간 리포트', desc: '매주 월요일' },
];

export default function AlertsPage() {
  const [settings, setSettings] = useState<Record<string, boolean>>({});
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api.getAlertSettings().then(setSettings).catch(console.error);
    api.getAlerts().then((list) => setAlerts(list as unknown as AlertItem[])).catch(console.error);
  }, []);

  const toggle = (key: string) => {
    setSettings((s) => ({ ...s, [key]: !s[key] }));
    setSaved(false);
  };

  const save = async () => {
    await api.updateAlertSettings(settings);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <PageHeader
        title="알림센터"
        desc="위험 상황 발생 시 받을 알림을 설정합니다"
        breadcrumb={[{ label: '알림센터' }]}
      />

      <div className="card">
        <p className="card-title">알림 수신 설정</p>
        <div className="divide-y divide-border-light">
          {ALERT_TYPES.map((t) => (
            <label
              key={t.key}
              className="flex items-center justify-between py-3.5 first:pt-0 last:pb-0 cursor-pointer group"
            >
              <div>
                <p className="font-semibold text-sm text-ink group-hover:text-rda-700 transition-colors">{t.label}</p>
                <p className="text-xs text-ink-muted mt-0.5">{t.desc}</p>
              </div>
              <div className={`w-11 h-6 rounded-full transition-colors relative shrink-0 ${settings[t.key] ?? true ? 'bg-rda-600' : 'bg-surface-subtle'}`}>
                <input
                  type="checkbox"
                  checked={settings[t.key] ?? true}
                  onChange={() => toggle(t.key)}
                  className="sr-only"
                />
                <span
                  className={`absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${
                    settings[t.key] ?? true ? 'left-[22px]' : 'left-0.5'
                  }`}
                />
              </div>
            </label>
          ))}
        </div>
        <div className="pt-5 mt-2 border-t border-border-light">
          <button onClick={save} className="btn-primary w-full sm:w-auto min-w-[140px]">
            {saved ? '저장됨' : '설정 저장'}
          </button>
        </div>
      </div>

      <div className="card">
        <p className="card-title">알림 이력 ({alerts.length})</p>
        <AlertList alerts={alerts} />
      </div>
    </div>
  );
}
