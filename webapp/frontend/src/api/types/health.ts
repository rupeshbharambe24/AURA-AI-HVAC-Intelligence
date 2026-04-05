import { BaseResponse } from "./common";

export interface HealthResponse extends BaseResponse {
  status: string;
  service: string;
  version: string;
  time_utc: string;
}

export interface HealthMetricsResponse extends BaseResponse {
  api_latency_ms: number;
  error_rate_pct: number;
  uptime_pct: number;
  active_jobs: number;
  drift_detected: boolean;
  models_in_prod: number;
}
