import { defineStore } from "pinia";
import { computed, ref } from "vue";
import type {
  Factor,
  FactorKey,
  Region,
  RegionsPayload,
  ScenarioPreset,
  ScoredRegion,
} from "../types";

const DEFAULT_WEIGHTS: Record<FactorKey, number> = {
  power: 18, temp: 8, earthquake: 10, typhoon: 7, price: 12,
  industry: 12, companies: 8, vitality: 15, renewable: 10,
};

export const SCENARIO_PRESETS: ScenarioPreset[] = [
  {
    id: "cost_first",
    label: "비용 최우선",
    description: "토지비/세제/산업 인센티브 중심. 빠른 ROI.",
    weights: { power: 15, temp: 5, earthquake: 5, typhoon: 5,
      price: 25, industry: 15, companies: 10, vitality: 10, renewable: 10 },
    highlight: ["cost", "industry"],
  },
  {
    id: "stability_first",
    label: "안정성 최우선",
    description: "전력/재해/냉각 중심. 미션 크리티컬.",
    weights: { power: 25, temp: 12, earthquake: 15, typhoon: 13,
      price: 5, industry: 5, companies: 5, vitality: 10, renewable: 10 },
    highlight: ["power", "safety"],
  },
  {
    id: "regional_balance",
    label: "지역균형 최우선 ★",
    description: "지역활력·재생에너지 중심. 14회 공모전 주제 정합.",
    weights: { power: 12, temp: 5, earthquake: 8, typhoon: 5,
      price: 10, industry: 10, companies: 5, vitality: 25, renewable: 20 },
    highlight: ["regional", "esg"],
  },
];

function normalizeMinMax(values: number[]): number[] {
  const valid = values.filter((v) => Number.isFinite(v));
  if (valid.length === 0) return values.map(() => 0);
  const min = Math.min(...valid);
  const max = Math.max(...valid);
  const span = max - min || 1;
  return values.map((v) => (Number.isFinite(v) ? (v - min) / span : 0));
}

export const useScoringStore = defineStore("scoring", () => {
  const factors = ref<Factor[]>([]);
  const regions = ref<Region[]>([]);
  const weights = ref<Record<FactorKey, number>>({ ...DEFAULT_WEIGHTS });
  const compareSet = ref<Set<string>>(new Set());
  const activePresetId = ref<string | null>(null);
  const loaded = ref(false);
  const error = ref<string | null>(null);

  async function load(): Promise<void> {
    try {
      const res = await fetch(`${import.meta.env.BASE_URL}data/regions.json`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const payload = (await res.json()) as RegionsPayload;
      factors.value = payload.factors;
      regions.value = payload.regions;
      loaded.value = true;
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e);
    }
  }

  const weightSum = computed(() =>
    Object.values(weights.value).reduce((s, w) => s + w, 0),
  );

  const normalized = computed(() => {
    const out = {} as Record<FactorKey, number[]>;
    for (const f of factors.value) {
      const raw = regions.value.map((r) => r.factors[f.key]);
      const n = normalizeMinMax(raw);
      out[f.key] = f.direction === "lower_is_better" ? n.map((v) => 1 - v) : n;
    }
    return out;
  });

  const scored = computed<ScoredRegion[]>(() => {
    const sum = weightSum.value || 1;
    const result: ScoredRegion[] = regions.value.map((r, i) => {
      const componentScores = {} as Record<FactorKey, number>;
      let total = 0;
      for (const f of factors.value) {
        const v = normalized.value[f.key]?.[i] ?? 0;
        const w = weights.value[f.key] / sum;
        componentScores[f.key] = v;
        total += v * w;
      }
      return { ...r, score: total, rank: 0, componentScores };
    });
    const sorted = [...result].sort((a, b) => b.score - a.score);
    sorted.forEach((r, i) => (r.rank = i + 1));
    return result;
  });

  const topN = computed(() =>
    [...scored.value].sort((a, b) => b.score - a.score).slice(0, 10),
  );

  const topNonMetropolitan = computed(() =>
    [...scored.value]
      .filter((r) => !r.is_metropolitan)
      .sort((a, b) => b.score - a.score)
      .slice(0, 10),
  );

  function setWeight(key: FactorKey, value: number): void {
    weights.value[key] = value;
    activePresetId.value = null;
  }

  function resetWeights(): void {
    weights.value = { ...DEFAULT_WEIGHTS };
    activePresetId.value = null;
  }

  function applyPreset(id: string): void {
    const preset = SCENARIO_PRESETS.find((p) => p.id === id);
    if (!preset) return;
    weights.value = { ...preset.weights };
    activePresetId.value = id;
  }

  function toggleCompare(name: string): void {
    const next = new Set(compareSet.value);
    if (next.has(name)) next.delete(name);
    else if (next.size < 3) next.add(name);
    compareSet.value = next;
  }

  function clearCompare(): void {
    compareSet.value = new Set();
  }

  const compared = computed(() =>
    scored.value.filter((r) => compareSet.value.has(r.name)),
  );

  return {
    factors, regions, weights, weightSum, scored, topN, topNonMetropolitan,
    compareSet, compared, activePresetId,
    presets: SCENARIO_PRESETS, loaded, error,
    load, setWeight, resetWeights, applyPreset, toggleCompare, clearCompare,
  };
});
