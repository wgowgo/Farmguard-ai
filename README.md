# 팜가드 AI (FarmGuard AI)

> 필지 단위 병해충, 기상 리스크를 예측하고 행동 지침을 알려주는 AI 농업 리스크 코치

## 배포 (Netlify + Render)

| 방법 | 문서 |
|------|------|
| **GitHub 없이** (CLI + Docker) | [DEPLOY-NOGIT.md](./DEPLOY-NOGIT.md) |
| **GitHub 연동** | [DEPLOY.md](./DEPLOY.md) |

| 서비스 | 역할 |
|--------|------|
| **Netlify** | Next.js 프론트 |
| **Render** | FastAPI 백엔드 |

Netlify 환경변수: `NEXT_PUBLIC_API_URL=https://your-api.onrender.com`

## 빠른 시작

```powershell
cd farmguard-ai
.\start.ps1
```

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **관리자**: http://localhost:3000/admin

## 환경변수 (`.env`)

```env
PUBLIC_DATA_SERVICE_KEY=...   # data.go.kr (팜맵, 기상청, 토양/비료)
NONGSARO_API_KEY=...          # 농사로 Open API 8종
DEMO_MODE=false               # true면 API 없이 데모 데이터
```

> `start.ps1`은 `.env`의 `DEMO_MODE` 값을 존중합니다.

## 연동 API (NCPMS 제외)

| 구분 | API | 용도 |
|------|-----|------|
| **팜맵** | 조회, 기상, 토양, 병해충 | 필지 등록, 위험도 산출 |
| **기상청** | 초단기실황, 예보, 단기예보 | 방제 타이밍, 7일 예보(단기 3일+추정) |
| **농사로** | 8종 (발생정보, 농약, 재해예방 등) | 병해충 뉴스, 등록농약 |
| **흙토람** | 토양검정 V2, 비료처방 | 필지 상세 토양, 비료 |

### 농사로 8종

병해충발생정보, 건강안전정보, 공공데이터, 관련사이트, 농약품질검사, 농약등록현황, 농약안전사용지침, 농작물재해예방정보

## 주요 화면

| 경로 | 기능 |
|------|------|
| `/` | **홈** — 서비스 소개, 공공데이터 활용, 테스트 챗봇 |
| `/dashboard` | 대시보드 — 위험도, 7일 예보, 방제 타이밍, 지도 |
| `/fields/register` | 지도에서 필지 등록 → 자동 수집 |
| `/fields/[id]` | 토양, 기상, **시비 캘린더**, 병해충 |
| `/fields/[id]/pest/[name]` | 병해충 상세, **방제 처방 카드**, 권고 |
| `/disasters` | 재해 예방 센터 — KMA 예보, 체크리스트 |
| `/knowledge` | 농사로 API 탐색, 통합검색 |
| `/alerts` | 알림 5종 설정, 이력 (수집 시 자동 생성) |
| `/admin` | API 상태, 수집 로그, 데모 토글 |

## API 테스트

```powershell
cd backend
.\.venv\Scripts\python.exe scripts\test_apis.py
```

## 프로젝트 구조

```
farmguard-ai/
├── .env
├── start.ps1
├── backend/
│   ├── app/
│   │   ├── routers/       # fields, admin, knowledge
│   │   └── services/      # collector, risk_engine, nongsaro, soil...
│   └── scripts/test_apis.py
└── frontend/              # Next.js 14
```

## MVP 범위

- 작물: **12종** (고추, 토마토, 딸기, 벼, 오이, 가지, 사과, 포도, 마늘, 양파, 콩, 옥수수) — 작물별 병해충 2~3종
- 병해충: 탄저병, 역병, 담배나방
- 좌표계: 팜맵 **EPSG:5179**

## 라이선스

공공데이터 출처 표시 및 각 API 이용허락범위를 준수하세요.
