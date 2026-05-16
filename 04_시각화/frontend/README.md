# frontend/

Vue 3 + Vite + TypeScript 인터랙티브 입지 탐색 웹앱.

## 실행

```bash
# 1) 데이터 먼저 빌드 (한 번만)
cd ../analysis && python build_scores.py && cd ../frontend

# 2) 개발 서버
npm install
npm run dev
# → http://localhost:5173

# 3) 빌드
npm run build
# → dist/
```

## 스택

- **Vue 3.5** + **TypeScript** + **Vite 6**
- **MapLibre GL** — OSM 타일 + 시군별 점수 마커
- **ECharts** (vue-echarts) — 막대/산점/레이더 차트
- **Pinia** — 가중치/점수 상태 관리
- **Tailwind CSS** — UI

## 구조

```
src/
├── App.vue                     # 탭 라우터 (지도/대시보드/비교)
├── main.ts
├── types.ts                    # FactorKey, Region, ScoredRegion 타입
├── stores/
│   └── scoring.ts              # 가중치 → 정규화 → 점수 (반응형)
└── components/
    ├── MapView.vue             # MapLibre 지도 + 마커
    ├── WeightPanel.vue         # 가중치 슬라이더 + Top 10 리스트
    ├── Dashboard.vue           # ECharts 대시보드
    └── CompareView.vue         # 후보지 레이더 비교 + 표
public/
└── data/regions.json           # ← analysis/build_scores.py 산출물
```

## 점수 계산 로직

`stores/scoring.ts`:

1. 각 요인을 시군 전체 min-max 정규화 → [0, 1]
2. `direction === 'lower_is_better'` 인 요인은 `1 - v` 로 반전
3. 가중치 합으로 정규화 (슬라이더 값의 합이 100%가 되도록)
4. 가중 평균 → 종합점수 [0, 1]

## TODO

- [ ] 좌표를 행정구역 GeoJSON 폴리곤으로 교체 (점 마커 → 채색)
- [ ] 실제 데이터센터 위치 마커 추가 (`데이터센터위치.csv`)
- [ ] 시계열 슬라이더 (월별 전력사용량 변화)
- [ ] GitHub Pages 배포 워크플로
