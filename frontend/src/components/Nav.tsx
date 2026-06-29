'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const links = [
  { href: '/', label: '홈' },
  { href: '/dashboard', label: '대시보드' },
  { href: '/fields/register', label: '필지등록' },
  { href: '/alerts', label: '알림센터' },
  { href: '/disasters', label: '재해예방' },
  { href: '/knowledge', label: '지식허브' },
  { href: '/admin', label: '관리' },
];

export default function Nav() {
  const pathname = usePathname();

  const isActive = (href: string) =>
    pathname === href || (href !== '/' && pathname.startsWith(href));

  return (
    <header className="sticky top-0 z-50 shadow-portal">
      {/* 공공 포털 상단 바 */}
      <div className="bg-portal-gov text-white text-xs">
        <div className="max-w-portal mx-auto px-4 md:px-6 h-8 flex items-center justify-between">
          <span className="opacity-90">농업 리스크 예측, 행동 권고 서비스</span>
          <span className="hidden sm:inline opacity-75">팜맵, 기상청, 농사로 연동</span>
        </div>
      </div>

      {/* 로고 영역 */}
      <div className="bg-white border-b border-border">
        <div className="max-w-portal mx-auto px-4 md:px-6 h-[72px] flex items-center justify-between gap-4">
          <Link href="/" className="flex items-center gap-3 no-underline group shrink-0">
            <div className="w-11 h-11 rounded-portal bg-rda-600 flex items-center justify-center text-white">
              <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
                <path d="M12 2C8.5 2 5.5 4.5 4.5 8c-.8 3.2.5 6.5 3 8.5L12 22l4.5-5.5c2.5-2 3.8-5.3 3-8.5C18.5 4.5 15.5 2 12 2zm0 10.5a3 3 0 110-6 3 3 0 010 6z" />
              </svg>
            </div>
            <div>
              <p className="text-[11px] text-rda-600 font-semibold leading-none mb-0.5">농촌진흥청 연계</p>
              <h1 className="text-xl font-bold text-ink leading-tight group-hover:text-rda-700 transition-colors">
                팜가드 <span className="text-rda-600">AI</span>
              </h1>
            </div>
          </Link>

          <div className="hidden md:flex items-center gap-6 text-sm text-ink-secondary">
            <div className="text-right">
              <p className="text-xs text-ink-muted">Farm Risk Coach</p>
              <p className="font-medium text-ink">필지 단위 병해충, 기상 리스크</p>
            </div>
          </div>
        </div>
      </div>

      {/* 메인 네비게이션 — 농사로 그린 바 */}
      <nav className="bg-rda-600 border-b-2 border-rda-800" aria-label="주메뉴">
        <div className="max-w-portal mx-auto px-2 md:px-4 flex overflow-x-auto scrollbar-hide">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className={isActive(l.href) ? 'nav-link-active' : 'nav-link'}
            >
              {l.label}
            </Link>
          ))}
        </div>
      </nav>
    </header>
  );
}
