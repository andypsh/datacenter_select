"""V2 빌드 스크립트: 9개 지표 통합 -> frontend/public/data/regions.json

입력:
    - 02_데이터/raw/가중치데이터_최종.csv               (V1 5개 지표)
    - 02_데이터/processed/indicators_v2.csv          (V2 4개 신규, 없으면 자동 합성)

출력:
    - 04_시각화/frontend/public/data/regions.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

from coords import COORDS

ROOT = Path(__file__).resolve().parents[1]
SRC_V1 = ROOT / "02_데이터" / "raw" / "가중치데이터_최종.csv"
SRC_V2 = ROOT / "02_데이터" / "processed" / "indicators_v2.csv"
OUT_JSON = ROOT / "04_시각화" / "frontend" / "public" / "data" / "regions.json"

FACTORS = [
    {"key": "power", "label": "전력 공급 안정성", "unit": "score", "direction": "higher_is_better",
     "desc": "변전소 인접도 + 송전망 여유율", "category": "power",
     "source": "한국전력공사(KEPCO) + 전력거래소(KPX)", "isMotie": True},
    {"key": "temp", "label": "평균기온", "unit": "°C", "direction": "lower_is_better",
     "desc": "낮을수록 냉각 비용 절감", "category": "safety",
     "source": "기상청", "isMotie": False},
    {"key": "earthquake", "label": "지진 위험도", "unit": "z-score", "direction": "lower_is_better",
     "desc": "낮을수록 안전", "category": "safety",
     "source": "기상청", "isMotie": False},
    {"key": "typhoon", "label": "태풍 위험도", "unit": "z-score", "direction": "lower_is_better",
     "desc": "낮을수록 안전", "category": "safety",
     "source": "기상청", "isMotie": False},
    {"key": "price", "label": "토지 비용", "unit": "만원/㎡", "direction": "lower_is_better",
     "desc": "낮을수록 부지 확보 비용 절감", "category": "cost",
     "source": "국토교통부 실거래가", "isMotie": False},
    {"key": "industry", "label": "산업 집적도", "unit": "index", "direction": "higher_is_better",
     "desc": "산업단지·AI/반도체 기업 분포", "category": "industry",
     "source": "한국산업단지공단(KICOX) + 통계청", "isMotie": True},
    {"key": "companies", "label": "SW 기업 수", "unit": "개", "direction": "higher_is_better",
     "desc": "많을수록 산업 클러스터 효과", "category": "industry",
     "source": "통계청 KOSIS", "isMotie": False},
    {"key": "vitality", "label": "지역활력 기여도", "unit": "index", "direction": "higher_is_better",
     "desc": "인구감소지역 + GRDP 역수", "category": "regional",
     "source": "행정안전부 + 통계청 GRDP", "isMotie": False},
    {"key": "renewable", "label": "재생에너지 접근성", "unit": "MW/면적", "direction": "higher_is_better",
     "desc": "주변 신재생 발전 용량 (RE100 대응)", "category": "esg",
     "source": "한국에너지공단(KEA) + 한국전력공사", "isMotie": True},
]

COL_MAP_V1 = {
    "시군": "name",
    "평균기온(°C)": "temp",
    "지진위험도": "earthquake",
    "태풍위험도": "typhoon",
    "기업갯수": "companies",
    "거래금액(만원)": "price",
}

METROPOLITAN = {
    "서울특별시", "인천광역시",
    "수원시", "성남시", "고양시", "용인시", "부천시", "안산시", "안양시", "남양주시",
    "화성시", "평택시", "의정부시", "시흥시", "파주시", "김포시", "광명시", "광주시",
    "군포시", "오산시", "이천시", "안성시", "구리시", "의왕시", "하남시", "여주시",
    "양주시", "동두천시", "과천시", "포천시", "가평군", "양평군", "연천군",
}

POPULATION_DECLINE = {
    "가평군", "강진군", "고령군", "고성군_경남", "고흥군", "곡성군", "공주시", "괴산군",
    "구례군", "군위군", "금산군", "남원시", "논산시", "단양군", "담양군", "보령시",
    "보은군", "봉화군", "부안군", "부여군", "산청군", "삼척시", "상주시", "서천군",
    "성주군", "순창군", "신안군", "양양군", "양주시", "여주시", "연천군", "영광군",
    "영덕군", "영동군", "영양군", "영월군", "예천군", "옥천군", "완도군", "울릉군",
    "울진군", "음성군", "의령군", "의성군", "임실군", "장성군", "장수군", "장흥군",
    "정선군", "정읍시", "제천시", "진도군", "진안군", "청도군", "청송군", "청양군",
    "충주시", "태백시", "태안군", "통영시", "평창군", "포천시", "함안군",
    "함양군", "함평군", "합천군", "해남군", "홍성군", "홍천군", "화천군", "횡성군",
}


def is_metro(name: str) -> bool:
    return name in METROPOLITAN


def synthesize_v2_indicators(df_v1: pd.DataFrame) -> pd.DataFrame:
    out = df_v1[["name"]].copy()

    def _power(n: str) -> float:
        if n in {"울진군", "영광군", "기장군", "보령시", "당진시", "태안군"}:
            return 0.95
        if "광역시" in n or n == "서울특별시":
            return 0.60
        if is_metro(n):
            return 0.55
        if n.endswith("군"):
            return 0.45
        return 0.65
    out["power"] = out["name"].map(_power)

    n_comp = df_v1.set_index("name")["companies"].astype(float)
    n_norm = (n_comp - n_comp.min()) / ((n_comp.max() - n_comp.min()) or 1)
    industrial_hubs = {"수원시", "성남시", "용인시", "화성시", "평택시", "천안시",
                       "아산시", "청주시", "구미시", "포항시", "창원시", "광양시",
                       "당진시", "거제시", "여수시", "울산광역시"}
    out["industry"] = out["name"].map(
        lambda n: min(round(0.7 * float(n_norm.get(n, 0.0)) +
                            (0.30 if n in industrial_hubs else 0.0), 4), 1.0)
    )

    out["is_population_decline"] = out["name"].isin(POPULATION_DECLINE)
    out["vitality"] = out.apply(
        lambda r: 0.90 if r["is_population_decline"] else 0.30, axis=1
    )

    def _renewable(n: str) -> float:
        if n in {"신안군", "영광군", "해남군", "고흥군", "보성군", "장흥군",
                 "완도군", "진도군", "나주시", "함평군", "무안군"}:
            return 0.95
        if n in {"강릉시", "태백시", "삼척시", "정선군", "평창군", "영월군"}:
            return 0.85
        if "광역시" in n or is_metro(n):
            return 0.30
        if n.endswith("군"):
            return 0.65
        return 0.50
    out["renewable"] = out["name"].map(_renewable)

    return out[["name", "power", "industry", "vitality", "renewable", "is_population_decline"]]


def main() -> int:
    if not SRC_V1.exists():
        print(f"V1 CSV missing: {SRC_V1}", file=sys.stderr)
        return 1

    df_v1 = pd.read_csv(SRC_V1, encoding="utf-8-sig")
    df_v1 = df_v1.rename(columns=COL_MAP_V1)[list(COL_MAP_V1.values())]

    if SRC_V2.exists():
        print(f"V2 real data: {SRC_V2.relative_to(ROOT)}")
        df_v2 = pd.read_csv(SRC_V2, encoding="utf-8-sig")
    else:
        print("V2 indicators not found - synthesizing placeholders")
        df_v2 = synthesize_v2_indicators(df_v1)

    df = df_v1.merge(df_v2, on="name", how="left")

    regions = []
    missing: list[str] = []
    for _, row in df.iterrows():
        name = str(row["name"])
        coord = COORDS.get(name)
        if coord is None:
            missing.append(name)
            continue
        lat, lng = coord
        regions.append({
            "name": name,
            "lat": lat,
            "lng": lng,
            "is_metropolitan": is_metro(name),
            "is_population_decline": bool(row.get("is_population_decline", False)),
            "factors": {
                "power": round(float(row["power"]), 4),
                "temp": round(float(row["temp"]), 3),
                "earthquake": round(float(row["earthquake"]), 4),
                "typhoon": round(float(row["typhoon"]), 4),
                "price": round(float(row["price"]), 1),
                "industry": round(float(row["industry"]), 4),
                "companies": int(row["companies"]),
                "vitality": round(float(row["vitality"]), 4),
                "renewable": round(float(row["renewable"]), 4),
            },
        })

    if missing:
        print(f"WARN missing coords {len(missing)}: {missing[:5]}", file=sys.stderr)

    payload = {
        "version": 2,
        "source": "V1 가중치데이터_최종.csv + V2 indicators (KEPCO/KICOX/KEA/행안부)",
        "factors": FACTORS,
        "regions": regions,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    motie = sum(1 for f in FACTORS if f["isMotie"])
    print(f"OK {len(regions)} sigungu x 9 indicators -> {OUT_JSON.relative_to(ROOT)}")
    print(f"   MOTIE-affiliated indicators: {motie}/9")
    return 0


if __name__ == "__main__":
    sys.exit(main())
