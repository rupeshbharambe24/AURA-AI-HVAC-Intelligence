import { useQuery } from "@tanstack/react-query";
import { apiGet, isMockMode } from "@/lib/api-client";
import { useApiErrorToast } from "@/hooks/use-api-error";
import { HealthMetricsResponse, HealthResponse } from "@/api/types/health";
import { mockHealthMetrics } from "@/lib/mock-data";

export const useHealth = () => {
  const onError = useApiErrorToast();
  const mock = isMockMode();
  return useQuery({
    queryKey: ["health", mock],
    queryFn: async () => {
      if (mock) {
        const data: HealthResponse = {
          request_id: "mock",
          status: "ok",
          service: "scale-ai-backend",
          version: "0.1.0",
          time_utc: new Date().toISOString(),
        };
        return data;
      }
      return apiGet<HealthResponse>("/health");
    },
    staleTime: 30_000,
    retry: 1,
    onError,
  });
};

export const useHealthMetrics = () => {
  const onError = useApiErrorToast();
  const mock = isMockMode();
  return useQuery({
    queryKey: ["healthMetrics", mock],
    queryFn: async () => {
      if (mock) {
        const data: HealthMetricsResponse = {
          request_id: "mock",
          api_latency_ms: mockHealthMetrics.apiLatency,
          error_rate_pct: mockHealthMetrics.errorRate,
          uptime_pct: mockHealthMetrics.uptime,
          active_jobs: mockHealthMetrics.activeJobs,
          drift_detected: mockHealthMetrics.driftDetected,
          models_in_prod: mockHealthMetrics.modelsInProd,
        };
        return data;
      }
      return apiGet<HealthMetricsResponse>("/health/metrics");
    },
    staleTime: 30_000,
    retry: 1,
    onError,
  });
};
