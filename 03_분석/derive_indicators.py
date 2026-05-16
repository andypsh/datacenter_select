"""V2 파생변수 생성 — V1 원본 자료 + coords.py 기반.

입력 (02_데이터/raw/):
  - 광케이블/광케이블.xlsx        — 전국 광케이블 백본 노드 좌표 (66개)
  - 데이터센터위치/데이터센터위치.csv  — 기존 데이터센터 위치 (89개)
  - 재해위험도/재해위험도.csv          — 시군별 지진/태풍 z-score (참고)

출력:
  - 02_데이터/processed/indicators_v2.csv  (109 시군 × 6 컬럼)

산출 변수:
  1) power          — 광케이블 백본 30km 내 노드 수 (정규화)
                      통신=전력 백본은 콜로케이션 경향 → 송전 안정성 프록시
  2) industry       — 기존 데이터센터 30km 내 개수 (정규화)
                      클러스터 효과: 기존 IDC 인근일수록 인프라·인력 풍부
  3) vitality       — 데이터센터 결핍도 + 인구감소지역 가중
                      = (1 - existing_dc_density) × 0.6 + is_decline × 0.4
                      → 신규 IDC 입주로 활력 회복 잠재력
  4) renewable      — 재생에너지 허브 거리 기반 점수
                      호남 태양광 벨트 + 강원 풍력 벨트 중심 좌표 활용
                      → 거리 가까울수록 ↑

산식 메모:
  - 거리: Haversine (km)
  - 정규화: Min-Max (0~1)
  - 인구감소지역: 행안부 89개 지정 (참고 — 코드 동봉)
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pandas as pd

from coords import COORDS

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "02_데이터" / "raw"
OUT = ROOT / "02_데이터" / "processed" / "indicators_v2.csv"

# === Population decline (행정안전부 인구감소지역, 2021 지정) ===
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

# === 재생에너지 허브 좌표 (대표지점) ===
RENEWABLE_HUBS = {
    # 호남 태양광 벨트
    "신안군_솔라": (34.834, 126.351),
    "해남군_솔라": (34.573, 126.599),
    "영광군_솔라": (35.277, 126.512),
    "보성군_솔라": (34.771, 127.080),
    # 강원 풍력 벨트
    "강릉시_풍력": (37.751, 128.876),
    "태백시_풍력": (37.164, 128.985),
    "정선군_풍력": (37.380, 128.661),
    # 서해안 풍력 (영광/부안 해상)
    "부안군_해상풍": (35.732, 126.733),
}


def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """두 좌표 간 거리 (km)."""
    R = 6371.0
    rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlng / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def count_within(target_lat: float, target_lng: float,
                 points: list[tuple[float, float]], radius_km: float) -> int:
    """target에서 radius_km 안에 있는 points 개수."""
    return sum(1 for (la, ln) in points
               if haversine(target_lat, target_lng, la, ln) <= radius_km)


def min_distance(target_lat: float, target_lng: float,
                 points: list[tuple[float, float]]) -> float:
    """target에서 가장 가까운 point까지 거리 (km)."""
    if not points:
        return float("inf")
    return min(haversine(target_lat, target_lng, la, ln) for (la, ln) in points)


def load_fiber_optic() -> list[tuple[float, float]]:
    """광케이블 백본 노드 좌표 추출."""
    df = pd.read_excel(RAW / "광케이블" / "광케이블.xlsx")
    # 컬럼 인덱스: [번호, 지역, 경도?, 위도?, 주소]
    # 헤더 깨짐 → 컬럼명 대신 위치로 접근
    # 샘플 확인: row 0 = 강화 (37.61, 126.71) — 강화군 위치와 부합
    # 즉 컬럼 2=위도, 컬럼 3=경도 (혹은 반대) — 검증 필요
    lat_col, lng_col = None, None
    for i, col in enumerate(df.columns):
        sample = df[col].dropna().iloc[0] if len(df[col].dropna()) else None
        if isinstance(sample, (int, float)):
            if 33 < sample < 39:   # 한국 위도 범위
                lat_col = col
            elif 124 < sample < 132:  # 한국 경도 범위
                lng_col = col
    if lat_col is None or lng_col is None:
        raise ValueError("위경도 컬럼 자동 식별 실패")
    pts = list(zip(df[lat_col].tolist(), df[lng_col].tolist()))
    return [(float(la), float(ln)) for la, ln in pts
            if pd.notna(la) and pd.notna(ln)]


def load_existing_data_centers() -> list[tuple[float, float]]:
    """기존 데이터센터 위치 — 시군구코드만 있고 좌표 없음.
    주소 패턴으로 시 이름 추출 → coords.py 매핑.
    """
    df = pd.read_csv(RAW / "데이터센터위치" / "데이터센터위치.csv", encoding="utf-8-sig")
    df.columns = df.columns.str.strip()
    addr_col = next((c for c in df.columns if "주소" in c or c.endswith("ּ")), None)
    if addr_col is None:
        addr_col = df.columns[3]  # 위치 기반 fallback

    # 주소에서 시군 단위 추출 (간단 휴리스틱)
    name_to_pt: list[tuple[float, float]] = []
    for addr in df[addr_col].dropna():
        addr_str = str(addr)
        for sgg_name, coord in COORDS.items():
            short = sgg_name.replace("_경남", "").replace("특별자치", "").replace("광역", "")
            short = short.rstrip("시군구").strip()
            if short and short in addr_str:
                name_to_pt.append(coord)
                break
    return name_to_pt


def main() -> int:
    print(f"Loading fiber optic backbone...")
    fiber_pts = load_fiber_optic()
    print(f"  {len(fiber_pts)} fiber nodes")

    print(f"Loading existing data centers...")
    dc_pts = load_existing_data_centers()
    print(f"  {len(dc_pts)} DC locations resolved")

    renew_pts = list(RENEWABLE_HUBS.values())
    print(f"Renewable hubs: {len(renew_pts)} reference points")

    rows = []
    for name, (lat, lng) in COORDS.items():
        fiber_count = count_within(lat, lng, fiber_pts, radius_km=30)
        dc_count = count_within(lat, lng, dc_pts, radius_km=30)
        dist_renew = min_distance(lat, lng, renew_pts)
        rows.append({
            "name": name,
            "fiber_count_30km": fiber_count,
            "dc_count_30km": dc_count,
            "min_renew_dist_km": dist_renew,
            "is_population_decline": name in POPULATION_DECLINE,
        })

    df = pd.DataFrame(rows)

    # === 정규화 → 4개 V2 지표 산출 ===
    def mm_norm(s: pd.Series) -> pd.Series:
        rng = s.max() - s.min()
        return (s - s.min()) / rng if rng > 0 else pd.Series(0.0, index=s.index)

    # 1) power: 광케이블 노드 30km 내 개수 정규화
    df["power"] = mm_norm(df["fiber_count_30km"].astype(float)).round(4)

    # 2) industry: 기존 DC 30km 내 개수 정규화 (산업 클러스터 효과)
    df["industry"] = mm_norm(df["dc_count_30km"].astype(float)).round(4)

    # 3) vitality: 데이터센터 결핍도 (60%) + 인구감소지역 가중 (40%)
    dc_density = mm_norm(df["dc_count_30km"].astype(float))
    df["vitality"] = (
        (1.0 - dc_density) * 0.6
        + df["is_population_decline"].astype(float) * 0.4
    ).round(4)

    # 4) renewable: 재생에너지 허브까지 거리의 지수감쇠 정규화
    # score = exp(-dist / 100km) — 100km에서 ~0.37, 300km에서 ~0.05
    # 0km 일치점 = 1.0, 거리 멀수록 부드럽게 감쇠
    import math as _m
    renewable_raw = df["min_renew_dist_km"].apply(lambda d: _m.exp(-d / 100.0))
    df["renewable"] = mm_norm(renewable_raw).round(4)

    out_df = df[["name", "power", "industry", "vitality", "renewable", "is_population_decline"]]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(OUT, index=False, encoding="utf-8-sig")
    print(f"\nOK derived {len(out_df)} rows -> {OUT.relative_to(ROOT)}")

    # === 진단 출력 ===
    print("\n=== 진단 ===")
    print(f"power     min={df['power'].min():.3f} max={df['power'].max():.3f} mean={df['power'].mean():.3f}")
    print(f"industry  min={df['industry'].min():.3f} max={df['industry'].max():.3f} mean={df['industry'].mean():.3f}")
    print(f"vitality  min={df['vitality'].min():.3f} max={df['vitality'].max():.3f} mean={df['vitality'].mean():.3f}")
    print(f"renewable min={df['renewable'].min():.3f} max={df['renewable'].max():.3f} mean={df['renewable'].mean():.3f}")

    print(f"\n인구감소지역: {df['is_population_decline'].sum()}개 시군")
    print(f"\n광케이블 30km 내 0개: {(df['fiber_count_30km']==0).sum()}개 시군")
    print(f"기존 DC 30km 내 0개:  {(df['dc_count_30km']==0).sum()}개 시군")

    # Top 5 per indicator (sanity check)
    for col in ["power", "industry", "vitality", "renewable"]:
        top5 = df.nlargest(5, col)[["name", col]]
        print(f"\nTop 5 [{col}]:")
        for _, r in top5.iterrows():
            print(f"  {r['name']:<15} {r[col]:.4f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
