import { useMutation, useQuery } from "@tanstack/react-query";
import { ApiError, apiGet, apiPost, apiUpload, isMockMode } from "@/lib/api-client";
import { useApiErrorToast } from "@/hooks/use-api-error";
import {
  AnomalyBatchResponse,
  AnomalyDetectRequest,
  AnomalyDetectResponse,
  AnomalyMetricsResponse,
  AnomalyOptionsResponse,
} from "@/api/types/anomaly";
import { mockAnomalyData, mockProducts } from "@/lib/mock-data";

const buildMockDetect = (req: AnomalyDetectRequest): AnomalyDetectResponse => {
  const series = mockAnomalyData.map(row => ({
    date: row.date,
    demand: row.value,
    expected: row.expected,
    residual: row.value - row.expected,
    anomaly_score: row.score,
    is_anomaly: row.isAnomaly,
    anomaly_family: row.isAnomaly ? "demand_spike" : null,
    anomaly_type: row.isAnomaly ? "spike_promo" : null,
    root_cause: row.isAnomaly ? "Promo-driven spike" : null,
    explanation: row.isAnomaly ? "Promo overlap detected" : null,
    evidence: row.isAnomaly ? [{ type: "promotion", strength: 0.7, detail: "Promotion active", ref: null }] : [],
  }));
  return {
    request_id: "mock",
    product_id: req.product_id,
    aps: req.aps,
    baseline_method: "mock",
    effective_thresholds: { point: 3, pattern: 0.5, trend: 1.5 },
    series,
    summary: {
      total: series.length,
      anomalies: series.filter(s => s.is_anomaly).length,
      by_family: { demand_spike: series.filter(s => s.is_anomaly).length },
    },
    warnings: [],
  };
};

export const useAnomalyOptions = () => {
  const onError = useApiErrorToast();
  const mock = isMockMode();
  return useQuery({
    queryKey: ["anomalyOptions", mock],
    queryFn: async () => {
      if (mock) {
        return { request_id: "mock", products: mockProducts, aps_list: ["APS-North", "APS-South"], default_thresholds: { point: 3, pattern: 0.5, trend: 1.5 } } as AnomalyOptionsResponse;
      }
      return apiGet<AnomalyOptionsResponse>("/anomaly/options");
    },
    staleTime: 60_000,
    retry: 1,
    onError,
  });
};

export const useAnomalyDetect = () => {
  const onError = useApiErrorToast();
  const mock = isMockMode();
  return useMutation({
    mutationFn: async (req: AnomalyDetectRequest) => {
      if (mock) return buildMockDetect(req);
      return apiPost<AnomalyDetectResponse>("/anomaly/detect", req);
    },
    onError,
  });
};

export const useAnomalyBatch = () => {
  const onError = useApiErrorToast();
  const mock = isMockMode();
  return useMutation({
    mutationFn: async (file: File) => {
      if (mock) {
        const mockResult = buildMockDetect({ product_id: "mock", aps: "ALL" });
        return { request_id: "mock", results: [mockResult], warnings: [] } as AnomalyBatchResponse;
      }
      const form = new FormData();
      form.append("file", file);
      return apiUpload<AnomalyBatchResponse>("/anomaly/batch", form);
    },
    onError,
  });
};

export const useAnomalyMetrics = () => {
  const onError = useApiErrorToast();
  const mock = isMockMode();
  return useQuery({
    queryKey: ["anomalyMetrics", mock],
    queryFn: async () => {
      if (mock) {
        return { request_id: "mock", metrics: [{ label: "F1", value: "0.94" }] } as AnomalyMetricsResponse;
      }
      try {
        return await apiGet<AnomalyMetricsResponse>("/anomaly/metrics");
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) {
          return null as unknown as AnomalyMetricsResponse;
        }
        throw err;
      }
    },
    staleTime: 60_000,
    retry: 1,
    onError,
  });
};
