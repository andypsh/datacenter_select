"""V1 CSV → 프론트엔드 JSON 빌드 스크립트.

입력: ../_v1_data/06_실거래가/가중치데이터_최종.csv
출력: ../04_시각화/frontend/public/data/regions.json

사용:
    python build_scores.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

from coords import COORDS

ROOT = Path(__file__).resolve().parents[1]
SRC_CSV = ROOT / "_v1_data" / "06_실거래가" / "가중치데이터_최종.csv"
OUT_JSON = ROOT / "04_시각화" / "frontend" / "public" / "data" / "regions.json"

FACTORS = [
    {"key": "temp", "label": "평균기온", "unit": "°C", "direction": "lower_is_better",
     "desc": "낮을수록 냉각 비용 ↓"},
    {"key": "earthquake", "label": "지진위험도", "unit": "z", "direction": "lower_is_better",
     "desc": "낮을수록 안전"},
    {"key": "typhoon", "label": "태풍위험도", "unit": "z", "direction": "lower_is_better",
     "desc": "낮을수록 안전"},
    {"key": "companies", "label": "SW 기업 갯수", "unit": "개", "direction": "higher_is_better",
     "desc": "많을수록 산업 클러스터 효과 ↑"},
    {"key": "price", "label": "실거래가", "unit": "만원", "direction": "lower_is_better",
     "desc": "낮을수록 부지 확보 비용 ↓"},
]

COL_MAP = {
    "시군": "name",
    "평균기온(°C)": "temp",
    "지진위험도": "earthquake",
    "태풍위험도": "typhoon",
    "기업갯수": "companies",
    "거래금액(만원)": "price",
}


def main() -> int:
    if not SRC_CSV.exists():
        print(f"❌ 입력 CSV 없음: {SRC_CSV}", file=sys.stderr)
        return 1

    df = pd.read_csv(SRC_CSV, encoding="utf-8-sig")
    df = df.rename(columns=COL_MAP)[list(COL_MAP.values())]

    regions = []
    missing_coords: list[str] = []
    for _, row in df.iterrows():
        name = str(row["name"])
        coord = COORDS.get(name)
        if coord is None:
            missing_coords.append(name)
            continue
        lat, lng = coord
        regions.append({
            "name": name,
            "lat": lat,
            "lng": lng,
            "factors": {
                "temp": round(float(row["temp"]), 3),
                "earthquake": round(float(row["earthquake"]), 4),
                "typhoon": round(float(row["typhoon"]), 4),
                "companies": int(row["companies"]),
                "price": round(float(row["price"]), 1),
            },
        })

    if missing_coords:
        print(f"⚠️  좌표 없는 시군 {len(missing_coords)}개: {missing_coords}", file=sys.stderr)

    payload = {
        "version": 1,
        "source": "_v1_data/06_실거래가/가중치데이터_최종.csv",
        "factors": FACTORS,
        "regions": regions,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ {len(regions)}개 시군 → {OUT_JSON.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
