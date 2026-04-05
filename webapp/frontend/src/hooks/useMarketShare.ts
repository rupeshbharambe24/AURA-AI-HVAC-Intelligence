import { useMutation, useQuery } from "@tanstack/react-query";
import { ApiError, apiGet, apiPost, apiUpload, isMockMode } from "@/lib/api-client";
import { useApiErrorToast } from "@/hooks/use-api-error";
import {
  MarketShareBatchResponse,
  MarketShareMetricsResponse,
  MarketShareOptionsResponse,
  MarketShareRequest,
  MarketShareResponse,
} from "@/api/types/marketShare";
import { mockMarketShareData, mockNewsTimeline, mockProducts } from "@/lib/mock-data";

const mockOptions: MarketShareOptionsResponse = {
  request_id: "mock",
  products: mockProducts,
  supported_horizons_months: [3, 4, 5, 6],
  default_as_of_date: new Date().toISOString().slice(0, 10),
};

const buildMockPredict = (req: MarketShareRequest): MarketShareResponse => {
  const forecast = mockMarketShareData.slice(0, req.horizon_months).map(row => ({
    month: row.month,
    our_share: row.ourShare,
    lower: row.ourShare - 1.5,
    upper: row.ourShare + 1.5,
  }));
  return {
    request_id: "mock",
    product_id: req.product_id,
    as_of_date: req.as_of_date || new Date().toISOString().slice(0, 10),
    horizon_months: req.horizon_months,
    forecast,
    alerts: [{ type: "watch", message: "Mock data", severity: "low" }],
    news_timeline: mockNewsTimeline.map(n => ({
      date: n.date,
      headline: n.headline,
      sentiment: n.sentiment,
      tags: [],
      relevance: Math.abs(n.impact),
    })),
    drivers: [
      { name: "Competitor News", importance_pct: 32 },
      { name: "Pricing Changes", importance_pct: 24 },
    ],
    metrics: { mae_pct: 2.4, rmse_pct: 3.1, mape_pct: 4.6, coverage_pct: 92 },
    warnings: [],
  };
};

export const useMarketShareOptions = () => {
  const onError = useApiErrorToast();
  const mock = isMockMode();
  return useQuery({
    queryKey: ["marketShareOptions", mock],
    queryFn: async () => {
      if (mock) return mockOptions;
      return apiGet<MarketShareOptionsResponse>("/market-share/options");
    },
    staleTime: 60_000,
    retry: 1,
    onError,
  });
};

export const useMarketSharePredict = () => {
  const onError = useApiErrorToast();
  const mock = isMockMode();
  return useMutation({
    mutationFn: async (req: MarketShareRequest) => {
      if (mock) return buildMockPredict(req);
      return apiPost<MarketShareResponse>("/market-share/predict", req);
    },
    onError,
  });
};

export const useMarketShareBatch = () => {
  const onError = useApiErrorToast();
  const mock = isMockMode();
  return useMutation({
    mutationFn: async (file: File) => {
      if (mock) {
        const mockResult = buildMockPredict({ product_id: "mock", horizon_months: 3 });
        return { request_id: "mock", results: [mockResult] } as MarketShareBatchResponse;
      }
      const form = new FormData();
      form.append("file", file);
      return apiUpload<MarketShareBatchResponse>("/market-share/batch", form);
    },
    onError,
  });
};

export const useMarketShareMetrics = () => {
  const onError = useApiErrorToast();
  const mock = isMockMode();
  return useQuery({
    queryKey: ["marketShareMetrics", mock],
    queryFn: async () => {
      if (mock) {
        return { request_id: "mock", metrics: [{ label: "MAPE", value: "4.6%" }] } as MarketShareMetricsResponse;
      }
      try {
        return await apiGet<MarketShareMetricsResponse>("/market-share/metrics");
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) {
          return null as unknown as MarketShareMetricsResponse;
        }
        throw err;
      }
    },
    staleTime: 60_000,
    retry: 1,
    onError,
  });
};
