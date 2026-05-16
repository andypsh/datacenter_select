# 데이터센터 최적입지 선정 — V2 (Interactive)

V1 (2022) 분석을 Vue.js 인터랙티브 웹앱으로 리뉴얼.
사용자가 가중치를 직접 조절하면서 지도 위에서 입지를 탐색하고 비교할 수 있음.

## 빠른 시작

```bash
# 1) 데이터 전처리 (Python) — V1 CSV → JSON
cd analysis
pip install -r requirements.txt
python build_scores.py
# → frontend/public/data/regions.json 생성

# 2) 프론트엔드 (Vue) 실행
cd ../frontend
npm install
npm run dev
# → http://localhost:5173
```

## 아키텍처

```
데이터센터_프로젝트_V2/
├── frontend/              # Vue 3 + Vite + TypeScript
│   ├── src/
│   │   ├── components/
│   │   │   ├── MapView.vue       # MapLibre 지도 + 히트맵
│   │   │   ├── WeightPanel.vue   # 가중치 슬라이더
│   │   │   ├── Dashboard.vue     # ECharts 차트
│   │   │   └── CompareView.vue   # 후보지 비교
│   │   ├── stores/scoring.ts     # Pinia 가중치/점수 상태
│   │   ├── types.ts
│   │   └── App.vue
│   ├── public/data/regions.json  # ← analysis/build_scores.py 산출물
│   └── package.json
├── analysis/              # Python 모던 분석
│   ├── build_scores.py    # V1 CSV → regions.json 변환
│   ├── coords.py          # 시군 좌표 매핑 (109개)
│   ├── requirements.txt   # pandas 2.x, geopandas 등
│   └── README.md
├── 01_데이터센터/ ~ 07_QGIS병합/  # V1 원본 자료 (참조용, 점진 마이그레이션)
├── 기타_자료/                     # 참고 PDF (gitignore)
├── 발표자료/                      # V1 보고서 (gitignore)
└── README.md
```

## 핵심 기능

- 🗺️ **지도 기반 입지 탐색** — MapLibre GL 위에 시군별 점수 히트맵, 데이터센터 위치 마커
- 🎚️ **가중치 슬라이더** — 전력·기온·재해·실거래가·SW기업 등 요인별 가중치를 즉시 조절
- 📊 **데이터 대시보드** — ECharts로 시계열·분포·요인별 기여도 시각화
- 🆚 **비교 모드** — 후보지 2~3곳을 나란히 비교 (레이더 차트)

## V1 vs V2

| 항목 | V1 (2022) | V2 (2026~) |
|------|-----------|-----------|
| 분석 도구 | Jupyter Notebook (수동) | Python 스크립트 (재현 가능) |
| 시각화 | QGIS 정적 PNG, PPTX | Vue + MapLibre + ECharts (인터랙티브) |
| 가중치 | 고정값, 보고서 작성 시점 결정 | 사용자가 슬라이더로 실시간 조절 |
| 결과물 | PDF 보고서 | 웹앱 (배포 가능) + 보고서 |
| 데이터 갱신 | 수동 재작업 | `build_scores.py` 재실행 |

## V1 위치 (보존)

- `../데이터센터_프로젝트/` — 2022 원본
- `../데이터센터_프로젝트_정리/` — 주제별 정리본 (V2 베이스)
- `../데이터센터_최적입지선정_행안부/` — 2023 행안부 공모전

## 로드맵

- [x] V1 자료 V2로 이관, `.gitignore` 정리, GitHub 푸시
- [ ] **(진행 중)** Vue 스캐폴딩 + 1차 데모 (지도 + 가중치 슬라이더 + 차트 + 비교)
- [ ] 데이터 최신화 — 2023~ 한국전력/기상청/실거래가
- [ ] QGIS 작업물 → geopandas 스크립트화
- [ ] 후보지 자동 추천 (top-N) 로직
- [ ] 보고서 재작성 (V2 결과 반영)
- [ ] GitHub Pages 배포

## 라이선스

내부 학습/연구용. 외부 공개 전 데이터 출처 확인 필요.
