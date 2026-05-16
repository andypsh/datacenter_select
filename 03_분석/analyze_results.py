"""결과 통계표 생성 — 보고서/PPT용 임베드 자료.

출력: 05_보고서/results_tables.md
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGIONS_JSON = ROOT / "04_시각화" / "frontend" / "public" / "data" / "regions.json"
OUT_MD = ROOT / "05_보고서" / "results_tables.md"

DEFAULT_WEIGHTS = {
    "power": 18, "temp": 8, "earthquake": 10, "typhoon": 7, "price": 12,
    "industry": 12, "companies": 8, "vitality": 15, "renewable": 10,
}

PRESETS = {
    "cost_first": {"power": 15, "temp": 5, "earthquake": 5, "typhoon": 5,
                   "price": 25, "industry": 15, "companies": 10, "vitality": 10, "renewable": 10},
    "stability_first": {"power": 25, "temp": 12, "earthquake": 15, "typhoon": 13,
                         "price": 5, "industry": 5, "companies": 5, "vitality": 10, "renewable": 10},
    "regional_balance": {"power": 12, "temp": 5, "earthquake": 8, "typhoon": 5,
                         "price": 10, "industry": 10, "companies": 5, "vitality": 25, "renewable": 20},
}
PRESET_LABEL = {
    "cost_first": "비용 최우선",
    "stability_first": "안정성 최우선",
    "regional_balance": "지역균형 최우선 ★",
}


def mm_norm(values, direction):
    lo, hi = min(values), max(values)
    rng = hi - lo or 1
    norm = [(v - lo) / rng for v in values]
    return [1 - x for x in norm] if direction == "lower_is_better" else norm


def score_all(regions, factors, weights):
    normed = {}
    for f in factors:
        vals = [r["factors"][f["key"]] for r in regions]
        normed[f["key"]] = mm_norm(vals, f["direction"])
    total_w = sum(weights.values())
    out = []
    for i, r in enumerate(regions):
        s = sum(normed[f["key"]][i] * weights[f["key"]] / total_w for f in factors)
        out.append({**r, "score": s})
    out.sort(key=lambda x: -x["score"])
    return out


def main() -> int:
    payload = json.loads(REGIONS_JSON.read_text(encoding="utf-8"))
    factors = payload["factors"]
    regions = payload["regions"]

    lines = []
    lines.append("# 분석 결과 통계표\n")
    lines.append(f"> 분석 대상: {len(regions)}개 시군 / 9개 지표\n")
    lines.append(f"> 산업부 산하 데이터: {sum(1 for f in factors if f['isMotie'])}/9 지표 — "
                 + ", ".join(f["label"] for f in factors if f["isMotie"]))

    # 1) 기본 가중치 Top 10
    scored = score_all(regions, factors, DEFAULT_WEIGHTS)
    lines.append("\n\n## 1. 기본 가중치 Top 10\n")
    lines.append("| 순위 | 시군 | 종합점수 | 수도권 | 인구감소 |")
    lines.append("|---|---|---|---|---|")
    for i, r in enumerate(scored[:10], 1):
        lines.append(f"| {i} | {r['name']} | {r['score']:.3f} | "
                     f"{'O' if r.get('is_metropolitan') else '-'} | "
                     f"{'O' if r.get('is_population_decline') else '-'} |")

    # 2) 비수도권 Top 10
    non_metro = [r for r in scored if not r.get("is_metropolitan")][:10]
    lines.append("\n## 2. 비수도권 Top 10 (지역균형 발전 관점 ★)\n")
    lines.append("| 순위 | 시군 | 점수 | 인구감소지역 |")
    lines.append("|---|---|---|---|")
    for i, r in enumerate(non_metro, 1):
        lines.append(f"| {i} | {r['name']} | {r['score']:.3f} | "
                     f"{'O' if r.get('is_population_decline') else '-'} |")

    # 3) 시나리오별 Top 5
    lines.append("\n## 3. 시나리오 프리셋별 Top 5\n")
    lines.append("| 순위 | 비용 최우선 | 안정성 최우선 | **지역균형 최우선** ★ |")
    lines.append("|---|---|---|---|")
    scenario_top5 = {}
    for pid, w in PRESETS.items():
        s = score_all(regions, factors, w)
        scenario_top5[pid] = s[:5]
    for i in range(5):
        cells = []
        for pid in ["cost_first", "stability_first", "regional_balance"]:
            r = scenario_top5[pid][i]
            cells.append(f"{r['name']} ({r['score']:.3f})")
        lines.append(f"| {i+1} | {cells[0]} | {cells[1]} | {cells[2]} |")

    # 4) 인구감소지역 적합도 Top 5
    decline_scored = [r for r in scored if r.get("is_population_decline")][:5]
    lines.append("\n## 4. 인구감소지역 적합 후보지 Top 5\n")
    lines.append("> 데이터센터 입주 시 지역활력 회복 잠재력이 높은 행안부 지정 인구감소지역.\n")
    lines.append("| 순위 | 시군 | 종합점수 |")
    lines.append("|---|---|---|")
    for i, r in enumerate(decline_scored, 1):
        lines.append(f"| {i} | {r['name']} | {r['score']:.3f} |")

    # 5) 수도권 집중도 통계
    metro_in_top = sum(1 for r in scored[:10] if r.get("is_metropolitan"))
    decline_in_top = sum(1 for r in scored[:10] if r.get("is_population_decline"))
    lines.append("\n## 5. 종합 통계 (기본 가중치 기준)\n")
    lines.append(f"- Top 10 중 수도권 비중: **{metro_in_top}/10 = {metro_in_top*10}%**")
    lines.append(f"- Top 10 중 인구감소지역 비중: **{decline_in_top}/10 = {decline_in_top*10}%**")
    lines.append(f"- 인구감소지역 전체 평균 점수: **{sum(r['score'] for r in scored if r.get('is_population_decline'))/max(sum(1 for r in scored if r.get('is_population_decline')),1):.3f}**")
    lines.append(f"- 수도권 전체 평균 점수: **{sum(r['score'] for r in scored if r.get('is_metropolitan'))/max(sum(1 for r in scored if r.get('is_metropolitan')),1):.3f}**")
    lines.append(f"- 비수도권 전체 평균 점수: **{sum(r['score'] for r in scored if not r.get('is_metropolitan'))/max(sum(1 for r in scored if not r.get('is_metropolitan')),1):.3f}**")

    # 6) 지표별 평균
    lines.append("\n## 6. 지표별 평균 (정규화 전 원시값)\n")
    lines.append("| 지표 | 평균 | 최솟값 | 최댓값 |")
    lines.append("|---|---|---|---|")
    for f in factors:
        vals = [r["factors"][f["key"]] for r in regions]
        avg = sum(vals) / len(vals)
        unit = f.get("unit", "")
        lines.append(f"| {f['label']} ({unit}) | {avg:.3f} | {min(vals):.3f} | {max(vals):.3f} |")

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"OK -> {OUT_MD.relative_to(ROOT)}")
    print(f"  Top 10 중 수도권 {metro_in_top}개, 인구감소 {decline_in_top}개")
    return 0


if __name__ == "__main__":
    sys.exit(main())
