import { BaseResponse } from "./common";

export interface ForecastOptionsResponse extends BaseResponse {
  products: string[];
  aps_list: string[];
  max_horizon_months: number;
}

export interface ForecastRequest {
  product_id: string;
  aps: string;
  horizon_months: number;
  cutoff_date?: string | null;
  scenarios?: Record<string, number> | null;
  include_actuals?: boolean;
  include_explain?: boolean;
}

export interface ForecastItem {
  date: string;
  actual?: number | null;
  predicted: number;
  lower?: number | null;
  upper?: number | null;
  drivers: string[];
}

export interface ForecastMetrics {
  mape?: number | null;
  rmse?: number | null;
  coverage_95?: number | null;
  bias_pct?: number | null;
}

export interface ForecastResponse extends BaseResponse {
  model_id: string;
  product_id: string;
  aps: string;
  cutoff_date: string;
  forecast: ForecastItem[];
  metrics: ForecastMetrics;
  explain?: {
    local?: Array<Record<string, number>>;
    global?: Array<Record<string, number>>;
  } | null;
  applied_scenarios: Record<string, Record<string, number>>;
  warnings?: string[];
}

export interface ForecastModelMetricsResponse extends BaseResponse {
  metrics: { label: string; value: string }[];
  warnings?: string[];
}
