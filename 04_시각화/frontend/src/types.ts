export type FactorKey =
  | "power"
  | "temp"
  | "earthquake"
  | "typhoon"
  | "price"
  | "industry"
  | "companies"
  | "vitality"
  | "renewable";

export type Direction = "lower_is_better" | "higher_is_better";

export type FactorCategory = "power" | "safety" | "cost" | "industry" | "regional" | "esg";

export interface Factor {
  key: FactorKey;
  label: string;
  unit: string;
  direction: Direction;
  desc: string;
  category: FactorCategory;
  source: string;
  isMotie: boolean;
}

export interface Region {
  name: string;
  sgg_code?: string;
  lat: number;
  lng: number;
  factors: Record<FactorKey, number>;
  is_population_decline?: boolean;
  is_metropolitan?: boolean;
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

export interface ScenarioPreset {
  id: string;
  label: string;
  description: string;
  weights: Record<FactorKey, number>;
  highlight?: FactorCategory[];
}
