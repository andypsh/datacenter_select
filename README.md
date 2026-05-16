# 🗺️ AI 데이터센터 최적입지 — 지역균형 발전 관점

> **제14회 산업통상자원부 공공데이터 활용 아이디어 공모전** 출품작 · 제품·서비스 개발 부문

[![Vue](https://img.shields.io/badge/Vue-3.5-42b883?logo=vue.js&logoColor=white)](https://vuejs.org/)
[![Vite](https://img.shields.io/badge/Vite-6.0-646cff?logo=vite&logoColor=white)](https://vitejs.dev/)
[![MapLibre](https://img.shields.io/badge/MapLibre-GL-396ca7?logo=maplibre&logoColor=white)](https://maplibre.org/)
[![ECharts](https://img.shields.io/badge/Apache-ECharts-aa344d?logo=apache&logoColor=white)](https://echarts.apache.org/)
[![Vercel](https://img.shields.io/badge/Deploy-Vercel-000000?logo=vercel&logoColor=white)](https://vercel.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776ab?logo=python&logoColor=white)](https://python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](#)

**🚀 Live Demo**: https://datacenter-select-ds9x.vercel.app
**📑 기술문서 (라이브)**: https://datacenter-select-ds9x.vercel.app/docs/
**📁 GitHub**: [contest-v2-14th](https://github.com/andypsh/datacenter_select/tree/contest-v2-14th)

---

## 1. 프로젝트 개요

AI 산업 폭증으로 데이터센터 수요가 급증하고 있으나, 국내 데이터센터의 **수도권 집중**과 **전력계통 부담**이 심화되고 있다. 본 프로젝트는 산업통상부 산하 공공데이터를 활용해 전국 **109개 시군 × 9개 평가지표** 입지 적합도 모델을 구축하고, 정책 담당자가 **가중치를 직접 조절**하며 후보지를 탐색할 수 있는 **인터랙티브 의사결정 지원 대시보드**를 제공한다.

**핵심 차별점**

| 차원 | 일반 입지 분석 | 본 프로젝트 |
|---|---|---|
| 지표 | 5~7개 | **9개** (지역활력 포함) |
| 가중치 | 고정 | **실시간 슬라이더** |
| 시나리오 | 단일 | **프리셋 3종** (비용/안정성/지역균형) |
| 견고성 검증 | ❌ | **민감도 분석 18 시나리오** |
| 결과물 | PDF 보고서 | **인터랙티브 웹앱 + 자동 정책 제언 5종** |
| 데이터 출처 | 불명확 | **산업부 산하 데이터 명시 (3/9)** |

---

## 2. 기술 스택

| 영역 | 기술 |
|---|---|
| **분석** | Python 3.10 · pandas 2.2 · numpy · geopandas · openpyxl |
| **프론트엔드** | Vue 3.5 (Composition API) · Vite 6 · TypeScript 5.6 |
| **상태관리** | Pinia 2.2 |
| **시각화** | MapLibre GL JS 4.7 (지도) · Apache ECharts 5.5 (차트) |
| **스타일** | Tailwind CSS 3.4 · Pretendard 폰트 |
| **배포** | Vercel (자동 배포, contest-v2-14th 브랜치) |
| **데이터** | KEPCO 광케이블 · 데이터센터 위치 · 행안부 인구감소지역 · 기상청 재해위험도 |

---

## 3. 아키텍처

```
공공 raw 데이터 ──┐
(광케이블 66노드,    │
 DC 89곳,           │   ┌─────────────────────┐    ┌─────────────────────┐
 행안부 지정,       ├──▶│ derive_indicators.py│───▶│ indicators_v2.csv   │
 재생E 허브,        │   │  (Haversine·Min-Max)│    │  (109시군 × 4지표)  │
 기상청 재해)       │   └─────────────────────┘    └──────────┬──────────┘
                  │                                          │
                  │                                          ▼
                  │   ┌─────────────────────┐    ┌─────────────────────┐
V1 통합 CSV       ├──▶│  build_scores.py    │───▶│  regions.json       │
(5개 V1 지표)     │   │  (9지표 통합 JSON)  │    │ (109시군 × 9지표)   │
                  │   └─────────────────────┘    └──────────┬──────────┘
                  │                                          │
                  └──────────────────────────────────────────│
                                                             ▼
                                              ┌─────────────────────────┐
                                              │   Vue 3 Dashboard       │
                                              │   (MapLibre+ECharts)    │
                                              │ ─ 가중치 슬라이더 9개   │
                                              │ ─ 시나리오 프리셋 3종    │
                                              │ ─ Top10 / 비수도권 Top10│
                                              │ ─ 정책 제언 5종         │
                                              └──────────┬──────────────┘
                                                         │
                                                         ▼ Vercel auto-deploy
                                          datacenter-select-ds9x.vercel.app
```

---

## 4. 디렉토리 구조

```
datacenter_contest/
├── README.md                          # 본 문서
├── docs/
│   └── index.html                     # 기술문서 (1페이지 SPA, source-of-truth)
│                                      # → Vercel에는 frontend/public/docs/ 로 복사되어 서빙됨
│                                      # → 라이브: /docs/ 경로로 접근
├── 00_공모전정보/
│   └── 14회_요강.md                   # 14회 공모전 요강·과거 수상작
├── 01_프로젝트기획/
│   └── 컨셉.md                        # 컨셉·차별화·9지표 정의
├── 02_데이터/
│   ├── raw/                           # 원본 공공데이터
│   │   ├── 가중치데이터_최종.csv     # V1 통합 (5지표)
│   │   ├── 광케이블/광케이블.xlsx     # 백본 66 노드
│   │   ├── 데이터센터위치/            # 기존 IDC 89곳
│   │   └── 재해위험도/                # 기상청 z-score
│   └── processed/
│       └── indicators_v2.csv          # 파생 4지표 산출 결과
├── 03_분석/                           # Python 분석 코드
│   ├── derive_indicators.py           # 파생변수 산출 (Haversine·정규화)
│   ├── build_scores.py                # 9지표 통합 → regions.json
│   ├── sensitivity_analysis.py        # 가중치 ±20% 민감도 (18시나리오)
│   ├── analyze_results.py             # 보고서용 통계표 자동 생성
│   ├── coords.py                      # 시군 좌표 매핑 (109개)
│   └── requirements.txt
├── 04_시각화/
│   └── frontend/                      # Vue 3 + Vite 대시보드
│       ├── src/
│       │   ├── App.vue                # 4탭 라우팅 (지도/대시보드/비교/정책)
│       │   ├── types.ts               # 9 FactorKey 정의
│       │   ├── stores/scoring.ts      # Pinia 가중치·점수 상태
│       │   └── components/
│       │       ├── MapView.vue        # MapLibre 지도
│       │       ├── WeightPanel.vue    # 가중치 슬라이더 9개 + 프리셋
│       │       ├── Dashboard.vue      # ECharts 차트
│       │       ├── CompareView.vue    # 후보지 비교 레이더
│       │       └── PolicyView.vue     # 정책 제언 5종
│       ├── public/data/regions.json   # 분석 산출물 (109×9)
│       └── vercel.json
├── 05_보고서/
│   ├── 보고서.md                      # 8장 본문 (실데이터 채움)
│   ├── results_tables.md              # 결과 통계표 (자동 생성)
│   └── sensitivity_table.md           # 민감도 분석표 (자동 생성)
└── 06_발표/
    └── PPT_슬라이드.md                # Marp 형식 18장 + Q&A
```

---

## 5. Gitflow-lite 브랜치 전략

```
main                  ←  V1 (2022) 보존 + 부분 V2 작업 흔적
  │
  └── contest-v2-14th ←  ★ 14회 공모전 출품 작업물 (production)
                         · Vercel auto-deploy 연결
                         · 모든 분석·문서·발표자료 포함
```

- **main**: V1 원본 코드/데이터 보존용. 수정 없음
- **contest-v2-14th**: 모든 V2 작업이 들어간 단일 브랜치. Vercel production branch
- 향후 통합 시 main으로 재정리 또는 별도 PR

---

## 6. Vercel 배포 파이프라인

```
git push origin contest-v2-14th
    │
    ▼
GitHub webhook → Vercel
    │
    ▼
┌─────────────────────────────────────┐
│ Root directory: 04_시각화/frontend  │
│ Build cmd:      npm run build       │
│ Output:         dist/               │
│ Node version:   20.x (cloud)        │
└────────────────┬────────────────────┘
                 ▼
        datacenter-select-ds9x.vercel.app
        (~20s 빌드 → 자동 배포)
```

- **Production Branch**: `contest-v2-14th` (Vercel Settings → Environments → Production)
- **Auto-rebuild**: 푸시 시 약 20초 만에 라이브 반영

---

## 7. 로컬 개발

### 7.1 데이터 분석 파이프라인
```bash
cd 03_분석
pip install -r requirements.txt

# 1) 4개 V2 파생지표 산출 (광케이블·DC분포·인구감소·재생E)
python derive_indicators.py

# 2) 9개 지표 통합 → regions.json
python build_scores.py

# 3) 민감도 분석 (가중치 ±20% × 9지표 = 18 시나리오)
python sensitivity_analysis.py

# 4) 보고서용 결과 통계표
python analyze_results.py
```

### 7.2 프론트엔드
```bash
cd 04_시각화/frontend
npm install            # Node 18+ 필요
npm run dev            # http://localhost:5173
npm run build          # production 빌드
npm run typecheck      # TS 타입 검사
```

---

## 8. 핵심 기술 결정

### 8.1 왜 시군 단위인가
- **정책 단위 일치**: 지자체 인센티브 설계의 기본 단위
- **인구감소지역 지정 단위**와 동일 (행안부 89개 지정)
- **데이터 결손 적음**: 격자/읍면동 단위보다 안정적
- **109개**: 인터랙티브 지도 + 시나리오 분석에 적합한 카디널리티

### 8.2 왜 파생변수를 raw에서 직접 산출하나
플레이스홀더 합성 대신 원본 raw 데이터(광케이블 좌표·DC 좌표 등)에서 **Haversine 거리 + 카운트** 기반으로 직접 산출. 산출 레시피가 코드로 공개되어 **재현 가능성·심사 신뢰성** 확보.

| 파생변수 | 원본 raw | 산출 방법 |
|---|---|---|
| `power` | 광케이블 66 노드 | 시군 30km 내 노드 수 → Min-Max |
| `industry` | 기존 IDC 89곳 | 시군 30km 내 DC 수 → Min-Max |
| `vitality` | 행안부 + DC 분포 | `(1-DC밀도)×0.6 + 인구감소×0.4` |
| `renewable` | 호남솔라/강원풍력 | `exp(-거리/100km)` 지수감쇠 |

### 8.3 왜 MapLibre + ECharts 조합인가
- **MapLibre GL**: Mapbox v1 fork, 오픈소스, OSM 타일 무료, GPU 렌더링 → 109 마커 부드러움
- **Apache ECharts**: 레이더/막대/산점도 모두 한 라이브러리로 일관성, 한국어 폰트 호환성 우수

### 8.4 왜 Pinia 상태관리인가
- 9개 가중치 + 109시군 점수 + 비교셋 + 시나리오 = 다층 reactive 상태
- Pinia의 `computed` chain → 가중치 변경 시 정규화·점수·Top10 모두 자동 재계산
- DevTools에서 슬라이더 액션 추적 용이

---

## 9. 디버깅 회고

### 9.1 OneDrive 한글 경로 파일 사라짐 이슈
- **증상**: `C:\Users\andyp\Desktop\공모전\` 안에 만든 파일이 시간 지나면 사라짐
- **원인**: Desktop이 OneDrive 동기화 대상이라 한글 경로 파일이 cloud-only로 변환
- **해결**: 작업폴더를 `C:\dev\datacenter_contest\` 로 이전 (OneDrive 영역 밖)

### 9.2 Vercel CLI Node 16 호환성
- **증상**: `vercel login` 실행 시 `ReferenceError: ReadableStream is not defined`
- **원인**: Vercel CLI 54.x가 Node 18+ API에 의존
- **해결**: 로컬 CLI 폐기, **Vercel 웹 UI + GitHub 연동** 경로로 대체. Vercel 클라우드는 Node 20 사용하므로 빌드 정상

### 9.3 한글 경로 + Korean filename encoding
- **증상**: 광케이블 CSV/XLSX의 컬럼명이 깨진 문자로 표시
- **원인**: V1에서 저장 과정 중 cp949/utf-8 mismatch
- **해결**: 컬럼명 무시하고 **위경도 범위 (33-39 lat / 124-132 lng)로 자동 식별**

### 9.4 Vercel 초기 배포가 main 브랜치로 시작
- **증상**: `contest-v2-14th` 푸시했는데 라이브에 V1 콘텐츠 표시
- **원인**: Vercel 프로젝트 import 시 default branch(main)를 production으로 자동 지정
- **해결**: Settings → Environments → Production → Branch Tracking을 `contest-v2-14th`로 변경 후 Promote to Production

---

## 10. UX 결정 노트

### 10.1 가중치 슬라이더 + 프리셋 동시 제공
초보자는 프리셋 3종(비용/안정성/**지역균형**)으로 즉시 결과 확인, 전문가는 슬라이더 미세 조정. 슬라이더 조작 시 활성 프리셋 자동 해제.

### 10.2 비수도권 Top 10을 별도 패널로
전국 Top 10에는 수도권이 섞이지만 정책 담당자가 가장 보고 싶어할 **비수도권 후보지를 항상 시야 안에** 배치.

### 10.3 정책 제언이 가중치에 반응
정적 텍스트 대신 `computed()` 로 현재 가중치 기준 Top10·인구감소비율을 받아 정책 문장에 직접 인용. 가중치 바꿀 때마다 추천 내용이 살아 움직임.

### 10.4 산업부 산하 데이터 시각 배지
9개 지표 라벨 옆에 산업부 산하 데이터에만 파란색 "산업부" 배지 부착. 심사위원이 한눈에 데이터 출처 정합성 파악.

---

## 11. 향후 개선

- [ ] 시군 단위 → **격자(1km) 단위** 정밀도 향상 (행정구역 GeoJSON 도입)
- [ ] V1 (2022) → **2023~2025 시계열** 데이터 갱신
- [ ] 추가 지표: **광케이블 거리** · 물류 접근성 · 인력 공급 (KOSIS)
- [ ] **AHP/Entropy** 객관 가중치 옵션 (현재 Min-Max + 사용자 슬라이더)
- [ ] 단일 입지 → **권역별 클러스터링** 분석 확장
- [ ] **PWA** 변환 (오프라인 동작 + 모바일 설치)
- [ ] **다국어** (영문) — 글로벌 빅테크 투자 유치 도구 활용

---

## 12. 라이선스 / 데이터 출처

- **코드**: MIT
- **공공데이터**: 공공데이터포털 (https://data.go.kr) 개방 라이선스 준수
- **지도 타일**: OpenStreetMap © contributors
- **폰트**: Pretendard (OFL)
