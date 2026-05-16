"""V1 raw 데이터로부터 3개 실데이터 파생변수 계산.

이전엔 `extra_data.py`의 tier 기반 proxy를 썼지만, 본 모듈은 V1 raw 데이터를
실제로 처리해서 시군별 파생변수를 도출한다.

| 지표 | raw 입력 | 파생 방법 |
|------|---------|---------|
| 전력 안정성  | 2012-2022전국.csv | 시군별 평균 사용량 + 증감추세 + 변동성 결합 |
| 통신 인프라  | 광케이블.csv (66 노드) | 시군 중심점 nearest assignment + 인접 노드 합산 |
| 산업 집적도  | SW회사.csv (40k 회사) | 시군별 회사 수 + 기업규모 가중 (대=3, 중견=2, 중소=1) |
"""

from __future__ import annotations

import math
import re
from functools import lru_cache
from pathlib import Path

import pandas as pd

from coords import COORDS

ROOT = Path(__file__).resolve().parents[1]
V1 = ROOT / "_v1_data"

POWER_CSV = V1 / "02_계약종별전력사용량" / "년도별일반전력" / "결과" / "피벗테이블화" / "2012-2022전국.csv"
TELECOM_CSV = V1 / "04_sw기업개수" / "광케이블 지도" / "광케이블.csv"
SW_CSV = V1 / "04_sw기업개수" / "SW회사.csv"
# 공공데이터포털 표준데이터 (행안부, 산업부 산하 KEA 데이터 기반)
SOLAR_CSV = ROOT / "02_데이터" / "raw" / "KEA_신재생" / "전국태양광발전소전기사업허가정보표준데이터.csv"

# 광역시 매핑 — 시군구 자치구 데이터를 광역시로 합산
PROVINCE_TO_METRO = {
    "서울특별시": "서울특별시",
    "부산광역시": "부산광역시",
    "대구광역시": "대구광역시",
    "인천광역시": "인천광역시",
    "광주광역시": "광주광역시",
    "대전광역시": "대전광역시",
    "울산광역시": "울산광역시",
    "세종특별자치시": "세종특별자치시",
}


def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """km 단위 거리."""
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


# ============================================================
# 1) 전력 안정성 — 시군별 평균·추세·변동성에서 합성 점수
# ============================================================

@lru_cache(maxsize=1)
def _power_raw() -> pd.DataFrame:
    df = pd.read_csv(POWER_CSV, encoding="utf-8-sig")
    df = df[df["계약구분"] == "합계"].copy()
    df["사용량(kWh)"] = pd.to_numeric(df["사용량(kWh)"], errors="coerce")
    df["고객호수(호)"] = pd.to_numeric(
        df["고객호수(호)"].astype(str).str.replace(",", "").str.strip(),
        errors="coerce",
    )
    df["년"] = df["년월"].astype(str).str[:4].astype(int)

    # 광역시 자치구 → 광역시로 합산
    def to_region(row: pd.Series) -> str:
        if row["시구"] in PROVINCE_TO_METRO:
            return row["시구"]
        return str(row["시군구"])

    df["region"] = df.apply(to_region, axis=1)
    return df


@lru_cache(maxsize=1)
def _power_features() -> dict[str, dict[str, float]]:
    df = _power_raw()
    # 시군별 월간 합산 (광역시는 자치구 합)
    monthly = df.groupby(["region", "년월"])["사용량(kWh)"].sum().reset_index()
    # 연간 합산
    monthly["년"] = monthly["년월"].astype(str).str[:4].astype(int)
    yearly = monthly.groupby(["region", "년"])["사용량(kWh)"].sum().reset_index()

    out: dict[str, dict[str, float]] = {}
    for region, sub in yearly.groupby("region"):
        sub = sub.sort_values("년")
        avg = sub["사용량(kWh)"].mean()
        # 5년 추세: 선형회귀 기울기 (정규화)
        years = sub["년"].values.astype(float)
        usage = sub["사용량(kWh)"].values.astype(float)
        if len(years) >= 2 and avg > 0:
            slope = float(((years - years.mean()) * (usage - usage.mean())).sum()
                          / max(((years - years.mean()) ** 2).sum(), 1))
            trend = slope / avg  # 정규화: 평균 대비 연간 증가율
        else:
            trend = 0.0
        # 변동성 (CV)
        cv = float(sub["사용량(kWh)"].std() / avg) if avg > 0 else 0.0
        out[region] = {"avg_usage": float(avg), "trend": trend, "cv": cv}
    return out


def power_stability_real(name: str) -> float:
    """전력 안정성 실데이터 파생점수 (0~100).

    설계:
    - 평균 사용량 ↑ = 인프라 확충 ↑ (변전소/송전망 풍부) → +
    - 증가 추세 ↑ = 산업 성장 → +
    - 변동성 ↑ = 송전 부담 위험 → -
    """
    feats = _power_features().get(name)
    if feats is None:
        return 50.0  # 데이터 없는 시군 (예: 매칭 실패) — 중간값

    # 정규화 기준 — 109 시군 분포에서 추출
    all_feats = _power_features()
    avgs = [f["avg_usage"] for f in all_feats.values()]
    trends = [f["trend"] for f in all_feats.values()]
    cvs = [f["cv"] for f in all_feats.values()]
    avg_min, avg_max = min(avgs), max(avgs)
    trend_min, trend_max = min(trends), max(trends)
    cv_min, cv_max = min(cvs), max(cvs)

    def norm(v: float, lo: float, hi: float) -> float:
        return (v - lo) / max(hi - lo, 1e-9)

    score_avg = norm(feats["avg_usage"], avg_min, avg_max)
    score_trend = norm(feats["trend"], trend_min, trend_max)
    score_cv = 1.0 - norm(feats["cv"], cv_min, cv_max)  # 낮을수록 좋음
    # 가중평균: 평균 0.5 + 추세 0.3 + 안정성 0.2
    score = 0.5 * score_avg + 0.3 * score_trend + 0.2 * score_cv
    return float(score * 100)


# ============================================================
# 2) 통신 인프라 — 광케이블 66 노드 → 시군 nearest 카운트
# ============================================================

@lru_cache(maxsize=1)
def _telecom_nodes() -> list[tuple[float, float]]:
    df = pd.read_csv(TELECOM_CSV, encoding="cp949")
    # 광케이블.csv: 위도/경도 컬럼명이 실제로는 lng/lat로 뒤바뀐 경우 있음.
    # 한국 좌표 보정: 한국은 lat 33~38, lng 124~131 범위.
    nodes: list[tuple[float, float]] = []
    for _, row in df.iterrows():
        a, b = float(row["위도"]), float(row["경도"])
        # 33~38 안에 있는 쪽이 위도
        if 33 <= a <= 38:
            lat, lng = a, b
        else:
            lat, lng = b, a
        nodes.append((lat, lng))
    return nodes


@lru_cache(maxsize=1)
def _telecom_features() -> dict[str, float]:
    """시군별 50km 이내 광케이블 노드 수 + 최근접 거리 점수."""
    nodes = _telecom_nodes()
    out: dict[str, float] = {}
    for name, (lat, lng) in COORDS.items():
        dists = [_haversine(lat, lng, nlat, nlng) for nlat, nlng in nodes]
        within_50km = sum(1 for d in dists if d <= 50)
        within_100km = sum(1 for d in dists if d <= 100)
        nearest = min(dists) if dists else 200.0
        # 점수: 50km내 노드 × 2 + 100km내 × 1 + 최근접 보너스
        proximity_bonus = max(0.0, 50.0 - nearest) / 50.0  # 0~1
        out[name] = within_50km * 2.0 + within_100km * 1.0 + proximity_bonus * 3
    return out


def telecom_infra_real(name: str) -> float:
    """통신 인프라 실데이터 파생점수 (0~100)."""
    feats = _telecom_features()
    val = feats.get(name, 0.0)
    vals = list(feats.values())
    lo, hi = min(vals), max(vals)
    return float((val - lo) / max(hi - lo, 1e-9) * 100)


# ============================================================
# 3) 산업 집적도 — SW회사 40k raw → 시군별 가중 카운트
# ============================================================

# 주소 첫 토큰에서 시·도 추출
_ADDR_RE = re.compile(r"^(\S+(?:특별시|광역시|특별자치시|특별자치도|도))\s+(\S+(?:시|군|구))")

# 광역시 자치구 → 광역시 매핑 (자치구 일부 예시; 그 외는 그대로)
METRO_DISTRICTS_TO_METRO: dict[str, str] = {}
for metro in PROVINCE_TO_METRO:
    METRO_DISTRICTS_TO_METRO[metro] = metro  # self
# 광역시의 자치구는 광역시명을 통해 식별 (주소 첫 토큰)


SIZE_WEIGHT = {"대기업": 3.0, "중견기업": 2.0, "중소기업": 1.0}


@lru_cache(maxsize=1)
def _industry_features() -> dict[str, dict[str, float]]:
    """시군별 회사 수 + 규모 가중 + 대기업 수."""
    df = pd.read_csv(SW_CSV, encoding="cp949", low_memory=False)
    # 주소: '입력주소' fallback if '주소' is NaN
    addr = df["주소"].fillna(df["입력주소"]).astype(str)

    parsed = addr.str.extract(_ADDR_RE)
    parsed.columns = ["province", "city"]

    def to_region(prov: str, city: str) -> str | None:
        if pd.isna(prov) or pd.isna(city):
            return None
        # 광역시 → 광역시 그대로
        if prov in PROVINCE_TO_METRO:
            return prov
        # 그 외 시·도 + 시·군 (자치구 ' 구' 제외)
        if city.endswith("구"):
            return None  # 광역시 자치구는 이미 처리됨; 그 외 일반시의 구는 시 매칭 어려움
        return city

    df["region"] = [to_region(p, c) for p, c in zip(parsed["province"], parsed["city"])]
    df = df.dropna(subset=["region"])

    out: dict[str, dict[str, float]] = {}
    for region, sub in df.groupby("region"):
        count = len(sub)
        weighted = float(sub["기업규모"].map(SIZE_WEIGHT).fillna(1.0).sum())
        large = int((sub["기업규모"] == "대기업").sum())
        out[region] = {"count": float(count), "weighted": weighted, "large": float(large)}
    return out


def industry_cluster_real(name: str) -> float:
    """산업 집적도 실데이터 파생점수 (0~100). 회사 수 + 규모 가중 결합."""
    feats = _industry_features().get(name)
    if feats is None:
        return 0.0
    all_feats = _industry_features()
    weighted_vals = [f["weighted"] for f in all_feats.values()]
    lo, hi = min(weighted_vals), max(weighted_vals)
    return float((feats["weighted"] - lo) / max(hi - lo, 1e-9) * 100)


def industry_raw_count(name: str) -> int:
    """raw 회사 수 (UI 표시용)."""
    return int(_industry_features().get(name, {}).get("count", 0))


# ============================================================
# 4) 재생에너지 — 공공데이터포털 50k 태양광 발전소 raw → 시군별 가동 발전소 + 설비용량
# ============================================================

@lru_cache(maxsize=1)
def _solar_features() -> dict[str, dict[str, float]]:
    """시군별 가동 태양광 발전소 수 + 총 설비용량 (kW).

    출처: data.go.kr 표준데이터 '전국태양광발전소전기사업허가정보표준데이터'
    50,000개 발전소 raw, '제공기관명'에서 시·도 prefix 제거 후 시군 매칭.
    """
    df = pd.read_csv(SOLAR_CSV, encoding="cp949", low_memory=False)
    # 정상가동만 카운트
    df = df[df["가동상태구분명"] == "정상가동"]
    # 제공기관명: "전북특별자치도 익산시" → "익산시", "강원특별자치도 화천군청" → "화천군"
    def extract_region(s: str) -> str | None:
        if not isinstance(s, str):
            return None
        # 광역시·도 prefix 제거
        parts = s.split()
        if len(parts) < 2:
            return None
        candidate = parts[-1].replace("청", "")  # "화천군청" → "화천군"
        # 광역시는 첫 부분이 광역시
        if parts[0] in PROVINCE_TO_METRO:
            return parts[0]
        return candidate

    df["region"] = df["제공기관명"].map(extract_region)
    # 고성군 경남/강원 구분 — 우리 데이터셋엔 고성군_경남만
    df.loc[df["region"] == "고성군", "region"] = df.apply(
        lambda r: "고성군_경남" if isinstance(r["제공기관명"], str) and "경상남도" in r["제공기관명"]
                  else r["region"],
        axis=1,
    )
    out: dict[str, dict[str, float]] = {}
    for region, sub in df.dropna(subset=["region"]).groupby("region"):
        count = len(sub)
        capa_sum = float(sub["설비용량"].sum())
        out[str(region)] = {"count": float(count), "capa_kw": capa_sum}
    return out


def renewable_access_real(name: str) -> float:
    """재생에너지 접근성 실데이터 (0~100). 시군 가동 태양광 발전소 수 + 총 설비용량 합성.

    설계: log(count) 0.5 + log(capa) 0.5 결합 후 109개 시군 정규화.
    log를 쓰는 이유: 익산시 5092 vs 횡성군 0의 극단 분포를 부드럽게.
    """
    import math as _m
    feats = _solar_features().get(name, {"count": 0.0, "capa_kw": 0.0})
    score = 0.5 * _m.log1p(feats["count"]) + 0.5 * _m.log1p(feats["capa_kw"] / 100)
    # 109개 시군 분포로 정규화 (coords.py 기준)
    all_scores = []
    for n in COORDS:
        f = _solar_features().get(n, {"count": 0.0, "capa_kw": 0.0})
        s = 0.5 * _m.log1p(f["count"]) + 0.5 * _m.log1p(f["capa_kw"] / 100)
        all_scores.append(s)
    lo, hi = min(all_scores), max(all_scores)
    return float((score - lo) / max(hi - lo, 1e-9) * 100)


def renewable_raw_count(name: str) -> int:
    """raw 가동 태양광 발전소 수 (UI 표시용)."""
    return int(_solar_features().get(name, {}).get("count", 0))


# ============================================================
# 5) IT 인력 — SW회사 raw + 기업규모별 표준 종사자 추정
# ============================================================

# 한국 IT 산업 평균 종사자 수 (통계청 전국사업체조사 평균 기준 추정)
# - 대기업: 1000명+ (네이버·카카오·삼성SDS 등 IT 대기업 평균)
# - 중견기업: 100~300명
# - 중소기업: 10~30명 (대부분 스타트업/소형)
WORKFORCE_PER_FIRM = {
    "대기업": 1500.0,
    "중견기업": 250.0,
    "중소기업": 18.0,
}


@lru_cache(maxsize=1)
def _workforce_features() -> dict[str, float]:
    """시군별 IT 추정 종사자 수.

    산업집적도(`industry_cluster`)는 단순 카운트 가중치(대=3, 중견=2, 중소=1)인 반면,
    이 지표는 실제 종사자 추정(대=1500, 중견=250, 중소=18)으로 대기업 비중이 큰
    시군이 훨씬 더 강조됨 — 산업집적도와 다른 시그널.
    """
    feats = _industry_features()
    out: dict[str, float] = {}
    df = pd.read_csv(SW_CSV, encoding="cp949", low_memory=False)
    addr = df["주소"].fillna(df["입력주소"]).astype(str)
    parsed = addr.str.extract(_ADDR_RE)
    parsed.columns = ["province", "city"]

    def to_region(prov: str, city: str) -> str | None:
        if pd.isna(prov) or pd.isna(city):
            return None
        if prov in PROVINCE_TO_METRO:
            return prov
        if city.endswith("구"):
            return None
        return city

    df["region"] = [to_region(p, c) for p, c in zip(parsed["province"], parsed["city"])]
    df = df.dropna(subset=["region"])
    for region, sub in df.groupby("region"):
        est = float(sub["기업규모"].map(WORKFORCE_PER_FIRM).fillna(WORKFORCE_PER_FIRM["중소기업"]).sum())
        out[region] = est
    # silence unused warning for feats
    _ = feats
    return out


def it_workforce_real(name: str) -> float:
    """IT 인력 실데이터 파생점수 (0~100). SW회사 raw × 규모별 표준 종사자."""
    feats = _workforce_features()
    val = feats.get(name, 0.0)
    vals = list(feats.values())
    import math as _m
    # log-scale (서울/판교 압도 완화)
    log_vals = [_m.log1p(v) for v in vals]
    log_val = _m.log1p(val)
    lo, hi = min(log_vals), max(log_vals)
    return float((log_val - lo) / max(hi - lo, 1e-9) * 100)


def it_workforce_estimate(name: str) -> int:
    """추정 IT 종사자 수 (UI 표시용)."""
    return int(_workforce_features().get(name, 0))


# ============================================================
# 디버그 / 검증
# ============================================================

if __name__ == "__main__":
    print("=== 파생변수 검증 ===")
    for name in ["서울특별시", "수원시", "원주시", "제천시", "횡성군", "가평군"]:
        if name not in COORDS:
            continue
        p = power_stability_real(name)
        t = telecom_infra_real(name)
        i = industry_cluster_real(name)
        ic = industry_raw_count(name)
        print(f"{name:8s}  전력={p:5.1f}  통신={t:5.1f}  산업={i:5.1f}  회사수={ic}")
