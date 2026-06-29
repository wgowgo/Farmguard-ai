'use client';

import { useMemo, useRef, useState } from 'react';
import { FAQ_CATEGORIES, FAQ_ITEMS, findFaqByQuestion, type FaqItem } from '@/data/chatbot-faq';

type ChatMessage = {
  role: 'bot' | 'user';
  text: string;
};

const WELCOME =
  '안녕하세요, 팜가드 AI 상담 도우미입니다. 아래 예시 질문을 눌러 병해충, 방제, 기상, 토양, 서비스 이용 방법을 확인해 보세요. (테스트용 챗봇, AI API 미연동)';

export default function DemoChatbot() {
  const [messages, setMessages] = useState<ChatMessage[]>([{ role: 'bot', text: WELCOME }]);
  const [category, setCategory] = useState<string>('전체');
  const [pending, setPending] = useState(false);
  const chatRef = useRef<HTMLDivElement>(null);

  const filtered = useMemo(
    () => (category === '전체' ? FAQ_ITEMS : FAQ_ITEMS.filter((f) => f.category === category)),
    [category],
  );

  const scrollToBottom = () => {
    requestAnimationFrame(() => {
      chatRef.current?.scrollTo({ top: chatRef.current.scrollHeight, behavior: 'smooth' });
    });
  };

  const ask = (item: FaqItem) => {
    if (pending) return;
    setPending(true);
    setMessages((prev) => [...prev, { role: 'user', text: item.question }]);
    scrollToBottom();
    window.setTimeout(() => {
      setMessages((prev) => [...prev, { role: 'bot', text: item.answer }]);
      setPending(false);
      scrollToBottom();
    }, 400);
  };

  const reset = () => {
    setMessages([{ role: 'bot', text: WELCOME }]);
    setPending(false);
  };

  const handleManualSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const q = String(fd.get('q') ?? '').trim();
    if (!q || pending) return;
    const found = findFaqByQuestion(q)
      ?? FAQ_ITEMS.find((f) => f.question.includes(q) || q.includes(f.question.slice(0, 8)));
    if (found) {
      ask(found);
    } else {
      setMessages((prev) => [
        ...prev,
        { role: 'user', text: q },
        {
          role: 'bot',
          text: '아래 예시 질문 목록에서 가장 가까운 항목을 선택해 주세요. 테스트용 챗봇은 등록된 예시 질문에만 답변합니다.',
        },
      ]);
      scrollToBottom();
    }
    e.currentTarget.reset();
  };

  return (
    <div className="home-card overflow-hidden">
      <div className="px-6 py-5 md:px-8 md:py-6 border-b border-border bg-rda-50">
        <p className="section-label mb-2">농업 상담 챗봇 (테스트)</p>
        <p className="text-sm text-ink-secondary pl-3 leading-relaxed">
          예시 질문 {FAQ_ITEMS.length}개, AI API 미연동, 클릭하면 즉시 답변
        </p>
      </div>

      <div className="grid lg:grid-cols-5 gap-0">
        <div className="lg:col-span-2 border-b lg:border-b-0 lg:border-r border-border flex flex-col min-h-[400px] lg:min-h-[520px]">
          <div ref={chatRef} className="flex-1 overflow-y-auto p-5 md:p-6 space-y-4 bg-surface-muted">
            {messages.map((m, i) => (
              <div
                key={i}
                className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={
                    m.role === 'user'
                      ? 'max-w-[90%] rounded-portal px-4 py-3 text-sm bg-rda-600 text-white leading-relaxed'
                      : 'max-w-[90%] rounded-portal px-4 py-3 text-sm bg-white border border-border text-ink-secondary leading-relaxed'
                  }
                >
                  {m.text}
                </div>
              </div>
            ))}
            {pending && (
              <div className="flex justify-start">
                <div className="rounded-portal px-4 py-2.5 text-sm bg-white border border-border text-ink-muted">
                  답변 작성 중…
                </div>
              </div>
            )}
          </div>

          <form onSubmit={handleManualSubmit} className="p-4 md:p-5 border-t border-border bg-white flex gap-3">
            <input
              name="q"
              type="text"
              placeholder="직접 입력 (예시 질문과 유사하면 매칭)"
              className="input-field flex-1"
              disabled={pending}
            />
            <button type="submit" className="btn-primary shrink-0" disabled={pending}>
              전송
            </button>
          </form>
          <div className="px-5 pb-4 flex justify-end">
            <button type="button" onClick={reset} className="btn-ghost text-xs">
              대화 초기화
            </button>
          </div>
        </div>

        <div className="lg:col-span-3 p-5 md:p-8">
          <div className="flex flex-wrap gap-2.5 mb-6">
            {FAQ_CATEGORIES.map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => setCategory(cat)}
                className={category === cat ? 'chip-active text-xs' : 'chip text-xs'}
              >
                {cat}
                {cat !== '전체' && (
                  <span className="ml-1 opacity-70">
                    ({FAQ_ITEMS.filter((f) => f.category === cat).length})
                  </span>
                )}
              </button>
            ))}
          </div>

          <p className="text-xs text-ink-muted mb-5">
            {filtered.length}개 질문, 클릭하면 왼쪽 채팅창에 답변이 표시됩니다
          </p>

          <div className="max-h-[420px] overflow-y-auto pr-2 space-y-3">
            {filtered.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => ask(item)}
                disabled={pending}
                className="w-full text-left px-4 py-3.5 rounded-portal border border-border bg-white text-sm text-ink-secondary
                  hover:border-rda-400 hover:bg-rda-50 hover:text-rda-800 transition-colors disabled:opacity-50 leading-relaxed"
              >
                <span className="block text-[10px] font-bold text-rda-600 tracking-wide mb-1.5">
                  {item.category}
                </span>
                {item.question}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
