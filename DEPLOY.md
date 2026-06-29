# Netlify + Render 배포 가이드

프론트엔드(Netlify) + 백엔드 API(Render) 분리 배포입니다.

## 1. GitHub 업로드

### 1-1. 로컬 준비 (완료됨)

프로젝트 폴더에서 이미 실행된 상태:

- `git init` + 첫 커밋 (96개 파일)
- 브랜치: `main`
- `.env`, `backend/.env`, DB, `node_modules` 등은 `.gitignore`로 제외

### 1-2. GitHub에서 새 저장소 만들기

1. [github.com](https://github.com) 로그인
2. 우측 상단 **+** → **New repository**
3. 설정:
   - Repository name: `farmguard-ai` (원하면 다른 이름 가능)
   - **Public** 또는 **Private** 선택
   - **Add a README file** — 체크 **하지 않음** (로컬에 이미 있음)
   - **Add .gitignore** — **None**
   - **Choose a license** — **None**
4. **Create repository** 클릭
5. 생성 후 나오는 URL 복사  
   예: `https://github.com/내아이디/farmguard-ai.git`

### 1-3. 원격 연결 후 푸시

PowerShell에서 (`YOUR_USER`를 본인 GitHub 아이디로 바꿈):

```powershell
cd "C:\Users\seong\Downloads\농업,농촌_공공데이터\farmguard-ai"
git remote add origin https://github.com/YOUR_USER/farmguard-ai.git
git push -u origin main
```

처음 push 시 GitHub 로그인 창이 뜹니다. (브라우저 또는 Personal Access Token)

### 1-4. 확인

GitHub 저장소 페이지에서 파일 목록이 보이면 성공.  
`.env` 파일이 **없어야** 정상입니다. (`.env.example`만 있음)

> API 키는 GitHub에 올리지 마세요. Render·Netlify 대시보드에서만 설정합니다.

---

## 2. Render (백엔드) — 먼저 배포

1. [render.com](https://render.com) 가입 → **New** → **Blueprint**
2. GitHub 저장소 연결 → `render.yaml` 자동 인식
3. **Environment**에서 Secret 입력:
   - `PUBLIC_DATA_SERVICE_KEY` — 공공데이터포털 키
   - `NONGSARO_API_KEY` — 농사로 키
   - `DEMO_MODE` — `false` (실 API) / `true` (데모)
4. Deploy 완료 후 URL 확인  
   예: `https://farmguard-api.onrender.com`
5. `/health` 접속 → `{"status":"ok"}` 확인

> Render 무료 플랜: 15분 미사용 시 슬립 → 첫 요청 30초~1분 걸릴 수 있음  
> SQLite 데이터는 재배포 시 초기화될 수 있습니다.

---

## 3. Netlify (프론트엔드)

1. [netlify.com](https://netlify.com) 가입 → **Add new site** → **Import an existing project**
2. GitHub 저장소 선택
3. 빌드 설정 (`netlify.toml`이 자동 적용됨):
   - Base directory: `frontend`
   - Build command: `npm run build`
   - Plugin: `@netlify/plugin-nextjs`
4. **Environment variables** 추가:

   | Key | Value |
   |-----|-------|
   | `NEXT_PUBLIC_API_URL` | `https://farmguard-api.onrender.com` (Render URL) |

5. **Deploy site**

배포 URL 예: `https://farmguard-ai.netlify.app`

---

## 4. 동작 확인

| URL | 확인 |
|-----|------|
| `https://YOUR-API.onrender.com/health` | ok |
| `https://YOUR-API.onrender.com/docs` | Swagger |
| `https://YOUR-SITE.netlify.app` | 홈 |
| Netlify → 필지 등록 | API 연동 |

---

## 5. 문제 해결

| 증상 | 해결 |
|------|------|
| Netlify에서 API 호출 실패 | `NEXT_PUBLIC_API_URL` Render URL 확인 (끝 `/` 없음) |
| Render 502 / 슬립 | 1분 대기 후 재시도 (무료 플랜) |
| API 403 | Render에 `PUBLIC_DATA_SERVICE_KEY` 설정 |
| 빌드 실패 | Netlify Node 20, `frontend` base directory 확인 |

---

## 로컬 vs 배포

| | 로컬 | 배포 |
|---|------|------|
| 프론트 | localhost:3000 | Netlify |
| 백엔드 | localhost:8000 | Render |
| API URL | `.env` / 기본값 | Netlify `NEXT_PUBLIC_API_URL` |
