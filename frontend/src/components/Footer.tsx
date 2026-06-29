import Link from 'next/link';

export default function Footer() {
  return (
    <footer className="mt-auto bg-white border-t border-border">
      <div className="max-w-portal mx-auto px-4 md:px-6 py-8">
        <div className="grid md:grid-cols-3 gap-6 text-sm">
          <div>
            <p className="font-bold text-ink mb-2">팜가드 AI</p>
            <p className="text-ink-muted text-xs leading-relaxed">
              필지 단위 병해충, 기상 리스크 예측 및 행동 권고 서비스
            </p>
          </div>
          <div>
            <p className="font-bold text-ink mb-2">데이터 출처</p>
            <ul className="text-xs text-ink-muted space-y-1">
              <li>팜맵, 기상청, 농사로 Open API</li>
              <li>제공: 농림축산식품부, 기상청</li>
            </ul>
          </div>
          <div>
            <p className="font-bold text-ink mb-2">바로가기</p>
            <ul className="text-xs space-y-1">
              <li>
                <a
                  href="https://www.nongsaro.go.kr/portal/portalMain.ps?menuId=PS00001"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-portal-link"
                >
                  농사로 포털
                </a>
              </li>
              <li><Link href="/knowledge" className="text-portal-link no-underline hover:underline">지식허브</Link></li>
              <li><Link href="/admin" className="text-portal-link no-underline hover:underline">관리</Link></li>
            </ul>
          </div>
        </div>
        <div className="mt-6 pt-4 border-t border-border-light text-xs text-ink-muted text-center">
          © 팜가드 AI, 공공데이터 기반 농업 리스크 코치
        </div>
      </div>
    </footer>
  );
}
