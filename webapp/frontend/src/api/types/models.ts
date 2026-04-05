import { BaseResponse } from "./common";

export interface ModelRegistryEntry {
  id: string;
  name: string;
  version: string;
  alias: string;
  owner?: string;
  status: string;
  training_period?: string;
  dataset_hash?: string;
  key_metric?: string;
  bundle_filename?: string;
  notes?: string;
}

export interface MetricEntry {
  label: string;
  value: string;
}

export interface VersionEntry {
  version: string;
  date?: string;
  run_id?: string;
  note?: string;
}

export interface ExplainabilityEntry {
  feature: string;
  importance: number;
}

export interface ModelListResponse extends BaseResponse {
  models: ModelRegistryEntry[];
  warnings?: string[];
}

export interface ModelDetailResponse extends BaseResponse {
  model: ModelRegistryEntry;
  warnings?: string[];
}

export interface ModelMetricsResponse extends BaseResponse {
  metrics: MetricEntry[];
  warnings?: string[];
}

export interface ModelVersionsResponse extends BaseResponse {
  versions: VersionEntry[];
  warnings?: string[];
}

export interface ModelExplainabilityResponse extends BaseResponse {
  explainability: ExplainabilityEntry[];
  warnings?: string[];
}

export interface ExperimentEntry {
  id: string;
  model: string;
  name: string;
  owner: string;
  date: string;
  mape?: number | null;
  rmse?: number | null;
  f1?: number | null;
  status: string;
}

export interface ExperimentsResponse extends BaseResponse {
  experiments: ExperimentEntry[];
  warnings?: string[];
}
