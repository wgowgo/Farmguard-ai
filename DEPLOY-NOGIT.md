# GitHub 없이 Netlify + Render 배포

Git 연결 없이 **로컬에서 직접** 올리는 방법입니다.

---

## 준비물

- [Netlify CLI](https://docs.netlify.com/cli/get-started/) (프론트)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (백엔드 → Render)
- [Docker Hub](https://hub.docker.com) 계정 (무료)

---

## 1. Render (백엔드) — Docker 이미지로 배포

Render는 Git 없이 **Docker Hub 이미지**로 웹 서비스를 만들 수 있습니다.

### 1-1. Docker 이미지 빌드 & 푸시

```powershell
cd farmguard-ai\backend

# Docker Hub 사용자명으로 바꾸세요
$DOCKER_USER = "YOUR_DOCKERHUB_USERNAME"

docker build -t ${DOCKER_USER}/farmguard-api:latest .
docker login
docker push ${DOCKER_USER}/farmguard-api:latest
```

### 1-2. Render에서 서비스 생성

1. [render.com](https://render.com) 가입
2. **New +** → **Web Service**
3. **Deploy an existing image from a registry** 선택
4. Image URL: `docker.io/YOUR_DOCKERHUB_USERNAME/farmguard-api:latest`
5. Name: `farmguard-api` (원하는 이름)
6. Region: Singapore (또는 가까운 지역)
7. Instance: **Free**
8. **Environment Variables** 추가:

   | Key | Value |
   |-----|-------|
   | `PUBLIC_DATA_SERVICE_KEY` | 공공데이터포털 키 |
   | `NONGSARO_API_KEY` | 농사로 키 |
   | `DEMO_MODE` | `false` |
   | `DATABASE_URL` | `sqlite+aiosqlite:///./farmguard.db` |

9. **Create Web Service**

### 1-3. 확인

배포 URL 예: `https://farmguard-api.onrender.com`

브라우저에서 `https://farmguard-api.onrender.com/health` → `{"status":"ok"}`

> 코드 수정 후: 다시 `docker build` → `docker push` → Render **Manual Deploy** → Deploy latest image

---

## 2. Netlify (프론트) — CLI로 배포

GitHub 연결 없이 **Netlify CLI**로 로컬 빌드 결과를 올립니다.

### 2-1. CLI 설치 & 로그인

```powershell
npm install -g netlify-cli
netlify login
```

### 2-2. 배포 (프로젝트 루트에서)

```powershell
cd farmguard-ai

# Render 백엔드 URL로 바꾸세요 (끝에 / 없음)
$env:NEXT_PUBLIC_API_URL = "https://farmguard-api.onrender.com"

netlify deploy --build --prod
```

- 첫 실행: **Create & configure a new site** 선택
- Site name 입력 (예: `farmguard-ai`) → `https://farmguard-ai.netlify.app`

`netlify.toml`이 자동으로 Next.js 플러그인을 사용합니다.

### 2-3. 환경변수 (Netlify 대시보드)

**Site configuration → Environment variables** 에서도 설정 가능:

| Key | Value |
|-----|-------|
| `NEXT_PUBLIC_API_URL` | `https://farmguard-api.onrender.com` |

변경 후 **Deploys → Trigger deploy → Clear cache and deploy site**

---

## 3. 동작 확인

| URL | 기대 결과 |
|-----|-----------|
| Render `/health` | ok |
| Netlify `/` | 홈, 챗봇 |
| Netlify `/fields/register` | 필지 등록 (Render API 연동) |

---

## 4. 업데이트할 때

| 변경 | 방법 |
|------|------|
| **프론트** | `netlify deploy --build --prod` (farmguard-ai 루트) |
| **백엔드** | `docker build` → `docker push` → Render Manual Deploy |

---

## 5. 주의

- Render 무료: 15분 미사용 시 슬립 → 첫 API 호출 30초~1분
- Netlify **Drop**(드래그 zip)은 Next.js SSR에 **안 됨** → CLI 필수
- `.env` 파일은 Netlify/Render 대시보드에만 입력, 업로드하지 말 것
- SQLite는 Render 재배포 시 데이터 초기화 가능

---

## GitHub 쓰고 싶을 때

[DEPLOY.md](./DEPLOY.md) 참고 (Blueprint + Netlify Git 연동)
