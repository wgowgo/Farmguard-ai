'use client';

import { useState } from 'react';

export interface WeeklyReport {
  title: string;
  text: string;
  generated_at: string;
  spray_summary?: string;
}

interface Props {
  report: WeeklyReport;
  fieldId: number;
  onClose: () => void;
}

export default function ShareReportModal({ report, fieldId, onClose }: Props) {
  const [toast, setToast] = useState('');

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(''), 2500);
  };

  const copyText = async () => {
    await navigator.clipboard.writeText(report.text);
    showToast('클립보드에 복사되었습니다');
  };

  const shareKakao = () => {
    if (navigator.share) {
      navigator.share({ title: report.title, text: report.text }).catch(() => {});
    } else {
      copyText();
      showToast('텍스트 복사됨 — 카카오톡에 붙여넣기');
    }
  };

  const shareSms = () => {
    const body = encodeURIComponent(report.text.slice(0, 500));
    window.open(`sms:?body=${body}`, '_self');
    showToast('문자 앱으로 이동합니다');
  };

  const printReport = () => {
    const w = window.open('', '_blank');
    if (!w) return;
    w.document.write(`
      <html><head><title>${report.title}</title>
      <style>body{font-family:system-ui,sans-serif;padding:32px;max-width:560px;margin:auto;line-height:1.7;color:#1c2e24}
      h1{font-size:20px;font-weight:600}pre{white-space:pre-wrap;font-size:14px;color:#4a5f52}</style></head>
      <body><h1>${report.title}</h1><pre>${report.text}</pre>
      <p style="color:#a1a1aa;font-size:12px">팜가드 AI, 필지 #${fieldId}</p></body></html>
    `);
    w.document.close();
    w.print();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/20 backdrop-blur-sm" onClick={onClose}>
      <div
        className="bg-white rounded-portal shadow-portal max-w-lg w-full max-h-[90vh] overflow-hidden border border-border"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-6 border-b border-border-light">
          <h3 className="font-semibold text-lg tracking-tight">주간 리포트 공유</h3>
          <p className="text-sm text-ink-muted mt-1">이번 주 위험, 방제 요약</p>
        </div>

        <div className="p-6 overflow-y-auto max-h-48 bg-surface-muted text-sm whitespace-pre-line text-ink-secondary leading-relaxed font-mono">
          {report.text}
        </div>

        <div className="p-6 grid grid-cols-2 gap-3">
          <button
            onClick={shareKakao}
            className="py-3 rounded-xl bg-[#FEE500] text-[#3c1e1e] font-medium text-sm hover:opacity-90 transition-opacity"
          >
            카카오톡
          </button>
          <button onClick={shareSms} className="btn-primary py-3">
            문자 (SMS)
          </button>
          <button onClick={copyText} className="btn-secondary py-3">복사</button>
          <button onClick={printReport} className="btn-secondary py-3">PDF / 인쇄</button>
        </div>

        <div className="px-6 pb-6">
          <button onClick={onClose} className="btn-ghost w-full py-2">닫기</button>
        </div>

        {toast && (
          <div className="absolute bottom-24 left-1/2 -translate-x-1/2 px-4 py-2 bg-rda-700 text-white text-sm rounded-portal shadow-portal">
            {toast}
          </div>
        )}
      </div>
    </div>
  );
}
