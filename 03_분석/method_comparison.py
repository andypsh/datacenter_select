"""교차 방법론 비교 — 4가지 MCDM 방법으로 같은 데이터 점수화 → 일치도 검증.

방법:
1. **WSM (Weighted Sum Method)** — 현재 우리 모델. 정규화 후 가중평균.
2. **TOPSIS** (Technique for Order Preference by Similarity to Ideal Solution)
   - 이상해(최고)·반이상해(최저) 정의 → 각 시군의 두 거리 계산
   - 상대 근접도 C* = D⁻ / (D⁺ + D⁻)
3. **Entropy-weighted WSM** — 가중치를 entropy method로 객관화 후 WSM
4. **Borda count** — 각 지표마다 순위 부여 → 순위 합산
   - 가중치 영향을 받지 않는 비모수 ranking

결론: 4개 방법이 공통으로 상위로 분류하는 시군 = "어떤 평가 관점에서도 강건한 후보"
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REGIONS_JSON = ROOT / "04_시각화" / "frontend" / "public" / "data" / "regions.json"
OUT_MD = ROOT / "05_보고서" / "method_comparison.md"

DEFAULT_WEIGHTS = {
    "power": 18, "temp": 8, "earthquake": 10, "typhoon": 7, "price": 12,
    "industry": 12, "companies": 8, "vitality": 15, "renewable": 10,
}


def normalize_minmax_directional(values: list[float], direction: str) -> list[float]:
    valid = [v for v in values if isinstance(v, (int, float))]
    lo, hi = min(valid), max(valid)
    span = max(hi - lo, 1e-9)
    n = [(v - lo) / span for v in values]
    if direction == "lower_is_better":
        n = [1 - v for v in n]
    return n


def load_normalized(payload: dict) -> tuple[list[str], dict[str, list[float]], list[dict]]:
    """region 이름, 정규화 행렬, factor meta 반환."""
    factors = payload["factors"]
    regions = payload["regions"]
    names = [r["name"] for r in regions]
    norm: dict[str, list[float]] = {}
    for f in factors:
        raw = [r["factors"][f["key"]] for r in regions]
        norm[f["key"]] = normalize_minmax_directional(raw, f["direction"])
    return names, norm, factors


# ---------- 1. WSM (가중평균) ----------
def wsm(names, norm, factors, weights):
    wsum = sum(weights.values())
    scores = []
    for i in range(len(names)):
        s = sum(norm[f["key"]][i] * weights[f["key"]] / wsum for f in factors)
        scores.append(s)
    return scores


# ---------- 2. TOPSIS ----------
def topsis(names, norm, factors, weights):
    """이상해(1) vs 반이상해(0)와의 거리 기반."""
    wsum = sum(weights.values())
    N = len(names)
    # 가중 정규화 행렬
    weighted = {f["key"]: [norm[f["key"]][i] * weights[f["key"]] / wsum for i in range(N)]
                for f in factors}
    # 모든 지표는 normalize 후 "높을수록 좋음"으로 통일됨 (방향 반전 이미 적용)
    ideal = {f["key"]: max(weighted[f["key"]]) for f in factors}
    anti  = {f["key"]: min(weighted[f["key"]]) for f in factors}
    scores = []
    for i in range(N):
        d_plus = math.sqrt(sum((weighted[f["key"]][i] - ideal[f["key"]]) ** 2 for f in factors))
        d_minus = math.sqrt(sum((weighted[f["key"]][i] - anti[f["key"]]) ** 2 for f in factors))
        c = d_minus / (d_plus + d_minus) if (d_plus + d_minus) > 0 else 0
        scores.append(c)
    return scores


# ---------- 3. Entropy-weighted WSM ----------
def entropy_weights_from_norm(norm, factors, N):
    k = 1.0 / math.log(N)
    diversities = {}
    for f in factors:
        col = [max(v, 1e-9) for v in norm[f["key"]]]
        col_sum = sum(col)
        p = [v / col_sum for v in col]
        e = -k * sum(pi * math.log(pi) for pi in p if pi > 0)
        diversities[f["key"]] = 1 - e
    total = sum(diversities.values())
    return {k_: v / total * 100 for k_, v in diversities.items()}


def wsm_entropy(names, norm, factors):
    w = entropy_weights_from_norm(norm, factors, len(names))
    return wsm(names, norm, factors, w)


# ---------- 4. Borda count ----------
def borda(names, norm, factors):
    """각 지표별 순위 부여 후 합산. 작을수록 좋음 → 음수로 변환."""
    N = len(names)
    rank_sum = [0.0] * N
    for f in factors:
        col = norm[f["key"]]
        # 내림차순 순위 (높은 값 = 좋음 = 작은 순위)
        ranks = pd.Series(col).rank(ascending=False, method="average").values
        for i in range(N):
            rank_sum[i] += ranks[i]
    # 순위 합 작을수록 좋음 → 점수는 큰 값일수록 좋음으로 변환
    max_sum = max(rank_sum)
    return [max_sum - s for s in rank_sum]


def to_ranks(scores: list[float]) -> list[float]:
    """점수 → 내림차순 순위 (1이 최상위)."""
    return pd.Series(scores).rank(ascending=False, method="average").tolist()


def spearman_rho_pair(x: list[float], y: list[float]) -> float:
    n = len(x)
    rx = pd.Series(x).rank().values
    ry = pd.Series(y).rank().values
    mx, my = sum(rx) / n, sum(ry) / n
    cov = sum((rx[i] - mx) * (ry[i] - my) for i in range(n))
    sx = (sum((v - mx) ** 2 for v in rx)) ** 0.5
    sy = (sum((v - my) ** 2 for v in ry)) ** 0.5
    return cov / (sx * sy) if sx * sy > 0 else 0.0


def main() -> int:
    payload = json.loads(REGIONS_JSON.read_text(encoding="utf-8"))
    names, norm, factors = load_normalized(payload)
    N = len(names)

    # 4개 방법 점수
    s_wsm = wsm(names, norm, factors, DEFAULT_WEIGHTS)
    s_topsis = topsis(names, norm, factors, DEFAULT_WEIGHTS)
    s_entropy = wsm_entropy(names, norm, factors)
    s_borda = borda(names, norm, factors)

    # DataFrame
    df = pd.DataFrame({
        "name": names,
        "WSM": s_wsm,
        "TOPSIS": s_topsis,
        "Entropy": s_entropy,
        "Borda": s_borda,
    })
    df["rank_WSM"] = to_ranks(s_wsm)
    df["rank_TOPSIS"] = to_ranks(s_topsis)
    df["rank_Entropy"] = to_ranks(s_entropy)
    df["rank_Borda"] = to_ranks(s_borda)
    df["rank_mean"] = df[["rank_WSM", "rank_TOPSIS", "rank_Entropy", "rank_Borda"]].mean(axis=1)

    print("=" * 60)
    print("4개 MCDM 방법 비교")
    print("=" * 60)

    # 일치도 행렬
    methods = ["WSM", "TOPSIS", "Entropy", "Borda"]
    print(f"\nSpearman 상관 행렬 (4개 방법 간 순위 일치도):")
    print(f"{'':<10s}" + "".join(f"{m:>10s}" for m in methods))
    rho_matrix = {}
    for m1 in methods:
        row = [f"{m1:<10s}"]
        rho_matrix[m1] = {}
        for m2 in methods:
            x = df[f"rank_{m1}"].tolist()
            y = df[f"rank_{m2}"].tolist()
            rho = spearman_rho_pair(x, y)
            rho_matrix[m1][m2] = rho
            row.append(f"{rho:>10.4f}")
        print("".join(row))

    # Top 10 by each method
    print("\n각 방법의 Top 10:")
    for m in methods:
        top = df.sort_values(f"rank_{m}").head(10)["name"].tolist()
        print(f"  {m:<8s}: {', '.join(top)}")

    # 공통 Top 10 (모든 방법에서 Top N 진입)
    for n_top in [10, 15, 20]:
        sets = [set(df.sort_values(f"rank_{m}").head(n_top)["name"].tolist()) for m in methods]
        common = sets[0]
        for s in sets[1:]:
            common &= s
        print(f"\n4개 방법 공통 Top {n_top}: {sorted(common)} ({len(common)}개)")

    # Borda를 종합 추천 (방법 비모수)
    df_final = df.sort_values("rank_mean").head(15)
    print(f"\n=== 4개 방법 평균 순위 Top 15 (가장 견고) ===")
    for _, r in df_final.iterrows():
        print(f"  {r['name']:12s} avg_rank={r['rank_mean']:>5.1f}  "
              f"WSM={int(r['rank_WSM']):>3d}  TOPSIS={int(r['rank_TOPSIS']):>3d}  "
              f"Entropy={int(r['rank_Entropy']):>3d}  Borda={int(r['rank_Borda']):>3d}")

    # 보고서
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 교차 방법론 비교 — 4개 MCDM 일치도 검증",
        "",
        "## 방법",
        "동일 데이터(109 시군 × 9 지표)에 4가지 다기준 의사결정 방법 적용:",
        "1. **WSM (Weighted Sum Method)** — 현재 모델. 정규화 후 가중평균.",
        "2. **TOPSIS** — 이상해·반이상해와의 거리 기반.",
        "3. **Entropy-weighted WSM** — 가중치를 entropy 기반으로 객관 도출 후 WSM.",
        "4. **Borda count** — 지표별 순위 합 (비모수, 가중치 영향 X).",
        "",
        "## 4개 방법 순위 일치도 (Spearman ρ)",
        "",
        "| | " + " | ".join(methods) + " |",
        "|" + "|".join(["---"] * 5) + "|",
    ]
    for m1 in methods:
        row = [m1] + [f"{rho_matrix[m1][m2]:.4f}" for m2 in methods]
        lines.append("| " + " | ".join(row) + " |")

    lines += [
        "",
        "## 각 방법의 Top 10",
        "",
    ]
    for m in methods:
        top = df.sort_values(f"rank_{m}").head(10)["name"].tolist()
        lines.append(f"- **{m}**: {', '.join(top)}")

    lines += [
        "",
        "## 4개 방법 공통 Top N (가장 견고한 후보)",
        "",
        "| N | 공통 시군 수 | 시군 |",
        "|---|---|---|",
    ]
    for n_top in [10, 15, 20]:
        sets = [set(df.sort_values(f"rank_{m}").head(n_top)["name"].tolist()) for m in methods]
        common = sorted(sets[0].intersection(*sets[1:]))
        lines.append(f"| {n_top} | {len(common)} | {', '.join(common)} |")

    lines += [
        "",
        "## 평균 순위 Top 15 (4개 방법 합산)",
        "방법별 가중치 가정과 무관하게 일관되게 상위로 평가받는 시군:",
        "",
        "| 순위 | 시군 | 평균 | WSM | TOPSIS | Entropy | Borda |",
        "|---|---|---|---|---|---|---|",
    ]
    for i, (_, r) in enumerate(df_final.iterrows(), 1):
        lines.append(f"| {i} | {r['name']} | {r['rank_mean']:.1f} | "
                     f"{int(r['rank_WSM'])} | {int(r['rank_TOPSIS'])} | "
                     f"{int(r['rank_Entropy'])} | {int(r['rank_Borda'])} |")

    lines += [
        "",
        "## 결론",
        f"- 4개 방법 간 평균 Spearman ρ = "
        f"**{sum(rho_matrix[m1][m2] for m1 in methods for m2 in methods if m1 != m2) / 12:.4f}**",
        "- 0.7 이상이면 방법론 견고성 입증. 0.5 미만은 가중치 가정에 매우 민감 = 추가 검증 필요.",
        "- 4개 방법 공통 Top N에 들어가는 시군은 **방법론 가정과 무관하게 일관된 후보** — 최우선 정책 대상.",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n✓ 방법론 비교 → {OUT_MD.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
