'use client';

export interface SprayPrescription {
  brand_name: string;
  product_name?: string;
  crop_name: string;
  pest_name: string;
  purpose?: string;
  action_type?: string;
  company?: string;
  dilution?: string;
  safe_period?: string;
  harvest_before_days?: string;
  manual_title?: string;
  manual_url?: string;
  manual_matched?: boolean;
  usage_note?: string;
}

export default function SprayPrescriptionCard({ items }: { items: SprayPrescription[] }) {
  if (!items.length) {
    return (
      <div className="card">
        <p className="section-label">방제 처방</p>
        <p className="text-sm text-ink-muted py-4">등록 농약 정보가 없습니다.</p>
      </div>
    );
  }

  return (
    <div className="card">
      <p className="section-label">방제 처방 카드</p>
      <p className="text-xs text-ink-muted mb-4">농사로 등록현황 + 안전사용지침 연동</p>
      <div className="space-y-3">
        {items.map((p, i) => (
          <div key={i} className="p-4 rounded-xl border border-border-light bg-surface-muted/50">
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div>
                <p className="font-semibold text-sm">{p.brand_name}</p>
                {p.product_name && p.product_name !== p.brand_name && (
                  <p className="text-xs text-ink-muted">{p.product_name}</p>
                )}
              </div>
              {p.purpose && (
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-white ring-1 ring-border-light">
                  {p.purpose}{p.action_type ? `, ${p.action_type}` : ''}
                </span>
              )}
            </div>
            <p className="text-xs text-ink-secondary mt-2">{p.usage_note}</p>
            <dl className="grid grid-cols-2 gap-x-4 gap-y-1 mt-3 text-xs">
              {p.dilution && (
                <>
                  <dt className="text-ink-muted">희석배율</dt>
                  <dd className="font-medium">{p.dilution}</dd>
                </>
              )}
              {p.safe_period && (
                <>
                  <dt className="text-ink-muted">안전기간</dt>
                  <dd className="font-medium">{p.safe_period}</dd>
                </>
              )}
              {p.harvest_before_days && (
                <>
                  <dt className="text-ink-muted">수확 전</dt>
                  <dd className="font-medium">{p.harvest_before_days}일</dd>
                </>
              )}
              {p.company && (
                <>
                  <dt className="text-ink-muted">업체</dt>
                  <dd className="font-medium">{p.company}</dd>
                </>
              )}
            </dl>
            {p.manual_url && (
              <a
                href={p.manual_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block mt-3 text-xs text-ink underline underline-offset-2"
              >
                {p.manual_title || '안전사용지침 보기'}
              </a>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
