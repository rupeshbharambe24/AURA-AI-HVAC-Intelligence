import { useMutation, useQuery } from "@tanstack/react-query";
import { apiGet, apiPost, isMockMode } from "@/lib/api-client";
import { useApiErrorToast } from "@/hooks/use-api-error";
import {
  JobStatusResponse,
  OptimizeResult,
  OptimizeSubmitRequest,
  OptimizeSubmitResponse,
} from "@/api/types/optimize";
import { mockOptimizationResult } from "@/lib/mock-data";

const mockJobs = new Map<string, OptimizeResult>();

const buildMockResult = (): OptimizeResult => {
  return {
    summary: {
      baseline_profit_mean: mockOptimizationResult.totalProfit * 0.85,
      optimized_profit_mean: mockOptimizationResult.totalProfit,
      profit_improvement_pct: mockOptimizationResult.profitIncrease,
      capacity_utilization_pct: mockOptimizationResult.capacityUtilization,
      lost_sales_pct: mockOptimizationResult.lostSales,
      volatility_metric: 0.0,
      violations: 0,
    },
    promo_calendar: mockOptimizationResult.promoCalendar.map(p => ({
      month: p.month,
      promos: p.promos,
      expected_lift_pct: p.expectedLift,
      budget: p.budget,
    })),
    schedule: [],
    constraint_report: {
      max_promos_ok: true,
      exclude_months_ok: true,
      capacity_ok: true,
      variance_ok: true,
      chance_ok: true,
      details: [],
    },
    warnings: [],
  };
};

export const useOptimizeSubmit = () => {
  const onError = useApiErrorToast();
  const mock = isMockMode();
  return useMutation({
    mutationFn: async (req: OptimizeSubmitRequest) => {
      if (mock) {
        const jobId = `mock_${Date.now()}`;
        mockJobs.set(jobId, buildMockResult());
        return { request_id: "mock", job_id: jobId, status: "completed" } as OptimizeSubmitResponse;
      }
      return apiPost<OptimizeSubmitResponse>("/optimize/submit", req);
    },
    onError,
  });
};

export const useJobStatus = (jobId?: string, enabled = true) => {
  const onError = useApiErrorToast();
  const mock = isMockMode();
  return useQuery({
    queryKey: ["jobStatus", jobId, mock],
    enabled: !!jobId && enabled,
    queryFn: async () => {
      if (!jobId) throw new Error("missing jobId");
      if (mock) {
        const result = mockJobs.get(jobId);
        return { request_id: "mock", job_id: jobId, status: "completed", progress: 1, result } as JobStatusResponse;
      }
      return apiGet<JobStatusResponse>(`/jobs/${jobId}`);
    },
    refetchInterval: (data) => {
      if (!data) return 2000;
      return data.status === "completed" || data.status === "failed" ? false : 2000;
    },
    retry: 1,
    onError,
  });
};
