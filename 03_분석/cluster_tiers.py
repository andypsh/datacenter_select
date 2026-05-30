"""k-means 클러스터링 — 109 시군을 9개 지표 공간에서 Tier 그룹화.

목적: 단순 순위 외에 "비슷한 특성을 가진 시군 그룹" 식별 → 정책 패키지 차별화.

방법:
1. 9개 지표 정규화 (방향 반전 포함, [0,1])
2. k = 3, 4, 5에 대해 k-means 실행 (scipy 없이 직접 구현)
3. silhouette score로 최적 k 선택
4. 각 클러스터의 특성 (지표별 평균) → Tier 라벨 부여
   - 종합 점수 평균이 가장 높은 클러스터 = Tier 1 (최우수)
   - 그 다음 = Tier 2 ...
5. 시군별 Tier 라벨을 regions.json에 추가
"""

from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REGIONS_JSON = ROOT / "04_시각화" / "frontend" / "public" / "data" / "regions.json"
OUT_MD = ROOT / "05_보고서" / "cluster_tiers.md"
OUT_JSON = ROOT / "04_시각화" / "frontend" / "public" / "data" / "tiers.json"

SEED = 14_2026
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


def euclidean(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(len(a))))


def kmeans(X: list[list[float]], k: int, n_init: int = 10, max_iter: int = 100, seed: int = SEED):
    """단순 k-means 구현. n_init번 반복 후 inertia 가장 낮은 결과 반환."""
    N, D = len(X), len(X[0])
    rng = random.Random(seed)

    best_labels = None
    best_centers = None
    best_inertia = float("inf")

    for trial in range(n_init):
        # k-means++ 비스무리: 무작위 초기 + 거리 가중
        rnd = random.Random(seed + trial)
        centers = [X[rnd.randint(0, N - 1)][:]]
        while len(centers) < k:
            d2 = [min(euclidean(x, c) ** 2 for c in centers) for x in X]
            total = sum(d2) or 1
            r = rnd.random() * total
            acc = 0.0
            for i, val in enumerate(d2):
                acc += val
                if acc >= r:
                    centers.append(X[i][:])
                    break

        # Lloyd's
        for _ in range(max_iter):
            labels = [min(range(k), key=lambda j: euclidean(X[i], centers[j])) for i in range(N)]
            new_centers = []
            for j in range(k):
                members = [X[i] for i in range(N) if labels[i] == j]
                if not members:
                    new_centers.append(X[rnd.randint(0, N - 1)][:])
                else:
                    new_centers.append([sum(m[d] for m in members) / len(members) for d in range(D)])
            if all(euclidean(centers[j], new_centers[j]) < 1e-6 for j in range(k)):
                centers = new_centers
                break
            centers = new_centers

        inertia = sum(euclidean(X[i], centers[labels[i]]) ** 2 for i in range(N))
        if inertia < best_inertia:
            best_inertia = inertia
            best_labels = labels
            best_centers = centers

    return best_labels, best_centers, best_inertia


def silhouette(X: list[list[float]], labels: list[int]) -> float:
    """평균 silhouette score. O(N²)."""
    N = len(X)
    scores = []
    for i in range(N):
        same_cluster = [j for j in range(N) if labels[j] == labels[i] and j != i]
        other_clusters: dict[int, list[int]] = {}
        for j in range(N):
            if labels[j] != labels[i]:
                other_clusters.setdefault(labels[j], []).append(j)
        if not same_cluster or not other_clusters:
            continue
        a = sum(euclidean(X[i], X[j]) for j in same_cluster) / len(same_cluster)
        b = min(
            sum(euclidean(X[i], X[j]) for j in members) / len(members)
            for members in other_clusters.values()
        )
        s = (b - a) / max(a, b) if max(a, b) > 0 else 0
        scores.append(s)
    return sum(scores) / len(scores) if scores else 0.0


def main() -> int:
    payload = json.loads(REGIONS_JSON.read_text(encoding="utf-8"))
    factors = payload["factors"]
    regions = payload["regions"]
    names = [r["name"] for r in regions]

    # 정규화 행렬 X (109 × 9)
    norm: dict[str, list[float]] = {}
    for f in factors:
        raw = [r["factors"][f["key"]] for r in regions]
        norm[f["key"]] = normalize_minmax_directional(raw, f["direction"])
    X = [[norm[f["key"]][i] for f in factors] for i in range(len(regions))]

    print("=" * 60)
    print(f"k-means 클러스터링 (N={len(regions)} 시군, D={len(factors)} 지표)")
    print("=" * 60)

    # 종합점수 (Tier 라벨 부여 기준)
    wsum = sum(DEFAULT_WEIGHTS.values())
    scores = []
    for i in range(len(regions)):
        s = sum(norm[f["key"]][i] * DEFAULT_WEIGHTS[f["key"]] / wsum for f in factors)
        scores.append(s)

    # k 탐색
    print(f"\nElbow + silhouette 탐색:")
    print(f"{'k':<4s} {'inertia':>12s} {'silhouette':>12s}")
    best_k = 4
    best_sil = -1.0
    inertias = {}
    for k in [3, 4, 5, 6]:
        labels, centers, inertia = kmeans(X, k, n_init=15)
        sil = silhouette(X, labels)
        inertias[k] = inertia
        print(f"{k:<4d} {inertia:>12.4f} {sil:>12.4f}")
        if sil > best_sil:
            best_sil = sil
            best_k = k

    print(f"\n최적 k = {best_k} (silhouette = {best_sil:.4f})")

    # 최적 k로 최종 클러스터링
    labels, centers, _ = kmeans(X, best_k, n_init=30)

    # 클러스터별 평균 종합점수로 정렬 → Tier 라벨
    cluster_scores: dict[int, list[float]] = {}
    for i, lbl in enumerate(labels):
        cluster_scores.setdefault(lbl, []).append(scores[i])
    cluster_avg = {c: sum(s) / len(s) for c, s in cluster_scores.items()}
    sorted_clusters = sorted(cluster_avg.keys(), key=lambda c: -cluster_avg[c])
    tier_labels = ["Tier 1 (최우수)", "Tier 2 (우수)", "Tier 3 (유망)", "Tier 4 (가능)", "Tier 5 (보류)"]
    cluster_to_tier = {c: tier_labels[i] for i, c in enumerate(sorted_clusters)}

    print(f"\n=== Tier 별 시군 분포 ===")
    for c in sorted_clusters:
        members = sorted(
            [(names[i], scores[i]) for i in range(len(names)) if labels[i] == c],
            key=lambda x: -x[1],
        )
        tier = cluster_to_tier[c]
        print(f"\n{tier}: 평균 종합점수 {cluster_avg[c]:.3f}, {len(members)}개 시군")
        # 상위 10개만 표시
        for name, s in members[:10]:
            print(f"  {name:12s} {s:.3f}")
        if len(members) > 10:
            print(f"  ... ({len(members) - 10}개 더)")

    # 클러스터 특성 (지표별 평균)
    print(f"\n=== 클러스터 특성 (9개 지표 평균) ===")
    factor_keys = [f["key"] for f in factors]
    factor_labels = [f["label"] for f in factors]
    print(f"{'Tier':<18s}" + "".join(f"{l[:6]:>8s}" for l in factor_labels))
    for c in sorted_clusters:
        tier = cluster_to_tier[c]
        cluster_X = [X[i] for i in range(len(X)) if labels[i] == c]
        means = [sum(x[j] for x in cluster_X) / len(cluster_X) for j in range(len(factor_keys))]
        row = [f"{tier:<18s}"]
        for m in means:
            row.append(f"{m:>8.2f}")
        print("".join(row))

    # JSON 저장 (Vue 앱에서 사용)
    tier_data = {
        "k": best_k,
        "silhouette": best_sil,
        "regions": [
            {"name": names[i], "tier": cluster_to_tier[labels[i]], "score": scores[i]}
            for i in range(len(names))
        ],
    }
    OUT_JSON.write_text(json.dumps(tier_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✓ Tier JSON → {OUT_JSON.relative_to(ROOT)}")

    # 보고서
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 클러스터링 Tier 분류 — k-means",
        "",
        "## 방법",
        "109 시군을 9개 지표 (정규화된) 공간에서 k-means로 그룹화 → Tier 라벨 부여.",
        "",
        f"- 거리: 유클리디안",
        f"- 초기화: k-means++ × 15회 반복, inertia 최소 채택",
        f"- 시드: `SEED = 14_2026` (재현 가능)",
        f"- 최적 k 선택: silhouette score 최대",
        "",
        "## k 탐색 결과",
        "",
        "| k | Inertia | Silhouette |",
        "|---|---|---|",
    ]
    for k in [3, 4, 5, 6]:
        labels_k, _, inertia_k = kmeans(X, k, n_init=15)
        sil_k = silhouette(X, labels_k)
        marker = " ★" if k == best_k else ""
        lines.append(f"| {k}{marker} | {inertia_k:.4f} | {sil_k:.4f} |")

    lines += [
        "",
        f"**최적 k = {best_k}** (silhouette = {best_sil:.4f})",
        "",
        "## Tier 별 시군 분포",
        "",
    ]
    for c in sorted_clusters:
        members = sorted(
            [(names[i], scores[i]) for i in range(len(names)) if labels[i] == c],
            key=lambda x: -x[1],
        )
        tier = cluster_to_tier[c]
        lines.append(f"### {tier} ({len(members)}개)")
        lines.append(f"클러스터 평균 종합점수: **{cluster_avg[c]:.3f}**")
        lines.append("")
        lines.append("| 순위 | 시군 | 점수 |")
        lines.append("|---|---|---|")
        for i, (name, s) in enumerate(members, 1):
            lines.append(f"| {i} | {name} | {s:.3f} |")
        lines.append("")

    lines += [
        "## 클러스터 특성 표 (9개 지표 평균)",
        "",
        "| Tier | " + " | ".join(f["label"] for f in factors) + " |",
        "|" + "|".join(["---"] * (len(factors) + 1)) + "|",
    ]
    for c in sorted_clusters:
        tier = cluster_to_tier[c]
        cluster_X = [X[i] for i in range(len(X)) if labels[i] == c]
        means = [sum(x[j] for x in cluster_X) / len(cluster_X) for j in range(len(factor_keys))]
        row = [tier] + [f"{m:.2f}" for m in means]
        lines.append("| " + " | ".join(row) + " |")

    lines += [
        "",
        "## 정책 활용",
        "Tier별로 차별화된 정책 패키지 설계 가능:",
        "- **Tier 1**: 즉시 입지 검토, 기본 인센티브",
        "- **Tier 2**: 부분 인프라 보완 + 인센티브 패키지",
        "- **Tier 3**: 전력·통신 인프라 확충 우선, 중장기 계획",
        "- **Tier 4~5**: 단기 검토 보류, 환경 개선 정책 우선",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"✓ 클러스터링 보고서 → {OUT_MD.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
