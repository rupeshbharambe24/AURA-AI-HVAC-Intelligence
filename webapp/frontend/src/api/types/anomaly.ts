import { BaseResponse } from "./common";

export interface Evidence {
  type: string;
  strength: number;
  detail: string;
  ref?: string | null;
}

export interface AnomalyThresholds {
  point: number;
  pattern: number;
  trend: number;
}

export interface AnomalyDetectRequest {
  product_id: string;
  aps: string;
  date_range?: [string, string] | null;
  thresholds?: AnomalyThresholds | null;
  threshold?: number | null;
  include_explanations?: boolean;
}

export interface AnomalySeriesItem {
  date: string;
  demand: number;
  expected: number;
  residual: number;
  anomaly_score: number;
  is_anomaly: boolean;
  anomaly_family?: string | null;
  anomaly_type?: string | null;
  root_cause?: string | null;
  explanation?: string | null;
  evidence: Evidence[];
}

export interface AnomalySummary {
  total: number;
  anomalies: number;
  by_family: Record<string, number>;
}

export interface AnomalyDetectResponse extends BaseResponse {
  product_id: string;
  aps: string;
  baseline_method: string;
  effective_thresholds: AnomalyThresholds;
  series: AnomalySeriesItem[];
  summary: AnomalySummary;
  warnings?: string[];
}

export interface AnomalyOptionsResponse extends BaseResponse {
  products: string[];
  aps_list: string[];
  default_thresholds: AnomalyThresholds;
}

export interface AnomalyBatchResponse extends BaseResponse {
  results?: AnomalyDetectResponse[];
  job_id?: string;
  status?: string;
  warnings?: string[];
}

export interface AnomalyMetricsResponse extends BaseResponse {
  metrics: { label: string; value: string }[];
  warnings?: string[];
}
