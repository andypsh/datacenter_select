# 03_분석/

V1 CSV 결과물을 프론트엔드가 소비할 JSON으로 변환하는 Python 코드.

## 구성

- `coords.py` — 시군 이름 → 위경도 매핑 (109개, 수기 작성)
- `build_scores.py` — `../_v1_data/06_실거래가/가중치데이터_최종.csv` + `coords.py` → `../04_시각화/frontend/public/data/regions.json`
- `requirements.txt` — pandas, geopandas 등

## 실행

```bash
pip install -r requirements.txt
python build_scores.py
```

## 산출물 스키마

`frontend/public/data/regions.json`:

```json
{
  "factors": [
    {"key": "temp", "label": "평균기온", "unit": "°C", "direction": "lower_is_better"},
    {"key": "earthquake", "label": "지진위험도", "unit": "z", "direction": "lower_is_better"},
    {"key": "typhoon", "label": "태풍위험도", "unit": "z", "direction": "lower_is_better"},
    {"key": "companies", "label": "SW 기업 갯수", "unit": "개", "direction": "higher_is_better"},
    {"key": "price", "label": "실거래가", "unit": "만원", "direction": "lower_is_better"}
  ],
  "regions": [
    {
      "name": "가평군",
      "lat": 37.831,
      "lng": 127.510,
      "factors": {
        "temp": 10.92,
        "earthquake": -0.225,
        "typhoon": 0.532,
        "companies": 24,
        "price": 15387.63
      }
    }
  ]
}
```

## V1에서 가져오는 데이터

| 출처 | 컬럼 | 비고 |
|------|------|------|
| `_v1_data/06_실거래가/가중치데이터_최종.csv` | 시군, 평균기온, 지진위험도, 태풍위험도, 기업갯수, 거래금액 | 109개 시군 |
| `coords.py` | lat, lng | 수기 좌표 (시청·군청 위치 기준) |

## 다음 단계 (TODO — 공모전 9개 지표 확장)

- [ ] 좌표 데이터를 행정구역 GeoJSON으로 교체 (히트맵 → 폴리곤 채색)
- [ ] **9개 지표 확장**: 신규 4개 (통신·인력·지역활력·ESG) 수집/계산 스크립트
- [ ] 실시간 데이터 (KEPCO OpenAPI, KPX, KICOX, 기상청) 페치 스크립트 → `02_데이터/raw/`
- [ ] 시계열 데이터 추가 (`_v1_data/02_계약종별전력사용량` 연도별 결과 활용)
