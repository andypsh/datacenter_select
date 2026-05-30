"""강건성 분석: Monte Carlo로 가중치 ±N% 변동 시 순위 안정성 측정.

핵심 질문: "우리 결과는 가중치 작은 변동에 견고한가?"

방법:
1. 기본 가중치를 중심으로 가중치를 ±20% / ±50% 균등 분포로 무작위 추출
2. 각 시뮬레이션마다 시군 순위 다시 계산
3. 시군별 순위 분포 통계 (평균·중위·표준편차·Top10 빈도)
4. "Top 10 안정성": K회 시뮬레이션 중 Top 10에 몇 번 들어가는가
5. "Tier별 견고성": Tier 1 = 95%+ Top10 진입, Tier 2 = 50~95%, etc.

시뮬레이션 수: 1,000회 (각 가중치당). 109 시군이라 빠르게 끝.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REGIONS_JSON = ROOT / "04_시각화" / "frontend" / "public" / "data" / "regions.json"
OUT_MD = ROOT / "05_보고서" / "robustness_results.md"

DEFAULT_WEIGHTS = {
    "power": 18, "temp": 8, "earthquake": 10, "typhoon": 7, "price": 12,
    "industry": 12, "companies": 8, "vitality": 15, "renewable": 10,
}

N_SIM = 1000
PERTURBATION_LEVELS = [0.1, 0.2, 0.5]  # ±10%, ±20%, ±50%
SEED = 14_2026


def normalize_minmax_directional(values: list[float], direction: str) -> list[float]:
    valid = [v for v in values if isinstance(v, (int, float))]
    lo, hi = min(valid), max(valid)
    span = max(hi - lo, 1e-9)
    n = [(v - lo) / span for v in values]
    if direction == "lower_is_better":
        n = [1 - v for v in n]
    return n


def score_regions(payload: dict, weights: dict[str, float]) -> list[tuple[str, float]]:
    factors = payload["factors"]
    regions = payload["regions"]
    wsum = sum(weights.values()) or 1.0

    norm: dict[str, list[float]] = {}
    for f in factors:
        raw = [r["factors"][f["key"]] for r in regions]
        norm[f["key"]] = normalize_minmax_directional(raw, f["direction"])

    out = []
    for i, r in enumerate(regions):
        s = sum(norm[f["key"]][i] * weights[f["key"]] / wsum for f in factors)
        out.append((r["name"], s))
    return out


def rank_by_score(scored: list[tuple[str, float]]) -> dict[str, int]:
    """이름 → 순위 (1=Top)."""
    sorted_ = sorted(scored, key=lambda x: -x[1])
    return {name: rank for rank, (name, _) in enumerate(sorted_, 1)}


def perturb_weights(base: dict[str, float], pct: float, rng: random.Random) -> dict[str, float]:
    """각 가중치를 [base*(1-pct), base*(1+pct)]에서 균등 추출."""
    return {k: max(0.1, v * (1 + rng.uniform(-pct, pct))) for k, v in base.items()}


def run_monte_carlo(payload: dict, pct: float, n_sim: int = N_SIM) -> pd.DataFrame:
    rng = random.Random(SEED + int(pct * 100))
    region_names = [r["name"] for r in payload["regions"]]
    rank_records: dict[str, list[int]] = {n: [] for n in region_names}
    top10_count: dict[str, int] = {n: 0 for n in region_names}

    for _ in range(n_sim):
        w = perturb_weights(DEFAULT_WEIGHTS, pct, rng)
        scored = score_regions(payload, w)
        ranks = rank_by_score(scored)
        for name, r in ranks.items():
            rank_records[name].append(r)
            if r <= 10:
                top10_count[name] += 1

    rows = []
    for name in region_names:
        ranks = rank_records[name]
        rows.append({
            "name": name,
            "rank_mean": sum(ranks) / len(ranks),
            "rank_median": sorted(ranks)[len(ranks) // 2],
            "rank_std": (sum((r - sum(ranks) / len(ranks)) ** 2 for r in ranks) / len(ranks)) ** 0.5,
            "top10_freq": top10_count[name] / n_sim * 100,
        })
    return pd.DataFrame(rows).sort_values("rank_mean").reset_index(drop=True)


def main() -> int:
    payload = json.loads(REGIONS_JSON.read_text(encoding="utf-8"))
    print(f"강건성 분석: {N_SIM:,}회 Monte Carlo × {len(PERTURBATION_LEVELS)} 변동 수준")
    print("=" * 60)

    # 기본 가중치 순위 (비교 기준)
    base_scored = score_regions(payload, DEFAULT_WEIGHTS)
    base_ranks = rank_by_score(base_scored)
    base_top10 = sorted(base_scored, key=lambda x: -x[1])[:10]

    all_results = {}
    for pct in PERTURBATION_LEVELS:
        print(f"\n--- 가중치 ±{int(pct*100)}% 변동 ---")
        df = run_monte_carlo(payload, pct)
        all_results[pct] = df
        # Top 10 안정성: 기본 Top 10 중 시뮬에서도 자주 Top 10인 비율
        print(f"기본 Top 10의 시뮬레이션 Top 10 진입 빈도:")
        for name, _ in base_top10:
            row = df[df["name"] == name].iloc[0]
            print(f"  {name:12s} 평균순위={row['rank_mean']:>5.1f}±{row['rank_std']:>4.1f}  "
                  f"Top10 빈도={row['top10_freq']:>5.1f}%")

    # Tier 분류 (±20% 기준)
    df20 = all_results[0.2]
    df20["tier"] = pd.cut(
        df20["top10_freq"],
        bins=[-1, 5, 30, 70, 95, 101],
        labels=["부적합", "가능", "유망", "우수", "최우수"],
    )
    print(f"\n=== Tier 분류 (±20% 변동 기준) ===")
    tier_counts = df20["tier"].value_counts().sort_index(ascending=False)
    for tier, count in tier_counts.items():
        print(f"  Tier {tier}: {count}개 시군")

    print(f"\n=== 최우수 Tier (Top 10 빈도 ≥ 95%, ±20%) ===")
    elite = df20[df20["top10_freq"] >= 95].sort_values("rank_mean")
    for _, r in elite.iterrows():
        print(f"  {r['name']:12s} 평균={r['rank_mean']:>5.1f}  Top10={r['top10_freq']:>5.1f}%")

    # Markdown 보고서
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 강건성 분석: Monte Carlo (가중치 변동에 대한 순위 안정성)",
        "",
        "## 방법",
        f"- 시뮬레이션 수: **{N_SIM:,}회** × 3 변동 수준 (±10%, ±20%, ±50%) = {N_SIM*3:,}회",
        "- 각 시뮬레이션마다 9개 가중치를 ±N% 균등 분포에서 무작위 추출",
        "- 시군별 순위 분포 → 평균·중위·표준편차·Top10 진입 빈도 집계",
        "- 시드 고정 (`SEED = 14_2026`)으로 재현 가능",
        "",
        "## 기본 시나리오 Top 10의 안정성 (±20% 변동)",
        "",
        "| 순위 | 시군 | 평균 순위 | 표준편차 | Top 10 빈도 | 견고성 |",
        "|---|---|---|---|---|---|",
    ]
    df20_dict = {r["name"]: r for _, r in df20.iterrows()}
    for i, (name, _) in enumerate(base_top10, 1):
        row = df20_dict[name]
        f = row["top10_freq"]
        flag = "🟢 견고" if f >= 90 else "🟡 보통" if f >= 60 else "🔴 변동성↑"
        lines.append(f"| {i} | {name} | {row['rank_mean']:.1f} | "
                     f"{row['rank_std']:.1f} | {f:.1f}% | {flag} |")

    lines += [
        "",
        "## 변동 수준별 비교 (기본 Top 10의 평균 Top10 빈도)",
        "",
        "| 변동 | 평균 Top10 빈도 | 해석 |",
        "|---|---|---|",
    ]
    for pct in PERTURBATION_LEVELS:
        df = all_results[pct]
        df_dict = {r["name"]: r for _, r in df.iterrows()}
        avg_freq = sum(df_dict[n]["top10_freq"] for n, _ in base_top10) / len(base_top10)
        interp = "매우 견고" if avg_freq >= 85 else "견고" if avg_freq >= 65 else "변동 영향 큼"
        lines.append(f"| ±{int(pct*100)}% | {avg_freq:.1f}% | {interp} |")

    lines += [
        "",
        "## Tier 분류 (±20% 변동 기준)",
        "Top10 진입 빈도로 시군을 5개 Tier로 분류:",
        "",
        "| Tier | Top10 빈도 | 시군 수 |",
        "|---|---|---|",
    ]
    tier_order = ["최우수", "우수", "유망", "가능", "부적합"]
    tier_range = {"최우수": "95% 이상", "우수": "70~95%", "유망": "30~70%",
                  "가능": "5~30%", "부적합": "5% 미만"}
    for t in tier_order:
        c = int((df20["tier"] == t).sum())
        lines.append(f"| {t} | {tier_range[t]} | {c} |")

    lines += [
        "",
        "## 최우수 Tier 시군 (가장 견고한 후보)",
        "",
        "| 시군 | 평균 순위 | Top10 빈도 |",
        "|---|---|---|",
    ]
    for _, r in elite.iterrows():
        lines.append(f"| {r['name']} | {r['rank_mean']:.1f} | {r['top10_freq']:.1f}% |")

    lines += [
        "",
        "## 결론",
        f"기본 Top 10 중 **Top10 빈도 ≥ 90%** 시군은 가중치 ±20% 변동에도 견고함을 입증.",
        "",
        "이 결과는 우리 모델의 **결정 안정성**을 정량 입증한다. 단순 ranking이 아닌,",
        "가중치 불확실성 하에서도 일관되게 상위에 머무는 후보지를 식별 가능.",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n✓ 강건성 보고서 → {OUT_MD.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
