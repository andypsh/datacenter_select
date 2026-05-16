"""민감도 분석 — 가중치 ±20% 변동에 Top 10 결과가 얼마나 견고한가.

방법:
  - 기본 가중치 (default) Top 10 산출
  - 9개 지표 각각의 가중치를 ±20% 변동시켜 18개 시나리오 생성
  - 각 시나리오에서 Top 10 재계산
  - 모든 시나리오에서 일관되게 Top 10에 등장하는 시군 = 견고한 후보

출력: 05_보고서/sensitivity_table.md (보고서에 임베드용)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REGIONS_JSON = ROOT / "04_시각화" / "frontend" / "public" / "data" / "regions.json"
OUT_MD = ROOT / "05_보고서" / "sensitivity_table.md"

# scoring.ts 기본 가중치와 동일
DEFAULT_WEIGHTS = {
    "power": 18, "temp": 8, "earthquake": 10, "typhoon": 7, "price": 12,
    "industry": 12, "companies": 8, "vitality": 15, "renewable": 10,
}


def mm_norm(values: list[float], direction: str) -> list[float]:
    arr = [v for v in values if v is not None]
    lo, hi = min(arr), max(arr)
    rng = hi - lo or 1
    norm = [(v - lo) / rng for v in values]
    return [1 - x for x in norm] if direction == "lower_is_better" else norm


def compute_topn(regions: list[dict], factors: list[dict],
                 weights: dict[str, float], n: int = 10) -> list[str]:
    """가중치로 점수 계산 후 상위 N개 시군 이름 반환."""
    # 정규화
    normed = {}
    for f in factors:
        key, direction = f["key"], f["direction"]
        vals = [r["factors"][key] for r in regions]
        normed[key] = mm_norm(vals, direction)

    total_w = sum(weights.values())
    scores = []
    for i, r in enumerate(regions):
        s = sum(normed[f["key"]][i] * weights[f["key"]] / total_w for f in factors)
        scores.append((r["name"], s))
    scores.sort(key=lambda x: -x[1])
    return [name for name, _ in scores[:n]]


def main() -> int:
    payload = json.loads(REGIONS_JSON.read_text(encoding="utf-8"))
    factors = payload["factors"]
    regions = payload["regions"]
    factor_keys = [f["key"] for f in factors]

    # 1) baseline Top 10
    base_top = compute_topn(regions, factors, DEFAULT_WEIGHTS, n=10)
    print(f"Baseline Top 10:")
    for i, n in enumerate(base_top, 1):
        print(f"  {i:2}. {n}")

    # 2) 9개 지표 각각 ±20% 시나리오 (총 18개)
    appearance = {n: 0 for n in [r["name"] for r in regions]}
    scenarios = []
    for key in factor_keys:
        for delta in (-0.20, +0.20):
            w = dict(DEFAULT_WEIGHTS)
            w[key] = max(0.01, w[key] * (1.0 + delta))
            top = compute_topn(regions, factors, w, n=10)
            scenarios.append({
                "factor": key,
                "delta_pct": int(delta * 100),
                "top": top,
            })
            for n in top:
                appearance[n] += 1

    # 3) 견고성 점수: 각 시군이 18 시나리오 중 몇 번 Top 10에 등장?
    robust_ranking = sorted(appearance.items(), key=lambda x: -x[1])

    # 4) 출력 markdown
    lines = []
    lines.append("# 민감도 분석 결과\n")
    lines.append("> 가중치 ±20% 변동(9개 지표 × 2방향 = 18 시나리오) 하에 Top 10 결과의 견고성.\n")

    lines.append("\n## 기본 가중치 Top 10\n")
    lines.append("| 순위 | 시군 |")
    lines.append("|---|---|")
    for i, n in enumerate(base_top, 1):
        lines.append(f"| {i} | {n} |")

    lines.append("\n## 견고성 랭킹 (18 시나리오 중 Top 10 등장 횟수)\n")
    lines.append("| 시군 | 등장 횟수 | 견고성 |")
    lines.append("|---|---|---|")
    for n, c in robust_ranking[:20]:
        if c == 0:
            continue
        robustness = "★★★ 매우 견고" if c >= 17 else ("★★ 견고" if c >= 12 else ("★ 보통" if c >= 6 else ""))
        lines.append(f"| {n} | {c}/18 | {robustness} |")

    lines.append("\n## 시나리오별 Top 5 변화\n")
    lines.append("| 변동 지표 | Δ% | Top 5 |")
    lines.append("|---|---|---|")
    for s in scenarios:
        top5 = ", ".join(s["top"][:5])
        lines.append(f"| {s['factor']} | {s['delta_pct']:+d}% | {top5} |")

    lines.append("\n## 해석\n")
    always_top = [n for n, c in robust_ranking if c == 18]
    lines.append(f"- **모든 18 시나리오에서 Top 10 유지**: {len(always_top)}개 시군 — {', '.join(always_top) if always_top else '(없음)'}\n")
    near_robust = [n for n, c in robust_ranking if 14 <= c < 18]
    lines.append(f"- **14~17 시나리오에서 Top 10**: {len(near_robust)}개 — {', '.join(near_robust) if near_robust else '(없음)'}\n")
    lines.append("- 베이스라인 Top 10 외 새로 등장하는 시군이 있다면, 특정 지표 강세 후보로 정책 인센티브 시 고려.")

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nOK -> {OUT_MD.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
