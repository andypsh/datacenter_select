"""Shannon entropy 기반 객관 가중치 도출.

방법론 (MCDM 표준):
1. raw 행렬을 [0,1]로 min-max 정규화 (방향 반전 포함)
2. 각 셀의 비율 p_ij = x_ij / sum_i(x_ij) 계산
3. 지표 j의 entropy E_j = -k * sum_i(p_ij * ln(p_ij)), k = 1/ln(N)
4. 다양성 d_j = 1 - E_j  (entropy 낮을수록 정보량 높음)
5. 가중치 w_j = d_j / sum_j(d_j)

직관: 시군 간 차이가 큰 (variance 큰) 지표는 정보량이 많아 가중치 ↑.
반대로 모든 시군이 비슷한 값을 가지면 의사결정 기여도 ↓.

주관 가중치(Vue 앱 DEFAULT_WEIGHTS)와 비교하여 객관성 검증.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REGIONS_JSON = ROOT / "04_시각화" / "frontend" / "public" / "data" / "regions.json"
OUT_MD = ROOT / "05_보고서" / "entropy_weights.md"

# 주관 가중치 (Vue 앱 scoring.ts DEFAULT_WEIGHTS와 동일)
SUBJECTIVE = {
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
    # entropy 계산 위해 0 회피 (log 0 방지)
    n = [max(v, 1e-9) for v in n]
    return n


def entropy_weights(payload: dict) -> dict[str, float]:
    """payload의 9개 지표에서 entropy method로 객관 가중치 도출."""
    factors = payload["factors"]
    regions = payload["regions"]
    N = len(regions)
    k = 1.0 / math.log(N)

    # 1) 정규화 (방향 반전 포함)
    norm: dict[str, list[float]] = {}
    for f in factors:
        raw = [r["factors"][f["key"]] for r in regions]
        norm[f["key"]] = normalize_minmax_directional(raw, f["direction"])

    # 2) 비율
    ratios: dict[str, list[float]] = {}
    for f in factors:
        col_sum = sum(norm[f["key"]])
        ratios[f["key"]] = [v / col_sum for v in norm[f["key"]]]

    # 3) entropy E_j
    entropies: dict[str, float] = {}
    for f in factors:
        p = ratios[f["key"]]
        e = -k * sum(pi * math.log(pi) for pi in p if pi > 0)
        entropies[f["key"]] = e

    # 4) 다양성 d_j = 1 - E_j
    diversities = {k_: 1.0 - v for k_, v in entropies.items()}

    # 5) 가중치 w_j = d_j / sum(d_j) × 100
    total_d = sum(diversities.values())
    weights = {k_: v / total_d * 100 for k_, v in diversities.items()}

    return {
        "entropy": entropies,
        "diversity": diversities,
        "weights": weights,
    }


def spearman_rho_pair(d1: dict[str, float], d2: dict[str, float]) -> float:
    """두 가중치 dict의 Spearman 상관."""
    keys = list(d1.keys())
    x = [d1[k] for k in keys]
    y = [d2[k] for k in keys]
    n = len(keys)
    rx = pd.Series(x).rank().values
    ry = pd.Series(y).rank().values
    mx, my = sum(rx) / n, sum(ry) / n
    cov = sum((rx[i] - mx) * (ry[i] - my) for i in range(n))
    sx = (sum((v - mx) ** 2 for v in rx)) ** 0.5
    sy = (sum((v - my) ** 2 for v in ry)) ** 0.5
    return cov / (sx * sy) if sx * sy > 0 else 0.0


def main() -> int:
    payload = json.loads(REGIONS_JSON.read_text(encoding="utf-8"))
    result = entropy_weights(payload)

    factors = payload["factors"]
    print("=" * 60)
    print("Shannon Entropy 기반 객관 가중치 도출")
    print("=" * 60)
    print(f"{'지표':<15s} {'Entropy':>10s} {'Diversity':>10s} {'객관 W':>8s} {'주관 W':>8s} {'차이':>8s}")
    print("-" * 70)
    rows = []
    for f in factors:
        k = f["key"]
        e = result["entropy"][k]
        d = result["diversity"][k]
        w_obj = result["weights"][k]
        w_subj = SUBJECTIVE.get(k, 0)
        diff = w_obj - w_subj
        print(f"{f['label'][:14]:<15s} {e:>10.4f} {d:>10.4f} {w_obj:>7.1f}% {w_subj:>7d}% {diff:>+7.1f}%")
        rows.append({"label": f["label"], "key": k, "entropy": e, "diversity": d,
                     "w_obj": w_obj, "w_subj": w_subj, "diff": diff})

    # 일치도
    rho = spearman_rho_pair(SUBJECTIVE, result["weights"])
    print(f"\nSpearman 상관 (주관 vs 객관 가중치 순위) = {rho:+.4f}")

    # 객관 가중치 합 검증
    s = sum(result["weights"].values())
    print(f"객관 가중치 합 = {s:.2f} (100% 기대)")

    # markdown 저장
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 객관 가중치 도출 — Shannon Entropy Method",
        "",
        "## 방법론",
        "1. 9개 지표를 시군 109개에 대해 min-max 정규화 (방향 반전 포함)",
        "2. 각 셀 비율 p_ij = x_ij / Σ_i(x_ij) 계산",
        "3. 지표 j 엔트로피 E_j = −(1/ln N) · Σ p_ij · ln(p_ij)",
        "4. 다양성 d_j = 1 − E_j (정보량)",
        "5. 객관 가중치 w_j = d_j / Σ d_j × 100",
        "",
        "## 결과",
        "",
        "| 지표 | Entropy | Diversity | 객관 W (%) | 주관 W (%) | 차이 |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(f"| {r['label']} | {r['entropy']:.4f} | {r['diversity']:.4f} | "
                     f"{r['w_obj']:.1f}% | {r['w_subj']}% | {r['diff']:+.1f}% |")
    lines += [
        "",
        f"**주관 vs 객관 가중치 순위 상관 (Spearman): {rho:+.4f}**",
        "",
        "## 해석",
    ]
    # 가장 큰 차이 지표 식별
    rows_sorted = sorted(rows, key=lambda r: abs(r["diff"]), reverse=True)
    top_diff = rows_sorted[:3]
    lines.append(f"- 객관·주관 가중치가 가장 큰 차이를 보이는 지표:")
    for r in top_diff:
        direction = "객관 가중치 ↑" if r["diff"] > 0 else "객관 가중치 ↓"
        lines.append(f"  - **{r['label']}**: 주관 {r['w_subj']}% → 객관 {r['w_obj']:.1f}% ({direction})")
    lines += [
        "",
        "- Spearman ρ > 0.5: 주관과 객관 가중치가 대체로 일치하는 방향 (전문가 직관 검증)",
        "- Spearman ρ < 0.3: 주관 가중치 재검토 권장",
        "",
        "객관 가중치는 시군 간 변동성(정보량)이 큰 지표에 더 큰 비중을 부여하는 성질이 있어,",
        "데이터 자체의 변별력을 우선하는 평가 관점을 제공한다. 본 프로젝트에서는 두 가중치 모두를",
        "Vue 대시보드에서 선택 가능하도록 노출하여 정책 담당자가 비교 검토할 수 있게 한다.",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n✓ Entropy 가중치 → {OUT_MD.relative_to(ROOT)}")

    # 객관 가중치를 JSON으로도 저장 (Vue에서 옵션으로 노출 가능)
    out_json = ROOT / "04_시각화" / "frontend" / "public" / "data" / "entropy_weights.json"
    out_json.write_text(json.dumps({
        "weights": {k: round(v, 2) for k, v in result["weights"].items()},
        "entropy": {k: round(v, 4) for k, v in result["entropy"].items()},
        "diversity": {k: round(v, 4) for k, v in result["diversity"].items()},
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ 객관 가중치 JSON → {out_json.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
