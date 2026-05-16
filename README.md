# 제14회 산업통상자원부 공공데이터 활용 아이디어 공모전

> **프로젝트명**: AI 데이터센터 최적입지 분석 — 지역균형 발전 관점
> **참가 부문**: 제품·서비스 개발 (인터랙티브 웹앱)
> **공간 단위**: 시군구 (전국 109개)
> **마감**: 2026-07-06
> **공식**: https://datacontest.kr
> **GitHub**: https://github.com/andypsh/datacenter_select/tree/contest-v2-14th
> **🚀 라이브 데모**: https://datacenter-select-ds9x.vercel.app

---

## 폴더 구조

```
datacenter_contest/
├── 00_공모전정보/        # 14회 요강, 평가기준, 과거 수상작 분석
├── 01_프로젝트기획/      # 컨셉, 차별화 포인트, 정책 프레이밍
├── 02_데이터/
│   ├── raw/             # 원본 공공데이터
│   └── processed/       # 전처리된 V2 지표
├── 03_분석/             # build_scores.py, coords.py, requirements.txt
├── 04_시각화/frontend/  # Vue 3 + MapLibre + ECharts 대시보드
├── 05_보고서/           # 최종 보고서
└── 06_발표/             # PPT, 데모 GIF
```

---

## 14회 공모전 핵심 요약

| 항목 | 내용 |
|---|---|
| 주제 | "공공데이터로 견인하는 **지역활력**, AI 데이터로 도약하는 **기업 성장**" |
| 부문 | 아이디어 기획 / **제품·서비스 개발** (선택) |
| 모집 기간 | 2026-03-30 ~ 2026-07-06 |
| 총 상금 | 5,700만원 / 대상 = 산업부 장관상 |
| 필수 조건 | 산업부 + 산하 공공기관 데이터 활용 |

---

## 빠른 시작

### 1) 데이터 전처리 (Python)
```bash
cd 03_분석
pip install -r requirements.txt
python build_scores.py
# → 04_시각화/frontend/public/data/regions.json 생성
```

### 2) 프론트엔드 (Vue)
```bash
cd 04_시각화/frontend
npm install
npm run dev
# → http://localhost:5173
```

> Node 18+ 필요. 현재 Node 16 사용 중이면 업그레이드 필요.

---

## 9개 평가지표

| # | 지표 | 출처 | 산업부 산하 |
|---|---|---|---|
| 1 | 전력 공급 안정성 | KEPCO + KPX | ✅ |
| 2 | 평균기온 (냉각 효율) | 기상청 | ❌ |
| 3 | 지진 위험도 | 기상청 | ❌ |
| 4 | 태풍 위험도 | 기상청 | ❌ |
| 5 | 토지 비용 | 국토부 실거래가 | ❌ |
| 6 | 산업 집적도 | KICOX + 통계청 | ✅ |
| 7 | SW 기업 수 | 통계청 KOSIS | ❌ |
| 8 | 지역활력 기여도 | 행안부 + 통계청 | ❌ |
| 9 | 재생에너지 접근성 | KEA + 한전 | ✅ |

---

## 차별화 (V1 → V2)

| 항목 | V1 (2022) | V2 (2026) |
|---|---|---|
| 지표 | 5개 | **9개** |
| 가중치 | 고정 | **인터랙티브 슬라이더** |
| 시나리오 | 단일 | **프리셋 3종** (비용/안정성/지역균형) |
| 지역균형 분석 | ❌ | **비수도권 Top 10 별도** |
| 정책 제언 | ❌ | **5개 자동 생성** |
| 데이터 출처 추적 | ❌ | **산업부 산하 명시** |

---

## 진행 상황

- [x] V1 자산 마이그레이션
- [x] 9개 지표 데이터 구조 확장 (V2 placeholder 합성 동작)
- [x] 시나리오 프리셋 3종 (지역균형/비용/안정성)
- [x] 정책 제언 5종 자동 생성
- [x] 비수도권 Top 10 별도 표시
- [ ] V2 4개 지표 실데이터 수집 (전력/산단/지역활력/재생에너지)
- [ ] npm install + 빌드 검증
- [ ] 보고서 / PPT 완성
- [ ] Vercel 배포 (또는 GitHub Pages / Netlify)
- [ ] 7/6 제출

---

## 배포 (Vercel)

Vue 3 + Vite 프로젝트라 **Vercel이 가장 간단**. CLI 또는 GitHub 연동 모두 OK.

### 옵션 A: Vercel CLI (가장 빠름)
```powershell
cd C:\dev\datacenter_contest\04_시각화\frontend
npm install -g vercel
vercel login
vercel --prod
# → https://datacenter-contest-xxx.vercel.app
```

빌드 설정 자동 감지(`vite`). 첫 배포 후 `vercel --prod` 한 번 더 누르면 production URL 확정.

### 옵션 B: GitHub 연동 (자동 재배포)
1. https://vercel.com/new → "Import Git Repository"
2. `andypsh/datacenter_contest_v2` 선택
3. **Root Directory**: `04_시각화/frontend` ← 중요 (모노레포 구조라 필수)
4. Framework Preset: **Vite** (자동 감지됨)
5. Build Command: `npm run build` / Output: `dist/`
6. Deploy → push할 때마다 자동 재배포

### 대안: Netlify
- 거의 동일. `netlify deploy --prod --dir=04_시각화/frontend/dist`
- GitHub 연동 시 Base directory를 `04_시각화/frontend`로

### 대안: GitHub Pages
- 무료지만 SPA 라우팅 + base path 손봐야 함. `vite.config.ts`에 `base: '/datacenter_contest_v2/'` 추가 필요.
- Vercel이 훨씬 편함.

> ⚠️ **Node 18+ 필수**. 현재 Node 16이면 `nvm-windows`로 18 LTS 설치 먼저.
