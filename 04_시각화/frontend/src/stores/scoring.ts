import { defineStore } from "pinia";
import { computed, ref } from "vue";
import type { Factor, FactorKey, Region, RegionsPayload, ScoredRegion } from "../types";

function normalizeMinMax(values: number[]): number[] {
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  return values.map((v) => (v - min) / span);
}

export const useScoringStore = defineStore("scoring", () => {
  const factors = ref<Factor[]>([]);
  const regions = ref<Region[]>([]);
  const weights = ref<Record<FactorKey, number>>({});
  const compareSet = ref<Set<string>>(new Set());
  const loaded = ref(false);
  const error = ref<string | null>(null);

  function defaultWeightsFor(fs: Factor[]): Record<FactorKey, number> {
    const out: Record<FactorKey, number> = {};
    for (const f of fs) out[f.key] = f.default_weight;
    return out;
  }

  async function load(): Promise<void> {
    try {
      const res = await fetch(`${import.meta.env.BASE_URL}data/regions.json`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const payload = (await res.json()) as RegionsPayload;
      factors.value = payload.factors;
      regions.value = payload.regions;
      weights.value = defaultWeightsFor(payload.factors);
      loaded.value = true;
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e);
    }
  }

  const weightSum = computed(() =>
    Object.values(weights.value).reduce((s, w) => s + w, 0),
  );

  const normalized = computed(() => {
    const out: Record<FactorKey, number[]> = {};
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
        const v = normalized.value[f.key][i];
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

  function setWeight(key: FactorKey, value: number): void {
    weights.value[key] = value;
  }

  function resetWeights(): void {
    weights.value = defaultWeightsFor(factors.value);
  }

  function toggleCompare(name: string): void {
    const next = new Set(compareSet.value);
    if (next.has(name)) next.delete(name);
    else if (next.size < 3) next.add(name);
    compareSet.value = next;
  }

  const compared = computed(() =>
    scored.value.filter((r) => compareSet.value.has(r.name)),
  );

  return {
    factors,
    regions,
    weights,
    weightSum,
    scored,
    topN,
    compareSet,
    compared,
    loaded,
    error,
    load,
    setWeight,
    resetWeights,
    toggleCompare,
  };
});
