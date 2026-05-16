"""V1 CSV + 신규 지표 → 프론트엔드 JSON 빌드.

9개 평가지표 (공모전 컨셉 확정안):
  1. 전력 안정성  (extra_data proxy, higher better)
  2. 자연재해 안전 (V1 지진+태풍 평균, lower better)
  3. 기온         (V1, lower better)
  4. 토지비용     (V1 실거래가, lower better)
  5. 산업 집적도  (V1 SW기업, higher better)
  6. 통신 인프라  (extra_data proxy, higher better)
  7. IT 인력      (extra_data proxy, higher better)
  8. 지역활력     (인구감소지역, higher better) ★주제 직격
  9. 재생에너지   (extra_data proxy, higher better)

입력: ../_v1_data/06_실거래가/가중치데이터_최종.csv
출력: ../04_시각화/frontend/public/data/regions.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

from coords import COORDS
from derived import (
    industry_cluster_real,
    industry_raw_count,
    it_workforce_real,
    power_stability_real,
    renewable_access_real,
    telecom_infra_real,
)
from extra_data import (
    regional_vitality,  # 행안부 89개 인구감소지역 (공식)
)

ROOT = Path(__file__).resolve().parents[1]
SRC_CSV = ROOT / "_v1_data" / "06_실거래가" / "가중치데이터_최종.csv"
OUT_JSON = ROOT / "04_시각화" / "frontend" / "public" / "data" / "regions.json"

# Factor 정의 (순서 = UI 표시 순서)
FACTORS = [
    {
        "key": "power_stability", "label": "전력 안정성", "unit": "점",
        "direction": "higher_is_better", "default_weight": 18,
        "desc": "V1 전력사용량 시계열 (평균·추세·변동성) 합성",
        "category": "전력",
    },
    {
        "key": "disaster_risk", "label": "자연재해 위험", "unit": "z",
        "direction": "lower_is_better", "default_weight": 10,
        "desc": "지진·태풍 위험도 평균 (낮을수록 안전)",
        "category": "안전",
    },
    {
        "key": "temp", "label": "평균기온", "unit": "°C",
        "direction": "lower_is_better", "default_weight": 8,
        "desc": "낮을수록 냉각 비용 ↓",
        "category": "환경",
    },
    {
        "key": "price", "label": "토지 비용", "unit": "만원",
        "direction": "lower_is_better", "default_weight": 10,
        "desc": "실거래가 평균 (낮을수록 부지 확보 비용 ↓)",
        "category": "비용",
    },
    {
        "key": "companies", "label": "산업 집적도", "unit": "개",
        "direction": "higher_is_better", "default_weight": 10,
        "desc": "SW회사 raw 40k에서 시군별 가중 카운트 (대=3, 중견=2, 중소=1)",
        "category": "산업",
    },
    {
        "key": "telecom_infra", "label": "통신 인프라", "unit": "점",
        "direction": "higher_is_better", "default_weight": 9,
        "desc": "광케이블 66 노드 → 시군 50/100km 인접도 점수",
        "category": "통신",
    },
    {
        "key": "it_workforce", "label": "IT 인력", "unit": "점",
        "direction": "higher_is_better", "default_weight": 8,
        "desc": "SW회사 raw × 규모별 표준 종사자 추정 (대=1500, 중견=250, 중소=18) log합성",
        "category": "인력",
    },
    {
        "key": "regional_vitality", "label": "지역활력", "unit": "점",
        "direction": "higher_is_better", "default_weight": 18,
        "desc": "★14회 주제 직격 — 행안부 인구감소지역 지정",
        "category": "지역활력",
    },
    {
        "key": "renewable_access", "label": "재생에너지", "unit": "점",
        "direction": "higher_is_better", "default_weight": 9,
        "desc": "공공데이터포털 50k 태양광 발전소 raw → 시군별 가동수+설비용량 log합성",
        "category": "ESG",
    },
]
# 합계 검증
assert sum(f["default_weight"] for f in FACTORS) == 100, "default_weight 합 ≠ 100"

V1_COL_MAP = {
    "시군": "name",
    "평균기온(°C)": "temp",
    "지진위험도": "earthquake_z",
    "태풍위험도": "typhoon_z",
    "기업갯수": "companies",
    "거래금액(만원)": "price",
}


def main() -> int:
    if not SRC_CSV.exists():
        print(f"❌ 입력 CSV 없음: {SRC_CSV}", file=sys.stderr)
        return 1

    df = pd.read_csv(SRC_CSV, encoding="utf-8-sig")
    df = df.rename(columns=V1_COL_MAP)[list(V1_COL_MAP.values())]

    regions = []
    missing_coords: list[str] = []
    for _, row in df.iterrows():
        name = str(row["name"])
        coord = COORDS.get(name)
        if coord is None:
            missing_coords.append(name)
            continue
        lat, lng = coord
        eq = float(row["earthquake_z"])
        ty = float(row["typhoon_z"])
        disaster = (eq + ty) / 2.0

        factors_value = {
            # 실데이터 파생 (derived.py)
            "power_stability": round(power_stability_real(name), 2),
            "telecom_infra": round(telecom_infra_real(name), 2),
            "companies": industry_raw_count(name) or int(row["companies"]),
            # V1 그대로
            "disaster_risk": round(disaster, 4),
            "temp": round(float(row["temp"]), 3),
            "price": round(float(row["price"]), 1),
            # 실데이터 (KEA 신재생)
            "renewable_access": round(renewable_access_real(name), 2),
            # 행안부 89개 인구감소지역 (공식)
            "regional_vitality": round(regional_vitality(name), 2),
            # SW회사 raw × 기업규모별 표준 종사자 추정
            "it_workforce": round(it_workforce_real(name), 2),
        }
        assert set(factors_value.keys()) == {f["key"] for f in FACTORS}

        regions.append({
            "name": name,
            "lat": lat,
            "lng": lng,
            "factors": factors_value,
        })

    if missing_coords:
        print(f"⚠️  좌표 없는 시군 {len(missing_coords)}개: {missing_coords}", file=sys.stderr)

    payload = {
        "version": 2,
        "source": [
            "_v1_data/06_실거래가/가중치데이터_최종.csv (자연재해·기온·실거래가)",
            "_v1_data/02_계약종별전력사용량/.../2012-2022전국.csv (전력 안정성 파생)",
            "_v1_data/04_sw기업개수/광케이블 지도/광케이블.csv (통신 인프라 파생)",
            "_v1_data/04_sw기업개수/SW회사.csv (산업 집적도 + IT 인력 추정 파생)",
            "02_데이터/raw/KEA_신재생/전국태양광발전소....csv (재생에너지 파생, 50k raw)",
            "행안부 89개 인구감소지역 공식 리스트 (지역활력)",
        ],
        "factors": FACTORS,
        "regions": regions,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ {len(regions)}개 시군 × {len(FACTORS)}개 지표 → {OUT_JSON.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
