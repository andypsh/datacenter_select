// 9개 지표를 동적으로 지원 — FactorKey는 더 이상 enum이 아니라 string.
// payload.factors[].key 로부터 런타임 확정.
export type FactorKey = string;

export type Direction = "lower_is_better" | "higher_is_better";

export interface Factor {
  key: FactorKey;
  label: string;
  unit: string;
  direction: Direction;
  default_weight: number;
  desc: string;
  category?: string;
}

export interface Region {
  name: string;
  lat: number;
  lng: number;
  factors: Record<FactorKey, number>;
}

export interface RegionsPayload {
  version: number;
  source: string | string[];
  factors: Factor[];
  regions: Region[];
}

export interface ScoredRegion extends Region {
  score: number;
  rank: number;
  componentScores: Record<FactorKey, number>;
}
