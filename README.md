# FarmGuard AI

> Field-level pest, weather, and soil risk coach powered by Korean public agricultural APIs

FarmGuard AI helps farmers register a parcel on a map, automatically collect data from government open APIs, and receive integrated risk scores with actionable guidance — spray timing, fertilizer schedules, disaster checklists, and pest management advice — all in one web dashboard.

---

## Features

| Area | What it does |
|------|----------------|
| **Field registration** | Pick a location on the map, set crop and planting date, auto-collect parcel, weather, soil, and pest data |
| **Risk scoring** | 0–100 scores for pest, weather, and soil risk with explanations and data sources |
| **Spray timing** | Hourly forecast analysis — when spraying is safe vs. when rain or wind should delay it |
| **Spray prescription** | Registered pesticides and safety guidelines from Nongsaro, matched to crop and pest |
| **Fertilizer calendar** | Soil test and fertilizer prescription from Heuktoram (흙토람) APIs |
| **Alerts** | Risk spikes, rain before spray, high humidity, nearby pest reports, weekly summary |
| **Disaster center** | Heat, cold, flood, drought risk with seasonal checklists |
| **Knowledge hub** | Search pests, crops, and pesticides across integrated APIs |
| **Demo mode** | Full UI flow with sample data when API keys are not configured |

## Tech stack

| Layer | Stack |
|-------|--------|
| Frontend | Next.js 14, React, Tailwind CSS, Leaflet |
| Backend | FastAPI, SQLAlchemy (async), SQLite |
| Deployment | Netlify (frontend) + Render (backend) — see `render.yaml` |

## Quick start

**Prerequisites:** Python 3.11+, Node.js 20+, npm

```powershell
git clone https://github.com/wgowgo/farmguard-ai.git
cd farmguard-ai
copy .env.example .env
.\start.ps1
```

| URL | Description |
|-----|-------------|
| http://localhost:3000 | Frontend |
| http://localhost:8000 | Backend API |
| http://localhost:8000/docs | OpenAPI docs |
| http://localhost:3000/admin | Admin dashboard |

On first run, `start.ps1` copies `.env.example` → `.env` if missing, installs dependencies, and starts both servers.

## Environment variables

Copy `.env.example` to `.env` at the project root. **Never commit `.env`.**

```env
PUBLIC_DATA_SERVICE_KEY=   # data.go.kr — Farmmap, KMA, soil/fertilizer
NONGSARO_API_KEY=          # Nongsaro Open API (8 services)
NCPMS_API_KEY=             # Optional — NCPMS pest API (currently unused)
DEMO_MODE=true             # true = sample data without real API keys
DATABASE_URL=sqlite+aiosqlite:///./farmguard.db
OPENAI_API_KEY=            # Optional — reserved for future use
```

Set `DEMO_MODE=false` and fill in keys to use live public APIs.

## Data sources

| Source | APIs used | Purpose |
|--------|-----------|---------|
| **Farmmap** | Parcel, agro-weather, soil, pest occurrence | Field matching, risk inputs |
| **KMA** | Ultra-short nowcast/forecast, short-term forecast | Spray timing, 7-day outlook |
| **Nongsaro** | 8 services (pest info, pesticides, disaster prevention, etc.) | Pest news, registered chemicals |
| **Heuktoram** | Soil test V2, fertilizer prescription | Soil detail, fertilization plan |

Coordinate system for Farmmap: **EPSG:5179**.

## Main routes

| Path | Description |
|------|-------------|
| `/` | Landing page and demo chatbot |
| `/dashboard` | Risk overview, forecast chart, spray timing, map |
| `/fields/register` | Register a field on the map |
| `/fields/[id]` | Soil, weather, fertilizer calendar, pests |
| `/fields/[id]/pest/[name]` | Pest detail and spray prescription |
| `/disasters` | Disaster prevention center |
| `/knowledge` | Nongsaro API explorer and search |
| `/alerts` | Alert settings and history |
| `/admin` | API status, collection logs, demo toggle |

## API integration test

```powershell
cd backend
.\.venv\Scripts\python.exe scripts\test_apis.py
```

## Project structure

```
farmguard-ai/
├── .env.example
├── start.ps1
├── render.yaml
├── backend/
│   ├── app/
│   │   ├── routers/       # fields, admin, knowledge, crops, disasters
│   │   └── services/      # collector, risk_engine, nongsaro, soil, ...
│   └── scripts/test_apis.py
└── frontend/              # Next.js 14
```

---

# 팜가드 AI (FarmGuard AI)

> 공공 농업 API를 활용한 필지 단위 병해충,기상,토양 리스크 코치

농업인이 지도에서 필지를 등록하면 정부 공공데이터를 자동 수집, 분석하고, 방제 타이밍, 시비 일정, 재해 체크리스트, 병해충 대응 지침을 한 화면의 대시보드로 제공합니다.

---

## 주요 기능

| 영역 | 설명 |
|------|------|
| **필지 등록** | 지도에서 위치 선택, 작물, 파종일 입력 후 필지, 기상, 토양, 병해충 데이터 자동 수집 |
| **리스크 점수** | 병해충, 기상, 토양 위험도 0~100점, 원인 설명 및 데이터 출처 제공 |
| **방제 타이밍** | 시간별 예보 분석 — 살포 가능 시간 vs 강수, 풍속으로 연기 권고 |
| **방제 처방** | 농사로 등록 농약, 안전 사용 지침을 작물, 병해충에 맞게 연계 |
| **시비 캘린더** | 흙토람 토양검정, 비료처방 기반 시비 일정 |
| **알림** | 위험 급상승, 방제 전 강수, 고습도, 인근 병해충, 주간 리포트 |
| **재해 예방 센터** | 폭염, 한파, 호우, 건조 위험 및 계절별 체크리스트 |
| **지식 허브** | 병해충, 작물, 농약 통합 검색 |
| **데모 모드** | API 키 없이 샘플 데이터로 전체 UI 체험 |

## 기술 스택

| 구분 | 기술 |
|------|------|
| 프론트엔드 | Next.js 14, React, Tailwind CSS, Leaflet |
| 백엔드 | FastAPI, SQLAlchemy (async), SQLite |
| 배포 | Netlify (프론트) + Render (백엔드) — `render.yaml` 참고 |

## 빠른 시작

**필요 환경:** Python 3.11+, Node.js 20+, npm

```powershell
git clone https://github.com/wgowgo/farmguard-ai.git
cd farmguard-ai
copy .env.example .env
.\start.ps1
```

| URL | 설명 |
|-----|------|
| http://localhost:3000 | 프론트엔드 |
| http://localhost:8000 | 백엔드 API |
| http://localhost:8000/docs | API 문서 |
| http://localhost:3000/admin | 관리자 화면 |

`start.ps1`은 `.env`가 없으면 `.env.example`을 복사하고, 의존성 설치 후 두 서버를 실행합니다.

## 환경변수

프로젝트 루트에 `.env.example`을 `.env`로 복사하세요. **`.env`는 절대 커밋하지 마세요.**

```env
PUBLIC_DATA_SERVICE_KEY=   # data.go.kr — 팜맵, 기상청, 토양/비료
NONGSARO_API_KEY=          # 농사로 Open API 8종
NCPMS_API_KEY=             # 선택 — NCPMS (현재 미사용)
DEMO_MODE=true             # true = API 키 없이 데모 데이터
DATABASE_URL=sqlite+aiosqlite:///./farmguard.db
OPENAI_API_KEY=            # 선택 — 추후 확장용
```

실 API 사용 시 `DEMO_MODE=false`로 설정하고 키를 입력하세요.

## 연동 데이터

| 출처 | API | 용도 |
|------|-----|------|
| **팜맵** | 조회, 기상, 토양, 병해충 | 필지 매칭, 위험도 산출 |
| **기상청** | 초단기실황, 예보, 단기예보 | 방제 타이밍, 7일 전망 |
| **농사로** | 8종 (발생정보, 농약, 재해예방 등) | 병해충 정보, 등록 농약 |
| **흙토람** | 토양검정 V2, 비료처방 | 토양 상세, 시비 계획 |

팜맵 좌표계: **EPSG:5179**

## 주요 화면

| 경로 | 기능 |
|------|------|
| `/` | 홈, 데모 챗봇 |
| `/dashboard` | 위험도, 예보 차트, 방제 타이밍, 지도 |
| `/fields/register` | 지도에서 필지 등록 |
| `/fields/[id]` | 토양, 기상, 시비 캘린더, 병해충 |
| `/fields/[id]/pest/[name]` | 병해충 상세, 방제 처방 |
| `/disasters` | 재해 예방 센터 |
| `/knowledge` | 농사로 API 탐색, 검색 |
| `/alerts` | 알림 설정 및 이력 |
| `/admin` | API 상태, 수집 로그, 데모 토글 |

## API 테스트

```powershell
cd backend
.\.venv\Scripts\python.exe scripts\test_apis.py
```

## 프로젝트 구조

```
farmguard-ai/
├── .env.example
├── start.ps1
├── render.yaml
├── backend/
│   ├── app/
│   │   ├── routers/       # fields, admin, knowledge, crops, disasters
│   │   └── services/      # collector, risk_engine, nongsaro, soil, ...
│   └── scripts/test_apis.py
└── frontend/              # Next.js 14
```
