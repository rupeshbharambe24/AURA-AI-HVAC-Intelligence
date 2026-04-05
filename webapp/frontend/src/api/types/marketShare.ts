import { BaseResponse } from "./common";

export interface MarketShareOptionsResponse extends BaseResponse {
  products: string[];
  supported_horizons_months: number[];
  default_as_of_date: string;
}

export interface MarketShareRequest {
  product_id: string;
  horizon_months: number;
  as_of_date?: string | null;
  news_filters?: Record<string, boolean> | null;
}

export interface MarketShareForecastItem {
  month: string;
  our_share: number;
  lower?: number | null;
  upper?: number | null;
}

export interface MarketShareAlert {
  type: string;
  message: string;
  severity: string;
}

export interface MarketShareNewsItem {
  date: string;
  headline: string;
  sentiment: string;
  tags: string[];
  relevance: number;
}

export interface MarketShareDriver {
  name: string;
  importance_pct: number;
}

export interface MarketShareMetrics {
  mae_pct?: number | null;
  rmse_pct?: number | null;
  mape_pct?: number | null;
  coverage_pct?: number | null;
}

export interface MarketShareResponse extends BaseResponse {
  product_id: string;
  as_of_date: string;
  horizon_months: number;
  forecast: MarketShareForecastItem[];
  alerts: MarketShareAlert[];
  news_timeline: MarketShareNewsItem[];
  drivers: MarketShareDriver[];
  metrics: MarketShareMetrics;
  warnings?: string[];
}

export interface MarketShareBatchResponse extends BaseResponse {
  results?: MarketShareResponse[];
  job_id?: string;
  status?: string;
  warnings?: string[];
}

export interface MarketShareMetricsResponse extends BaseResponse {
  metrics: { label: string; value: string }[];
  warnings?: string[];
}
