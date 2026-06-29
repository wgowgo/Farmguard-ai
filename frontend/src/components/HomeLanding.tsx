import Image from 'next/image';
import Link from 'next/link';
import DemoChatbot from '@/components/DemoChatbot';
import { HOME_IMAGES } from '@/data/home-images';

const STATS = [
  { value: '12종', label: '지원 작물' },
  { value: '9+', label: '연동 공공 API' },
  { value: '5종', label: '스마트 알림' },
  { value: '4단계', label: '위험도 등급' },
];

const SPOTLIGHT = [
  {
    title: '스마트팜, 데이터',
    desc: '드론, IoT 센서, 기상 관측과 팜맵, 기상청, 농사로, 흙토람 공공데이터를 연계합니다. 필지별 환경과 생육, 예보 데이터를 한곳에서 수집, 분석해 위험도를 산출합니다.',
    image: HOME_IMAGES.smartFarm,
    alt: '스마트팜, 드론, 센서, 농업 데이터',
  },
  {
    title: '작물관리',
    desc: '작물별 병해충, 재배 관리 요령, 토양, 시비, 방제 정보를 필지 단위로 제공합니다. 12종 작물, 대표 병해충별 맞춤 권고를 지원합니다.',
    image: HOME_IMAGES.agriData,
    alt: '작물 재배 관리, 생육 그래프, 환경 모니터링',
  },
  {
    title: '농업상담',
    desc: '농업기술센터 상담처럼 병해충, 방제, 기상, 토양, 서비스 이용 방법을 챗봇과 지식 허브에서 바로 확인할 수 있습니다.',
    image: HOME_IMAGES.cropConsult,
    alt: '농업 상담, 농업기술센터',
  },
];

const FEATURES = [
  {
    title: '필지 단위 리스크 분석',
    desc: '지도에서 밭을 등록하면 팜맵, 기상청, 흙토람, 농사로 데이터를 자동 수집합니다. 기상, 예찰, 토양, 생육 민감기를 종합해 병해충별 위험도를 0~100점으로 산출합니다.',
    image: HOME_IMAGES.fieldPanorama,
    alt: '농경지 전경',
  },
  {
    title: '방제, 시비 행동 권고',
    desc: '기상청 예보 기반 방제 타이밍, 농사로 등록 농약, 안전지침 연계 방제 처방, 흙토람 비료처방 시비 캘린더까지 현장에서 바로 실행할 수 있는 지침을 제공합니다.',
    image: HOME_IMAGES.sprayFertilizer,
    alt: '방제, 시비 행동 권고',
  },
  {
    title: '맞춤 알림, 재해 예방',
    desc: '위험 급상승, 방제 전 강수, 고습도, 인근 병해충, 주간 리포트 5종 알림과 폭염, 한파, 호우 대응 체크리스트로 선제 대응을 돕습니다.',
    image: HOME_IMAGES.alertDisaster,
    alt: '맞춤 알림, 재해 예방',
  },
];

const VALUES = [
  {
    title: '데이터 기반 농업',
    desc: '공공데이터를 현장 의사결정 도구로 전환해, 경험에만 의존하던 관리를 과학적, 예측적 농업으로 확장합니다.',
  },
  {
    title: '소규모 농가 지원',
    desc: '전담 컨설턴트 없이도 필지 단위 리스크 코칭을 받을 수 있어, 소규모, 청년 농업인의 경영 부담을 줄입니다.',
  },
  {
    title: '지속가능한 생산',
    desc: '적기 방제, 시비로 농약 낭비와 피해를 줄이고, 수확량, 품질 유지에 기여합니다.',
  },
];

const PREDICT = [
  {
    title: '기상 리스크 예측',
    desc: '습도, 결로, 강수, 온도 스트레스를 분석해 곰팡이병, 역병 등 기상 연계 병해 위험을 미리 알립니다.',
  },
  {
    title: '예찰, 발생 연계',
    desc: '주변 병해충 발생 지수, 거리, 경과일을 반영해 인근 확산 위험을 수치화합니다.',
  },
  {
    title: '7일, 14일 전망',
    desc: '단기예보와 과거 패턴을 결합한 위험 추이로 이번 주, 다음 주 작업 계획을 세울 수 있습니다.',
  },
];

const PRODUCTIVITY = [
  {
    title: '방제 적기 최적화',
    desc: '강수, 풍속, 습도를 고려한 살포 가능 시간 안내로 약효 저하와 재작업을 줄입니다.',
  },
  {
    title: '토양, 시비 연계',
    desc: '토양 취약성과 비료처방을 연결해 작물 저항성을 높이는 시비 시기를 놓치지 않도록 돕습니다.',
  },
  {
    title: '통합 필지 관리',
    desc: '대시보드, 알림, 재해예방, 지식허브를 하나의 서비스에서 이용해 관리 효율을 높입니다.',
  },
];

const DATA_SOURCES = [
  { name: '팜맵', items: ['필지 조회', '농업기상', '토양검정', '병해충발생'], pct: 35 },
  { name: '기상청', items: ['초단기실황', '초단기예보', '단기예보'], pct: 25 },
  { name: '농사로', items: ['발생정보', '농약등록', '안전지침', '재해예방'], pct: 25 },
  { name: '흙토람', items: ['토양검정 V2', '비료처방'], pct: 15 },
];

function SectionHeader({ title, desc }: { title: string; desc?: string }) {
  return (
    <header className="mb-8 md:mb-12">
      <h2 className="home-section-title">{title}</h2>
      {desc && <p className="home-section-desc mb-0">{desc}</p>}
    </header>
  );
}

export default function HomeLanding() {
  return (
    <div className="home-wrap">
      {/* 히어로 */}
      <section className="home-section">
        <div className="home-card overflow-hidden">
          <div className="grid lg:grid-cols-2 gap-0">
            <div className="home-card-body flex flex-col justify-center lg:py-12 lg:pl-10 lg:pr-8">
              <p className="text-xs font-bold text-rda-600 mb-4 tracking-wide">
                농업, 농촌 공공데이터 활용
              </p>
              <h1 className="text-2xl md:text-4xl font-bold text-ink tracking-tight leading-snug mb-6">
                내 밭의 병해충, 기상 리스크,
                <br />
                <span className="text-rda-600">팜가드 AI</span>가 알려 드립니다
              </h1>
              <p className="text-sm md:text-base text-ink-secondary leading-relaxed mb-8 max-w-lg">
                필지를 등록하면 팜맵, 기상청, 농사로, 흙토람 공공데이터를 자동으로 모아
                위험도, 방제 타이밍, 시비, 재해 대응 방법을 한곳에서 확인할 수 있는
                웹 기반 농업 리스크 코치입니다.
              </p>
              <div className="flex flex-wrap gap-4">
                <Link href="/fields/register" className="btn-primary no-underline">
                  필지 등록하기
                </Link>
                <Link href="/dashboard" className="btn-secondary no-underline">
                  대시보드 바로가기
                </Link>
                <a href="#chatbot" className="btn-ghost no-underline">
                  챗봇 체험
                </a>
              </div>
            </div>
            <div className="relative min-h-[280px] lg:min-h-[420px]">
              <Image
                src={HOME_IMAGES.hero}
                alt="농업인이 밭에서 작업하는 모습"
                fill
                className="home-img"
                sizes="(max-width: 1024px) 100vw, 50vw"
                priority
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent lg:bg-gradient-to-l lg:from-black/40 lg:via-transparent" />
              <div className="absolute bottom-0 left-0 right-0 p-6 md:p-8 text-white">
                <p className="text-sm font-bold mb-4 opacity-95">한 번의 등록으로</p>
                <ul className="space-y-4 text-sm leading-relaxed">
                  <li className="flex gap-3">
                    <span className="text-rda-200 font-bold shrink-0">01</span>
                    <span>지도에서 필지 위치 선택, PNU, 작물 정보 자동 매칭</span>
                  </li>
                  <li className="flex gap-3">
                    <span className="text-rda-200 font-bold shrink-0">02</span>
                    <span>공공데이터 자동 수집, 위험도, 예보, 알림 생성</span>
                  </li>
                  <li className="flex gap-3">
                    <span className="text-rda-200 font-bold shrink-0">03</span>
                    <span>방제, 시비, 재해 대응, 현장 행동 지침 확인</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
        <p className="text-[11px] text-ink-muted mt-3 text-right">
          섹션 일부 이미지: Pixabay (저작권 프리)
        </p>
      </section>

      {/* 핵심 수치 */}
      <section className="home-section">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-5 md:gap-8">
          {STATS.map((s) => (
            <div key={s.label} className="home-card home-card-body text-center py-8 md:py-10">
              <p className="stat-value text-rda-700">{s.value}</p>
              <p className="stat-label mt-2">{s.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* 공공데이터 + 이미지 배너 */}
      <section className="home-section">
        <SectionHeader
          title="공공데이터로 보는 농업 리스크"
          desc="농식품 공공데이터포털, 농사로 Open API를 필지 단위로 통합 활용합니다"
        />
        <div className="grid lg:grid-cols-5 gap-8 md:gap-10 mb-10 md:mb-14">
          <div className="lg:col-span-2 relative min-h-[220px] rounded-portal overflow-hidden border border-border">
            <Image
              src={HOME_IMAGES.soil}
              alt="토양, 농업 데이터, 스마트팜 센서"
              fill
              className="home-img"
              sizes="(max-width: 1024px) 100vw, 40vw"
            />
          </div>
          <div className="lg:col-span-3 grid sm:grid-cols-2 gap-5 md:gap-6 content-start">
            {DATA_SOURCES.map((d) => (
              <div key={d.name} className="home-card home-card-body">
                <div className="flex items-center justify-between mb-4">
                  <p className="font-bold text-ink text-base">{d.name}</p>
                  <span className="text-xs text-ink-muted">활용 {d.pct}%</span>
                </div>
                <div className="h-2.5 bg-surface-subtle rounded-full mb-4 overflow-hidden">
                  <div
                    className="h-full bg-rda-600 rounded-full transition-all"
                    style={{ width: `${d.pct}%` }}
                  />
                </div>
                <p className="text-sm text-ink-secondary leading-relaxed">{d.items.join(', ')}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 스마트팜, 데이터, 작물관리, 농업상담 */}
      <section className="home-section">
        <SectionHeader
          title="스마트 농업, 데이터 기반 관리"
          desc="스마트팜, 데이터, 작물관리, 농업상담을 하나의 서비스로 연결합니다"
        />
        <div className="grid md:grid-cols-3 gap-6 md:gap-8">
          {SPOTLIGHT.map((item) => (
            <article key={item.title} className="home-card flex flex-col">
              <div className="relative h-44 md:h-48">
                <Image src={item.image} alt={item.alt} fill className="home-img" sizes="25vw" />
              </div>
              <div className="home-card-body flex-1">
                <h3 className="font-bold text-rda-700 text-lg mb-3">{item.title}</h3>
                <p className="text-sm text-ink-secondary leading-relaxed">{item.desc}</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      {/* 핵심 기능 */}
      <section className="home-section">
        <SectionHeader title="핵심 기능" desc="필지 등록부터 방제, 시비, 알림까지 한 번에" />
        <div className="grid md:grid-cols-3 gap-6 md:gap-8">
          {FEATURES.map((f, i) => (
            <article key={f.title} className="home-card flex flex-col">
              <div className="relative h-44 md:h-52">
                <Image src={f.image} alt={f.alt} fill className="home-img" sizes="33vw" />
                <span className="absolute top-4 left-4 w-9 h-9 rounded-portal bg-white/95 text-rda-700 text-sm font-bold flex items-center justify-center shadow-card">
                  {i + 1}
                </span>
              </div>
              <div className="home-card-body flex-1">
                <h3 className="font-bold text-ink text-lg mb-3">{f.title}</h3>
                <p className="text-sm text-ink-secondary leading-relaxed">{f.desc}</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      {/* 주요 과제 */}
      <section className="home-section rounded-portal bg-rda-50/60 border border-rda-100 px-5 py-10 md:px-10 md:py-14">
        <SectionHeader
          title="농업 현장의 과제, 팜가드 AI의 해결"
          desc="분산된 데이터와 늦은 대응, 정보 접근의 어려움을 줄입니다"
        />
        <div className="grid md:grid-cols-3 gap-6 md:gap-8">
          <div className="home-card home-card-body">
            <h3 className="font-bold text-rda-700 text-lg mb-3">분산된 공공데이터</h3>
            <p className="text-sm text-ink-secondary leading-relaxed">
              팜맵, 기상청, 농사로, 흙토람을 각각 조회해야 하는 불편을 없애고, 필지 등록 한 번으로 자동 통합합니다.
            </p>
          </div>
          <div className="home-card home-card-body">
            <h3 className="font-bold text-rda-700 text-lg mb-3">늦은 병해충, 기상 대응</h3>
            <p className="text-sm text-ink-secondary leading-relaxed">
              위험도 점수와 근거 설명, 알림으로 “언제, 무엇을, 왜” 해야 하는지 농업인이 빠르게 판단할 수 있게 합니다.
            </p>
          </div>
          <div className="home-card home-card-body">
            <h3 className="font-bold text-rda-700 text-lg mb-3">전문 지식 접근 장벽</h3>
            <p className="text-sm text-ink-secondary leading-relaxed">
              병해충 증상, 등록 농약, 재해 대응 정보를 지식 허브와 테스트 챗봇으로 쉽게 탐색할 수 있습니다.
            </p>
          </div>
        </div>
      </section>

      {/* 사회적 가치 */}
      <section className="home-section">
        <SectionHeader title="팜가드 AI의 사회적 가치" />
        <div className="grid md:grid-cols-3 gap-6 md:gap-8">
          {VALUES.map((v) => (
            <div key={v.title} className="home-card home-card-body border-l-4 border-l-rda-600">
              <h3 className="font-bold text-ink text-lg mb-4">{v.title}</h3>
              <p className="text-sm text-ink-secondary leading-relaxed">{v.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* AI 예측 */}
      <section className="home-section">
        <div className="relative rounded-portal overflow-hidden bg-rda-700 text-white">
          <div className="absolute inset-0 opacity-20">
            <Image
              src={HOME_IMAGES.fieldPanorama}
              alt=""
              fill
              className="home-img"
              sizes="100vw"
              aria-hidden
            />
          </div>
          <div className="relative p-8 md:p-12 lg:p-14">
            <h2 className="text-xl md:text-2xl font-bold mb-4">
              미리 알고, 먼저 대응하는 리스크 예측
            </h2>
            <p className="text-sm md:text-base text-white/85 mb-10 max-w-2xl leading-relaxed">
              공공데이터 기반 설명 가능한 점수식으로 병해충, 기상, 토양 리스크를 산출합니다.
              블랙박스 AI가 아니라 근거와 출처를 함께 제시합니다.
            </p>
            <div className="grid md:grid-cols-3 gap-5 md:gap-6">
              {PREDICT.map((p) => (
                <div
                  key={p.title}
                  className="rounded-portal bg-white/10 backdrop-blur-sm border border-white/25 p-6 md:p-7"
                >
                  <h3 className="font-bold text-lg mb-3">{p.title}</h3>
                  <p className="text-sm text-white/90 leading-relaxed">{p.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* 생산성 */}
      <section className="home-section">
        <SectionHeader title="생산성 향상의 핵심 포인트" />
        <div className="grid md:grid-cols-3 gap-6 md:gap-8">
          {PRODUCTIVITY.map((p) => (
            <div key={p.title} className="home-card home-card-body">
              <h3 className="font-bold text-ink text-lg mb-4">{p.title}</h3>
              <p className="text-sm text-ink-secondary leading-relaxed">{p.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* 챗봇 */}
      <section className="home-section" id="chatbot">
        <SectionHeader
          title="궁금증을 해결해 주는 농업 상담 챗봇"
          desc="병해충, 방제, 기상, 토양, 서비스 이용 등 예시 질문을 눌러 답변을 확인해 보세요"
        />
        <DemoChatbot />
      </section>

      {/* CTA */}
      <section className="home-section">
        <div className="home-card text-center py-12 md:py-16 px-6 bg-rda-50 border-rda-200">
          <h2 className="text-xl md:text-2xl font-bold text-ink mb-4">
            지금 내 밭의 리스크를 확인해 보세요
          </h2>
          <p className="text-sm md:text-base text-ink-secondary mb-8 max-w-md mx-auto leading-relaxed">
            필지 등록 후 1분이면 위험도, 예보, 방제 타이밍을 확인할 수 있습니다
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link href="/fields/register" className="btn-primary no-underline">
              무료로 필지 등록
            </Link>
            <Link href="/knowledge" className="btn-secondary no-underline">
              지식 허브 둘러보기
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
