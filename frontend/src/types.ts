export type FactorKey = "temp" | "earthquake" | "typhoon" | "companies" | "price";

export type Direction = "lower_is_better" | "higher_is_better";

export interface Factor {
  key: FactorKey;
  label: string;
  unit: string;
  direction: Direction;
  desc: string;
}

export interface Region {
  name: string;
  lat: number;
  lng: number;
  factors: Record<FactorKey, number>;
}

export interface RegionsPayload {
  version: number;
  source: string;
  factors: Factor[];
  regions: Region[];
}

export interface ScoredRegion extends Region {
  score: number;
  rank: number;
  componentScores: Record<FactorKey, number>;
}
