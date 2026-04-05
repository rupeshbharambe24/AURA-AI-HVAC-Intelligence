import { BaseResponse } from "./common";

export interface OptimizeConstraints {
  max_promos_per_year: number;
  exclude_months?: number[];
  capacity_limit_pct?: number;
  variance_limit_ratio?: number;
  chance_level?: number;
  min_mean_uplift_pct?: number;
  target_year?: number;
}

export interface PromoTemplate {
  type: string;
  discount_pct: number;
  duration_weeks: number;
}

export interface OptimizeSubmitRequest {
  constraints: OptimizeConstraints;
  candidate_promos: PromoTemplate[];
  products: string[];
}

export interface OptimizeSubmitResponse extends BaseResponse {
  job_id: string;
  status: string;
}

export interface OptimizeSummary {
  baseline_profit_mean: number;
  optimized_profit_mean: number;
  profit_improvement_pct: number;
  capacity_utilization_pct: number;
  lost_sales_pct: number;
  volatility_metric: number;
  violations: number;
}

export interface PromoCalendarItem {
  month: string;
  promos: number;
  expected_lift_pct: number;
  budget: number;
}

export interface ScheduleItem {
  product_id: string;
  month: number;
  promo_type: string;
  discount_pct: number;
  duration_days: number;
  expected_lift_pct: number;
  expected_profit_uplift: number;
}

export interface ConstraintReport {
  max_promos_ok: boolean;
  exclude_months_ok: boolean;
  capacity_ok: boolean;
  variance_ok: boolean;
  chance_ok: boolean;
  details: string[];
}

export interface OptimizeResult {
  summary: OptimizeSummary;
  promo_calendar: PromoCalendarItem[];
  schedule: ScheduleItem[];
  constraint_report: ConstraintReport;
  warnings?: string[];
}

export interface JobStatusResponse<T = any> extends BaseResponse {
  job_id: string;
  status: string;
  progress: number;
  result?: T | null;
  error?: string | null;
}
